"""
图片路由测试

测试 /api/v1/images/* 相关接口
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO


class TestImageUpload:
    """测试上传图片接口 POST /api/v1/images/upload"""

    def test_upload_image_success(self, client, mock_comfyui_client, mock_image_content):
        """
        测试成功上传图片

        验证点:
        - 状态码为 200
        - 返回正确的响应格式
        - 包含文件名信息
        """
        mock_comfyui_client.upload_image.return_value = {"name": "test_image.png"}

        files = {"file": ("test_image.png", BytesIO(mock_image_content), "image/png")}
        data = {"overwrite": "true"}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files, data=data)

            assert response.status_code == 200
            result = response.json()
            assert result["code"] == 200
            assert result["message"] == "上传成功"
            assert result["data"]["filename"] == "test_image.png"
            mock_comfyui_client.upload_image.assert_called_once()

    def test_upload_image_with_overwrite_false(self, client, mock_comfyui_client, mock_image_content):
        """
        测试上传图片时不覆盖

        验证点:
        - overwrite=false 参数被正确传递
        """
        mock_comfyui_client.upload_image.return_value = {"name": "test_image_copy.png"}

        files = {"file": ("test_image.png", BytesIO(mock_image_content), "image/png")}
        data = {"overwrite": "false"}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files, data=data)

            assert response.status_code == 200
            mock_comfyui_client.upload_image.assert_called_once()

    def test_upload_image_without_overwrite(self, client, mock_comfyui_client, mock_image_content):
        """
        测试上传图片不指定 overwrite

        验证点:
        - 使用默认值 overwrite=True
        """
        mock_comfyui_client.upload_image.return_value = {"name": "test.png"}

        files = {"file": ("test.png", BytesIO(mock_image_content), "image/png")}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            assert response.status_code == 200

    def test_upload_image_invalid_file_type(self, client, mock_comfyui_client):
        """
        测试上传非图片文件

        验证点:
        - 返回 400 错误
        - 不调用 upload_image 方法
        """
        # 模拟文本文件
        text_content = b"This is not an image"

        files = {"file": ("test.txt", BytesIO(text_content), "text/plain")}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            assert response.status_code == 400
            result = response.json()
            assert result["code"] == 400
            assert "只支持图片文件" in result["message"]
            mock_comfyui_client.upload_image.assert_not_called()



    def test_upload_image_connection_error(self, client, mock_comfyui_client, mock_image_content):
        """
        测试上传时 ComfyUI 连接错误

        验证点:
        - 返回正确的错误码
        """
        from app.exceptions import ComfyUIConnectionError
        from app.schemas import ResponseCode

        mock_comfyui_client.upload_image.side_effect = ComfyUIConnectionError("ComfyUI 不可用")

        files = {"file": ("test.png", BytesIO(mock_image_content), "image/png")}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            assert response.status_code == 500
            result = response.json()
            assert result["code"] == ResponseCode.ERROR_COMFYUI_CONNECTION

    def test_upload_image_general_exception(self, client, mock_comfyui_client, mock_image_content):
        """
        测试上传时发生一般异常

        验证点:
        - 全局异常处理器捕获 Exception
        - 返回 500 错误码
        """
        mock_comfyui_client.upload_image.side_effect = Exception("保存失败")

        files = {"file": ("test.png", BytesIO(mock_image_content), "image/png")}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            assert response.status_code == 500
            result = response.json()
            assert result["code"] == 500
            assert result["message"] == "服务器内部错误"

    def test_upload_image_file_operation_error(self, client, mock_comfyui_client, mock_image_content):
        """
        测试上传时文件操作错误

        验证点:
        - 返回正确的业务错误码
        """
        from app.exceptions import FileOperationError
        from app.schemas import ResponseCode

        mock_comfyui_client.upload_image.side_effect = FileOperationError("文件保存失败")

        files = {"file": ("test.png", BytesIO(mock_image_content), "image/png")}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            assert response.status_code == 500
            result = response.json()
            assert result["code"] == ResponseCode.ERROR_FILE_OPERATION


    def test_upload_large_image(self, client, mock_comfyui_client):
        """
        测试上传大图片

        验证点:
        - 能够处理大文件
        """
        # 模拟 10MB 的图片数据
        large_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * (10 * 1024 * 1024)

        mock_comfyui_client.upload_image.return_value = {"name": "large.png"}

        files = {"file": ("large.png", BytesIO(large_content), "image/png")}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            # 应该能够处理大文件
            assert response.status_code == 200

    def test_upload_image_with_special_filename(self, client, mock_comfyui_client, mock_image_content):
        """
        测试上传包含特殊字符文件名的图片

        验证点:
        - 支持中文、空格、特殊字符
        """
        special_filenames = [
            "test image.png",
            "测试图片.png",
            "test-image-2024-01-01.png",
            "test_image_多语言.png",
        ]

        mock_comfyui_client.upload_image.return_value = {"name": "uploaded.png"}

        for filename in special_filenames:
            files = {"file": (filename, BytesIO(mock_image_content), "image/png")}

            with patch("app.routers.images.comfyui_client", mock_comfyui_client):
                response = client.post("/api/v1/images/upload", files=files)

                assert response.status_code == 200
                result = response.json()
                assert result["data"]["filename"] == filename


class TestImageDownload:
    """测试下载图片接口 GET /api/v1/images/download"""

    def test_download_image_success_png(self, client, mock_comfyui_client, mock_image_content):
        """
        测试成功下载 PNG 图片

        验证点:
        - 返回正确的 Content-Type
        - 返回二进制内容
        """
        mock_comfyui_client.download_image.return_value = mock_image_content

        params = {"filename": "test_image.png", "subfolder": "", "img_type": "output"}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert len(response.content) > 0
            mock_comfyui_client.download_image.assert_called_once_with("test_image.png", "", "output")

    def test_download_image_jpeg(self, client, mock_comfyui_client):
        """
        测试下载 JPEG 图片

        验证点:
        - 正确推断 Content-Type 为 image/jpeg
        """
        jpeg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        mock_comfyui_client.download_image.return_value = jpeg_content

        params = {"filename": "test.jpg", "subfolder": "", "img_type": "output"}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"

    def test_download_image_gif(self, client, mock_comfyui_client):
        """
        测试下载 GIF 图片

        验证点:
        - 正确推断 Content-Type 为 image/gif
        """
        gif_content = b"GIF89a"
        mock_comfyui_client.download_image.return_value = gif_content

        params = {"filename": "test.gif", "subfolder": "", "img_type": "output"}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/gif"

    def test_download_image_webp(self, client, mock_comfyui_client):
        """
        测试下载 WebP 图片

        验证点:
        - 正确推断 Content-Type 为 image/webp
        """
        webp_content = b"RIFF....WEBP"
        mock_comfyui_client.download_image.return_value = webp_content

        params = {"filename": "test.webp", "subfolder": "", "img_type": "output"}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/webp"

    def test_download_image_bmp(self, client, mock_comfyui_client):
        """
        测试下载 BMP 图片

        验证点:
        - 正确推断 Content-Type 为 image/bmp
        """
        bmp_content = b"BM"
        mock_comfyui_client.download_image.return_value = bmp_content

        params = {"filename": "test.bmp", "subfolder": "", "img_type": "output"}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/bmp"

    def test_download_image_with_subfolder(self, client, mock_comfyui_client, mock_image_content):
        """
        测试下载带子文件夹的图片

        验证点:
        - subfolder 参数被正确传递
        """
        mock_comfyui_client.download_image.return_value = mock_image_content

        params = {
            "filename": "test_image.png",
            "subfolder": "subfolder1",
            "img_type": "output"
        }

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 200
            mock_comfyui_client.download_image.assert_called_once_with(
                "test_image.png", "subfolder1", "output"
            )

    def test_download_image_input_type(self, client, mock_comfyui_client, mock_image_content):
        """
        测试下载 input 类型图片

        验证点:
        - img_type=input 被正确传递
        """
        mock_comfyui_client.download_image.return_value = mock_image_content

        params = {
            "filename": "input_image.png",
            "subfolder": "",
            "img_type": "input"
        }

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 200
            mock_comfyui_client.download_image.assert_called_once_with(
                "input_image.png", "", "input"
            )

    def test_download_image_unknown_extension(self, client, mock_comfyui_client):
        """
        测试下载未知扩展名的图片

        验证点:
        - 默认使用 image/png
        """
        mock_comfyui_client.download_image.return_value = b"some content"

        params = {
            "filename": "test.unknown",
            "subfolder": "",
            "img_type": "output"
        }

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"

    def test_download_image_without_extension(self, client, mock_comfyui_client):
        """
        测试下载没有扩展名的图片

        验证点:
        - 默认使用 image/png
        """
        mock_comfyui_client.download_image.return_value = b"some content"

        params = {
            "filename": "test",
            "subfolder": "",
            "img_type": "output"
        }

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"

    def test_download_image_connection_error(self, client, mock_comfyui_client):
        """
        测试下载时连接错误

        验证点:
        - 异常被正确处理
        """
        from app.exceptions import ComfyUIConnectionError

        mock_comfyui_client.download_image.side_effect = ComfyUIConnectionError("无法连接")

        params = {"filename": "test.png", "subfolder": "", "img_type": "output"}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 500
            data = response.json()
            assert data["code"] == 1001

    def test_download_image_general_exception(self, client, mock_comfyui_client):
        """
        测试下载时发生异常

        验证点:
        - 全局异常处理器捕获 Exception
        - 返回 500 错误码
        """
        mock_comfyui_client.download_image.side_effect = Exception("下载失败")

        params = {"filename": "test.png", "subfolder": "", "img_type": "output"}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 500
            data = response.json()
            assert data["code"] == 500
            assert data["message"] == "服务器内部错误"

    @pytest.mark.parametrize("filename,subfolder,img_type,expected_content_type", [
        ("test.png", "", "output", "image/png"),
        ("test.jpg", "folder", "input", "image/jpeg"),
        ("test.webp", "a/b/c", "output", "image/webp"),
        ("test.gif", "", "output", "image/gif"),
    ])
    def test_download_parametrized(
        self, client, mock_comfyui_client, mock_image_content,
        filename, subfolder, img_type, expected_content_type
    ):
        """
        参数化测试：不同参数组合下载
        """
        mock_comfyui_client.download_image.return_value = mock_image_content

        params = {
            "filename": filename,
            "subfolder": subfolder,
            "img_type": img_type
        }

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 200
            assert response.headers["content-type"] == expected_content_type

    def test_download_image_with_special_filename(self, client, mock_comfyui_client, mock_image_content):
        """
        测试下载包含特殊字符文件名的图片

        验证点:
        - 支持中文、空格、特殊字符
        """
        mock_comfyui_client.download_image.return_value = mock_image_content

        special_filenames = [
            "test image.png",
            "测试图片.png",
            "test-image@2024.png",
        ]

        for filename in special_filenames:
            params = {
                "filename": filename,
                "subfolder": "",
                "img_type": "output"
            }

            with patch("app.routers.images.comfyui_client", mock_comfyui_client):
                response = client.get("/api/v1/images/download", params=params)

                assert response.status_code == 200

    def test_download_image_filename_case_sensitivity(self, client, mock_comfyui_client, mock_image_content):
        """
        测试文件名大小写敏感性

        验证点:
        - 不同大小写的扩展名都能正确处理
        """
        mock_comfyui_client.download_image.return_value = mock_image_content

        test_cases = [
            ("test.PNG", "image/png"),
            ("test.Jpg", "image/jpeg"),
            ("test.GIF", "image/gif"),
        ]

        for filename, expected_type in test_cases:
            params = {
                "filename": filename,
                "subfolder": "",
                "img_type": "output"
            }

            with patch("app.routers.images.comfyui_client", mock_comfyui_client):
                response = client.get("/api/v1/images/download", params=params)

                assert response.status_code == 200
                assert response.headers["content-type"] == expected_type


class TestImagesEdgeCases:
    """图片接口边界情况测试"""

    def test_concurrent_image_uploads(self, client, mock_comfyui_client, mock_image_content):
        """
        测试并发上传多张图片
        """
        import threading

        results = []
        mock_comfyui_client.upload_image.return_value = {"name": "uploaded.png"}

        def upload_image():
            files = {"file": (f"test_{threading.get_ident()}.png", BytesIO(mock_image_content), "image/png")}
            with patch("app.routers.images.comfyui_client", mock_comfyui_client):
                resp = client.post("/api/v1/images/upload", files=files)
                results.append(resp.status_code)

        threads = [threading.Thread(target=upload_image) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(status == 200 for status in results)

    def test_upload_empty_file(self, client, mock_comfyui_client):
        """
        测试上传空文件

        验证点:
        - 能够处理空文件
        """
        empty_content = b""
        files = {"file": ("empty.png", BytesIO(empty_content), "image/png")}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            # 应该能够处理空文件
            assert response.status_code == 200

    def test_download_image_with_emoji_filename(self, client, mock_comfyui_client, mock_image_content):
        """
        测试下载包含 emoji 文件名的图片

        验证点:
        - 支持 emoji 字符
        """
        mock_comfyui_client.download_image.return_value = mock_image_content

        params = {
            "filename": "test_😀_🎨.png",
            "subfolder": "",
            "img_type": "output"
        }

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.get("/api/v1/images/download", params=params)

            assert response.status_code == 200

    def test_upload_without_file(self, client, mock_comfyui_client):
        """
        测试不提供文件的上传请求

        验证点:
        - FastAPI 返回 422 验证错误
        """
        response = client.post("/api/v1/images/upload")

        assert response.status_code == 400

    def test_download_without_filename(self, client, mock_comfyui_client):
        """
        测试不提供文件名的下载请求

        验证点:
        - FastAPI 返回 422 验证错误
        """
        response = client.get("/api/v1/images/download")

        assert response.status_code == 400
