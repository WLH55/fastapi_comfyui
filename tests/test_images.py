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
        """
        mock_comfyui_client.upload_image.return_value = {"name": "test_image_copy.png"}

        files = {"file": ("test_image.png", BytesIO(mock_image_content), "image/png")}
        data = {"overwrite": "false"}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files, data=data)

            assert response.status_code == 200
            mock_comfyui_client.upload_image.assert_called_once()

    def test_upload_image_invalid_file_type(self, client, mock_comfyui_client):
        """
        测试上传非图片文件
        """
        # 模拟文本文件
        text_content = b"This is not an image"

        files = {"file": ("test.txt", BytesIO(text_content), "text/plain")}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            assert response.status_code == 200
            result = response.json()
            assert result["code"] == 400
            assert "只支持图片文件" in result["message"]
            mock_comfyui_client.upload_image.assert_not_called()

    def test_upload_image_no_content_type(self, client, mock_comfyui_client, mock_image_content):
        """
        测试上传没有 content_type 的文件
        """
        mock_comfyui_client.upload_image.return_value = {"name": "test.png"}

        files = {"file": ("test.png", BytesIO(mock_image_content), None)}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            assert response.status_code == 200
            result = response.json()
            assert result["code"] == 400
            mock_comfyui_client.upload_image.assert_not_called()

    def test_upload_image_connection_error(self, client, mock_comfyui_client, mock_image_content):
        """
        测试上传时 ComfyUI 连接错误
        """
        from app.exceptions import ComfyUIConnectionError
        from app.schemas import ResponseCode

        mock_comfyui_client.upload_image.side_effect = ComfyUIConnectionError("ComfyUI 不可用")

        files = {"file": ("test.png", BytesIO(mock_image_content), "image/png")}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            assert response.status_code == 200
            result = response.json()
            assert result["code"] == ResponseCode.ERROR_COMFYUI_CONNECTION

    def test_upload_image_general_exception(self, client, mock_comfyui_client, mock_image_content):
        """
        测试上传时发生一般异常
        """
        mock_comfyui_client.upload_image.side_effect = Exception("保存失败")

        files = {"file": ("test.png", BytesIO(mock_image_content), "image/png")}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            assert response.status_code == 200
            result = response.json()
            assert result["code"] == 500
            assert "上传失败" in result["message"]

    @pytest.mark.parametrize("filename,content_type,expected_valid", [
        ("test.png", "image/png", True),
        ("test.jpg", "image/jpeg", True),
        ("test.gif", "image/gif", True),
        ("test.webp", "image/webp", True),
        ("test.bmp", "image/bmp", True),
        ("test.txt", "text/plain", False),
        ("test.pdf", "application/pdf", False),
    ])
    def test_upload_image_different_types(
        self, client, mock_comfyui_client, mock_image_content,
        filename, content_type, expected_valid
    ):
        """
        参数化测试：不同文件类型的上传
        """
        mock_comfyui_client.upload_image.return_value = {"name": filename}

        files = {"file": (filename, BytesIO(mock_image_content), content_type)}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            assert response.status_code == 200
            result = response.json()

            if expected_valid:
                assert result["code"] == 200
            else:
                assert result["code"] == 400

    def test_upload_large_image(self, client, mock_comfyui_client):
        """
        测试上传大图片
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


class TestImageURL:
    """测试获取图片URL接口 GET /api/v1/images/url"""

    def test_get_image_url_success(self, client):
        """
        测试成功获取图片URL
        """
        params = {"filename": "test_image.png", "subfolder": "", "img_type": "output"}

        response = client.get("/api/v1/images/url", params=params)

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 200
        assert result["message"] == "获取图片 URL 成功"
        assert "url" in result["data"]
        assert "test_image.png" in result["data"]["url"]
        assert result["data"]["filename"] == "test_image.png"

    def test_get_image_url_with_subfolder(self, client):
        """
        测试获取带子文件夹的图片URL
        """
        params = {
            "filename": "test_image.png",
            "subfolder": "subfolder1",
            "img_type": "output"
        }

        response = client.get("/api/v1/images/url", params=params)

        assert response.status_code == 200
        result = response.json()
        assert "subfolder=subfolder1" in result["data"]["url"]

    def test_get_image_url_with_input_type(self, client):
        """
        测试获取 input 类型图片的URL
        """
        params = {
            "filename": "input_image.png",
            "subfolder": "",
            "img_type": "input"
        }

        response = client.get("/api/v1/images/url", params=params)

        assert response.status_code == 200
        result = response.json()
        assert "type=input" in result["data"]["url"]

    @pytest.mark.parametrize("filename,subfolder,img_type", [
        ("test1.png", "", "output"),
        ("test2.jpg", "folder", "input"),
        ("test3.webp", "a/b/c", "output"),
    ])
    def test_get_image_url_parametrized(self, client, filename, subfolder, img_type):
        """
        参数化测试：不同参数组合获取URL
        """
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "img_type": img_type
        }

        response = client.get("/api/v1/images/url", params=params)

        assert response.status_code == 200
        result = response.json()
        assert result["data"]["filename"] == filename

    def test_get_image_url_with_special_characters(self, client):
        """
        测试获取包含特殊字符文件名的URL
        """
        params = {
            "filename": "test image 测试.png",
            "subfolder": "",
            "img_type": "output"
        }

        response = client.get("/api/v1/images/url", params=params)

        assert response.status_code == 200
        result = response.json()
        assert "test+image" in result["data"]["url"] or "test%20image" in result["data"]["url"]

    def test_get_image_url_without_filename(self, client):
        """
        测试不提供文件名获取URL
        """
        params = {"subfolder": "", "img_type": "output"}

        response = client.get("/api/v1/images/url", params=params)

        # FastAPI 会返回 422 验证错误
        assert response.status_code == 422

    def test_get_image_url_exception(self, client):
        """
        测试获取URL时发生异常
        """
        # 使用一个可能导致异常的参数
        params = {"filename": "test.png", "subfolder": "", "img_type": "invalid"}

        response = client.get("/api/v1/images/url", params=params)

        # 应该返回响应（即使参数可能不合法）
        assert response.status_code in [200, 422]


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
        """
        empty_content = b""
        files = {"file": ("empty.png", BytesIO(empty_content), "image/png")}

        with patch("app.routers.images.comfyui_client", mock_comfyui_client):
            response = client.post("/api/v1/images/upload", files=files)

            # 应该能够处理空文件（可能会在上传时失败）
            assert response.status_code == 200

    def test_get_url_with_unicode_emoji(self, client):
        """
        测试获取包含 emoji 的文件名 URL
        """
        params = {
            "filename": "test_😀_🎨.png",
            "subfolder": "",
            "img_type": "output"
        }

        response = client.get("/api/v1/images/url", params=params)

        assert response.status_code == 200
        result = response.json()
        assert result["data"]["filename"] == "test_😀_🎨.png"
