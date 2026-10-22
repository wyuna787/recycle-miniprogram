# 回收交易小程序

包含 UniApp / Vue 前端（`frontend/`）和 FastAPI 后端（`recycler/`），支持商家、回收商和平台端交易流程。

## 本地配置

- 前端：在 `frontend/manifest.json` 和 `frontend/project.config.json` 将示例 AppID 替换为自己的配置；`frontend/utils/request.js` 默认连接本机 `http://127.0.0.1:8000`。
- 后端：安装 `recycler/requirements.txt`，设置环境变量 `RECYCLE_SECRET_KEY` 为随机长字符串，按需设置 `RECYCLE_DATABASE_URL`。`.env.example` 仅作变量清单，程序不会自动加载 `.env`。
- 在 `recycler/` 目录运行 `uvicorn main:app --host 127.0.0.1 --port 8000`。
- 未设置签名密钥时进程会生成临时随机密钥，重启后旧登录会话失效；多进程部署须设置同一个持久密钥。
- 原项目自带的 mock 账号和演示初始化逻辑保留，仅用于开发；上线前需按实际环境检查。

## 上传范围

本仓库保存前后端源码和静态资源。AppID、原线上接口地址及原硬编码签名密钥已脱敏。未包含数据库、环境配置、私钥、依赖目录、构建输出、备份、发布压缩包和本地验收资料。

子目录原有 README 为历史说明，具体功能以当前代码为准。
