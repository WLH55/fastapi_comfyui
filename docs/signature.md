# API 签名验签文档

## 概述

签名验签功能用于防止第三方违规调用接口和篡改请求参数。采用**规范化签名字符串**方式，客户端使用 RSA 私钥对请求进行签名，服务端使用 RSA 公钥验证签名。

### 核心特性

- **防篡改**：任何参数修改都会导致签名验证失败
- **防重放**：通过时间戳 + Nonce 验证，防止请求被截获后重复使用
- **Body Hash**：直接对请求体原始字节进行哈希，无需解析 JSON
- **灵活启用**：支持全局开关和路由级可选启用
- **标准算法**：使用 RSA-PSS + SHA-256 签名算法

## 实现架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      签名验签流程                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  客户端                                                              │
│  ├─ 1. 生成随机 Nonce（32 位十六进制字符串）                          │
│  ├─ 2. 获取当前时间戳 Timestamp                                     │
│  ├─ 3. 计算 Body Hash（SHA256 哈希）                                │
│  ├─ 4. 构造规范化字符串                                             │
│  │     METHOD\nPATH\nQUERY\nBODY_HASH\nTIMESTAMP\nNONCE             │
│  ├─ 5. 用私钥 RSA-PSS 签名                                         │
│  └─ 6. 将签名信息通过 HTTP Header 传递                               │
│                      ↓                                              │
│  服务端 (FastAPI)                                                    │
│  ├─ 1. verify_signature 依赖从 Header 读取签名参数                    │
│  ├─ 2. X-Signature, X-Timestamp, X-Nonce                           │
│  ├─ 3. 构造相同的规范化字符串                                        │
│  ├─ 4. 用公钥验证签名                                               │
│  ├─ 5. 验证时间戳（防重放）                                          │
│  └─ 6. 验证通过 → 继续处理，失败 → 返回 401                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 签名算法

### 签名字符串构造（规范化字符串）

```
METHOD\nPATH\nQUERY\nBODY_HASH\nTIMESTAMP\nNONCE
```

| 字段 | 说明 | 示例 |
|------|------|------|
| METHOD | HTTP 方法（大写） | POST |
| PATH | 请求路径 | /api/v1/workflows/submit |
| QUERY | URL 编码的查询参数（按字母序） | client_id=123&format=json |
| BODY_HASH | 请求体的 SHA256 哈希值 | 9f86d081... |
| TIMESTAMP | Unix 时间戳（秒） | 1704614400 |
| NONCE | 随机字符串（防重放） | a8f3e4b2... |

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
import json
from app.internal.signature import SignatureManager

# 配置
API_URL = "http://localhost:8000"
PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
-----END PRIVATE KEY-----"""

# 请求参数
method = "POST"
path = "/api/v1/workflows/submit"
query_params = {"client_id": "123", "format": "json"}
body = {"workflow": "test", "steps": 20}
body_bytes = json.dumps(body).encode("utf-8")

# 生成签名
sig_result = SignatureManager.generate_signature(
    method=method,
    path=path,
    query_params=query_params,
    body_bytes=body_bytes,
    private_key_pem=PRIVATE_KEY_PEM
)

# 构造请求头
headers = {
    "X-Signature": sig_result["signature"],
    "X-Timestamp": sig_result["timestamp"],
    "X-Nonce": sig_result["nonce"],
    "Content-Type": "application/json"
}

# 发送请求
url = f"{API_URL}{path}"
response = requests.post(
    url,
    params=query_params,
    data=body_bytes,
    headers=headers
)

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

// 生成随机 Nonce
function generateNonce() {
    return crypto.randomBytes(16).toString('hex');
}

// 计算 Body Hash
function calculateBodyHash(body) {
    return body
        ? crypto.createHash('sha256').update(body).digest('hex')
        : '';
}

// 构造规范化字符串
function buildCanonicalString(method, path, query, bodyHash, timestamp, nonce) {
    const sortedQuery = Object.keys(query)
        .sort()
        .map(k => `${k}=${query[k]}`)
        .join('&');

    return `${method.toUpperCase()}\n${path}\n${sortedQuery}\n${bodyHash}\n${timestamp}\n${nonce}`;
}

// 生成签名
function generateSignature(canonicalString, privateKey) {
    const sign = crypto.createSign('SHA256');
    sign.update(canonicalString);
    sign.end();

    const signature = sign.sign({
        key: privateKey,
        padding: crypto.constants.RSA_PKCS1_PSS_PADDING
    });

    return signature.toString('base64');
}

// 发送请求
async function submitWorkflow() {
    const method = 'POST';
    const path = '/api/v1/workflows/submit';
    const query = { client_id: '123' };
    const body = JSON.stringify({ workflow: 'test', steps: 20 });
    const bodyHash = calculateBodyHash(body);
    const timestamp = Math.floor(Date.now() / 1000);
    const nonce = generateNonce();

    // 构造规范化字符串并签名
    const canonicalString = buildCanonicalString(
        method, path, query, bodyHash, timestamp, nonce
    );
    const signature = generateSignature(canonicalString, PRIVATE_KEY);

    // 发送请求
    const url = `${API_URL}${path}`;
    try {
        const response = await axios.post(url, body, {
            params: query,
            headers: {
                'X-Signature': signature,
                'X-Timestamp': timestamp.toString(),
                'X-Nonce': nonce,
                'Content-Type': 'application/json'
            }
        });
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
PRIVATE_KEY_FILE="private_key.pem"
TIMESTAMP=$(date +%s)
NONCE=$(cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 32 | head -n 1)

# 请求参数
METHOD="POST"
PATH="/api/v1/workflows/submit"
QUERY="client_id=123&format=json"
BODY='{"workflow":"test","steps":20}'

# 计算 Body Hash
BODY_HASH=$(echo -n "$BODY" | sha256sum | cut -d' ' -f1)

# 构造签名字符串
SIGN_STRING="POST
${PATH}
${QUERY}
${BODY_HASH}
${TIMESTAMP}
${NONCE}"

# 生成签名
SIGNATURE=$(echo -n "$SIGN_STRING" | openssl dgst -sha256 -sign "$PRIVATE_KEY_FILE" -pkeyopt rsa_padding_mode:pss | base64)

# 发送请求
curl -X "${API_URL}${PATH}?${QUERY}" \
  -H "X-Signature: ${SIGNATURE}" \
  -H "X-Timestamp: ${TIMESTAMP}" \
  -H "X-Nonce: ${NONCE}" \
  -H "Content-Type: application/json" \
  -d "$BODY"
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
    query_params: Optional[Dict[str, Any]] = None,
    body_bytes: Optional[bytes] = None,
    timestamp: Optional[int] = None,
    nonce: Optional[str] = None,
    private_key_pem: str = ""
) -> Dict[str, str]
```

**参数**：
- `method`: HTTP 方法
- `path`: 请求路径
- `query_params`: Query 参数字典（可选）
- `body_bytes`: 请求体的原始字节（可选）
- `timestamp`: Unix 时间戳（秒），不传则自动生成
- `nonce`: 随机字符串，不传则自动生成
- `private_key_pem`: PEM 格式的私钥

**返回**：
```python
{
    "signature": "Base64 编码的签名字符串",
    "timestamp": "Unix 时间戳",
    "nonce": "随机字符串"
}
```

#### 验证签名

```python
SignatureManager.verify_signature(
    method: str,
    path: str,
    query_params: Optional[Dict[str, Any]] = None,
    body_bytes: Optional[bytes] = None,
    signature: str = "",
    timestamp: str = "",
    nonce: str = "",
    public_key_pem: str = ""
) -> bool
```

**参数**：
- `method`: HTTP 方法
- `path`: 请求路径
- `query_params`: Query 参数字典（可选）
- `body_bytes`: 请求体的原始字节（可选）
- `signature`: 待验证的签名字符串
- `timestamp`: Unix 时间戳字符串
- `nonce`: 随机字符串
- `public_key_pem`: PEM 格式的公钥

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
    x_signature: str = Header(...),
    x_timestamp: str = Header(...),
    x_nonce: str = Header(...)
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
| 401 | 签名验证失败、时间戳过期或参数缺失 |
| 500 | 服务器签名配置错误（公钥未配置） |

### 常见错误

#### 1. 签名验证失败

**原因**：
- 签名计算错误
- 请求参数被篡改
- 使用了错误的私钥

**解决**：
- 检查规范化字符串构造是否正确
- 确认参数顺序（字典序）
- 验证 Body Hash 是否正确

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
6. **Nonce 随机性**：每次请求都使用新的 Nonce，防止重放攻击

## 签名流程详解

### 1. 客户端签名生成

```
原始请求：
POST /api/v1/workflows/submit?client_id=123&format=json
Body: {"workflow": "test", "steps": 20}

步骤：
1. 生成 Nonce: a8f3e4b2c1d6e7f8...
2. 获取时间戳: 1704614400
3. 计算 Body Hash: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
4. 构造规范化字符串:
   POST
   /api/v1/workflows/submit
   client_id=123&format=json
   9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
   1704614400
   a8f3e4b2c1d6e7f8...
5. RSA 签名并 Base64 编码
6. 放入 Header:
   X-Signature: ABc123...
   X-Timestamp: 1704614400
   X-Nonce: a8f3e4b2...
```

### 2. 服务端签名验证

```
收到请求后：
1. 从 Header 读取 X-Signature, X-Timestamp, X-Nonce
2. 获取 Method, Path, Query, Body
3. 计算 Body Hash（与客户端相同方式）
4. 构造相同的规范化字符串
5. 用公钥验证签名
6. 检查时间戳是否在容忍范围内
7. 全部通过则放行，否则返回 401
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
│   └── test_signature.py          # 单元测试（25 个测试用例）
├── .env                           # 环境配置
└── docs/
    └── signature.md               # 本文档
```

## 版本变更

### v2（当前版本）

- 使用 Header 传递签名参数（X-Signature, X-Timestamp, X-Nonce）
- 引入 Nonce 防重放机制
- 使用 Body Hash 代替解析 JSON
- 规范化字符串格式：METHOD\nPATH\nQUERY\nBODY_HASH\nTIMESTAMP\nNONCE

### v1（已废弃）

- 使用 Query 参数传递签名
- 无 Nonce 机制
- 需要解析 JSON 参数
