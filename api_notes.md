# 外部 API 接口说明

## 1. Pexels 真实图库 API

### 请求

```http
GET https://api.pexels.com/v1/search?query=street%20market&orientation=landscape&per_page=30
Authorization: PEXELS_API_KEY
Accept: application/json
```

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `query` | 是 | 英文搜索词 |
| `orientation` | 否 | `landscape`、`portrait` 或 `square` |
| `per_page` | 否 | 每页数量，最大 80；本项目为 30 |
| `Authorization` 请求头 | 是 | Pexels API Key |

### 关键响应结构

```json
{
  "page": 1,
  "per_page": 30,
  "photos": [{
    "id": 3573351,
    "url": "https://www.pexels.com/photo/example/",
    "photographer": "Example Photographer",
    "src": {
      "original": "https://images.pexels.com/photos/example/original.jpeg",
      "large2x": "https://images.pexels.com/photos/example/large2x.jpeg"
    }
  }]
}
```

项目优先使用 `large2x`，依次回退至 `large` 与 `original`。

## 2. Pollinations.ai AI 绘图接口

### 请求

```http
GET https://image.pollinations.ai/prompt/{URL_ENCODED_PROMPT}?width=1024&height=1024&seed=123456&model=flux&safe=true
```

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `prompt` | 是 | URL 编码后的英文图片描述 |
| `width` / `height` | 否 | 图片尺寸 |
| `seed` | 否 | 随机种子，保证 URL 可复现 |
| `model` | 否 | 图像模型；默认示例为 `flux` |
| `safe` | 否 | 安全内容过滤 |
| `Authorization` 请求头 | 视接口策略 | 格式 `Bearer POLLINATIONS_API_KEY` |

该接口返回图片二进制而非 JSON。脚本先验证响应 `Content-Type` 为 `image/*`，再将同一图片 URL 交给 WxPusher。

## 3. WxPusher 消息接口

### 请求

```http
POST https://wxpusher.zjiecode.com/api/send/message
Content-Type: application/json
```

```json
{
  "appToken": "AT_xxx",
  "content": "<img src=\"https://example.com/daily-image.jpg\" />",
  "contentType": 2,
  "uids": ["UID_xxx"],
  "verifyPayType": 0
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `appToken` | 是 | WxPusher 应用 Token |
| `content` | 是 | 仅一个 HTML 图片标签 |
| `contentType` | 是 | `2` 表示 HTML 消息 |
| `uids` | 是 | 接收者 UID 数组 |
| `verifyPayType` | 否 | 本项目为 `0` |
