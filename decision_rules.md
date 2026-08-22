# 业务决策与降级规则

## 正常路径

```text
开始
  |
  v
读取 Secrets 配置
  |
  v
random.random() < 0.5 ?
  |                      |
 是                     否
  |                      |
  v                      v
Pexels 真实图片       Pollinations AI 图片
  |                      |
  +------ 成功 ----------+
             |
             v
      WxPusher 只推送图片
             |
             v
            结束
```

## 50% 路由规则

```python
primary_source = "pexels" if random.random() < 0.5 else "pollinations"
```

`random.random()` 均匀返回 `[0.0, 1.0)`，两个来源各有约 50% 的主路线概率。

## Fallback 规则

```text
主来源获取失败
  |
  v
尝试另一个来源
  |
  +-- 成功 --> 推送图片
  |
  v
两个远程来源均失败
  |
  v
从 FALLBACK_IMAGE_URLS 随机取一张公网默认图片
  |
  +-- 已配置 --> 推送图片
  |
  v
未配置 --> 工作流失败；不推送任何文字
```

## 异常处理原则

- 缺少 Pexels Token、HTTP 非 2xx、返回无图片或超时，均视为 Pexels 失败。
- Pollinations 超时、HTTP 非 2xx 或返回非图片内容，均视为 AI 图片失败。
- WxPusher HTTP 或业务失败码会使工作流失败，便于排查。
- 降级过程不改变“零文字推送”规则。
- `assets/` 的本地文件必须被部署到公网；GitHub Runner 本地路径不能被微信客户端读取。
