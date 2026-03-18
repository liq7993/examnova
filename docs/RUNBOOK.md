# 运行流程

目标：让第一次使用者在 3 分钟内跑通演示版。

## 1. 启动后端

```powershell
cd apps/backend
python -m pip install -e .
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 2. 启动桌面端（Web UI）

```powershell
cd apps/desktop
npm install
npm run dev
```

## 3. 首次进入配置页

- 默认演示模式开启，不调用外部 LLM。
- 可以先直接进入工作区体验结构。

## 4. 如果要接真实模型

- 关闭演示模式。
- 填写 MiniMax Base URL、模型名与 API Key。
- 点击“测试连接”。

## 5. 工作区使用

- 学习：输入题目或 OCR 图片 → 输出知识点/讲解/例题/考点提示。
- 写作与复盘：输入想法或学习记录 → 生成草稿、复盘摘要与下一步行动。
- 最近记录：查看、导出、清空。
