"""
场景路由

为每个 workflow 提供专门的简化接口
"""

from fastapi import APIRouter

from app.internal.comfyui import comfyui_client
from app.internal.utils import apply_params_to_workflow
from app.internal.workflow_handlers import load_cpu_quickly_workflow
from app.schemas import ApiResponse, ResponseCode
from pydantic import BaseModel


router = APIRouter(prefix="/scenarios", tags=["scenarios"])


# ========== 请求模型 ==========

class Img2ImgRequest(BaseModel):
    """图生图请求 - 针对 cpu quickly.json workflow"""
    prompt: str
    negative_prompt: str = ""
    input_image: str = "your_image_here.png"


# ========== CPU Quickly Workflow 接口 ==========

@router.post("/cpu_quickly", summary="CPU Quickly 图生图", response_model=ApiResponse)
async def cpu_quickly(request: Img2ImgRequest):
    """
    针对 cpu quickly.json workflow 的简化接口

    用户只需传入:
    - prompt: 提示词
    - negative_prompt: 负面提示词
    - input_image: 输入图片文件名
    """
    try:
        # 加载 workflow 模板（使用专用处理器）
        workflow = load_cpu_quickly_workflow()

        # 定义参数映射
        param_mappings = {
            "prompt": {"node_id": "3", "field": "inputs.text"},
            "negative_prompt": {"node_id": "4", "field": "inputs.text"},
            "input_image": {"node_id": "2", "field": "inputs.image"},
        }

        # 构建参数
        params = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "input_image": request.input_image,
        }

        # 应用参数到 workflow
        final_workflow = apply_params_to_workflow(workflow, params, param_mappings)

        # 提交到 ComfyUI
        prompt_id = await comfyui_client.submit_prompt(final_workflow, None)

        return ApiResponse.success(
            data={
                "prompt_id": prompt_id,
                "scenario": "cpu_quickly"
            },
            message="图生图任务已提交"
        )

    except FileNotFoundError:
        return ApiResponse.error(
            code=ResponseCode.NOT_FOUND,
            message="Workflow 模板文件不存在"
        )
    except Exception as e:
        return ApiResponse.error(
            code=ResponseCode.INTERNAL_ERROR,
            message=f"执行失败: {str(e)}"
        )
