# FastAPI ComfyUI API 文档

## 项目简介

FastAPI ComfyUI 服务是一个 ComfyUI 接口封装层，作为 API 网关为内部服务提供简化的图像生成接口。内部服务只需调用本项目的封装接口，无需理解 ComfyUI 复杂的参数体系。

## 项目结构

```
fastapi_comfyui/
├── app/
│   ├── main.py              # 应用入口，全局异常处理
│   ├── config.py            # 配置管理
│   ├── schemas.py           # 统一响应格式定义
│   ├── exceptions.py        # 自定义异常
│   ├── dependencies.py      # 依赖注入
│   │
│   ├── routers/             # 路由模块（按功能划分）
│   │   ├── scenarios.py     # 场景化接口（如 cpu_quickly）
│   │   ├── workflows.py     # 工作流提交和管理
│   │   ├── queue.py         # 队列状态查询
│   │   ├── images.py        # 图片上传下载
│   │   └── websocket.py     # WebSocket 实时通信
│   │
│   ├── internal/            # 内部服务模块
│   │   ├── comfyui.py       # ComfyUI 客户端
│   │   └── utils.py         # 工具函数
│   │
│   └── templates/           # ComfyUI 工作流模板
│       └── cpu quickly.json # CPU 快速图生图工作流
│
├── input/                   # 输入图片目录
├── output/                  # 输出图片目录
├── requirements.txt         # Python 依赖
└── .env                     # 环境配置（可选）
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量（可选）

创建 `.env` 文件：

```env
# ComfyUI 服务地址
COMFYUI_HOST=127.0.0.1
COMFYUI_PORT=8188

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### 3. 启动服务

```bash
python -m app.main
```

或使用 uvicorn：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 统一响应格式

所有 API 接口返回统一的 JSON 格式：

### 成功响应

```json
{
    "code": 200,
    "message": "success",
    "data": {...}
}
```

### 错误响应

```json
{
    "code": 400,
    "message": "错误描述",
    "data": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 响应码 |
| message | str | 响应消息 |
| data | object/null | 成功时包含数据，错误时为 null |

### 响应码列表

| 响应码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 1001 | ComfyUI 连接失败 |
| 1002 | 工作流验证失败 |
| 1003 | 文件操作错误 |

---

## API 接口文档

### 场景化接口

场景化接口为特定工作流提供简化的调用方式，用户只需传入关键参数即可。

#### CPU Quickly 图生图

针对 CPU 快速工作流的图生图接口。

**接口地址：** `POST /api/v1/scenarios/cpu_quickly`

**请求参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| prompt | string | 是 | - | 正向提示词 |
| negative_prompt | string | 否 | "" | 负面提示词 |
| input_image | string | 否 | "your_image_here.png" | 输入图片文件名 |

**请求示例：**

```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/cpu_quickly" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a beautiful sunset over mountains",
    "negative_prompt": "blurry, low quality",
    "input_image": "input.png"
  }'
```

**响应示例：**

```json
{
    "code": 200,
    "message": "图生图任务已提交",
    "data": {
        "prompt_id": "abc123def456",
        "scenario": "cpu_quickly"
    }
}
```

---

### 工作流接口

直接操作 ComfyUI 工作流的接口。

#### 提交工作流

**接口地址：** `POST /api/v1/workflows/submit`

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| workflow | object | 是 | ComfyUI API 格式的工作流 |
| client_id | string | 否 | 客户端标识 |

**请求示例：**

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": {
      "3": {
        "class_type": "KSampler",
        "inputs": {
          "seed": 123456789,
          "steps": 20,
          "cfg": 7.0
        }
      }
    },
    "client_id": "my_client"
  }'
```

**响应示例：**

```json
{
    "code": 200,
    "message": "工作流已提交",
    "data": {
        "prompt_id": "abc123def456",
        "client_id": "my_client"
    }
}
```

#### 获取工作流历史

**接口地址：** `GET /api/v1/workflows/{prompt_id}/history`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| prompt_id | string | 工作流 ID |

**响应示例：**

```json
{
    "code": 200,
    "message": "获取历史记录成功",
    "data": {
        "prompt_id": "abc123def456",
        "outputs": {...}
    }
}
```

#### 中断工作流

**接口地址：** `POST /api/v1/workflows/interrupt`

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt_id | string | 是 | 要中断的工作流 ID |

**请求示例：**

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/interrupt" \
  -H "Content-Type: application/json" \
  -d '{"prompt_id": "abc123def456"}'
```

---

### 队列接口

查询和管理 ComfyUI 任务队列。

#### 获取队列状态

**接口地址：** `GET /api/v1/queue/status`

**响应示例：**

```json
{
    "code": 200,
    "message": "获取队列状态成功",
    "data": {
        "queue_running": [
            {
                "prompt_id": "abc123",
                "number": 1,
                "timestamp": 1234567890
            }
        ],
        "queue_pending": [
            {
                "prompt_id": "def456",
                "number": 2,
                "timestamp": 1234567891
            }
        ],
        "running_count": 1,
        "pending_count": 1
    }
}
```

#### 清空队列

**接口地址：** `POST /api/v1/queue/clear`

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| clear | boolean | 是 | true 表示清空队列 |

**请求示例：**

```bash
curl -X POST "http://localhost:8000/api/v1/queue/clear" \
  -H "Content-Type: application/json" \
  -d '{"clear": true}'
```

---

### 图片接口

图片上传、下载和 URL 获取。

#### 上传图片

**接口地址：** `POST /api/v1/images/upload`

**请求参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| file | file | 是 | - | 图片文件 |
| overwrite | boolean | 否 | true | 是否覆盖同名文件 |

**请求示例：**

```bash
curl -X POST "http://localhost:8000/api/v1/images/upload" \
  -F "file=@/path/to/image.png" \
  -F "overwrite=true"
```

**响应示例：**

```json
{
    "code": 200,
    "message": "上传成功",
    "data": {
        "filename": "image.png",
        "name": "image.png",
        "local_path": "/path/to/input/image.png"
    }
}
```

#### 下载图片

**接口地址：** `GET /api/v1/images/download`

**查询参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| filename | string | 是 | - | 图片文件名 |
| subfolder | string | 否 | "" | 子文件夹 |
| img_type | string | 否 | "output" | 图片类型 (input/output) |

**请求示例：**

```bash
curl -X GET "http://localhost:8000/api/v1/images/download?filename=result.png" -o output.png
```

#### 获取图片 URL

**接口地址：** `GET /api/v1/images/url`

**查询参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| filename | string | 是 | - | 图片文件名 |
| subfolder | string | 否 | "" | 子文件夹 |
| img_type | string | 否 | "output" | 图片类型 |

**响应示例：**

```json
{
    "code": 200,
    "message": "获取图片 URL 成功",
    "data": {
        "url": "http://127.0.0.1:8188/view?filename=result.png&subfolder=&type=output",
        "filename": "result.png"
    }
}
```

---

### WebSocket 接口

实时通信接口，用于监听工作流执行进度。

**连接地址：** `ws://localhost:8000/api/v1/ws/{client_id}`

#### 支持的消息类型

**客户端 -> 服务端：**

| 类型 | 说明 |
|------|------|
| submit | 提交工作流 |
| ping | 心跳检测 |

**服务端 -> 客户端：**

| 类型 | 说明 |
|------|------|
| connected | 连接建立 |
| submit_success | 提交成功 |
| submit_error | 提交失败 |
| pong | 心跳响应 |
| error | 错误消息 |

#### 消息格式

**提交工作流：**

```json
{
    "type": "submit",
    "data": {
        "workflow": {...}
    }
}
```

**心跳检测：**

```json
{
    "type": "ping"
}
```

**连接响应：**

```json
{
    "type": "connected",
    "data": {
        "message": "WebSocket 连接已建立",
        "client_id": "my_client"
    }
}
```

---

## 添加新场景接口

如需添加新的场景接口（如 text2img），按照以下步骤：

### 1. 创建工作流模板

将工作流 API 格式 JSON 文件放入 `app/templates/` 目录。

### 2. 定义请求模型

在 `app/routers/scenarios.py` 中添加：

```python
class Text2ImgRequest(BaseModel):
    """文生图请求"""
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    seed: int = -1
    steps: int = 20
    cfg: float = 7.0
```

### 3. 创建接口函数

```python
@router.post("/text2img", summary="文生图", response_model=ApiResponse)
async def text2img(request: Text2ImgRequest):
    """文生图接口"""
    try:
        # 加载 workflow 模板
        workflow = load_workflow_json("text2img.json")

        # 定义参数映射
        param_mappings = {
            "prompt": {"node_id": "3", "field": "inputs.text"},
            "negative_prompt": {"node_id": "4", "field": "inputs.text"},
            # ... 更多映射
        }

        # 构建参数
        params = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            # ... 更多参数
        }

        # 应用参数到 workflow
        final_workflow = apply_params_to_workflow(workflow, params, param_mappings)

        # 提交到 ComfyUI
        prompt_id = await comfyui_client.submit_prompt(final_workflow, request.client_id)

        return ApiResponse.success(
            data={"prompt_id": prompt_id, "scenario": "text2img"},
            message="文生图任务已提交"
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
```

### 4. 获取节点 ID

打开 ComfyUI，右键点击节点 -> "Save (API Format)"，查看生成的 JSON 文件中各节点的 ID。

---

## 错误处理

所有错误都会返回统一格式，**错误时 data 字段始终为 null**：

```json
{
    "code": 500,
    "message": "错误描述",
    "data": null
}
```

### 错误示例

**请求参数错误 (400):**
```json
{
    "code": 400,
    "message": "请求参数验证失败",
    "data": null
}
```

**资源不存在 (404):**
```json
{
    "code": 404,
    "message": "Workflow 模板文件不存在",
    "data": null
}
```

**服务器错误 (500):**
```json
{
    "code": 500,
    "message": "服务器内部错误",
    "data": null
}
```

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| 1001 | ComfyUI 连接失败 | 检查 ComfyUI 服务是否运行 |
| 1002 | 工作流验证失败 | 检查工作流格式是否正确 |
| 1003 | 文件操作错误 | 检查文件路径和权限 |
| 404 | 资源不存在 | 检查请求的资源 ID 是否正确 |
