"""
场景领域路由

场景化 API 路由定义
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, UploadFile, File

from src.scenarios.schemas import (
    ScenarioTemplateRequest,
    ScenarioTemplateResponse,
    ScenarioExecuteRequest,
    ScenarioExecuteResponse,
    Text2ImgRequest,
    Img2ImgRequest,
)
from src.scenarios.service import (
    save_workflow_template,
    get_workflow_template,
    list_workflow_templates,
    delete_workflow_template,
    execute_scenario_template,
    execute_text2img_scenario,
    execute_img2img_scenario,
)
from src.scenarios.exceptions import (
    TemplateNotFoundError,
    TemplateValidationError,
    TemplateExecutionError,
    ScenarioNotFoundError,
)
from src.scenarios.utils import (
    parse_workflow_api_file,
    generate_random_seed,
    infer_param_mappings_from_workflow,
)


# 创建路由器
router = APIRouter(prefix="/scenarios", tags=["scenarios"])

# ========== 模板管理路由 ==========

@router.post(
    "/templates",
    response_model=ScenarioTemplateResponse,
    summary="创建 workflow 模板",
    description="上传 workflow 并创建可复用的模板",
)
async def create_template(request: ScenarioTemplateRequest) -> ScenarioTemplateResponse:
    """
    创建 workflow 模板
    """
    try:
        result = await save_workflow_template(
            name=request.name,
            workflow=request.workflow,
            param_mappings=request.param_mappings,
            description=request.description,
        )

        return ScenarioTemplateResponse(
            id=result["id"],
            name=request.name,
            description=request.description,
            created_at=result["created_at"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "TEMPLATE_CREATE_ERROR",
                "message": f"创建模板失败: {str(e)}"
            }
        )


@router.post(
    "/templates/upload",
    summary="上传 workflow 文件创建模板",
    description="上传 ComfyUI API 格式的 workflow 文件并创建模板",
)
async def upload_template_file(
    name: str,
    file: UploadFile = File(..., description="Workflow JSON 文件"),
    auto_infer: bool = True,
) -> Dict[str, Any]:
    """
    上传 workflow 文件创建模板
    """
    try:
        # 读取文件内容
        content = await file.read()
        workflow_data = parse_workflow_api_file(content.decode("utf-8"))

        # 自动推断参数映射
        param_mappings = {}
        if auto_infer:
            param_mappings = infer_param_mappings_from_workflow(workflow_data)

        # 创建模板
        result = await save_workflow_template(
            name=name,
            workflow=workflow_data,
            param_mappings=param_mappings,
            description=f"从文件 {file.filename} 导入",
        )

        return {
            "id": result["id"],
            "name": name,
            "param_mappings": param_mappings,
            "message": "模板创建成功",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_FILE",
                "message": str(e)
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "TEMPLATE_UPLOAD_ERROR",
                "message": f"上传文件失败: {str(e)}"
            }
        )


@router.get(
    "/templates",
    summary="获取所有模板",
    description="列出所有已保存的 workflow 模板",
)
async def get_templates() -> List[Dict[str, Any]]:
    """
    获取所有模板
    """
    try:
        templates = await list_workflow_templates()
        return templates

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "TEMPLATES_LIST_ERROR",
                "message": f"获取模板列表失败: {str(e)}"
            }
        )


@router.get(
    "/templates/{template_id}",
    summary="获取模板详情",
    description="获取指定模板的详细信息",
)
async def get_template_detail(template_id: str) -> Dict[str, Any]:
    """
    获取模板详情
    """
    try:
        template = await get_workflow_template(template_id)
        return template

    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TEMPLATE_NOT_FOUND",
                "message": f"模板不存在: {template_id}"
            }
        )


@router.delete(
    "/templates/{template_id}",
    summary="删除模板",
    description="删除指定的 workflow 模板",
)
async def delete_template(template_id: str) -> Dict[str, Any]:
    """
    删除模板
    """
    try:
        await delete_workflow_template(template_id)
        return {
            "success": True,
            "message": f"模板 {template_id} 已删除"
        }

    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TEMPLATE_NOT_FOUND",
                "message": f"模板不存在: {template_id}"
            }
        )


# ========== 场景执行路由 ==========

@router.post(
    "/execute",
    response_model=ScenarioExecuteResponse,
    summary="执行场景模板",
    description="通过模板 ID 执行场景",
)
async def execute_scenario(request: ScenarioExecuteRequest) -> ScenarioExecuteResponse:
    """
    执行场景模板
    """
    try:
        if request.scenario_type:
            # 使用预定义场景
            if request.scenario_type == "text2img":
                result = await execute_text2img_scenario(
                    params=request.params,
                    client_id=request.client_id
                )
            elif request.scenario_type == "img2img":
                result = await execute_img2img_scenario(
                    params=request.params,
                    client_id=request.client_id
                )
            else:
                raise ScenarioNotFoundError(request.scenario_type)

            return ScenarioExecuteResponse(
                prompt_id=result["prompt_id"],
                scenario_type=request.scenario_type,
                client_id=request.client_id,
            )

        elif request.template_id:
            # 使用自定义模板
            result = await execute_scenario_template(
                template_id=request.template_id,
                params=request.params,
                client_id=request.client_id
            )

            return ScenarioExecuteResponse(
                prompt_id=result["prompt_id"],
                template_id=request.template_id,
                client_id=request.client_id,
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_REQUEST",
                    "message": "必须指定 template_id 或 scenario_type"
                }
            )

    except TemplateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TEMPLATE_NOT_FOUND",
                "message": f"模板不存在: {request.template_id}"
            }
        )

    except ScenarioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SCENARIO_NOT_FOUND",
                "message": f"场景不存在: {request.scenario_type}"
            }
        )

    except TemplateExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "EXECUTION_ERROR",
                "message": e.message
            }
        )


# ========== 预定义场景路由 ==========

@router.post(
    "/text2img",
    summary="文生图场景",
    description="通过文本提示生成图片",
)
async def text2img(request: Text2ImgRequest) -> Dict[str, Any]:
    """
    文生图场景
    """
    try:
        # 处理随机种子
        params = request.dict()
        if params["seed"] == -1:
            params["seed"] = generate_random_seed()

        result = await execute_text2img_scenario(
            params=params,
            client_id=request.client_id
        )

        return {
            "prompt_id": result["prompt_id"],
            "scenario_type": "text2img",
            "message": "文生图任务已提交",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "TEXT2IMG_ERROR",
                "message": f"文生图失败: {str(e)}"
            }
        )


@router.post(
    "/img2img",
    summary="图生图场景",
    description="基于输入图片生成新图片",
)
async def img2img(request: Img2ImgRequest) -> Dict[str, Any]:
    """
    图生图场景
    """
    try:
        # 处理随机种子
        params = request.dict()
        if params["seed"] == -1:
            params["seed"] = generate_random_seed()

        result = await execute_img2img_scenario(
            params=params,
            client_id=request.client_id
        )

        return {
            "prompt_id": result["prompt_id"],
            "scenario_type": "img2img",
            "message": "图生图任务已提交",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "IMG2IMG_ERROR",
                "message": f"图生图失败: {str(e)}"
            }
        )
