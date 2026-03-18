# Packaging Notes

## Current Direction

ExamNova 使用 `Electron + FastAPI` 打包路线：

1. `apps/backend/run_backend.py` 负责启动本地后端
2. `PyInstaller` 把后端打成 `examnova-backend.exe`
3. `apps/desktop` 生成静态前端输出
4. Electron 在桌面端自动拉起后端并加载 UI

## One-Command Packaging

```powershell
cd <repo-root>
.\scripts\package-electron.ps1
```

预期输出：

- `apps/backend-dist/examnova-backend.exe`
- `apps/desktop/release/ExamNova-Setup-<version>.exe`

## Runtime Data Location

运行数据默认写到项目目录或应用目录旁边：

```text
开发模式：<repo>\.examnova-data
桌面版：<ExamNova.exe 所在目录>\data
```

包括：

- `settings.json`
- `examnova.db`
- 可选 JSONL 迁移文件
- Electron 本地缓存和线程状态

## Notes

- 打包阶段需要当前机器可用的 `python`、`npm` 和 `PyInstaller`
- 终端打包成功后，最终用户不需要再单独配置 Python
- MiniMax API 获取方式见：[MINIMAX.md](./MINIMAX.md)
