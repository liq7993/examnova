# ExamNova

面向中国大学生的桌面复习工作台。  
A Windows-first AI study workbench for exam-focused review.

ExamNova 不是一个泛聊天助手，也不是“什么都能做一点”的 AI 壳。  
它更像一个围绕 `题目 -> 讲解 -> 解题 -> 整理 -> 回看` 这条链路搭出来的本地学习工作台，重点服务考试前的短期冲刺、结构化复习和题目驱动的学习过程。

## 1. 项目简介

这个项目的目标，不是把学习做成热闹的陪伴产品，而是把“复习流程”做清楚。

在一个比较理想的使用流程里，用户会这样用它：

1. 输入一道题，或者上传题目图片
2. 让系统先给出结构化讲解和解题步骤
3. 把结果整理成一张连续可读的康奈尔式长纸笔记
4. 在同一个线程里继续做这一门课的下一道题
5. 让复习提醒、学习时长和回看提示在后台安静工作

所以它最核心的产品形态不是“对话框”，而是：

- 左侧：线程 / 课程工作区
- 中间：长纸笔记主体
- 右侧：当前抓手、提醒、复习提示
- 底部：像聊天输入条一样的题目输入区

## 2. 这个项目解决什么问题

很多学习类 AI 产品的问题是：

- 回答是零散的，不像笔记
- 对话很长，但真正有用的信息不成体系
- 学习流程不清楚，用户不知道下一步该做什么
- 明明是考试前临时复习，却还在做长期陪伴型设计

ExamNova 试图解决的是另一类问题：

- 如何让一道题的输出结果更像“可复用笔记”
- 如何把题目讲解和复习链路放在同一页里
- 如何让一个本地 AI 工具更适合短周期冲刺
- 如何在不做复杂多 agent 的前提下，提高结构稳定度

## 3. 当前定位

当前版本更适合被理解成：

`面向中国大学生、偏理工科、偏考试前冲刺的单 Agent 学习系统`

它当前最适合的场景是：

- 高数 / 电路 / 大学物理 / 机械类题目复习
- 考前几天的集中刷题
- 想把题目结果沉淀成笔记的人
- 想把学习过程按课程拆开整理的人

它当前不适合被表述成：

- 通用全学科学术助手
- 高精度手写公式 OCR 平台
- 复杂多智能体协作系统
- 长期陪伴型学习社区

## 4. 当前能力

当前主线有两条：

- `learning`
  - 题目分析
  - 讲解
  - 解题步骤
  - 公式解答
  - 图解补充
  - 错题复盘
  - 学习状态与复习提示

- `thinking`
  - 随笔
  - 反思
  - 复盘记录
  - 下一步行动整理

学习页当前已经支持：

- 康奈尔式长纸笔记布局
- 多题连续输出
- 左侧线程工作区
- 新线程 / 改名 / 删除 / 按课程分组
- 公式在讲解、步骤、整理中混排显示
- 图示编辑和公式草稿
- 真实学习时长与后台提醒
- 冲刺模式 / 常规模式

## 5. 理工科稳定度策略

这个项目没有把“稳定度”完全押在 prompt 上。  
当前版本已经开始用 `题型模板 + 确定性解法 + 结构化输出` 来提高稳定度。

最近重点加强的是偏机械 / 理工科的高频题型，例如：

- 功率 / 转矩 / 转速
- 齿轮传动比
- 带传动
- 拉压杆变形
- 轴扭转
- 简支梁支反力
- 梁弯曲应力
- 匀速圆周运动
- 转动定律
- 弹簧振子

这意味着当前版本在“结构清晰、公式明确、可模板化”的题目上会更稳定，  
而不是对所有学科、所有题型都承诺同样质量。

## 6. 产品设计原则

这个项目的设计原则比较明确：

- 一页一题，但允许同一线程连续往下延展
- 主视线聚焦题目、讲解和解题，不堆碎卡片
- 给信心，但不做鸡汤式陪伴
- 优先本地运行、可解释、可演示
- 优先短周期冲刺，而不是长期轻陪伴
- 功能可以少，但结构必须清楚

## 7. 架构说明

ExamNova 当前采用的是：

`single-agent + skill modules + service layer`

可以简单理解成三层：

### Agent 层

负责统一入口、任务路由和结果归一化。

### Skill 层

负责不同产品能力的输出逻辑。

当前主要是：

- `learning`
- `thinking`

### Service 层

负责支撑能力：

- OCR
- LLM 调用
- SQLite 存储
- 学习状态
- 复习策略
- 历史记录
- 错题本

更详细的架构文档见：

- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

## 8. 仓库结构

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

说明：

- `apps/backend`
  - FastAPI 后端
  - agent 路由
  - schema
  - 本地存储
  - 学习状态和复习策略

- `apps/desktop`
  - Next.js + React 前端
  - Electron 桌面壳
  - 学习页 / 写作页 / 设置页

- `docs`
  - 架构说明
  - 打包说明
  - MiniMax 接入说明
  - GitHub 展示清单

- `scripts`
  - 启动脚本
  - 停止脚本
  - 模型设置脚本
  - Electron 打包脚本

## 9. 本地数据与开源安全

这个仓库默认按“适合公开发布”的方式处理运行数据。  
项目本身不应该提交个人 API Key、数据库或学习记录。

默认数据位置：

```text
开发模式：<repo>/.examnova-data
桌面版：<ExamNova 可执行文件所在目录>/data
```

这里可能包含：

- `settings.json`
- `examnova.db`
- Electron 缓存
- 线程状态
- 本地学习记录

已经在 `.gitignore` 中忽略的主要内容包括：

- `.examnova-data/`
- `apps/desktop/release/`
- `apps/backend-dist/`

## 10. 快速开始

### 后端

```powershell
cd apps/backend
python -m pip install -e .
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 前端

```powershell
cd apps/desktop
npm install
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:3000
```

### 脚本方式

```powershell
cd <repo-root>
.\scripts\start-backend.ps1
.\scripts\start-desktop.ps1
.\scripts\start-all.ps1
```

## 11. 模型与 API 接入

当前项目支持演示模式。  
如果只想先看结构和页面，不需要先购买外部模型。

如果要接真实模型，当前最直接的路线是 MiniMax：

- [docs/MINIMAX.md](./docs/MINIMAX.md)
- [docs/MINIMAX-BEGINNER.txt](./docs/MINIMAX-BEGINNER.txt)

设置页里也已经内置了“不会购买 MiniMax API？打开新手教程”的入口。

## 12. 打包

当前桌面打包路线是：

`Electron + FastAPI`

主要入口：

- 前端桌面壳：`apps/desktop/electron/`
- 后端入口：`apps/backend/run_backend.py`
- 一键打包脚本：`scripts/package-electron.ps1`

打包命令：

```powershell
cd <repo-root>
.\scripts\package-electron.ps1
```

更多说明见：

- [docs/PACKAGING.md](./docs/PACKAGING.md)

## 13. GitHub 展示建议

如果这个仓库用于项目展示，建议重点突出：

- 康奈尔式长纸学习页
- 线程式课程工作区
- 理工科结构化题解
- 公式渲染与图解
- 本地运行与桌面打包

相关文档：

- [docs/GITHUB-SHOWCASE.md](./docs/GITHUB-SHOWCASE.md)
- [docs/screenshots/README.md](./docs/screenshots/README.md)

## 14. 当前边界与限制

当前版本已经适合作为：

- GitHub 开源项目
- 简历项目经历
- 桌面端演示作品

但它还没有完全达到：

- 商用级稳定性
- 全学科泛化能力
- 高精度复杂手写 OCR
- 深度自动规划型 Agent 系统

换句话说，这个项目当前最大的价值，不是“功能很多”，而是：

- 方向明确
- 结构清楚
- 可运行
- 可打包
- 可解释

## 15. 项目状态

这是一个持续迭代中的项目。  
当前版本已经具备：

- 本地运行能力
- 桌面打包能力
- 开源展示能力
- 面向题目驱动复习的产品雏形

后续可以继续增强的方向包括：

- 更多理工科题型模板
- 更稳定的 OCR 体验
- 更完整的截图与 Release 展示
- 更细的线程管理与导出能力
