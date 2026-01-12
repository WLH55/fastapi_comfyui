# FastAPI ComfyUI Service

基于 FastAPI 的 ComfyUI HTTP API 和 WebSocket 服务封装，采用四层架构设计。

## 架构说明

本项目采用清晰的四层架构模式：

```
├── entry/          # L1 入口层 - 应用唯一对外接入点
├── coordinator/    # L2 协调层 - 编排分子能力、封装对外API
├── molecules/      # L3 分子层 - 业务功能单元（工作流、队列、图片等）
├── atoms/          # L4 原子层 - 最小可运行单元（HTTP、文件、验证等）
├── models/         # 数据模型定义
├── core/           # 核心配置和异常
└── constants/      # 常量定义
```

### 架构原则

- **依赖方向严格单向**: L1 → L2 → L3 → L4
- **分子之间禁止相互调用**: 所有协作经由协调层中转
- **原子之间禁止相互调用**: 所有组合由分子层完成
- **每层对外明确定义接口**: 隐藏内部实现细节

## 功能特性

- **工作流管理**: 提交、查询、中断工作流
- **队列管理**: 查询队列状态、清空队列
- **图片处理**: 上传输入图片、下载生成图片
- **实时通信**: WebSocket 实时推送执行进度
- **异步支持**: 全异步实现，高性能

## 安装

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 配置

编辑 `.env` 文件（可选）：

```env
# 应用配置
APP_NAME="FastAPI ComfyUI Service"
APP_VERSION="1.0.0"
HOST="0.0.0.0"
PORT="8000"
DEBUG="True"

# ComfyUI 配置
COMFYUI_HOST="127.0.0.1"
COMFYUI_PORT="8188"
COMFYUI_TIMEOUT="300"
```

## 运行

```bash
# 方式1: 直接运行
python -m app.entry.main

# 方式2: 使用 uvicorn
uvicorn app.entry.main:app --reload

# 方式3: 指定 host 和 port
uvicorn app.entry.main:app --host 0.0.0.0 --port 8000 --reload
```

## API 文档

启动服务后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 接口

### 工作流管理

#### 提交工作流（异步）
```http
POST /api/v1/workflows/submit
Content-Type: application/json

{
  "workflow": {
    "1": {
      "class_type": "CheckpointLoaderSimple",
      "inputs": {"ckpt_name": "model.safetensors"}
    }
  },
  "client_id": "my_client"
}
```

#### 获取工作流历史
```http
GET /api/v1/workflows/{prompt_id}/history
```

#### 获取工作流生成的图片
```http
GET /api/v1/workflows/{prompt_id}/images
```

#### 中断工作流
```http
POST /api/v1/workflows/interrupt
Content-Type: application/json

{
  "prompt_id": "optional-specific-prompt-id"
}
```

### 队列管理

#### 获取队列状态
```http
GET /api/v1/queue/status
```

#### 清空队列
```http
POST /api/v1/queue/clear
Content-Type: application/json

{
  "clear": true
}
```

### 图片处理

#### 上传图片
```http
POST /api/v1/images/upload
Content-Type: multipart/form-data

file: <图片文件>
overwrite: true
```

#### 下载图片
```http
GET /api/v1/images/download?filename=output.png&subfolder=&type=output
```

#### 获取图片 URL
```http
GET /api/v1/images/url?filename=output.png&subfolder=&type=output
```

### WebSocket

#### 建立 WebSocket 连接
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/my_client_id');

// 提交工作流
ws.send(JSON.stringify({
  type: 'submit',
  data: {
    workflow: { /* 工作流 JSON */ }
  }
}));

// 接收消息
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch(message.type) {
    case 'status':
      console.log('队列状态:', message.data);
      break;
    case 'progress':
      console.log('进度:', message.data.value, '/', message.data.max);
      break;
    case 'executing':
      console.log('正在执行节点:', message.data.node);
      break;
    case 'executed':
      console.log('节点执行完成:', message.data.node);
      break;
    case 'result':
      console.log('工作流完成:', message.data);
      break;
    case 'execution_error':
      console.error('执行错误:', message.data);
      break;
  }
};
```

## WebSocket 消息类型

| 类型 | 方向 | 说明 |
|------|------|------|
| `submit` | 客户端→服务端 | 提交工作流 |
| `status` | 服务端→客户端 | 队列状态更新 |
| `progress` | 服务端→客户端 | 进度更新 |
| `executing` | 服务端→客户端 | 节点开始执行 |
| `executed` | 服务端→客户端 | 节点执行完成 |
| `result` | 服务端→客户端 | 工作流执行结果 |
| `execution_error` | 服务端→客户端 | 执行错误 |
| `system` | 服务端→客户端 | 系统消息 |

## 项目结构

```
fastapi_comfyui/
├── app/
│   ├── entry/              # L1 入口层
│   │   └── main.py         # 应用入口
│   ├── coordinator/        # L2 协调层
│   │   ├── workflow_coordinator.py
│   │   ├── queue_coordinator.py
│   │   ├── image_coordinator.py
│   │   └── websocket_coordinator.py
│   ├── molecules/          # L3 分子层
│   │   ├── workflow_molecule.py
│   │   ├── queue_molecule.py
│   │   ├── history_molecule.py
│   │   ├── image_molecule.py
│   │   └── websocket_molecule.py
│   ├── atoms/              # L4 原子层
│   │   ├── http_atom.py
│   │   ├── file_atom.py
│   │   ├── websocket_atom.py
│   │   ├── validation_atom.py
│   │   └── time_atom.py
│   ├── models/             # 数据模型
│   │   ├── workflow.py
│   │   ├── queue.py
│   │   ├── image.py
│   │   └── websocket.py
│   ├── core/               # 核心配置
│   │   ├── config.py
│   │   └── exceptions.py
│   └── constants/          # 常量定义
│       └── comfyui.py
├── input/                  # 输入图片目录
├── output/                 # 输出图片目录
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 错误码

| 错误码 | 说明 |
|--------|------|
| `CONNECTION_ERROR` | 无法连接到 ComfyUI |
| `WORKFLOW_VALIDATION_ERROR` | 工作流验证失败 |
| `WORKFLOW_EXECUTION_ERROR` | 工作流执行错误 |
| `QUEUE_OPERATION_ERROR` | 队列操作错误 |
| `FILE_OPERATION_ERROR` | 文件操作错误 |
| `IMAGE_NOT_FOUND` | 图片未找到 |
| `TASK_TIMEOUT` | 任务执行超时 |
| `WEBSOCKET_ERROR` | WebSocket 错误 |

## 开发

```bash
# 运行测试
pytest

# 代码格式化
black app/

# 代码检查
ruff check app/
```

## 注意事项

1. 确保 ComfyUI 服务已启动并可访问
2. 工作流 JSON 必须是 API 格式（通过 ComfyUI 的 "Save (API Format)" 导出）
3. WebSocket 连接需要提供唯一的 client_id
4. 默认情况下，图片会保存在项目的 `input` 和 `output` 目录
