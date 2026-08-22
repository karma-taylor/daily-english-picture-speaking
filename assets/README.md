# 本地兜底图片资源

在此目录放置 3 至 10 张适合英语看图演讲的默认图片，例如：

```text
assets/
├── fallback-01.jpg
├── fallback-02.jpg
└── fallback-03.jpg
```

建议图片具有清晰人物、地点、动作或事件；不含文字、水印、二维码；分辨率至少为 1024 × 1024。

GitHub Actions Runner 上的本地文件不能被微信客户端直接访问。请将这些图片提交到公开仓库、GitHub Pages、对象存储或 CDN，并把公网 HTTPS URL 配置到 GitHub Secret `FALLBACK_IMAGE_URLS`。

```text
https://raw.githubusercontent.com/<owner>/<repo>/main/assets/fallback-01.jpg,https://raw.githubusercontent.com/<owner>/<repo>/main/assets/fallback-02.jpg
```
