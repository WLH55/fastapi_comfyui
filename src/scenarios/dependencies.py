"""
场景领域依赖项
"""

from typing import Optional
from fastapi import Header, HTTPException


async def validate_template_access(
    x_api_key: Optional[str] = Header(None)
) -> dict:
    """
    验证模板访问权限

    Args:
        x_api_key: API 密钥

    Returns:
        验证上下文字典
    """
    # TODO: 实现实际的 API 验证逻辑
    return {
        "authorized": True,
        "api_key": x_api_key
    }


def parse_scenario_type(scenario_type: str) -> tuple:
    """
    解析场景类型

    Args:
        scenario_type: 场景类型字符串

    Returns:
        (场景类型, 版本) 元组
    """
    if ":" in scenario_type:
        parts = scenario_type.split(":")
        return parts[0], parts[1] if len(parts) > 1 else "v1"
    return scenario_type, "v1"
