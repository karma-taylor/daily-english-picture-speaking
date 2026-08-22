# 每日 5 分钟英语看图演讲

## 产品目标

每天北京时间 08:00，自动向用户微信发送一张图片，不附带题目、提示词、说明文字或翻译。用户面对图片进行 5 分钟英文口语练习。

## 用户使用流程

1. 创建 Pexels API Key 与 WxPusher 应用。
2. 在 GitHub 仓库 Secrets 配置必要密钥。
3. 关注或绑定 WxPusher，并取得自己的 UID。
4. GitHub Actions 每日北京时间 08:00 自动运行。
5. 用户仅收到一张图片，开始 5 分钟无字英语演讲。

## 架构概述

```text
GitHub Actions（每天 08:00，北京时间）
              |
              v
       scripts/main.py
              |
       随机数 < 0.5 ?
          /           \
         v             v
 Pexels 真实图库   Pollinations.ai
         \             /
          v           v
       图片 URL 获取与校验
              |
              v
   WxPusher HTML 图片消息（零文字）
              |
              v
            微信用户
```

## 配置项

| 环境变量 | 必填 | 说明 |
| --- | --- | --- |
| `WXPUSHER_APP_TOKEN` | 是 | WxPusher 应用 AppToken |
| `WXPUSHER_UIDS` | 是 | 接收者 UID，多个 UID 用逗号分隔 |
| `PEXELS_API_KEY` | 建议 | Pexels API Key；未配置时自动转 AI 路线 |
| `POLLINATIONS_API_KEY` | 可选 | Pollinations 接口如要求鉴权时使用 |
| `FALLBACK_IMAGE_URLS` | 强烈建议 | 公网可访问的默认图片 URL，多个 URL 用逗号分隔 |
| `POLLINATIONS_BASE_URL` | 可选 | 默认 `https://image.pollinations.ai/prompt` |
| `IMAGE_WIDTH` / `IMAGE_HEIGHT` | 可选 | 默认均为 `1024` |

## 本地运行

```bash
cd scripts
python -m pip install -r requirements.txt
export WXPUSHER_APP_TOKEN="AT_xxx"
export WXPUSHER_UIDS="UID_xxx"
export PEXELS_API_KEY="xxx"
export FALLBACK_IMAGE_URLS="https://example.com/fallback-1.jpg"
python main.py
```

## 内容原则

WxPusher 正文只包含一个 HTML `<img>` 标签。图片 URL、提示词、来源和错误日志均不会推送给用户。
