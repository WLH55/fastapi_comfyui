"""
场景领域数据模型
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class TemplateParamDefinition(BaseModel):
    """
    模板参数定义

    Attributes:
        name: 参数名称
        type: 参数类型
        description: 参数描述
        default_value: 默认值
        required: 是否必需
        node_id: 对应的节点 ID
        field: 对应的字段路径
    """

    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型")
    description: str = Field("", description="参数描述")
    default_value: Any = Field(None, description="默认值")
    required: bool = Field(True, description="是否必需")
    node_id: str = Field(..., description="对应的节点 ID")
    field: str = Field(..., description="对应的字段路径")


class ScenarioTemplateRequest(BaseModel):
    """
    场景模板创建请求

    Attributes:
        name: 模板名称
        description: 模板描述
        workflow: workflow JSON
        param_mappings: 参数映射配置
    """

    name: str = Field(..., description="模板名称", min_length=1, max_length=100)
    description: str = Field("", description="模板描述")
    workflow: Dict[str, Any] = Field(..., description="workflow JSON")
    param_mappings: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="参数映射配置 {参数名: {node_id, field}}"
    )


class ScenarioTemplateResponse(BaseModel):
    """
    场景模板响应
    """

    id: str = Field(..., description="模板 ID")
    name: str = Field(..., description="模板名称")
    description: str = Field("", description="模板描述")
    param_definitions: List[TemplateParamDefinition] = Field(
        default_factory=list,
        description="参数定义列表"
    )
    created_at: str = Field(..., description="创建时间")


class TemplateParamRequest(BaseModel):
    """
    模板参数请求

    Attributes:
        params: 参数值字典
        client_id: 客户端 ID（可选）
    """

    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="参数值字典"
    )
    client_id: Optional[str] = Field(None, description="客户端 ID")


class ScenarioExecuteRequest(BaseModel):
    """
    场景执行请求

    Attributes:
        template_id: 模板 ID（可选，使用预定义场景时不传）
        scenario_type: 场景类型（可选，用于预定义场景）
        params: 参数字典
        client_id: 客户端 ID（可选）
    """

    template_id: Optional[str] = Field(None, description="模板 ID")
    scenario_type: Optional[str] = Field(None, description="预定义场景类型")
    params: Dict[str, Any] = Field(default_factory=dict, description="参数字典")
    client_id: Optional[str] = Field(None, description="客户端 ID")


class ScenarioExecuteResponse(BaseModel):
    """
    场景执行响应
    """

    prompt_id: str = Field(..., description="任务 ID")
    template_id: Optional[str] = Field(None, description="使用的模板 ID")
    scenario_type: Optional[str] = Field(None, description="场景类型")
    client_id: Optional[str] = Field(None, description="客户端 ID")


# ========== 预定义场景请求 ==========

class Text2ImgRequest(BaseModel):
    """
    文生图场景请求
    """

    prompt: str = Field(..., description="提示词")
    negative_prompt: str = Field("", description="负面提示词")
    width: int = Field(1024, description="图片宽度", ge=64, le=4096)
    height: int = Field(1024, description="图片高度", ge=64, le=4096)
    seed: int = Field(-1, description="随机种子，-1 表示随机")
    steps: int = Field(20, description="采样步数", ge=1, le=150)
    cfg: float = Field(7.0, description="CFG 强度", ge=1.0, le=30.0)
    sampler_name: str = Field("euler", description="采样器名称")
    scheduler: str = Field("normal", description="调度器名称")
    client_id: Optional[str] = Field(None, description="客户端 ID")


class Img2ImgRequest(BaseModel):
    """
    图生图场景请求
    """

    input_image: str = Field(..., description="输入图片文件名")
    prompt: str = Field(..., description="提示词")
    negative_prompt: str = Field("", description="负面提示词")
    denoise: float = Field(0.75, description="去噪强度", ge=0.0, le=1.0)
    seed: int = Field(-1, description="随机种子，-1 表示随机")
    steps: int = Field(20, description="采样步数", ge=1, le=150)
    cfg: float = Field(7.0, description="CFG 强度", ge=1.0, le=30.0)
    client_id: Optional[str] = Field(None, description="客户端 ID")


class UpscaleRequest(BaseModel):
    """
    图像放大场景请求
    """

    input_image: str = Field(..., description="输入图片文件名")
    scale_factor: float = Field(2.0, description="放大倍数", ge=1.0, le=4.0)
    model: str = Field("upscale_model", description="放大模型名称")
    client_id: Optional[str] = Field(None, description="客户端 ID")
