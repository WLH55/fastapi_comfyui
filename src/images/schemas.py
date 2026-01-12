"""
图片领域数据模型

定义图片请求和响应的数据结构
"""

from typing import Optional
from pydantic import BaseModel, Field


class ImageUploadResponse(BaseModel):
    """
    图片上传响应模型

    Attributes:
        filename: 文件名
        name: 上传后的文件名
        subfolder: 子文件夹
        type: 图片类型
    """

    filename: str = Field(..., description="原始文件名")
    name: str = Field(..., description="上传后的文件名")
    subfolder: str = Field("", description="子文件夹")
    type: str = Field("input", description="图片类型")


class ImageDownloadRequest(BaseModel):
    """
    图片下载请求模型

    Attributes:
        filename: 文件名
        subfolder: 子文件夹
        type: 图片类型
    """

    filename: str = Field(..., description="文件名")
    subfolder: str = Field("", description="子文件夹")
    type: str = Field("output", description="图片类型（output/input）")


class ImageInfo(BaseModel):
    """
    图片信息模型

    Attributes:
        filename: 文件名
        subfolder: 子文件夹
        type: 图片类型
    """

    filename: str = Field(..., description="文件名")
    subfolder: str = Field("", description="子文件夹")
    type: str = Field("output", description="图片类型")


class GeneratedImage(BaseModel):
    """
    生成的图片模型

    Attributes:
        filename: 文件名
        subfolder: 子文件夹
        type: 图片类型
        url: 下载 URL
    """

    filename: str = Field(..., description="文件名")
    subfolder: str = Field("", description="子文件夹")
    type: str = Field("output", description="图片类型")
    url: Optional[str] = Field(None, description="下载 URL")
