# LoanPilot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-2f74c0)](frontend/package.json)
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)](backend/requirements.txt)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](CHANGELOG.md)

LoanPilot 是一个银行贷款 AI Agent 开源演示项目。它将对话式贷款助手、FastAPI 工作流服务、Mock 银行业务适配器、SQLite 演示数据，以及基于 A2UI 的金融科技风卡片前端组合在一起。

[English README](README.md)

## 核心特性

- 覆盖贷款产品推荐、额度预评估、贷款申请、材料收集、还款服务、提前还款试算和人工接管等流程。
- 使用官方 A2UI v0.9 消息协议，并在前端注册 LoanPilot 自定义 catalog，渲染专业金融科技风业务卡片。
- 内置金融业务组件：`LoanInsightCard`、`LoanInfoCard`、`LoanComparisonCard`、`LoanApplicationCard`。
- 使用 Dify mock 编排，支持流式响应、意图识别、缺参追问和工具调用式事件。
- 银行业务能力封装在 Mock adapter 之后，便于未来替换为真实银行系统。
- 技术栈清晰：FastAPI 后端、React + Vite 前端、SQLAlchemy 数据模型、基础 API 测试。

## 技术架构

```text
React + Vite 前端
  -> LoanPilot 自定义 A2UI catalog
  -> @a2ui/react A2uiSurface
  -> @a2ui/web_core MessageProcessor
  -> FastAPI 后端
  -> AiGateway + MockDifyClient
  -> MockBankingAdapter
  -> SQLite 或配置的 SQLAlchemy 数据库
```

后端输出 A2UI v0.9 消息：

- `createSurface`
- `updateDataModel`
- `updateComponents`

前端通过 `MessageProcessor` 处理消息，并使用 `A2uiSurface` 渲染原生 React 业务组件。这样既保持 Agent UI 的声明式协议，又让 LoanPilot 拥有自己的金融科技视觉风格。

## 环境要求

- Python 3.11+
- Node.js 22+
- npm 10+
- Git

可选：

- `venv`、Conda 或 uv 等虚拟环境工具。
- SQLite CLI，用于查看本地演示数据。

## 安装方式

克隆仓库：

```bash
git clone https://github.com/kiedeng/LoanPilot.git
cd LoanPilot
```

安装后端依赖：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

安装前端依赖：

```bash
cd frontend
npm install
```

## 配置说明

如需本地覆盖配置，可以复制 `.env.example`：

```bash
cp .env.example .env
```

可用变量：

- `APP_NAME`：应用显示名称。
- `DATABASE_URL`：SQLAlchemy 数据库连接地址，默认使用本地 SQLite。
- `VITE_API_BASE`：前端 API 基础地址，通常为 `http://127.0.0.1:8001/api`。

不要提交 `.env`、本地数据库、日志、密钥、Token、生产数据库连接串。

## 快速开始

启动后端：

```bash
cd /mnt/d/1/LoanPilot
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8001 --reload
```

启动前端：

```bash
cd /mnt/d/1/LoanPilot/frontend
VITE_API_BASE=http://127.0.0.1:8001/api npm run dev -- --host 0.0.0.0 --port 5173
```

访问地址：

- 前端：`http://localhost:5173`
- 后端 API：`http://127.0.0.1:8001`
- OpenAPI：`http://127.0.0.1:8001/docs`

## 使用示例

可以在聊天界面输入：

- `我想贷20万装修，多久能放款？`
- `我是开餐饮店的，想贷50万周转`
- `我这个月贷款要还多少？`
- `我有理财产品，临时需要10万周转`
- `对比一下贷款方案`

HTTP 请求示例见 [examples/http](examples/http)。

## API 文档

主要接口：

| Method | Path | 说明 |
| --- | --- | --- |
| `POST` | `/api/chat/message` | 发送聊天消息并接收 A2UI 卡片消息。 |
| `POST` | `/api/actions/{action_id}` | 执行 A2UI 卡片动作。 |
| `GET` | `/api/conversations/{conversation_id}` | 查询会话历史和工作流状态。 |
| `GET` | `/api/loan/products` | 获取 Mock 贷款产品。 |
| `POST` | `/api/loan/pre-assess` | 执行 Mock 额度预评估。 |
| `POST` | `/api/loan/applications` | 创建 Mock 贷款申请。 |
| `GET` | `/api/loan/repayment-plan/{loan_id}` | 查询 Mock 还款计划。 |
| `POST` | `/api/loan/prepayment/quote` | 生成 Mock 提前还款试算。 |

完整 API schema 请启动后端后访问 `http://127.0.0.1:8001/docs`。

## 项目结构

```text
LoanPilot/
  backend/                 FastAPI API、领域模型、服务、工作流和测试
  frontend/                React + Vite 应用和自定义 A2UI catalog
  docs/                    架构、产品演示、安全和开发文档
  examples/                请求示例和集成片段
  .github/                 CI、Issue 模板、PR 模板
  README.md                英文文档
  README.zh-CN.md          中文文档
```

## 开发指南

后端源码位于 `backend/app`，前端源码位于 `frontend/src`。

推荐开发验证流程：

```bash
pytest -q
cd frontend && npm run build
```

更多开发说明见 [docs/development/local-setup.md](docs/development/local-setup.md)。

## 测试方式

后端：

```bash
pytest -q
```

前端：

```bash
cd frontend
npm run build
```

GitHub Actions 会在推送和 Pull Request 时运行后端测试和前端构建。

## 部署说明

LoanPilot 是演示应用。简单部署方式：

1. 使用 `npm run build` 构建前端。
2. 将 `frontend/dist` 交给静态 Web 服务托管。
3. 使用生产 ASGI 服务和反向代理运行 FastAPI。
4. 如果本地 SQLite 不适合部署场景，请通过 `DATABASE_URL` 配置托管数据库。
5. 为部署后的前端域名显式配置 CORS 白名单。

不要将演示 Mock adapter 用于真实贷款审批或放款决策。

## 版本计划

- 增加前后端契约的类型化 API client。
- 增加 A2UI 卡片交互的 Playwright 冒烟测试。
- 增加可选 Docker Compose 开发环境。
- 将 MockDifyClient 替换为真实 Dify API 客户端。
- 增加银行产品、材料、还款系统的 adapter 示例。

## 贡献指南

欢迎贡献代码、文档和建议。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，较大的改动建议先提交 Issue，再提交带验证说明的 Pull Request。

## 开源协议

本项目基于 MIT License 开源，详见 [LICENSE](LICENSE)。

## 致谢

- [A2UI](https://a2ui.org/) 提供声明式 Agent UI 协议和 React 渲染器。
- [FastAPI](https://fastapi.tiangolo.com/) 提供后端框架。
- [React](https://react.dev/) 和 [Vite](https://vite.dev/) 提供前端开发栈。
- [SQLAlchemy](https://www.sqlalchemy.org/) 提供 ORM 能力。
