"""
工作流路由
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from app.internal.comfyui import comfyui_client
from app.schemas import ApiResponse


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


@router.get("/{prompt_id}/history", summary="获取工作流历史", response_model=ApiResponse)
async def get_history(prompt_id: str) -> ApiResponse:
    """获取工作流执行历史"""
    history = await comfyui_client.get_history(prompt_id)
    if not history:
        raise HTTPException(status_code=404, detail="工作流不存在或者工作流尚未完成工作")

    return ApiResponse.success(
        data={"prompt_id": prompt_id, **history},
        message="获取历史记录成功"
    )


@router.post("/interrupt", summary="中断工作流", response_model=ApiResponse)
async def interrupt_workflow(request: Dict[str, Any]) -> ApiResponse:
    """
    中断工作流执行

    请求体 - 全局中断（中断所有正在运行的任务）:
    ```json
    {}
    ```

    请求体 - 指定中断（只中断指定的任务）:
    ```json
    {
        "prompt_id": "prompt_id_here"
    }
    ```
    """
    prompt_id = request.get("prompt_id")
    result = await comfyui_client.interrupt(prompt_id)
    return ApiResponse.success(
        data=result,
        message=f"{prompt_id}: 工作流已中断"
    )
