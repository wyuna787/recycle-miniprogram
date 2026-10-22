# 二手电子设备回收交易平台 — 后端

> 本文档已根据当前后端代码结构更新（2026-05）。

二手电子设备回收交易平台的 **Python / FastAPI** 后端，支撑商家发布设备、回收商报价、订单发货签收验机、商家确认/申诉及平台交易流监控等 **MVP 主流程**。

**说明：** 本项目后端不是 Node.js，无 `package.json`。依赖以 `requirements.txt` 为准。

---

## 项目简介

核心业务（MVP 已实现部分见下文「API 接口概览」）：

- 商家 / 回收商 / 平台账号注册与登录
- 平台账号入驻审核
- 商家发布设备、生成询价
- 回收商查看询价并报价
- 商家确认报价并生成订单
- 商家发货（快递公司与单号）
- 回收商签收
- 回收商提交验机结果（通过 / 调价 / 退货）
- 商家确认验机完成或发起申诉
- 平台管理员查看全量交易流、关闭异常订单

以下能力 **当前后端未实现**（前端可能有 mock 或隐藏入口）：

- 资金池 / 预付款额度池
- 平台抽成结算
- 真实支付、短信
- 真实物流对接
- 数据分析报表
- 消息通知服务

---

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.10+（本地开发可用 3.11 / 3.13） |
| Web 框架 | FastAPI |
| ASGI 服务器 | Uvicorn |
| ORM | SQLAlchemy |
| 校验 | Pydantic v2 |
| 数据库 | SQLite（`recycle.db`，见 `database.py`） |
| 认证 | JWT（`python-jose`）+ 密码哈希（`passlib` + `bcrypt`） |
| 跨域 | FastAPI `CORSMiddleware`（`allow_origins=["*"]`） |

---

## 目录结构

```text
recycler/
├── main.py              # FastAPI 入口、路由注册
├── models.py            # SQLAlchemy 模型
├── database.py          # 数据库连接、migrate_db() 轻量迁移
├── schemas.py           # Pydantic 请求/响应模型
├── auth.py              # JWT、登录鉴权
├── account_utils.py     # 账号序列化等
├── trade_utils.py       # 交易/订单序列化、平台交易流
├── requirements.txt     # Python 依赖
├── requirements.py      # 历史遗留（与 database 早期重复，非 pip 依赖文件）
├── recycle.db           # SQLite 数据文件（运行后生成）
├── README.md
├── 部署清单.md
└── DEPLOYMENT_CHECKLIST.md
```

无 `src/`、`routes/` 分包；路由集中在 `main.py`。

---

## 本地启动

### 1. 安装依赖

```bash
cd ~/Desktop/recycler
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

当前代码 **未使用** `.env` 或 `os.getenv`。数据库 URL、JWT 密钥等写在源码中（见「环境变量说明」）。本地开发可直接启动。

### 3. 初始化数据库

首次启动时 `main.py` 会执行：

- `Base.metadata.create_all()` 建表
- `migrate_db()` 对 SQLite 做列级迁移

可选：写入固定测试账号与公司：

```bash
curl -X POST http://127.0.0.1:8000/dev/init
```

### 4. 启动服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问地址

| 用途 | 地址 |
|------|------|
| 健康检查 | http://127.0.0.1:8000/ |
| Swagger 文档 | http://127.0.0.1:8000/docs |

---

## 环境变量说明

### 当前代码中的配置（硬编码）

| 配置项 | 位置 | 当前值 |
|--------|------|--------|
| 数据库 | `database.py` → `DATABASE_URL` | `sqlite:///./recycle.db` |
| JWT 密钥 | `auth.py` → `SECRET_KEY` | `YOUR_RANDOM_SECRET_KEY` |
| JWT 算法 | `auth.py` → `ALGORITHM` | `HS256` |
| Token 有效期 | `auth.py` | 7 天 |
| 服务端口 | 启动命令指定 | 默认 `8000` |
| CORS | `main.py` | `allow_origins=["*"]` |

### 建议生产环境补充（待实现）

- `DATABASE_URL`（如 MySQL）
- `SECRET_KEY`（强随机字符串）
- `ACCESS_TOKEN_EXPIRE_DAYS`
- 是否开放 `/dev/init` 的开关

---

## 角色说明

| role | 说明 |
|------|------|
| `platform_admin` | 平台管理员：审核账号、查看交易流、关闭订单 |
| `merchant_owner` | 商家老板：发布设备、看询价报价、确认报价、发货、确认验机/申诉 |
| `merchant_staff` | 商家员工：权限可配置（询价/看全部询价/接单等） |
| `recycler_owner` | 回收商老板：本公司询价与订单 |
| `recycler_staff` | 回收商员工：通常仅自己成交的订单 |
| `recycler_keeper` | 回收商库管：本公司订单（代码中权限与 owner 类似） |

---

## 核心业务规则

下列为产品规则记录。**已实现** 表示当前后端 API 已覆盖；**待确认/未实现** 表示代码中暂无或未验证。

| 规则 | 状态 |
|------|------|
| 账号注册后需平台审核通过方可登录 | **已实现**（`pending` / `approved` / `rejected`） |
| 商家发布设备 → 询价 `pending_quote` | **已实现** |
| 回收商报价 → `quoted` | **已实现** |
| 商家确认报价 → 订单 `confirmed` | **已实现** |
| 商家发货 → `shipped` | **已实现** |
| 回收商签收 → `received` | **已实现** |
| 回收商验机 → `inspection_done` | **已实现** |
| 商家确认验机 → `completed` | **已实现** |
| 商家申诉 → `appealing` | **已实现** |
| 平台关闭订单 → `closed` | **已实现** |
| 平台固定抽成成交价 2% | **待确认/未实现**（无抽成 API） |
| 商家端不展示平台 2% 明细 | **待确认**（前端展示逻辑） |
| 商家老板/员工自定义抽成 | **待确认/未实现** |
| 商家员工前台展示价去小数 | **待确认**（前端） |
| 真实成交数据在数据分析栏 | **待确认/未实现**（无分析 API） |
| 回收商预付款额度池 | **待确认/未实现** |
| 报价金额 ≤ 资金池余额 | **待确认/未实现** |
| 资金池低于 5000 不可报价 | **待确认/未实现** |
| 员工抢单后订单归属该员工 | **部分实现**（`recycler_staff` 仅看自己订单） |
| 放弃报价后他人可抢 | **待确认/未实现** |
| 商家当日未操作订单 24:00 自动关闭 | **待确认/未实现**（无定时任务） |
| 回收商老板/库管看本公司全部数据 | **部分实现** |
| 回收商员工按单号查同事报价 | **待确认/未实现** |
| 平台管理员全流程审核与全量数据 | **部分实现**（交易流 + 账号审核） |

订单状态链（MVP）：

```text
confirmed → shipped → received → inspection_done → completed
                                              ↘ appealing → closed（平台）
```

---

## API 接口概览

完整参数见 **http://127.0.0.1:8000/docs**。

### 账号（MVP）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/account/register` | 注册 |
| POST | `/api/account/login` | 登录 |
| GET | `/api/account/me` | 当前用户 |
| GET | `/api/account/companies` | 公司列表（注册用） |
| GET | `/api/admin/accounts/pending` | 待审账号（平台） |
| POST | `/api/admin/accounts/{id}/approve` | 通过 |
| POST | `/api/admin/accounts/{id}/reject` | 驳回 |

### 设备 / 询价 / 报价 / 订单（MVP）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/devices` | 商家发布设备 |
| GET | `/api/inquiries/my` | 商家询价列表 |
| GET | `/api/inquiries/recycler` | 回收商可见询价 |
| POST | `/api/quotes` | 回收商报价 |
| GET | `/api/quotes/my` | 我的报价 |
| GET | `/api/quotes/by-inquiry/{id}` | 询价下报价列表 |
| POST | `/api/quotes/{id}/accept` | 商家确认报价 |
| GET | `/api/orders/my` | 我的订单 |
| GET | `/api/orders/{id}` | 订单详情 |
| POST | `/api/orders/{id}/ship` | 商家发货 |
| POST | `/api/orders/{id}/receive` | 回收商签收 |
| POST | `/api/orders/{id}/inspect` | 回收商验机 |
| POST | `/api/orders/{id}/confirm` | 商家确认完成 |
| POST | `/api/orders/{id}/appeal` | 商家申诉 |
| GET | `/api/admin/trades` | 平台交易流 |
| POST | `/api/admin/orders/{id}/close` | 平台关闭订单 |

### 开发 / 遗留接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/dev/init` | 重置测试账号与公司（清空交易表后重建） |
| GET/POST | `/users`、`/inquiries`、`/quotes`、`/orders` 等 | **遗留** 早期接口，MVP 前端以 `/api/*` 为准 |

### 待补充接口（产品规划，当前无后端）

- 资金池 / 充值审核
- 抽成与结算
- 消息通知
- 数据分析
- 真实物流 / 支付 / 短信

---

## 测试账号

执行 `/dev/init` 后可用（密码均为 `111`）：

| 角色 | 手机号 |
|------|--------|
| 平台管理员 | 30001 |
| 商家老板 | 10001 |
| 商家员工 | 10002 |
| 回收商A老板 | 20001 |
| 回收商A员工 | 20002 |

---

## `/dev/init` 行为

每次调用会 **删除并重建**：

- 交易：`orders`、`quotes`、`device_inquiries`、`devices`、`inquiries`（遗留表）
- 账号与公司：`users`、`merchant_companies`、`recycler_companies`

然后插入固定测试用户与 1 家商家公司、4 家回收商公司。**不会无限叠加**交易数据；可重复执行。

---

## 部署说明

生产部署步骤见 **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)**（中文简版见 [部署清单.md](./部署清单.md)）。

简要流程：上传代码 → `pip install -r requirements.txt` → 修改 `SECRET_KEY` 与数据库 → `uvicorn` + Nginx + systemd → 小程序 `BASE_URL` 改为 HTTPS 域名。

---

## 前端联调

uni-app 前端在独立目录，本地在 `utils/request.js` 配置：

```js
// 本地开发：http://127.0.0.1:8000
// 微信开发者工具如无法访问 127.0.0.1，改为电脑局域网 IP
// 上线：HTTPS 域名
```

微信开发者工具需开启「不校验合法域名」（仅本地）。

---

## 常见问题

| 现象 | 处理 |
|------|------|
| `localhost refused to connect` | 确认已执行 `uvicorn main:app --host 0.0.0.0 --port 8000` |
| 端口被占用 | 换端口或 `lsof -i :8000` 结束占用进程 |
| 小程序连不上后端 | 改用局域网 IP；检查开发者工具域名校验 |
| 401 未登录 | 重新登录；生产需检查 `SECRET_KEY` 是否变更导致旧 token 失效 |
| CORS 报错 | 当前后端已 `allow_origins=["*"]`，若仍报错检查是否请求了错误域名 |
| `passlib` / `bcrypt` 警告 | 使用 `bcrypt<5`（见 requirements.txt） |
| 数据库结构旧 | 删除 `recycle.db` 后重启，或依赖 `migrate_db()` 自动加列 |

---

## 待确认项

- `requirements.py` 与 `database.py` 内容重复，是否保留仅作历史文件
- `python-multipart` 已列入依赖，当前路由未使用文件上传，为 FastAPI 可选依赖
- 遗留路由 `/inquiries`、`/quotes/accept` 是否与 MVP 长期并存
- 生产环境是否关闭 `/dev/init` 及如何限流
