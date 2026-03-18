# MiniMax API 获取说明

面向第一次接 MiniMax 的使用者，最推荐先看这份纯文本教程：

- [MINIMAX-BEGINNER.txt](./MINIMAX-BEGINNER.txt)

## 官方入口

- MiniMax 开发平台 Quickstart：
  - [https://platform.minimaxi.com/docs/guides/quickstart](https://platform.minimaxi.com/docs/guides/quickstart)
- MiniMax 定价页：
  - [https://www.minimaxi.com/pricing](https://www.minimaxi.com/pricing)
- OpenAI 兼容接口文档：
  - [https://platform.minimaxi.com/docs/api-reference/text-openai-api](https://platform.minimaxi.com/docs/api-reference/text-openai-api)
- API FAQ（包含余额不足、Key 与模型可用性等常见报错）：
  - [https://platform.minimaxi.com/docs/api-reference/basic-information/faq](https://platform.minimaxi.com/docs/api-reference/basic-information/faq)

## 对 ExamNova 最稳的接入路线

1. 注册并登录 MiniMax 开发平台。
2. 查看官方定价页，决定是否先充值或先用试用额度。
3. 在平台里创建 API Key。
4. 打开 ExamNova 设置页，关闭演示模式。
5. 填写：
   - `Base URL`：`https://api.minimaxi.com/v1`
   - `Model`：可以先用 `MiniMax-M2.5`，也可以按官方当前支持模型自行切换
   - `API Key`：你刚创建的 Key
6. 点击“测试连接”，通过后再进入工作区。

## 当前仓库的数据保存位置

为了方便开源和本地清理，ExamNova 不再把运行数据写到默认系统用户目录。

当前数据位置：

```text
开发模式：<repo>/.examnova-data
桌面版：<ExamNova.exe 所在目录>/data
```

这里会保存：

- `settings.json`
- `examnova.db`
- Electron 本地缓存

## 注意

- 不要把真实 API Key 提交到 GitHub。
- 如果你只想先看界面，可以保持演示模式开启。
- MiniMax 的价格、可用模型和套餐名称都可能变化；真正付款前请以官方页面为准。
