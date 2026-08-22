# v2.0 决策规则

## 模块 A：随机推送

`random.random() < 0.5` 时优先调用 Lorem Picsum，否则优先调用 Pollinations.ai。主来源请求超时、返回非 2xx 或非图片内容时，立即尝试另一个来源；两个来源均失败时，工作流失败且不发送文本替代品。

## 模块 B：打卡日期判断

### 时区

所有打卡日期统一以 `Asia/Shanghai` 计算，格式固定为 `YYYY-MM-DD`。Worker 不能使用 UTC 日期替代北京时间，否则北京时间凌晨可能被错误归入前一天。

### 判断流程

```text
收到 POST 回调
  -> 校验 webhook token、action、appId 和“打卡”关键词
  -> 计算 today（北京时间）和 yesterday（北京时间）
  -> 读取 checkin:{UID}
     -> last_checkin == today：回复“今天已经打过卡了”
     -> last_checkin == yesterday：streak = 旧 streak + 1
     -> 其他情况或无记录：streak = 1
  -> SET 新 {last_checkin: today, streak}
  -> WxPusher 回复连续练习天数
```

### 跨天与断签示例

| 上次打卡 | 今天 | 结果 |
| --- | --- | --- |
| `2026-08-22` | `2026-08-22` | 不写 Redis；回复今天已打卡 |
| `2026-08-21` | `2026-08-22` | 连续天数加 1 |
| `2026-08-20` 或更早 | `2026-08-22` | 已断签，连续天数重置为 1 |
| 无记录 | 任意日期 | 首次打卡，连续天数为 1 |

打卡记录必须在成功写入 Upstash 后才能回复“打卡成功”；任一外部请求失败时返回 HTTP 500，让 WxPusher 根据其策略重试或供日志排查。
