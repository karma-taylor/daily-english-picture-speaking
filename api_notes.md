# v2.0 外部 API 说明

## 1. Lorem Picsum

```http
GET https://picsum.photos/seed/{seed}/1024/1024
```

`seed` 是随机字符串。服务返回或重定向到图片，模块 A 校验最终响应为 `image/*` 后将最终 URL 推送。

## 2. Pollinations.ai

```http
GET https://image.pollinations.ai/prompt/{URL_ENCODED_PROMPT}?width=1024&height=1024&seed=123&model=flux&safe=true
Authorization: Bearer {POLLINATIONS_API_KEY}  # 可选，按服务策略提供
```

接口返回图片二进制。脚本以 `Content-Type: image/*` 作为成功判定。

## 3. WxPusher 下行消息

```http
POST https://wxpusher.zjiecode.com/api/send/message
Content-Type: application/json
```

图片推送示例：

```json
{
  "appToken": "AT_xxx",
  "content": "<img src=\"https://example.com/image.jpg\" />",
  "contentType": 2,
  "uids": ["UID_xxx"],
  "verifyPayType": 0
}
```

打卡回复示例：

```json
{
  "appToken": "AT_xxx",
  "content": "🎉 打卡成功！你已连续练习 3 天，继续保持！",
  "contentType": 1,
  "uids": ["UID_xxx"],
  "verifyPayType": 0
}
```

成功响应的顶级 `code` 为 `1000`。

## 4. WxPusher Webhook 上行 Payload

将 Worker URL 填入应用的“事件回调地址”。用户向应用发送指令时，WxPusher 使用 POST 调用：

```json
{
  "action": "send_up_cmd",
  "data": {
    "uid": "UID_xxx",
    "appId": 97,
    "appName": "每日 5 分钟英语看图演讲",
    "time": 1603002697386,
    "content": "打卡"
  }
}
```

Worker 仅处理 `action === "send_up_cmd"` 且 `content` 含“打卡”的请求；若设置 `WXPUSHER_APP_ID`，还会验证 `data.appId`。

## 5. Upstash Redis REST API

所有请求携带：

```http
Authorization: Bearer {UPSTASH_REDIS_REST_TOKEN}
```

读取：

```http
GET {UPSTASH_REDIS_REST_URL}/get/checkin%3AUID_xxx
```

写入使用 POST，键放在 URL，值放在 JSON body：

```http
POST {UPSTASH_REDIS_REST_URL}/set/checkin%3AUID_xxx
Content-Type: application/json

{"last_checkin":"2026-08-22","streak":3}
```

Redis 数据结构：

```json
{
  "last_checkin": "YYYY-MM-DD",
  "streak": 3
}
```
