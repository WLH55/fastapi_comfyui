"""
场景领域常量
"""

from enum import Enum


class PredefinedScenario(str, Enum):
    """预定义场景枚举"""

    TEXT2IMG = "text2img"
    IMG2IMG = "img2img"
    IMG2VID = "img2vid"
    UPSCALE = "upscale"


class NodeType(str, Enum):
    """常用节点类型枚举"""

    # 文本相关节点
    CLIP_TEXT_ENCODE = "CLIPTextEncode"
    CONDITIONING = "Conditioning"

    # 采样相关节点
    KSampler = "KSampler"
    KSamplerAdvanced = "KSamplerAdvanced"

    # 图像相关节点
    VAEDecode = "VAEDecode"
    VAEEncode = "VAEEncode"
    LoadImage = "LoadImage"
    SaveImage = "SaveImage"
    EmptyLatentImage = "EmptyLatentImage"

    # 模型加载节点
    CheckpointLoaderSimple = "CheckpointLoaderSimple"
    LoraLoader = "LoraLoader"


class TemplateParamType(str, Enum):
    """模板参数类型"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    IMAGE = "image"
    SEED = "seed"


# 预定义场景模板存储路径
TEMPLATES_DIR = "src/scenarios/templates"

# 默认参数映射配置
DEFAULT_PARAM_MAPPINGS = {
    # 文生图场景默认映射
    PredefinedScenario.TEXT2IMG: {
        "prompt": {"node_type": "CLIPTextEncode", "field": "text"},
        "negative_prompt": {"node_type": "CLIPTextEncode", "field": "text"},
        "width": {"node_type": "EmptyLatentImage", "field": "width"},
        "height": {"node_type": "EmptyLatentImage", "field": "height"},
        "seed": {"node_type": "KSampler", "field": "seed"},
        "steps": {"node_type": "KSampler", "field": "steps"},
        "cfg": {"node_type": "KSampler", "field": "cfg"},
        "sampler_name": {"node_type": "KSampler", "field": "sampler_name"},
        "scheduler": {"node_type": "KSampler", "field": "scheduler"},
    },
    # 图生图场景默认映射
    PredefinedScenario.IMG2IMG: {
        "prompt": {"node_type": "CLIPTextEncode", "field": "text"},
        "negative_prompt": {"node_type": "CLIPTextEncode", "field": "text"},
        "input_image": {"node_type": "LoadImage", "field": "image"},
        "denoise": {"node_type": "KSampler", "field": "denoise"},
        "seed": {"node_type": "KSampler", "field": "seed"},
        "steps": {"node_type": "KSampler", "field": "steps"},
        "cfg": {"node_type": "KSampler", "field": "cfg"},
    },
}
