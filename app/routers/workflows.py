"""
工作流路由
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

from app.internal.comfyui import comfyui_client
from app.exceptions import WorkflowValidationError, ComfyUIConnectionError
from app.schemas import ApiResponse, ResponseCode


router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/submit", summary="提交工作流", response_model=ApiResponse)
async def submit_workflow(request: Dict[str, Any]) -> ApiResponse:
    """
    提交工作流到 ComfyUI

    请求体:
    ```json
    {
        "workflow": {...},
        "client_id": "optional_client_id"
    }
    ```
    """
    try:
        workflow = request.get("workflow", {})
        client_id = request.get("client_id")

        prompt_id = await comfyui_client.submit_prompt(workflow, client_id)

        return ApiResponse.success(
            data={
                "prompt_id": prompt_id,
                "client_id": client_id
            },
            message="工作流已提交"
        )

    except ComfyUIConnectionError as e:
        return ApiResponse.error(
            code=e.code,
            message=e.message
        )


@router.get("/{prompt_id}/history", summary="获取工作流历史", response_model=ApiResponse)
async def get_history(prompt_id: str) -> ApiResponse:
    """获取工作流执行历史"""
    try:
        history = await comfyui_client.get_history(prompt_id)
        if not history:
            return ApiResponse.error(
                code=ResponseCode.NOT_FOUND,
                message="工作流不存在或者工作流尚未完成工作"
            )
        return ApiResponse.success(
            data={"prompt_id": prompt_id, **history},
            message="获取历史记录成功"
        )
    except Exception as e:
        return ApiResponse.error(
            code=ResponseCode.INTERNAL_ERROR,
            message=f"获取历史记录失败: {str(e)}"
        )


@router.post("/interrupt", summary="中断工作流", response_model=ApiResponse)
async def interrupt_workflow(request: Dict[str, Any]) -> ApiResponse:
    """中断工作流执行"""
    try:
        prompt_id = request.get("prompt_id")
        result = await comfyui_client.interrupt(prompt_id)
        return ApiResponse.success(
            data={"detail": result},
            message="工作流已中断"
        )
    except Exception as e:
        return ApiResponse.error(
            code=ResponseCode.INTERNAL_ERROR,
            message=f"中断工作流失败: {str(e)}"
        )
