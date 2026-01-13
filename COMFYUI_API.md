# ComfyUI HTTP API 调用文档

本文档说明如何通过 HTTP 请求调用 ComfyUI 的工作流，无需在界面中点击按钮。

---

## 目录

- [基础信息](#基础信息)
- [核心工作流 API](#核心工作流-api)
- [队列管理 API](#队列管理-api)
- [状态查询 API](#状态查询-api)
- [完整调用示例](#完整调用示例)

---

## 基础信息

### 默认地址

```
http://127.0.0.1:8188
```

### API 路径前缀

所有 API 支持两种路径格式：
- 原始格式：`http://host:8188/prompt`
- API 前缀格式：`http://host:8188/api/prompt`

### 认证

默认无需认证。如果启用了用户管理，需要添加 Cookie 或 Authorization 头。

---

## 核心工作流 API

### 1. 获取节点信息

获取所有可用节点的输入输出定义，用于构建工作流。

```http
GET /object_info
```

**响应示例：**

```json
{
  "KSampler": {
    "input": {
      "required": {
        "model": ["MODEL", "Model to use"],
        "positive": ["CONDITIONING", "The conditioning describing the attributes you want to assign to the latent space"],
        "negative": ["CONDITIONING"],
        "seed": ["INT", {"default": 0, "min": 0, "max": 18446744073709551615}],
        "steps": ["INT", {"default": 20, "min": 1, "max": 10000}]
      }
    },
    "output": ["LATENT"],
    "output_name": ["latent"],
    "name": "KSampler",
    "category": "sampling"
  }
}
```

**Python 示例：**

```python
import requests

response = requests.get("http://127.0.0.1:8188/object_info")
nodes_info = response.json()
print(nodes_info.keys())  # 所有可用节点
```

---

### 2. 获取特定节点信息

```http
GET /object_info/{node_class}
```

**示例：**

```python
response = requests.get("http://127.0.0.1:8188/object_info/KSampler")
ksampler_info = response.json()
```

---

### 3. 提交工作流（核心）

提交工作流到执行队列。

```http
POST /prompt
Content-Type: application/json
```

**请求体结构：**

```json
{
  "prompt": {
    "1": {
      "class_type": "KSampler",
      "inputs": {
        "model": ["4", 0],
        "positive": ["6", 0],
        "negative": ["7", 0],
        "seed": 123456789,
        "steps": 20,
        "cfg": 8,
        "sampler_name": "euler",
        "scheduler": "normal",
        "denoise": 1
      }
    }
  },
  "client_id": "my_client_001"
}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `prompt` | object | 工作流 JSON，键为节点 ID，值为节点配置 |
| `client_id` | string (可选) | 客户端标识，用于 WebSocket 推送 |
| `prompt_id` | string (可选) | 自定义 prompt ID，不传则自动生成 UUID |

**响应示例：**

```json
{
  "prompt_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "number": 1,
  "node_errors": {}
}
```

**Python 示例：**

```python
import requests
import json

workflow = {
    "1": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {
            "ckpt_name": "v1-5-pruned-emaonly.safetensors"
        }
    },
    "2": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "a beautiful landscape",
            "clip": ["1", 1]
        }
    },
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "model": ["1", 0],
            "positive": ["2", 0],
            "negative": ["2", 0],
            "seed": 42,
            "steps": 20,
            "cfg": 7,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0
        }
    },
    "4": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["3", 0],
            "vae": ["1", 2]
        }
    },
    "5": {
        "class_type": "SaveImage",
        "inputs": {
            "images": ["4", 0],
            "filename_prefix": "output"
        }
    }
}

response = requests.post(
    "http://127.0.0.1:8188/prompt",
    json={"prompt": workflow, "client_id": "python_client"}
)

result = response.json()
prompt_id = result["prompt_id"]
print(f"工作流已提交，ID: {prompt_id}")
```

---

### 4. 工作流引用语法

节点之间的连接通过引用语法实现：

```json
["节点ID", 输出索引]
```

**示例：**

```json
"inputs": {
  "model": ["4", 0],      // 引用节点 4 的第 0 个输出
  "positive": ["6", 0],   // 引用节点 6 的第 0 个输出
  "text": "hello world"   // 直接值
}
```

---

## 队列管理 API

### 1. 获取队列状态

```http
GET /queue
```

**响应示例：**

```json
{
  "queue_running": [
    ["a1b2c3d4-e5f6-7890-abcd-ef1234567890", 1, 1234567890]
  ],
  "queue_pending": [
    ["b2c3d4e5-f6g7-8901-bcde-f23456789012", 2, 1234567891]
  ]
}
```

**Python 示例：**

```python
response = requests.get("http://127.0.0.1:8188/queue")
queue = response.json()
print(f"正在运行: {len(queue['queue_running'])}")
print(f"等待中: {len(queue['queue_pending'])}")
```

---

### 2. 清空队列

```http
POST /queue
Content-Type: application/json

{
  "clear": true
}
```

**Python 示例：**

```python
requests.post(
    "http://127.0.0.1:8188/queue",
    json={"clear": True}
)
```

---

### 3. 删除指定任务

```http
POST /queue
Content-Type: application/json

{
  "delete": ["prompt_id_1", "prompt_id_2"]
}
```

**Python 示例：**

```python
requests.post(
    "http://127.0.0.1:8188/queue",
    json={"delete": [prompt_id]}
)
```

---

### 4. 中断执行

```http
POST /interrupt
Content-Type: application/json

{
  "prompt_id": "optional-specific-prompt-id"
}
```

| 参数 | 说明 |
|------|------|
| 不传 `prompt_id` | 全局中断，停止所有正在运行的任务 |
| 传入 `prompt_id` | 仅中断指定的 prompt |

**Python 示例：**

```python
# 全局中断
requests.post("http://127.0.0.1:8188/interrupt")

# 中断特定任务
requests.post(
    "http://127.0.0.1:8188/interrupt",
    json={"prompt_id": prompt_id}
)
```

---

## 状态查询 API

### 1. 获取执行历史

```http
GET /history
GET /history?max_items=10
GET /history?offset=0
GET /history/{prompt_id}
```

**响应示例：**

```json
{
  "a1b2c3d4-e5f6-7890-abcd-ef1234567890": {
    "prompt": {...},
    "outputs": {
      "5": {
        "images": [
          {
            "filename": "output_00001.png",
            "subfolder": "",
            "type": "output"
          }
        ]
      }
    }
  }
}
```

**Python 示例：**

```python
# 获取特定 prompt 的历史和结果
response = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}")
history = response.json()

# 提取生成的图片
if prompt_id in history:
    outputs = history[prompt_id]["outputs"]
    for node_id, node_output in outputs.items():
        if "images" in node_output:
            for img in node_output["images"]:
                print(f"图片: {img['filename']}")
```

---

### 2. 获取系统状态

```http
GET /system_stats
```

**响应示例：**

```json
{
  "system": {
    "os": "win32",
    "ram_total": 34257186816,
    "ram_free": 15236589568,
    "comfyui_version": "0.3.10",
    "python_version": "3.10.0",
    "pytorch_version": "2.1.0+cu121"
  },
  "devices": [
    {
      "name": "NVIDIA GeForce RTX 4090",
      "type": "cuda",
      "vram_total": 25388752896,
      "vram_free": 20876955648
    }
  ]
}
```

---

### 3. 获取模型列表

```http
GET /models                    # 获取所有模型类型
GET /models/{folder}           # 获取指定文件夹的模型
```

**示例：**

```python
# 获取所有模型类型
response = requests.get("http://127.0.0.1:8188/models")
model_types = response.json()  # ["checkpoints", "loras", "embeddings", ...]

# 获取所有 checkpoint 模型
response = requests.get("http://127.0.0.1:8188/models/checkpoints")
checkpoints = response.json()
```

---

## 完整调用示例

### 同步等待完成

```python
import requests
import time

COMFYUI_HOST = "http://127.0.0.1:8188"

def submit_workflow(workflow, client_id="python_client"):
    """提交工作流并返回 prompt_id"""
    response = requests.post(
        f"{COMFYUI_HOST}/prompt",
        json={"prompt": workflow, "client_id": client_id}
    )
    return response.json()["prompt_id"]

def wait_for_completion(prompt_id, timeout=300):
    """等待工作流执行完成"""
    start_time = time.time()

    while True:
        # 检查队列状态
        queue_response = requests.get(f"{COMFYUI_HOST}/queue")
        queue = queue_response.json()

        # 提取所有正在运行和等待的 prompt_id
        running = [item[0] for item in queue["queue_running"]]
        pending = [item[0] for item in queue["queue_pending"]]

        # 如果 prompt_id 不在队列中，说明已完成
        if prompt_id not in running + pending:
            # 获取历史记录确认结果
            history_response = requests.get(f"{COMFYUI_HOST}/history/{prompt_id}")
            if history_response.status_code == 200:
                return history_response.json()

        # 超时检查
        if time.time() - start_time > timeout:
            raise TimeoutError(f"工作流执行超时: {prompt_id}")

        time.sleep(0.5)

def get_generated_images(prompt_id):
    """从历史记录中提取生成的图片信息"""
    response = requests.get(f"{COMFYUI_HOST}/history/{prompt_id}")
    history = response.json()

    if prompt_id not in history:
        return []

    outputs = history[prompt_id].get("outputs", {})
    images = []

    for node_output in outputs.values():
        if "images" in node_output:
            for img in node_output["images"]:
                images.append({
                    "filename": img["filename"],
                    "subfolder": img.get("subfolder", ""),
                    "type": img.get("type", "output")
                })

    return images

def download_image(image_info, output_path="."):
    """下载生成的图片"""
    filename = image_info["filename"]
    subfolder = image_info["subfolder"]
    img_type = image_info["type"]

    params = {"filename": filename, "subfolder": subfolder, "type": img_type}
    response = requests.get(f"{COMFYUI_HOST}/view", params=params)

    save_path = f"{output_path}/{filename}"
    with open(save_path, "wb") as f:
        f.write(response.content)

    return save_path

# ========== 使用示例 ==========

# 从 ComfyUI 导出的 API 格式工作流
workflow = {
    "1": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "v1-5-pruned-emaonly.safetensors"}
    },
    "2": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "a sunset over mountains, digital art",
            "clip": ["1", 1]
        }
    },
    "3": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "ugly, blurry, low quality",
            "clip": ["1", 1]
        }
    },
    "4": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 12345,
            "steps": 20,
            "cfg": 7,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
            "model": ["1", 0],
            "positive": ["2", 0],
            "negative": ["3", 0]
        }
    },
    "5": {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["4", 0], "vae": ["1", 2]}
    },
    "6": {
        "class_type": "SaveImage",
        "inputs": {"images": ["5", 0], "filename_prefix": "API"}
    }
}

# 提交工作流
prompt_id = submit_workflow(workflow)
print(f"工作流已提交: {prompt_id}")

# 等待完成
print("等待执行完成...")
result = wait_for_completion(prompt_id)

# 获取图片信息
images = get_generated_images(prompt_id)
print(f"生成了 {len(images)} 张图片")

# 下载图片
for img in images:
    path = download_image(img, output_path="./output")
    print(f"已下载: {path}")
```

---

### WebSocket 实时监听

```python
import asyncio
import aiohttp
import json

async def listen_websocket(client_id="python_client"):
    """监听 WebSocket 获取实时进度"""
    uri = "ws://127.0.0.1:8188/ws?clientId={client_id}"

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(uri) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)

                    # 处理不同类型的消息
                    msg_type = data.get("type")
                    msg_data = data.get("data", {})

                    if msg_type == "status":
                        print(f"队列状态: 剩余 {msg_data['status']['exec_info']['queue_remaining']} 个任务")

                    elif msg_type == "executing":
                        node_id = msg_data.get("node")
                        if node_id is None:
                            print("执行完成")
                        else:
                            print(f"正在执行节点: {node_id}")

                    elif msg_type == "progress":
                        print(f"进度: {msg_data['value']}/{msg_data['max']}")

                    elif msg_type == "executed":
                        print(f"节点执行完成: {msg_data['node']}")

# 运行监听
asyncio.run(listen_websocket())
```

---

## 获取工作流 JSON

### 方法一：从 ComfyUI 界面导出

1. 在 ComfyUI 界面设计好工作流
2. 点击 **Save (API Format)** 按钮
3. 保存的 JSON 文件可直接用于 API 调用

### 方法二：转换普通工作流

普通工作流格式需要转换为 API 格式：
- 移除 UI 相关字段（`pos`, `size`, `flags` 等）
- 只保留 `class_type` 和 `inputs` 字段

---

## 常见问题

### 1. 如何获取工作流 JSON？

在 ComfyUI 界面点击 **Save (API Format)** 而非 **Save**，导出的 JSON 可直接用于 API。

### 2. 如何知道某个模型是否可用？

调用 `/models/checkpoints` 查看，确保 `ckpt_name` 参数与列表中的文件名一致。

### 3. 如何批量处理？

多次调用 `/prompt` 提交不同参数的工作流，使用 `/queue` 监控队列状态。

### 4. 如何设置生成图片的保存路径？

`SaveImage` 节点的 `filename_prefix` 参数设置文件名前缀，文件保存到 ComfyUI 的 `output` 目录。

---

## 完整的封装类示例

```python
import requests
import time
import json
from typing import Dict, List, Optional, Any

class ComfyUIClient:
    def __init__(self, host: str = "http://127.0.0.1:8188"):
        self.host = host
        self.client_id = "python_client"

    def submit_queue(self, workflow: Dict) -> str:
        """提交工作流到队列"""
        response = requests.post(
            f"{self.host}/prompt",
            json={"prompt": workflow, "client_id": self.client_id}
        )
        response.raise_for_status()
        return response.json()["prompt_id"]

    def get_queue(self) -> Dict:
        """获取当前队列状态"""
        response = requests.get(f"{self.host}/queue")
        response.raise_for_status()
        return response.json()

    def get_history(self, prompt_id: Optional[str] = None) -> Dict:
        """获取执行历史"""
        if prompt_id:
            response = requests.get(f"{self.host}/history/{prompt_id}")
        else:
            response = requests.get(f"{self.host}/history")
        response.raise_for_status()
        return response.json()

    def wait(self, prompt_id: str, timeout: int = 300) -> Dict:
        """等待工作流执行完成"""
        start = time.time()
        while True:
            queue = self.get_queue()
            running = [item[0] for item in queue["queue_running"]]
            pending = [item[0] for item in queue["queue_pending"]]

            if prompt_id not in running + pending:
                return self.get_history(prompt_id)

            if time.time() - start > timeout:
                raise TimeoutError(f"执行超时: {prompt_id}")

            time.sleep(0.5)

    def interrupt(self, prompt_id: Optional[str] = None):
        """中断执行"""
        if prompt_id:
            requests.post(f"{self.host}/interrupt", json={"prompt_id": prompt_id})
        else:
            requests.post(f"{self.host}/interrupt")

    def clear_queue(self):
        """清空队列"""
        requests.post(f"{self.host}/queue", json={"clear": True})

    def get_images(self, prompt_id: str) -> List[Dict]:
        """获取生成的图片列表"""
        history = self.get_history(prompt_id)
        if prompt_id not in history:
            return []

        images = []
        for node_output in history[prompt_id].get("outputs", {}).values():
            if "images" in node_output:
                images.extend(node_output["images"])

        return images

    def download_image(self, image: Dict, save_path: str) -> str:
        """下载图片"""
        filename = image["filename"]
        subfolder = image.get("subfolder", "")
        img_type = image.get("type", "output")

        params = {"filename": filename, "subfolder": subfolder, "type": img_type}
        response = requests.get(f"{self.host}/view", params=params)
        response.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(response.content)

        return save_path

    def execute(self, workflow: Dict, output_dir: str = "./output") -> List[str]:
        """执行工作流并下载所有生成的图片"""
        prompt_id = self.submit_queue(workflow)
        print(f"已提交: {prompt_id}")

        self.wait(prompt_id)
        print("执行完成")

        images = self.get_images(prompt_id)
        downloaded = []

        for i, img in enumerate(images):
            filename = img["filename"]
            save_path = f"{output_dir}/{filename}"
            self.download_image(img, save_path)
            downloaded.append(save_path)

        return downloaded

# 使用示例
if __name__ == "__main__":
    client = ComfyUIClient()

    # 你的工作流 JSON
    workflow = {
        # ... 工作流定义 ...
    }

    # 一键执行并下载
    saved_files = client.execute(workflow, output_dir="./generated")
    print(f"已保存: {saved_files}")
```

---

## 附录：HTTP 状态码

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 请求错误（参数无效、工作流验证失败）|
| 403 | 权限拒绝（路径安全检查失败）|
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
