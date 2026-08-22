# 技术选型与依赖说明

## Python 3.12

使用标准库处理随机路由、环境变量与日志，使用 `requests` 处理 HTTP 请求，保持部署简洁。

## GitHub Actions

任务无状态且每天仅执行一次，适合由 GitHub Actions 承载；GitHub Secrets 用于安全注入密钥。

Cron 按 UTC 解释：`0 0 * * *` 等于 UTC 00:00，即 Asia/Shanghai 08:00。中国标准时间没有夏令时。

## Pexels

使用 `GET https://api.pexels.com/v1/search` 搜索真实图片，并以 `Authorization: <API_KEY>` 鉴权。代码从返回的 `photos[*].src.large2x` 等字段中随机选图。

Pexels 官方建议在可行时提供摄影师署名和来源链接。微信推送受“零文字”产品约束而不展示；若未来增加展示页，应在该页面补充来源与署名。

- [Pexels API Documentation](https://www.pexels.com/api/documentation/)
- [Pexels API 使用规范](https://www.pexels.com/api/documentation/#guidelines)

## Pollinations.ai

将随机生成的英文奇幻场景 prompt URL 编码，调用 URL 型图片生成接口。默认地址为：

```text
GET https://image.pollinations.ai/prompt/{url_encoded_prompt}
```

Pollinations 的模型、限流和鉴权策略可能更新；必要时配置 `POLLINATIONS_API_KEY` 或用 `POLLINATIONS_BASE_URL` 切换到官方当前端点。

- [Pollinations 官方文档](https://gen.pollinations.ai/docs)
- [Pollinations API 文档](https://github.com/pollinations/pollinations/blob/main/APIDOCS.md)

## WxPusher

调用 `POST https://wxpusher.zjiecode.com/api/send/message` 投递 HTML 类型消息（`contentType: 2`），正文仅使用 `<img>` 标签，以实现零文字图片消息。

- [WxPusher 官方文档仓库](https://github.com/wxpusher/wxpusher-docs)
