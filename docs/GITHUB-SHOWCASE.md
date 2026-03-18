# GitHub Showcase Checklist

目标：让这个仓库在 GitHub 首页看起来像一个完整、克制、可运行的 AI 项目，而不是一堆本地开发痕迹。

## 1. 仓库首页设置

仓库名建议：

- `ExamNova`

仓库简介建议：

- `A Windows-first AI study workbench for exam-focused review, built with Electron, FastAPI, and structured note workflows.`

推荐 Topics：

- `electron`
- `fastapi`
- `nextjs`
- `react`
- `typescript`
- `python`
- `ai-agent`
- `study-assistant`
- `edtech`
- `ocr`

如果你后面继续深挖理工科，也可以补：

- `mechanical-engineering`
- `education`
- `desktop-app`

## 2. README 首页顺序

建议把 README 的阅读顺序固定成：

1. 项目一句话定位
2. Highlights
3. 项目定位
4. 仓库结构
5. 架构说明
6. 运行数据与开源安全
7. 本地启动
8. 打包
9. 产品原则

原则：

- 首页先讲“这是做什么的”，不要一上来堆命令
- 先讲用户和场景，再讲技术栈
- 不要把项目写成万能 AI
- 不要过度承诺 OCR、通用学科能力或完全自治 agent

## 3. 截图顺序

建议准备 4 到 6 张图，放在 `docs/screenshots/` 里。

推荐顺序：

1. `01-workbench-empty.png`
说明：空白新线程页面，展示左侧工作区和中间纸面

2. `02-study-note-long-page.png`
说明：一页多题的康奈尔式长纸笔记页

3. `03-formula-and-diagram.png`
说明：公式渲染、图解、手动画布同时出现的页面

4. `04-threads-by-course.png`
说明：左侧线程列表、按课程分组、改名/删除入口

5. `05-setup-and-connection.png`
说明：配置页、MiniMax 接入、演示模式

6. `06-writing-review.png`
说明：写作与复盘工作区

截图原则：

- 一张图只讲一个重点
- 不要一张图把所有功能都塞满
- 题目尽量选“有公式、有结构、有步骤”的例子
- 课程名称和线程名尽量看起来真实，但不要暴露个人信息

## 4. 最值得展示的功能

建议优先展示这些，不要平均用力：

- 康奈尔式长纸学习页
- 线程式课程工作区
- 理工科结构化解题
- 公式渲染和图解编辑
- 冲刺模式 / 常规模式的后台提醒逻辑
- 本地运行与 Electron 打包

## 5. Release 页面

如果你准备发 GitHub Release，建议放：

- `ExamNova-Setup-0.1.0.exe`
- 一个便携版压缩包（来自 `win-unpacked`）
- `Source code (zip)`
- `Source code (tar.gz)`

Release 标题建议：

- `v0.1.0 - Initial public release`

Release 说明建议写 3 部分：

- What it is
- What works now
- Known limitations

## 6. 开源前最终检查

发布前逐条确认：

- `.examnova-data/` 没有被提交
- `apps/desktop/release/` 没有被提交
- `apps/backend-dist/` 没有被提交
- 仓库里没有真实 API Key
- README 里的链接都是相对链接
- 截图里没有个人路径、真实账号、真实密钥
- 默认启动能进入空白线程页面
- 打包版启动后会在应用目录旁边生成 `data/`

## 7. 你在 GitHub 上最该传递的信息

你真正要让别人一眼看懂的是：

- 这不是聊天壳，而是学习工作流
- 这不是长期陪伴，而是考试前冲刺
- 这不是完全靠 prompt，而是有模板稳定度和本地状态管理
- 这不是 demo 图，而是能运行、能打包、能解释的项目

## 8. 不建议写得太重的地方

开源页不要过度强调这些：

- “多智能体系统”
- “全学科通用”
- “完全替代老师”
- “高精度手写 OCR”

更好的说法是：

- `single-agent study system`
- `exam-focused review workflow`
- `structured note generation`
- `mechanical / STEM-oriented stability improvements`
