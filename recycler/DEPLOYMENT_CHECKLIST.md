# 部署清单（DEPLOYMENT_CHECKLIST）

二手电子设备回收交易平台 **Python / FastAPI** 后端 + uni-app 小程序前端，MVP 上线前检查清单。

> 本文档已根据当前后端代码结构更新。后端入口：`main.py`，依赖：`requirements.txt`。

---

## 1. 服务器环境

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 22.04 LTS 或 CentOS 7/8 |
| Python | **3.10 / 3.11**（推荐；3.13 本地已验证） |
| Node.js | **不需要**（后端非 Node） |
| 数据库 | SQLite（文件 `recycle.db`）或后续 MySQL |
| Nginx | 建议（HTTPS 反向代理） |
| 进程守护 | **systemd** 或 supervisor（非 PM2，除非另有 Node 服务） |

---

## 2. 上传代码

建议目录：

```bash
/opt/recycler/
```

需包含：`main.py`、`models.py`、`database.py`、`auth.py`、`trade_utils.py`、`account_utils.py`、`schemas.py`、`requirements.txt` 等，**不要上传** `.venv/`。

---

## 3. 安装依赖

```bash
cd /opt/recycler
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

验证：

```bash
python -c "import fastapi, uvicorn, sqlalchemy; print('ok')"
```

---

## 4. 配置环境变量

当前代码 **无 `.env` 文件**，以下需在源码或 systemd `Environment=` 中修改（建议后续改为环境变量）：

| 项 | 文件 | 生产必做 |
|----|------|----------|
| `SECRET_KEY` | `auth.py` | 改为强随机字符串 |
| `DATABASE_URL` | `database.py` | 暂用 SQLite；迁 MySQL 时修改 |
| CORS | `main.py` | 按需收紧 `allow_origins` |

可选：新增 `.env.example` 文档化（代码侧待实现）。

---

## 5. 初始化数据库

| 方式 | 说明 |
|------|------|
| 自动 | 首次启动 `uvicorn` 时 `create_all` + `migrate_db()` |
| 测试数据 | `curl -X POST https://api.example.com/dev/init` |

**生产环境：** 限制或关闭 `POST /dev/init`（仅内网 / 仅测试环境）。

**备份：**

```bash
cp recycle.db recycle.db.bak.$(date +%Y%m%d)
```

---

## 6. 启动后端服务

### 手动验证

```bash
cd /opt/recycler && source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### systemd 示例

文件：`/etc/systemd/system/recycler.service`

```ini
[Unit]
Description=Recycler FastAPI
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/recycler
Environment="PATH=/opt/recycler/.venv/bin"
ExecStart=/opt/recycler/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable recycler
sudo systemctl start recycler
sudo systemctl status recycler
```

> 入口为 **`main:app`**，不是 `server.js`。

---

## 7. 配置 Nginx 反向代理

```nginx
server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate     /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

按实际域名与证书路径修改。后端仅监听本机 `8000` 时，外网只开放 443。

---

## 8. 配置端口和防火墙

| 端口 | 用途 |
|------|------|
| 443（及 80 跳转） | 对外 HTTPS |
| 8000 | 仅本机或内网，不对公网开放 |
| 3306 等 | 若使用 MySQL，仅内网访问 |

云厂商安全组需放行 80/443。

---

## 9. 日志查看

| 类型 | 命令 |
|------|------|
| systemd 服务日志 | `journalctl -u recycler -f` |
| Nginx 访问/错误 | `/var/log/nginx/access.log`、`error.log` |
| SQLite | 确认 `recycle.db` 路径权限与磁盘空间 |

当前应用未配置独立文件日志（uvicorn 输出到 stdout）。

---

## 10. 小程序前端准备

1. 修改 `utils/request.js`：`BASE_URL = 'https://api.example.com'`
2. 微信公众平台 → 开发设置 → **request 合法域名** 添加该 HTTPS 域名
3. 编译上传前关闭「不校验合法域名」（仅本地调试可开）
4. HBuilderX / 微信开发者工具发行上传

---

## 11. 上线前检查（MVP）

### 后端

- [ ] `https://api.example.com/docs` 可打开
- [ ] `POST /api/account/login` 测试账号可登录
- [ ] `GET /api/admin/trades`（平台 token）返回交易流
- [ ] `recycle.db` 已备份
- [ ] `SECRET_KEY` 已更换
- [ ] `/dev/init` 已限制或关闭
- [ ] systemd 重启后服务自启

### 主流程（建议按序）

- [ ] 注册 / 平台审核账号
- [ ] 商家发布设备 → 回收商可见询价
- [ ] 回收商报价
- [ ] 商家确认报价 → 生成订单
- [ ] 商家发货 → 状态 `shipped`
- [ ] 回收商签收 → `received`
- [ ] 回收商验机 → `inspection_done`
- [ ] 商家确认完成 → `completed` **或** 申诉 → `appealing` → 平台关闭 → `closed`
- [ ] 平台订单监控展示全链路状态

### 以下项为 **MVP 范围外**（勿作为上线阻塞项）

- [ ] ~~预付款额度池扣减~~（未实现）
- [ ] ~~消息通知~~（未实现）
- [ ] ~~数据分析~~（未实现）
- [ ] ~~抽成结算~~（未实现）

---

## 12. 常见报错排查

| 报错 / 现象 | 排查 |
|-------------|------|
| Connection refused | 服务未启动、端口错误、防火墙 |
| Address already in use | 8000 被占用，`lsof -i :8000` |
| 401 Unauthorized | Token 过期或 `SECRET_KEY` 变更 |
| CORS | 检查 `main.py` CORS；前端域名与 API 域名 |
| 小程序 request 失败 | 合法域名、HTTPS、非 localhost |
| `ModuleNotFoundError` | 未激活 venv 或未 `pip install -r requirements.txt` |
| Python 版本不匹配 | 使用 3.10+ |
| SQLite locked | 避免多进程写同一 `recycle.db`；或迁 MySQL |
| bcrypt / passlib 警告 | 安装 `bcrypt<5` |

---

## 13. 本地自测速查

```bash
cd ~/Desktop/recycler && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

curl -X POST http://127.0.0.1:8000/dev/init

curl -X POST http://127.0.0.1:8000/api/account/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"10001","password":"111"}'
```

---

## 14. 待确认项

- 生产是否迁移 MySQL 及迁移脚本
- 是否将 `SECRET_KEY`、`DATABASE_URL` 改为环境变量
- 遗留 API（`/inquiries` 等）是否在网关层禁用
- 前端 `utils/request.js` 路径以实际 uni-app 工程为准
