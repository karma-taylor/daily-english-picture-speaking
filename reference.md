# v2.0 技术选型

## GitHub Actions + Python

模块 A 是无状态的每日任务，GitHub Actions 免费额度足以承载。Cron 使用 UTC，`0 0 * * *` 对应北京时间 08:00。Python 仅依赖 `requests`，降低运行和维护复杂度。

## Lorem Picsum + Pollinations.ai

Lorem Picsum 提供无需密钥的真实照片占位服务，适合每日随机图。Pollinations.ai 使用文本提示词生成 AI 图片。两者均可按 URL 获取图片，便于直接交给 WxPusher 渲染。

## Cloudflare Workers

模块 B 只在收到回调时执行，无需常驻服务器。Worker 使用原生 `fetch`，没有 npm 运行时依赖；Cloudflare 免费套餐适用于这一低频 Webhook 场景。`wrangler.toml` 中必须指定 Worker 名称、入口和兼容日期。

## Upstash Redis

Upstash Redis 提供 HTTP REST 接口，非常适合 Worker。每个用户只保存一个 JSON 字符串，键为 `checkin:{UID}`，无需数据库连接池或服务器。

## WxPusher

WxPusher 同时提供下行消息和上行指令回调：模块 A 用它送图，模块 B 以其 `send_up_cmd` 回调接收“打卡”并回复结果。

参考：

- [GitHub Actions schedule](https://docs.github.com/actions/using-workflows/events-that-trigger-workflows#schedule)
- [Cloudflare Worker configuration](https://developers.cloudflare.com/workers/wrangler/configuration/)
- [Upstash Redis REST API](https://upstash.com/docs/redis/features/restapi)
- [WxPusher 官方文档](https://github.com/wxpusher/wxpusher-docs)
