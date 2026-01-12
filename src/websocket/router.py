"""
WebSocket 领域路由

WebSocket API 路由定义
"""

import asyncio
import json
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status

from src.websocket.schemas import WebSocketSubmitRequest
from src.websocket.service import (
    wait_for_workflow_completion,
    connection_manager,
)
from src.websocket.constants import WebSocketMessageType
from src.workflows.service import submit_workflow_to_comfyui
from src.exceptions import WebSocketError, WorkflowValidationError, ComfyUIConnectionError


# 创建路由器
router = APIRouter()


@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket 端点

    建立双向通信，支持：
    - 提交工作流并实时接收进度
    - 接收执行状态更新
    - 接收节点执行结果

    客户端消息格式：
    ```json
    {
        "type": "submit",
        "data": {
            "workflow": {...}
        }
    }
    ```

    服务端消息格式：
    ```json
    {
        "type": "progress|executing|executed|result",
        "data": {...}
    }
    ```
    """
    try:
        # 接受连接
        await connection_manager.connect(client_id, websocket)

        # 发送连接成功消息
        await connection_manager.send_to_client(
            client_id,
            WebSocketMessageType.SYSTEM,
            {
                "message": "WebSocket 连接已建立",
                "client_id": client_id
            }
        )

        # 监听客户端消息
        while True:
            try:
                # 接收消息
                data = await websocket.receive_json()

                # 处理不同类型的消息
                message_type = data.get("type")

                if message_type == "submit":
                    # 提交工作流
                    await _handle_workflow_submit(client_id, data.get("data", {}))

                elif message_type == "ping":
                    # 心跳消息
                    await connection_manager.send_to_client(
                        client_id,
                        "pong",
                        {"timestamp": asyncio.get_event_loop().time()}
                    )

                else:
                    # 未知消息类型
                    await connection_manager.send_to_client(
                        client_id,
                        WebSocketMessageType.SYSTEM,
                        {
                            "message": f"未知的消息类型: {message_type}"
                        }
                    )

            except WebSocketDisconnect:
                # 客户端断开连接
                connection_manager.disconnect(client_id)
                break

            except json.JSONDecodeError:
                # JSON 解析错误
                await connection_manager.send_to_client(
                    client_id,
                    WebSocketMessageType.SYSTEM,
                    {
                        "message": "无效的 JSON 消息"
                    }
                )

            except Exception as e:
                # 其他错误
                await connection_manager.send_to_client(
                    client_id,
                    WebSocketMessageType.SYSTEM,
                    {
                        "message": f"处理消息时出错: {str(e)}"
                    }
                )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "WEBSOCKET_ERROR",
                "message": f"WebSocket 连接失败: {str(e)}"
            }
        )


async def _handle_workflow_submit(
    client_id: str,
    data: Dict[str, Any]
) -> None:
    """
    处理通过 WebSocket 提交的工作流

    Args:
        client_id: 客户端 ID
        data: 工作流数据

    Raises:
        WebSocketError: 处理失败时
    """
    try:
        # 提取工作流
        workflow = data.get("workflow")
        if not workflow:
            await connection_manager.send_to_client(
                client_id,
                WebSocketMessageType.SYSTEM,
                {
                    "message": "工作流数据不能为空"
                }
            )
            return

        # 提交工作流
        prompt_id = await submit_workflow_to_comfyui(workflow, client_id)

        # 设置当前任务
        connection_manager.set_current_prompt(client_id, prompt_id)

        # 发送提交成功消息
        await connection_manager.send_to_client(
            client_id,
            WebSocketMessageType.SYSTEM,
            {
                "message": "工作流已提交",
                "prompt_id": prompt_id
            }
        )

        # 启动后台任务监听进度
        asyncio.create_task(
            _monitor_workflow_progress(client_id, prompt_id)
        )

    except WorkflowValidationError as e:
        await connection_manager.send_to_client(
            client_id,
            WebSocketMessageType.EXECUTION_ERROR,
            {
                "message": e.message,
                "code": e.code,
                "detail": e.detail
            }
        )

    except ComfyUIConnectionError as e:
        await connection_manager.send_to_client(
            client_id,
            WebSocketMessageType.EXECUTION_ERROR,
            {
                "message": e.message,
                "code": e.code
            }
        )


async def _monitor_workflow_progress(
    client_id: str,
    prompt_id: str
) -> None:
    """
    监听工作流执行进度

    Args:
        client_id: 客户端 ID
        prompt_id: 任务 ID
    """
    async def progress_callback(message: Dict[str, Any]) -> None:
        """进度回调函数"""
        try:
            # 转发进度消息到客户端
            msg_type = message.get("type")

            if msg_type == "status":
                await connection_manager.send_to_client(
                    client_id,
                    WebSocketMessageType.STATUS,
                    message.get("data", {})
                )

            elif msg_type == "executing":
                await connection_manager.send_to_client(
                    client_id,
                    WebSocketMessageType.EXECUTING,
                    {"node": message.get("node")}
                )

            elif msg_type == "progress":
                await connection_manager.send_to_client(
                    client_id,
                    WebSocketMessageType.PROGRESS,
                    {
                        "value": message.get("value", 0),
                        "max": message.get("max", 0)
                    }
                )

            elif msg_type == "executed":
                await connection_manager.send_to_client(
                    client_id,
                    WebSocketMessageType.EXECUTED,
                    {
                        "node": message.get("node"),
                        "output": message.get("output", {})
                    }
                )

        except Exception:
            # 客户端可能已断开
            pass

    try:
        # 等待工作流完成
        result = await wait_for_workflow_completion(
            client_id,
            prompt_id,
            progress_callback=progress_callback,
            timeout=300
        )

        # 发送最终结果
        await connection_manager.send_to_client(
            client_id,
            WebSocketMessageType.RESULT,
            {
                "prompt_id": prompt_id,
                "success": result["success"],
                "outputs": result["outputs"],
                "error": result["error"]
            }
        )

    except Exception as e:
        # 发送错误消息
        await connection_manager.send_to_client(
            client_id,
            WebSocketMessageType.RESULT,
            {
                "prompt_id": prompt_id,
                "success": False,
                "error": str(e)
            }
        )

    finally:
        # 清除当前任务
        connection_manager.set_current_prompt(client_id, None)
