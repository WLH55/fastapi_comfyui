# ComfyUI 多 GPU 负载均衡部署指南

本文档说明如何在多 GPU 环境下部署 ComfyUI，实现高效的负载均衡，充分发挥硬件性能。

---

## 目录

- [问题背景](#问题背景)
- [部署场景分析](#部署场景分析)
- [负载均衡方案](#负载均衡方案)
- [完整实现代码](#完整实现代码)
- [部署脚本](#部署脚本)
- [使用示例](#使用示例)
- [监控与运维](#监控与运维)

---

## 问题背景

### 为什么需要负载均衡？

```
默认情况（Nginx least_conn）：

请求1 ──> 实例:8188 (GPU0) ──> 队列: [任务1, 任务2, 任务3] ──> GPU 忙
请求2 ──> 实例:8188 (GPU0) ──> 连接数少，继续分配 ──> X
请求3 ──> 实例:8188 (GPU0) ──> 连接数少，继续分配 ──> X
        实例:8189 (GPU1) ──> 空闲！但没任务 ──> 浪费
        实例:8190 (GPU2) ──> 空闲！但没任务 ──> 浪费
        实例:8191 (GPU3) ──> 空闲！但没任务 ──> 浪费
```

**核心问题**：
- Nginx 的 `least_conn` 只看 HTTP 连接数，看不到实例内部的队列状态
- 一个生图任务执行期间（几十秒到几分钟），HTTP 连接早已关闭
- 导致所有任务都堆积到同一个实例，其他 GPU 空闲

**解决方案**：主动查询每个实例的 `/queue` 接口，获取真实负载状态，实现队列感知的调度。

---

## 部署场景分析

### 场景一：单机单卡

```
客户端请求 ──> ComfyUI 实例 ──> GPU 0
                  ↑
            内部队列自动排队
```

**结论**：单机单卡部署多实例**不会提升性能**，反而会显存冲突。使用 ComfyUI 自带的队列即可。

---

### 场景二：单机多卡

```
                    负载均衡器
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
   ┌───▼────┐       ┌───▼────┐       ┌───▼────┐
   │ GPU 0  │       │ GPU 1  │       │ GPU 2  │
   │ :8188  │       │ :8189  │       │ :8190  │
   └────────┘       └────────┘       └────────┘
```

**推荐方案**：每个 GPU 绑定一个 ComfyUI 实例，使用队列感知的负载均衡器。

---

### 场景三：多机多卡

```
                    负载均衡器
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
   ┌───▼────┐       ┌───▼────┐       ┌───▼────┐
   │ 机器 A  │       │ 机器 B  │       │ 机器 C  │
   │GPU 0,1  │       │GPU 0,1  │       │GPU 0,1  │
   │:8188,89 │       │:8188,89 │       │:8188,89 │
   └─────────┘       └─────────┘       └─────────┘
```

**推荐方案**：集群部署 + 带健康检查的负载均衡器。

---

## 负载均衡方案

### 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **Nginx 轮询** | 简单易用 | 不能感知队列，分配不均 | ⭐⭐ |
| **Nginx least_conn** | 考虑连接数 | 看不到实际队列，仍有不均 | ⭐⭐⭐ |
| **Nginx + 公平队列** | 较好分配 | 需要第三方模块，配置复杂 | ⭐⭐⭐ |
| **FastAPI 主动轮询** | 精确感知队列 | 需要额外一层 | ⭐⭐⭐⭐⭐ |
| **Consul 服务发现** | 动态扩展 | 架构复杂，学习成本高 | ⭐⭐⭐⭐ |

---

### 推荐方案：FastAPI 队列感知调度器

**核心思路**：

1. 定期轮询所有实例的 `/queue` 接口
2. 获取每个实例的 `queue_running`（正在执行）和 `queue_pending`（等待中）
3. 优先选择 `queue_running=0` 的空闲实例
4. 如果都忙碌，选择总负载最少的实例

**调度流程**：

```
┌─────────────────────────────────────────────────────────────────┐
│  步骤1: 轮询所有实例的 /queue 接口                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  实例:8188 (GPU0) → running: 1, pending: 3 → total: 4          │
│  实例:8189 (GPU1) → running: 0, pending: 0 → total: 0 ✓ 空闲    │
│  实例:8190 (GPU2) → running: 0, pending: 0 → total: 0 ✓ 空闲    │
│  实例:8191 (GPU3) → running: 1, pending: 1 → total: 2          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  步骤2: 选择空闲实例（running=0 且 pending 最小）                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GPU1 和 GPU2 都空闲，随机选择其一                               │
│  → 选中 GPU1 (实例:8189)                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  步骤3: 提交任务到选中的实例                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  POST http://127.0.0.1:8189/prompt                              │
│  {"prompt": workflow, "client_id": "api"}                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 完整实现代码

### 调度器核心代码

```python
# gpu_load_balancer.py
import asyncio
import httpx
from typing import List, Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class GPULoadBalancer:
    """
    GPU 队列感知的负载均衡器

    功能特性：
    - 主动查询每个实例的 /queue 接口，获取真实负载
    - 优先分配给完全空闲的 GPU
    - 健康检查，自动剔除不可用实例
    - 支持加权调度（不同性能的 GPU）
    """

    def __init__(
        self,
        instances: List[str],
        check_interval: float = 0.5,
        weights: Dict[str, float] = None
    ):
        """
        Args:
            instances: 实例列表 ["http://127.0.0.1:8188", ...]
            check_interval: 队列状态检查间隔（秒）
            weights: GPU 权重 {"http://127.0.0.1:8188": 2.0, ...}
                    数值越大性能越强，用于不同型号 GPU 混合部署
        """
        self.instances = instances
        self.check_interval = check_interval
        self.weights = weights or {url: 1.0 for url in instances}
        self.client = httpx.AsyncClient(timeout=5.0)
        self._monitor_task: Optional[asyncio.Task] = None

        # 初始化实例状态
        self.instance_states: Dict[str, dict] = {}
        for url in instances:
            self.instance_states[url] = {
                "queue_running": 0,
                "queue_pending": 0,
                "total_load": 0,
                "healthy": True,
                "last_error": None,
                "last_update": datetime.min,
                "gpu_id": self._extract_gpu_id(url)
            }

    def _extract_gpu_id(self, url: str) -> int:
        """从 URL 端口推算 GPU ID（假设 8188=GPU0, 8189=GPU1...）"""
        try:
            port = int(url.split(":")[-1])
            return port - 8188
        except:
            return -1

    async def _update_instance_state(self, url: str) -> bool:
        """
        更新单个实例的队列状态

        Returns:
            bool: 实例是否健康
        """
        try:
            response = await self.client.get(f"{url}/queue")
            if response.status_code == 200:
                data = response.json()
                running = len(data.get("queue_running", []))
                pending = len(data.get("queue_pending", []))

                old_healthy = self.instance_states[url]["healthy"]
                self.instance_states[url].update({
                    "queue_running": running,
                    "queue_pending": pending,
                    "total_load": running + pending,
                    "healthy": True,
                    "last_error": None,
                    "last_update": datetime.now()
                })

                # 状态恢复日志
                if not old_healthy:
                    logger.info(f"实例 {url} 已恢复健康")

                return True
            else:
                raise Exception(f"HTTP {response.status_code}")

        except asyncio.TimeoutError:
            error = "连接超时"
        except httpx.ConnectError:
            error = "连接失败"
        except Exception as e:
            error = str(e)

        self.instance_states[url].update({
            "healthy": False,
            "last_error": error,
            "last_update": datetime.now()
        })
        logger.warning(f"实例 {url} 不可用: {error}")
        return False

    async def _monitor_loop(self):
        """持续监控所有实例状态"""
        logger.info("开始监控 GPU 实例状态...")
        while True:
            tasks = [
                self._update_instance_state(url)
                for url in self.instances
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(self.check_interval)

    def start_monitoring(self):
        """启动监控任务"""
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info(f"GPU 实例监控已启动 (检查间隔: {self.check_interval}s)")

    def stop_monitoring(self):
        """停止监控任务"""
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
            logger.info("GPU 实例监控已停止")

    def get_least_loaded_instance(self) -> Optional[str]:
        """
        获取负载最低的健康实例

        选择逻辑：
        1. 过滤出健康的实例
        2. 优先选择 running=0 的实例（完全空闲）
        3. 如果都忙碌，选择加权负载最低的实例
        """
        # 过滤出健康的实例
        healthy_instances = {
            url: state
            for url, state in self.instance_states.items()
            if state["healthy"]
        }

        if not healthy_instances:
            logger.error("没有可用的健康实例！")
            return None

        # 分组：有空闲的 vs 都在忙的
        idle_instances = {
            url: state
            for url, state in healthy_instances.items()
            if state["queue_running"] == 0
        }

        if idle_instances:
            # 优先分配给完全空闲的实例
            # 按 pending 数量排序，选择最少的
            selected = min(idle_instances.items(), key=lambda x: x[1]["queue_pending"])
            logger.info(
                f"选择空闲实例: {selected[0]} (GPU{selected[1]['gpu_id']}, "
                f"pending: {selected[1]['queue_pending']})"
            )
            return selected[0]
        else:
            # 所有实例都在运行，选择加权负载最低的
            def weighted_load(item):
                url, state = item
                weight = self.weights.get(url, 1.0)
                return state["total_load"] / weight if weight > 0 else float('inf')

            selected = min(healthy_instances.items(), key=weighted_load)
            weight = self.weights[selected[0]]
            logger.info(
                f"选择负载最低实例: {selected[0]} (GPU{selected[1]['gpu_id']}, "
                f"负载: {selected[1]['total_load']}, 权重: {weight})"
            )
            return selected[0]

    async def submit_workflow(
        self,
        workflow: dict,
        client_id: str = "api",
        timeout: float = 30.0
    ) -> dict:
        """
        提交工作流到最优实例

        Args:
            workflow: ComfyUI 工作流 JSON（API 格式）
            client_id: 客户端标识，用于 WebSocket 推送
            timeout: 请求超时时间

        Returns:
            {
                "prompt_id": str,
                "instance": str,
                "gpu_id": int,
                "original_response": dict
            }
        """
        instance = self.get_least_loaded_instance()
        if not instance:
            return {
                "error": "No healthy instances available",
                "healthy_instances": sum(1 for s in self.instance_states.values() if s["healthy"])
            }

        try:
            response = await self.client.post(
                f"{instance}/prompt",
                json={
                    "prompt": workflow,
                    "client_id": client_id
                },
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()

            return {
                "prompt_id": result.get("prompt_id"),
                "instance": instance,
                "gpu_id": self.instance_states[instance]["gpu_id"],
                "number": result.get("number"),
                "node_errors": result.get("node_errors", {}),
                "original_response": result
            }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"提交到 {instance} 失败: {error_msg}")
            return {"error": error_msg, "instance": instance}

        except asyncio.TimeoutError:
            logger.error(f"提交到 {instance} 超时")
            return {"error": "请求超时", "instance": instance}

        except Exception as e:
            logger.error(f"提交到 {instance} 失败: {e}")
            return {"error": str(e), "instance": instance}

    async def get_queue_info(self, url: str) -> Optional[dict]:
        """获取指定实例的队列信息"""
        try:
            response = await self.client.get(f"{url}/queue")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"获取 {url} 队列信息失败: {e}")
        return None

    async def get_history(self, url: str, prompt_id: str = None) -> Optional[dict]:
        """获取指定实例的历史记录"""
        try:
            if prompt_id:
                response = await self.client.get(f"{url}/history/{prompt_id}")
            else:
                response = await self.client.get(f"{url}/history")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"获取 {url} 历史记录失败: {e}")
        return None

    def get_status(self) -> dict:
        """
        获取所有实例的状态概览

        Returns:
            {
                "instances": {
                    "url": {
                        "gpu_id": int,
                        "running": int,
                        "pending": int,
                        "total": int,
                        "healthy": bool,
                        "last_error": str
                    }
                },
                "summary": {
                    "total_instances": int,
                    "healthy_instances": int,
                    "total_running": int,
                    "total_pending": int
                }
            }
        """
        instances_status = {}
        for url, state in self.instance_states.items():
            instances_status[url] = {
                "gpu_id": state["gpu_id"],
                "running": state["queue_running"],
                "pending": state["queue_pending"],
                "total": state["total_load"],
                "healthy": state["healthy"],
                "last_error": state["last_error"],
                "last_update": state["last_update"].isoformat()
            }

        total_running = sum(s["queue_running"] for s in self.instance_states.values())
        total_pending = sum(s["queue_pending"] for s in self.instance_states.values())
        healthy_count = sum(1 for s in self.instance_states.values() if s["healthy"])

        return {
            "instances": instances_status,
            "summary": {
                "total_instances": len(self.instances),
                "healthy_instances": healthy_count,
                "total_running": total_running,
                "total_pending": total_pending,
                "total_load": total_running + total_pending
            }
        }

    async def wait_for_completion(
        self,
        prompt_id: str,
        instance_url: str,
        timeout: int = 600,
        check_interval: float = 1.0
    ) -> Optional[dict]:
        """
        等待指定 prompt 执行完成

        Args:
            prompt_id: 工作流 ID
            instance_url: 提交到的实例 URL
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）

        Returns:
            执行完成后的历史记录，或 None（超时/失败）
        """
        import time
        start_time = time.time()

        while True:
            # 超时检查
            if time.time() - start_time > timeout:
                logger.warning(f"等待 {prompt_id} 超时")
                return None

            # 检查队列状态
            queue_info = await self.get_queue_info(instance_url)
            if not queue_info:
                await asyncio.sleep(check_interval)
                continue

            # 提取所有正在运行和等待的 prompt_id
            running = [item[0] for item in queue_info.get("queue_running", [])]
            pending = [item[0] for item in queue_info.get("queue_pending", [])]

            # 如果不在队列中，说明已完成
            if prompt_id not in running + pending:
                # 获取历史记录
                history = await self.get_history(instance_url, prompt_id)
                if history and prompt_id in history:
                    return history[prompt_id]

            await asyncio.sleep(check_interval)

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()
```

---

### FastAPI 服务包装

```python
# api_server.py
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from gpu_load_balancer import GPULoadBalancer

logger = logging.getLogger(__name__)
app = FastAPI(
    title="ComfyUI GPU Load Balancer",
    description="多 GPU 队列感知的负载均衡服务",
    version="1.0.0"
)

# ============ 配置 ============

INSTANCES = [
    "http://127.0.0.1:8188",
    "http://127.0.0.1:8189",
    "http://127.0.0.1:8190",
    "http://127.0.0.1:8191",
]

# GPU 权重配置（可选，用于不同性能的 GPU）
# 例如: A100 的权重是 3090 的 2 倍
GPU_WEIGHTS = {
    "http://127.0.0.1:8188": 1.0,
    "http://127.0.0.1:8189": 1.0,
    "http://127.0.0.1:8190": 1.0,
    "http://127.0.0.1:8191": 1.0,
}

# 初始化负载均衡器
lb = GPULoadBalancer(
    instances=INSTANCES,
    check_interval=0.5,
    weights=GPU_WEIGHTS
)


# ============ 数据模型 ============

class GenerateRequest(BaseModel):
    """生图请求模型"""
    workflow: Dict[str, Any] = Field(..., description="ComfyUI 工作流（API 格式）")
    client_id: str = Field(default="api", description="客户端标识")
    wait_for_completion: bool = Field(default=False, description="是否等待执行完成")
    timeout: int = Field(default=600, description="等待超时时间（秒）")

    class Config:
        json_schema_extra = {
            "example": {
                "workflow": {
                    "1": {
                        "class_type": "CheckpointLoaderSimple",
                        "inputs": {"ckpt_name": "v1-5-pruned.safetensors"}
                    }
                },
                "client_id": "my_app",
                "wait_for_completion": False
            }
        }


class GenerateResponse(BaseModel):
    """生图响应模型"""
    prompt_id: Optional[str] = None
    assigned_gpu: Optional[int] = None
    assigned_instance: Optional[str] = None
    message: str
    error: Optional[str] = None


# ============ 生命周期事件 ============

@app.on_event("startup")
async def startup():
    """启动时初始化"""
    logger.info("正在启动负载均衡服务...")
    lb.start_monitoring()
    logger.info("负载均衡服务已启动")
    logger.info(f"管理的实例: {INSTANCES}")


@app.on_event("shutdown")
async def shutdown():
    """关闭时清理"""
    logger.info("正在关闭负载均衡服务...")
    lb.stop_monitoring()
    await lb.close()
    logger.info("负载均衡服务已关闭")


# ============ API 端点 ============

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    提交生成任务

    自动选择负载最低的 GPU 实例执行工作流
    """
    result = await lb.submit_workflow(
        workflow=request.workflow,
        client_id=request.client_id
    )

    if "error" in result:
        raise HTTPException(
            status_code=503,
            detail={
                "error": result["error"],
                "message": "任务提交失败，请稍后重试"
            }
        )

    # 如果需要等待完成
    if request.wait_for_completion:
        logger.info(f"等待任务 {result['prompt_id']} 完成...")
        history = await lb.wait_for_completion(
            prompt_id=result["prompt_id"],
            instance_url=result["instance"],
            timeout=request.timeout
        )

        if history:
            return GenerateResponse(
                prompt_id=result["prompt_id"],
                assigned_gpu=result["gpu_id"],
                assigned_instance=result["instance"],
                message=f"任务已完成，分配到 GPU {result['gpu_id']}"
            )
        else:
            return GenerateResponse(
                prompt_id=result["prompt_id"],
                assigned_gpu=result["gpu_id"],
                assigned_instance=result["instance"],
                message=f"任务已提交，等待超时",
                error="TIMEOUT"
            )

    return GenerateResponse(
        prompt_id=result["prompt_id"],
        assigned_gpu=result["gpu_id"],
        assigned_instance=result["instance"],
        message=f"任务已分配到 GPU {result['gpu_id']}"
    )


@app.get("/status")
async def get_status():
    """
    查看所有 GPU 实例状态

    返回每个实例的队列大小和健康状态
    """
    status = lb.get_status()

    return JSONResponse(content={
        "success": True,
        "data": status
    })


@app.get("/health")
async def health_check():
    """
    健康检查端点

    用于容器编排（K8s）或监控系统的健康检查
    """
    status = lb.get_status()
    healthy_count = status["summary"]["healthy_instances"]

    if healthy_count == 0:
        raise HTTPException(
            status_code=503,
            detail="No healthy instances available"
        )

    return JSONResponse(content={
        "status": "healthy",
        "healthy_instances": healthy_count,
        "total_instances": status["summary"]["total_instances"]
    })


@app.get("/instances")
async def list_instances():
    """获取所有实例列表"""
    return {
        "instances": [
            {
                "url": url,
                "gpu_id": lb._extract_gpu_id(url),
                "weight": lb.weights.get(url, 1.0)
            }
            for url in INSTANCES
        ]
    }


@app.get("/queue/{instance_url:path}")
async def get_instance_queue(instance_url: str):
    """
    获取指定实例的队列状态

    Args:
        instance_url: 实例 URL（如 http://127.0.0.1:8188）
    """
    # URL 解码
    from urllib.parse import unquote
    instance_url = unquote(instance_url)

    queue_info = await lb.get_queue_info(instance_url)
    if queue_info is None:
        raise HTTPException(status_code=404, detail="实例不可达")

    return queue_info


@app.post("/test/workflow")
async def test_workflow():
    """
    测试端点：返回一个简单的工作流用于测试
    """
    test_workflow = {
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
                "seed": 42,
                "steps": 20,
                "cfg": 7,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["2", 0]
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
                "filename_prefix": "test"
            }
        }
    }

    return {"workflow": test_workflow}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9999,
        log_level="info"
    )
```

---

## 部署脚本

### 一键启动脚本（单机多卡）

```bash
#!/bin/bash
# scripts/start_multi_gpu.sh

set -e

# ============ 配置区 ============

# ComfyUI 安装目录
COMFYUI_DIR="${COMFYUI_DIR:-/path/to/ComfyUI}"

# GPU 列表（CUDA 设备 ID）
GPUS=(${GPUS:-0 1 2 3})

# 基础端口
BASE_PORT=${BASE_PORT:-8188}

# 日志目录
LOG_DIR="$COMFYUI_DIR/logs"

# ComfyUI 启动参数
COMFYUI_ARGS="--listen 127.0.0.1 --gpu-only --force-fp16"

# ============ 函数定义 ============

log_info() {
    echo -e "\033[1;32m[INFO]\033[0m $1"
}

log_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

check_comfyui() {
    if [ ! -d "$COMFYUI_DIR" ]; then
        log_error "ComfyUI 目录不存在: $COMFYUI_DIR"
        exit 1
    fi

    if [ ! -f "$COMFYUI_DIR/main.py" ]; then
        log_error "ComfyUI main.py 不存在: $COMFYUI_DIR/main.py"
        exit 1
    fi
}

start_instance() {
    local gpu_id=$1
    local port=$2

    log_info "启动 GPU $gpu_id on port $port..."

    CUDA_VISIBLE_DEVICES=$gpu_id nohup python \
        "$COMFYUI_DIR/main.py" \
        $COMFYUI_ARGS \
        --port $port \
        > "$LOG_DIR/gpu${gpu_id}.log" 2>&1 &

    echo $! > "$LOG_DIR/gpu${gpu_id}.pid"
}

wait_for_instance() {
    local gpu_id=$1
    local port=$2
    local max_wait=30
    local waited=0

    log_info "等待 GPU $gpu_id 启动..."

    while [ $waited -lt $max_wait ]; do
        if curl -s "http://127.0.0.1:$port/system_stats" > /dev/null 2>&1; then
            log_info "✓ GPU $gpu_id 启动成功"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done

    log_error "✗ GPU $gpu_id 启动超时"
    log_error "查看日志: $LOG_DIR/gpu${gpu_id}.log"
    return 1
}

start_scheduler() {
    local scheduler_port=${SCHEDULER_PORT:-9999}

    log_info "启动负载均衡调度器..."

    nohup python api_server.py \
        --port $scheduler_port \
        > "$LOG_DIR/scheduler.log" 2>&1 &

    echo $! > "$LOG_DIR/scheduler.pid"

    sleep 2

    if curl -s "http://127.0.0.1:$scheduler_port/health" > /dev/null 2>&1; then
        log_info "✓ 调度器启动成功"
    else
        log_error "✗ 调度器启动失败"
        return 1
    fi
}

# ============ 主流程 ============

main() {
    log_info "=== ComfyUI 多 GPU 部署 ==="
    log_info "ComfyUI 目录: $COMFYUI_DIR"
    log_info "GPU 列表: ${GPUS[@]}"
    log_info ""

    # 检查环境
    check_comfyui

    # 创建日志目录
    mkdir -p "$LOG_DIR"

    # 启动 ComfyUI 实例
    log_info "=== 启动 ComfyUI 实例 ==="

    for i in "${!GPUS[@]}"; do
        gpu_id=${GPUS[$i]}
        port=$((BASE_PORT + i))

        start_instance $gpu_id $port
        sleep 1
    done

    # 等待所有实例启动
    log_info ""
    log_info "=== 等待实例启动 ==="

    for i in "${!GPUS[@]}"; do
        gpu_id=${GPUS[$i]}
        port=$((BASE_PORT + i))

        if ! wait_for_instance $gpu_id $port; then
            log_error "部分实例启动失败，正在退出..."
            exit 1
        fi
    done

    # 启动调度器
    log_info ""
    start_scheduler

    # 完成
    log_info ""
    log_info "=== 部署完成 ==="
    log_info ""
    log_info "负载均衡器地址: http://127.0.0.1:${SCHEDULER_PORT:-9999}"
    log_info ""
    log_info "查看状态:"
    log_info "  curl http://127.0.0.1:${SCHEDULER_PORT:-9999}/status"
    log_info ""
    log_info "提交任务:"
    log_info "  curl -X POST http://127.0.0.1:${SCHEDULER_PORT:-9999}/generate -d @workflow.json"
    log_info ""
    log_info "查看日志:"
    log_info "  tail -f $LOG_DIR/scheduler.log"
    log_info "  tail -f $LOG_DIR/gpu0.log"
    log_info ""
}

main "$@"
```

### 停止脚本

```bash
#!/bin/bash
# scripts/stop_multi_gpu.sh

LOG_DIR="${LOG_DIR:-/path/to/ComfyUI/logs}"

echo "=== 停止 ComfyUI 多 GPU 实例 ==="

# 停止调度器
if [ -f "$LOG_DIR/scheduler.pid" ]; then
    PID=$(cat "$LOG_DIR/scheduler.pid")
    echo "停止调度器 (PID: $PID)..."
    kill $PID 2>/dev/null || true
    rm -f "$LOG_DIR/scheduler.pid"
fi

# 停止所有 GPU 实例
for pid_file in "$LOG_DIR"/gpu*.pid; do
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        echo "停止 GPU 实例 (PID: $PID)..."
        kill $PID 2>/dev/null || true
        rm -f "$pid_file"
    fi
done

echo "完成"
```

### systemd 服务配置（推荐生产环境）

```ini
# /etc/systemd/system/comfyui-gpu@.service
# 用法: systemctl start comfyui-gpu@0 (启动 GPU 0)

[Unit]
Description=ComfyUI on GPU %i
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ComfyUI
Environment="CUDA_VISIBLE_DEVICES=%i"
ExecStart=/usr/bin/python /path/to/ComfyUI/main.py --listen 127.0.0.1 --port=%i --gpu-only --force-fp16
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/comfyui-scheduler.service

[Unit]
Description=ComfyUI Load Balancer Scheduler
After=network.target comfyui-gpu@0.service comfyui-gpu@1.service comfyui-gpu@2.service comfyui-gpu@3.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/scripts
ExecStart=/usr/bin/python /path/to/api_server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 使用示例

### 1. 基础调用

```bash
# 启动服务
bash scripts/start_multi_gpu.sh

# 提交任务
curl -X POST "http://localhost:9999/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": {
      "1": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "v1-5-pruned.safetensors"}
      },
      "2": {
        "class_type": "CLIPTextEncode",
        "inputs": {
          "text": "a sunset over mountains",
          "clip": ["1", 1]
        }
      },
      "3": {
        "class_type": "KSampler",
        "inputs": {
          "seed": 42,
          "steps": 20,
          "cfg": 7,
          "sampler_name": "euler",
          "scheduler": "normal",
          "denoise": 1.0,
          "model": ["1", 0],
          "positive": ["2", 0],
          "negative": ["2", 0]
        }
      },
      "4": {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["3", 0], "vae": ["1", 2]}
      },
      "5": {
        "class_type": "SaveImage",
        "inputs": {"images": ["4", 0], "filename_prefix": "output"}
      }
    },
    "client_id": "my_app"
  }'
```

### 2. Python 客户端

```python
import requests
import json

SCHEDULER_URL = "http://localhost:9999"

def generate_image(workflow, client_id="python_client", wait=False):
    """提交生图任务"""
    response = requests.post(
        f"{SCHEDULER_URL}/generate",
        json={
            "workflow": workflow,
            "client_id": client_id,
            "wait_for_completion": wait
        }
    )
    return response.json()

# 查看状态
status = requests.get(f"{SCHEDULER_URL}/status").json()
print(json.dumps(status, indent=2))

# 提交任务
result = generate_image(workflow)
print(f"任务已提交到 GPU {result['assigned_gpu']}")
```

### 3. 批量提交

```python
import asyncio
import aiohttp

async def batch_generate(workflows, scheduler_url="http://localhost:9999"):
    """批量提交多个任务"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, workflow in enumerate(workflows):
            task = session.post(
                f"{scheduler_url}/generate",
                json={
                    "workflow": workflow,
                    "client_id": f"batch_{i}"
                }
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        return [await r.json() for r in responses]

# 使用
workflows = [workflow1, workflow2, workflow3, ...]
results = asyncio.run(batch_generate(workflows))

for r in results:
    print(f"任务 {r['prompt_id']} -> GPU {r['assigned_gpu']}")
```

---

## 监控与运维

### 状态监控

```bash
# 查看所有 GPU 状态
curl http://localhost:9999/status | jq

# 输出示例
{
  "success": true,
  "data": {
    "instances": {
      "http://127.0.0.1:8188": {
        "gpu_id": 0,
        "running": 1,
        "pending": 2,
        "total": 3,
        "healthy": true,
        "last_error": null
      },
      "http://127.0.0.1:8189": {
        "gpu_id": 1,
        "running": 0,
        "pending": 0,
        "total": 0,
        "healthy": true,
        "last_error": null
      }
    },
    "summary": {
      "total_instances": 4,
      "healthy_instances": 4,
      "total_running": 1,
      "total_pending": 2,
      "total_load": 3
    }
  }
}
```

### 日志查看

```bash
# 调度器日志
tail -f logs/scheduler.log

# 各 GPU 实例日志
tail -f logs/gpu0.log
tail -f logs/gpu1.log
```

### 性能优化建议

| 优化项 | 说明 |
|--------|------|
| **显存优化** | 使用 `--gpu-only --force-fp16` 减少 VRAM 占用 |
| **批处理** | 在 KSampler 节点设置 `batch_size` 一次生成多张 |
| **模型预加载** | 启动后空跑一次让模型常驻显存 |
| **调整检查间隔** | 根据任务时长调整 `check_interval`（默认 0.5s） |
| **加权调度** | 不同性能 GPU 设置不同权重 |

### 常见问题

**Q: 为什么任务都集中到一个 GPU？**

A: 检查调度器是否正常启动，查看 `/status` 确认各实例负载。

**Q: 实例显示不健康？**

A: 检查 ComfyUI 进程是否正常运行，查看对应 GPU 的日志文件。

**Q: 如何处理不同型号的 GPU？**

A: 在 `GPU_WEIGHTS` 中为高性能 GPU 设置更高权重。

---

## 总结

| 部署场景 | 推荐方案 |
|----------|----------|
| 单机单卡 | 单实例，使用内置队列 |
| 单机多卡 | 每卡一实例 + FastAPI 调度器 |
| 多机多卡 | 集群部署 + 带健康检查的调度器 |

| 负载均衡策略 | 适用场景 |
|--------------|----------|
| 轮询 | 任务耗时相近 |
| least_conn | 任务耗时不一 |
| **队列感知** | **推荐，最优分配** |

通过队列感知的负载均衡，可以确保多 GPU 环境下任务均匀分配，充分发挥硬件性能。
