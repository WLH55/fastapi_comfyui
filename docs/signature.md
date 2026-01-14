# API 签名验签文档

## 概述

签名验签功能用于防止第三方违规调用接口和篡改请求参数。客户端使用 RSA 私钥对请求进行签名，服务端使用 RSA 公钥验证签名。

### 核心特性

- **防篡改**：任何参数修改都会导致签名验证失败
- **防重放**：通过时间戳验证，防止请求被截获后重复使用
- **灵活启用**：支持全局开关和路由级可选启用
- **标准算法**：使用 RSA-PSS + SHA-256 签名算法

## 实现架构

```
┌─────────────────────────────────────────────────────────────┐
│                      签名验签流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  客户端                                                       │
│  ├─ 1. 构造请求参数（按字典序排序）                            │
│  ├─ 2. 添加 timestamp（当前时间戳）                           │
│  ├─ 3. 拼接待签名字符串                                      │
│  ├─ 4. 用私钥 RSA-PSS 签名                                  │
│  └─ 5. 将 signature、timestamp 通过 Query 参数传递           │
│                      ↓                                       │
│  服务端 (FastAPI)                                            │
│  ├─ 1. verify_signature 依赖拦截请求                         │
│  ├─ 2. 从 Query 获取 signature 和 timestamp                  │
│  ├─ 3. 构造相同的签名字符串                                   │
│  ├─ 4. 用公钥验证签名                                         │
│  ├─ 5. 验证时间戳（防重放）                                   │
│  └─ 6. 验证通过 → 继续处理，失败 → 返回 401                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 签名算法

### 签名字符串构造

```
签名字符串 = HTTP方法 + "\n" +
             请求路径 + "\n" +
             排序后的查询参数 + "\n" +
             时间戳
```

**示例**：
```
POST
/api/v1/workflows/submit
client_id=test_client&workflow=test_workflow
1704614400
```

### 签名流程

1. **算法**：RSA-PSS (Probabilistic Signature Scheme)
2. **哈希**：SHA-256
3. **填充**：MGF1 with SHA-256
4. **编码**：Base64

## 快速开始

### 第一步：生成 RSA 密钥对

使用以下代码生成 RSA 密钥对：

```python
from app.internal.signature import SignatureManager

# 生成 2048 位 RSA 密钥对
private_key_pem, public_key_pem = SignatureManager.generate_rsa_keypair(key_size=2048)

# 保存私钥（客户端使用）
with open("private_key.pem", "w") as f:
    f.write(private_key_pem)

# 保存公钥（服务端使用）
with open("public_key.pem", "w") as f:
    f.write(public_key_pem)
```

或使用 OpenSSL 命令行工具：

```bash
# 生成私钥
openssl genrsa -out private_key.pem 2048

# 提取公钥
openssl rsa -in private_key.pem -pubout -out public_key.pem
```

### 第二步：配置服务端

在 `.env` 文件中添加配置：

```env
# 签名验签配置
SIGNATURE_ENABLED=true
SIGNATURE_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----"
SIGNATURE_TIMESTAMP_TOLERANCE=300
```

**配置说明**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `SIGNATURE_ENABLED` | 签名验证总开关 | `false` |
| `SIGNATURE_PUBLIC_KEY` | RSA 公钥（PEM 格式，换行用 `\n` 表示） | 空 |
| `SIGNATURE_TIMESTAMP_TOLERANCE` | 时间戳容忍度（秒），防止重放攻击 | `300` |

### 第三步：为接口添加签名验证

```python
from fastapi import APIRouter, Depends
from app.dependencies import verify_signature

router = APIRouter()

# 不需要签名验证的接口（默认）
@router.get("/queue/status")
async def get_queue_status():
    return {"status": "ok"}

# 需要签名验证的接口
@router.post("/workflows/submit", dependencies=[Depends(verify_signature)])
async def submit_workflow(workflow: dict):
    return {"prompt_id": "123"}
```

### 第四步：客户端调用

#### Python 客户端示例

```python
import time
import requests
from app.internal.signature import SignatureManager

# 配置
API_URL = "http://localhost:8000"
PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
-----END PRIVATE KEY-----"""

# 请求参数
params = {
    "workflow": "test_workflow",
    "client_id": "test_client_123"
}

# 生成时间戳
timestamp = int(time.time())

# 生成签名
signature = SignatureManager.generate_signature(
    method="POST",
    path="/api/v1/workflows/submit",
    params=params,
    timestamp=timestamp,
    private_key_pem=PRIVATE_KEY_PEM
)

# 构造请求 URL（将签名和时间戳添加到 Query 参数）
url = f"{API_URL}/api/v1/workflows/submit?timestamp={timestamp}&signature={signature}"

# 发送请求
response = requests.post(url, json=params)

# 处理响应
if response.status_code == 200:
    print("请求成功:", response.json())
else:
    print("请求失败:", response.status_code, response.text)
```

#### JavaScript/Node.js 客户端示例

```javascript
const crypto = require('crypto');
const axios = require('axios');
const querystring = require('querystring');

// 配置
const API_URL = 'http://localhost:8000';
const PRIVATE_KEY = `-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
-----END PRIVATE KEY-----`;

// 生成签名
function generateSignature(method, path, params, timestamp) {
    // 过滤签名相关参数并排序
    const filteredParams = Object.entries(params)
        .filter(([k]) => !['signature', 'timestamp'].includes(k))
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([k, v]) => `${k}=${v}`)
        .join('&');

    // 构造签名字符串
    const signString = `${method}\n${path}\n${filteredParams}\n${timestamp}`;

    // RSA-PSS 签名
    const sign = crypto.createSign('SHA256');
    sign.update(signString);
    sign.end();

    const signature = sign.sign({
        key: PRIVATE_KEY,
        padding: crypto.constants.RSA_PKCS1_PSS_PADDING
    });

    // Base64 编码
    return signature.toString('base64');
}

// 发送请求
async function submitWorkflow() {
    const params = {
        workflow: 'test_workflow',
        client_id: 'test_client_123'
    };
    const timestamp = Math.floor(Date.now() / 1000);
    const signature = generateSignature('POST', '/api/v1/workflows/submit', params, timestamp);

    const url = `${API_URL}/api/v1/workflows/submit?timestamp=${timestamp}&signature=${encodeURIComponent(signature)}`;

    try {
        const response = await axios.post(url, params);
        console.log('请求成功:', response.data);
    } catch (error) {
        console.error('请求失败:', error.response?.data || error.message);
    }
}

submitWorkflow();
```

#### cURL 示例

```bash
#!/bin/bash

# 配置
API_URL="http://localhost:8000"
TIMESTAMP=$(date +%s)

# 请求参数
PARAMS="client_id=test_client_123&workflow=test_workflow"

# 构造签名字符串
SIGN_STRING="POST
/api/v1/workflows/submit
${PARAMS}
${TIMESTAMP}"

# 生成签名（需要先准备好私钥文件）
SIGNATURE=$(echo -n "$SIGN_STRING" | openssl dgst -sha256 -sign private_key.pem -pkeyopt rsa_padding_mode:pss | base64)

# 发送请求
curl -X POST "${API_URL}/api/v1/workflows/submit?timestamp=${TIMESTAMP}&signature=$(echo -n "$SIGNATURE" | jq -sRr @uri)" \
  -H "Content-Type: application/json" \
  -d '{"workflow": "test_workflow", "client_id": "test_client_123"}'
```

## API 说明

### SignatureManager 工具类

#### 生成 RSA 密钥对

```python
SignatureManager.generate_rsa_keypair(key_size: int = 2048) -> tuple[str, str]
```

**参数**：
- `key_size`: 密钥长度（位），默认 2048

**返回**：
- `(private_key_pem, public_key_pem)`: 私钥和公钥的 PEM 格式字符串

#### 生成签名

```python
SignatureManager.generate_signature(
    method: str,
    path: str,
    params: dict,
    timestamp: int,
    private_key_pem: str
) -> str
```

**参数**：
- `method`: HTTP 方法（GET、POST、PUT、DELETE 等）
- `path`: 请求路径（不含域名，如 `/api/v1/workflows/submit`）
- `params`: 请求参数字典
- `timestamp`: Unix 时间戳（秒）
- `private_key_pem`: PEM 格式的私钥

**返回**：
- Base64 编码的签名字符串

#### 验证签名

```python
SignatureManager.verify_signature(
    method: str,
    path: str,
    params: dict,
    signature: str,
    public_key_pem: str,
    timestamp: int = None
) -> bool
```

**参数**：
- `method`: HTTP 方法
- `path`: 请求路径
- `params`: 请求参数字典
- `signature`: 待验证的签名字符串
- `public_key_pem`: PEM 格式的公钥
- `timestamp`: Unix 时间戳（可选）

**返回**：
- 验证成功返回 `True`，失败抛出 `SignatureException`

#### 验证时间戳

```python
SignatureManager.is_timestamp_valid(timestamp: int, tolerance: int = 300) -> bool
```

**参数**：
- `timestamp`: 待验证的时间戳（秒）
- `tolerance`: 容忍时间差（秒），默认 300

**返回**：
- 时间戳有效返回 `True`，否则返回 `False`

### verify_signature 依赖

```python
async def verify_signature(
    request: Request,
    signature: str = Query(...),
    timestamp: int = Query(...)
) -> None
```

**用法**：
```python
@router.post("/your/endpoint", dependencies=[Depends(verify_signature)])
async def your_endpoint():
    ...
```

## 错误处理

### 错误码说明

| HTTP 状态码 | 说明 |
|------------|------|
| 401 | 签名验证失败或时间戳过期 |
| 500 | 服务器签名配置错误（公钥未配置） |

### 常见错误

#### 1. 签名验证失败

**原因**：
- 签名计算错误
- 请求参数被篡改
- 使用了错误的私钥

**解决**：
- 检查签名字符串构造是否正确
- 确认参数顺序（字典序）
- 验证私钥是否正确

#### 2. 时间戳过期

**原因**：
- 客户端与服务器时间不同步
- 请求处理时间过长

**解决**：
- 同步客户端和服务器时间
- 增大 `SIGNATURE_TIMESTAMP_TOLERANCE` 值

#### 3. 公钥配置错误

**原因**：
- 服务器未配置公钥
- 公钥格式错误

**解决**：
- 在 `.env` 中配置 `SIGNATURE_PUBLIC_KEY`
- 确保公钥是 PEM 格式

## 安全建议

1. **私钥保护**：私钥必须妥善保管，不应泄露或提交到版本控制系统
2. **密钥轮换**：定期更换密钥对，提高安全性
3. **HTTPS**：生产环境必须使用 HTTPS，防止中间人攻击
4. **时间同步**：确保客户端和服务器时间同步（建议使用 NTP）
5. **容忍度设置**：根据网络情况合理设置时间戳容忍度

## 完整示例

### 服务端代码

```python
# app/routers/protected.py
from fastapi import APIRouter, Depends
from app.dependencies import verify_signature
from app.schemas import ApiResponse

router = APIRouter(prefix="/protected", tags=["受保护接口"])

@router.post("/submit", dependencies=[Depends(verify_signature)])
async def protected_submit(data: dict):
    """需要签名验证的接口"""
    return ApiResponse.success(data={"result": "success", "received": data})
```

### 客户端代码

```python
# client_example.py
import time
import requests
from app.internal.signature import SignatureManager

class APIClient:
    def __init__(self, base_url: str, private_key: str):
        self.base_url = base_url
        self.private_key = private_key

    def request(self, method: str, path: str, params: dict = None, json_data: dict = None):
        """发送带签名的请求"""
        # 合并参数
        all_params = {}
        if params:
            all_params.update(params)
        if json_data:
            all_params.update(json_data)

        # 生成签名
        timestamp = int(time.time())
        signature = SignatureManager.generate_signature(
            method=method,
            path=path,
            params=all_params,
            timestamp=timestamp,
            private_key_pem=self.private_key
        )

        # 构造 URL
        url = f"{self.base_url}{path}?timestamp={timestamp}&signature={signature}"

        # 发送请求
        if method.upper() == "GET":
            response = requests.get(url, params=params)
        else:
            response = requests.post(url, params=params, json=json_data)

        return response

# 使用示例
if __name__ == "__main__":
    # 配置
    BASE_URL = "http://localhost:8000"
    PRIVATE_KEY = open("private_key.pem").read()

    # 创建客户端
    client = APIClient(BASE_URL, PRIVATE_KEY)

    # 发送请求
    response = client.request(
        method="POST",
        path="/api/v1/protected/submit",
        json_data={"message": "Hello, API!"}
    )

    print("响应:", response.json())
```

## 文件结构

```
fastapi_comfyui/
├── app/
│   ├── internal/
│   │   └── signature.py          # 签名验签核心逻辑
│   ├── dependencies.py            # 签名验证依赖
│   └── config.py                  # 签名相关配置
├── tests/
│   └── test_signature.py          # 单元测试
├── .env                           # 环境配置
└── docs/
    └── signature.md               # 本文档
```
