# 每日 5 分钟英语看图演讲 · v2.0

## 产品说明

v2.0 在每日看图推送的基础上增加轻量级打卡。用户每天收到一张图片后，完成 5 分钟英语演讲，并在 WxPusher 中回复“打卡”。系统记录连续练习天数并自动回复结果。

## 核心交互闭环

1. 每天北京时间 08:00，GitHub Actions 触发模块 A。
2. 模块 A 以 50% 概率从 Lorem Picsum 获取真实图片，或以 50% 概率从 Pollinations.ai 获取 AI 图片。
3. 模块 A 通过 WxPusher 向用户发送纯图片。
4. 用户完成练习后回复“打卡”。
5. WxPusher 将上行消息 POST 到模块 B 的 Cloudflare Worker。
6. Worker 在 Upstash Redis 读取并更新该 UID 的连续打卡状态，再通过 WxPusher 回复结果。

## 架构图

```text
模块 A：定时单向推送
GitHub Actions (UTC 00:00 = 北京 08:00)
  -> daily_push.py
  -> 50% Lorem Picsum / 50% Pollinations.ai
  -> WxPusher
  -> 用户客户端

模块 B：状态记录与互动打卡
用户回复“打卡”
  -> WxPusher 上行消息回调
  -> Cloudflare Worker /webhook?token=...
  -> Upstash Redis: checkin:{UID}
  -> WxPusher 文本回复：连续练习 N 天
```

## 部署配置

### 模块 A：GitHub Secrets

| 名称 | 说明 |
| --- | --- |
| `WXPUSHER_APP_TOKEN` | WxPusher 应用 AppToken |
| `WXPUSHER_UIDS` | 接收图片的 UID，多个以逗号分隔 |
| `POLLINATIONS_API_KEY` | 可选；Pollinations 要求鉴权时使用 |

### 模块 B：Cloudflare Worker Secrets

| 名称 | 说明 |
| --- | --- |
| `WXPUSHER_APP_TOKEN` | 同一个 WxPusher AppToken |
| `WXPUSHER_APP_ID` | WxPusher 应用 ID，用于过滤其他应用回调 |
| `UPSTASH_REDIS_REST_URL` | Upstash Redis REST HTTPS 地址 |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash Redis REST Token |
| `WEBHOOK_TOKEN` | 自行生成的随机长字符串；放在回调 URL 的 `token` 查询参数中 |

将 Worker 部署后的地址配置到 WxPusher 应用的“事件回调地址”：

```text
https://<你的-worker>.<你的-subdomain>.workers.dev/webhook?token=<WEBHOOK_TOKEN>
```
