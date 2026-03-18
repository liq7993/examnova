# ExamNova

面向中国大学生的桌面复习工作台。  
A Windows-first study workbench for Chinese university students.

MiniMax API 获取说明见：[docs/MINIMAX.md](./docs/MINIMAX.md)  
新手购买与接入教程见：[docs/MINIMAX-BEGINNER.txt](./docs/MINIMAX-BEGINNER.txt)

## Highlights

- `single-agent + domain templates + local services` 的学习工作台
- 聚焦考试前冲刺，而不是泛聊天
- 康奈尔式长纸笔记页，支持多题连续滚动
- 线程式左侧工作区，适合按课程拆分复习
- Electron + FastAPI 本地运行，可打包为 Windows 桌面应用

## GitHub 展示

- 开源前展示清单见：[docs/GITHUB-SHOWCASE.md](./docs/GITHUB-SHOWCASE.md)
- 截图命名建议见：[docs/screenshots/README.md](./docs/screenshots/README.md)

## 项目定位

ExamNova 不是泛聊天助手，而是一个更偏向考试前冲刺、短期强化记忆的 AI 教师 / 复习助手。

当前主线只有两条：

- `learning`：题目分析、讲解、解题、错题复盘、冲刺模式与常规模式下的时间提醒
- `thinking`：随笔、反思、复盘记录、下一步行动

复习提醒和双遗忘机制仍然保留，但它们作为学习页的后台暗线工作，不再单独暴露成一个独立的“协助背诵”工作区。

## 仓库结构

```text
examnova/
├── apps/
│   ├── backend/
│   └── desktop/
├── codex-skills/
├── docs/
├── packages/
├── scripts/
├── .env.example
├── examnova.txt
└── README.md
```

其中：

- `apps/backend`：FastAPI 后端、agent 路由、学习状态、复习策略、SQLite 服务
- `apps/desktop`：Next.js + React 前端，以及 Electron 打包入口
- `docs`：架构说明、打包说明、MiniMax 接入说明
- `scripts`：本地启动、停止、设置 LLM、Electron 打包

## 当前架构

这是一个 `single-agent + skill modules + service layer` 的项目：

- Agent 负责统一路由与结果归一化
- Skills 负责学习与写作两条产品能力
- Services 负责 OCR、LLM、历史记录、错题本、学习状态、复习策略

更详细说明见：[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

## 运行数据与开源安全

仓库本身不应该保存你的 API Key、数据库或个人学习记录。

运行数据现在统一写入项目目录或应用目录旁边的数据文件夹，不会混进源码提交里：

```text
开发模式：<repo>/.examnova-data
桌面版：<ExamNova 可执行文件所在目录>\data
```

这里会保存：

- `settings.json`
- `examnova.db`
- 可选的 JSONL 迁移文件

浏览器线程和前端缓存也会跟随应用目录侧的数据目录，不再依赖默认 Electron 用户目录。

## 本地启动

后端：

```powershell
cd apps/backend
python -m pip install -e .
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd apps/desktop
npm install
npm run dev
```

浏览器打开：

```text
http://127.0.0.1:3000
```

脚本方式：

```powershell
cd <repo-root>
.\scripts\start-backend.ps1
.\scripts\start-desktop.ps1
.\scripts\start-all.ps1
```

## Electron 打包

你选择的是 `Electron` 路线。当前仓库已经提供：

- Electron 主进程入口：`apps/desktop/electron/`
- 后端打包入口：`apps/backend/run_backend.py`
- 一键打包脚本：`scripts/package-electron.ps1`

打包命令：

```powershell
cd <repo-root>
.\scripts\package-electron.ps1
```

更多细节见：[docs/PACKAGING.md](./docs/PACKAGING.md)

## 产品原则

- 一页一题，主视线聚焦题目和讲解
- 康奈尔式长纸笔记，不做碎卡片堆叠
- 给信心，但不做鸡汤陪伴
- 冲刺模式优先服务考试前复习
- 常规模式保留跨天回顾能力
- 本地优先，先保证可运行、可演示、可解释
