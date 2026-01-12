"""
工作流领域路由

工作流 API 路由定义
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

from src.workflows.schemas import (
    WorkflowSubmitRequest,
    WorkflowSubmitResponse,
    WorkflowHistoryResponse,
    WorkflowInterruptRequest,
)
from src.workflows.service import (
    submit_workflow_to_comfyui,
    interrupt_workflow,
    get_workflow_history,
    get_generated_images,
)
from src.exceptions import (
    WorkflowValidationError,
    ComfyUIConnectionError,
)
from src.workflows.exceptions import WorkflowNotFoundError


# 创建路由器
router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post(
    "/submit",
    response_model=WorkflowSubmitResponse,
    summary="提交工作流",
    description="提交工作流到 ComfyUI 并立即返回任务 ID（异步）",
)
async def submit_workflow(request: WorkflowSubmitRequest) -> WorkflowSubmitResponse:
    """
    提交工作流
    """
    try:
        # 提交工作流到 ComfyUI
        prompt_id = await submit_workflow_to_comfyui(
            request.workflow,
            request.client_id
        )

        # 构建响应
        return WorkflowSubmitResponse(
            prompt_id=prompt_id,
            number=0,  # ComfyUI 返回的 number
            client_id=request.client_id
        )

    except WorkflowValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": e.code,
                "message": e.message,
                "detail": e.detail
            }
        )

    except ComfyUIConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": e.code,
                "message": e.message
            }
        )


@router.get(
    "/{prompt_id}/history",
    response_model=WorkflowHistoryResponse,
    summary="获取工作流历史",
    description="获取指定工作流的执行历史和输出结果",
)
async def get_workflow_history_endpoint(prompt_id: str) -> WorkflowHistoryResponse:
    """
    获取工作流历史
    """
    try:
        history = await get_workflow_history(prompt_id)

        # 如果没有历史记录，返回 404
        if not history:
            raise WorkflowNotFoundError(prompt_id)

        # 提取输出结果
        outputs = history.get("outputs", {})

        return WorkflowHistoryResponse(
            prompt_id=prompt_id,
            outputs=outputs,
            status="completed"
        )

    except WorkflowNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "WORKFLOW_NOT_FOUND",
                "message": f"工作流 {prompt_id} 不存在或尚未完成"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"获取历史记录失败: {str(e)}"
            }
        )


@router.get(
    "/{prompt_id}/images",
    summary="获取工作流生成的图片",
    description="获取指定工作流生成的所有图片信息",
)
async def get_workflow_images_endpoint(prompt_id: str) -> Dict[str, Any]:
    """
    获取工作流生成的图片
    """
    try:
        images = await get_generated_images(prompt_id)

        if not images:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "NO_IMAGES",
                    "message": f"工作流 {prompt_id} 没有生成图片"
                }
            )

        return {
            "prompt_id": prompt_id,
            "count": len(images),
            "images": images
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"获取图片失败: {str(e)}"
            }
        )


@router.post(
    "/interrupt",
    summary="中断工作流执行",
    description="中断指定工作流或所有工作流的执行",
)
async def interrupt_workflow_endpoint(request: WorkflowInterruptRequest) -> Dict[str, Any]:
    """
    中断工作流执行
    """
    try:
        result = await interrupt_workflow(request.prompt_id)

        return {
            "success": True,
            "message": "工作流已中断" if request.prompt_id else "所有工作流已中断",
            "detail": result
        }

    except ComfyUIConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": e.code,
                "message": e.message
            }
        )
