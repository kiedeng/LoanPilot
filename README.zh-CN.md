# LoanPilot

LoanPilot 是一个银行贷款 AI Agent 开源演示项目。它将对话式贷款助手、FastAPI 工作流服务、Mock 银行业务适配器、SQLite 演示数据，以及基于 A2UI 的金融科技风卡片前端组合在一起。

[English README](README.md)

## 项目亮点

- 覆盖贷款产品推荐、额度预评估、贷款申请、材料收集、还款服务、提前还款试算和人工接管等流程。
- 使用官方 A2UI v0.9 消息协议，并在前端注册 LoanPilot 自定义 catalog，渲染专业金融科技风业务卡片。
- 工作流当前为确定性演示实现，结构上为后续 LangGraph 编排预留边界。
- 银行业务能力封装在 Mock adapter 之后，便于未来替换为真实银行系统。
- 技术栈清晰：FastAPI 后端、React + Vite 前端、SQLAlchemy 数据模型、基础 API 测试。

## 目录结构

```text
LoanPilot/
  backend/                 FastAPI API、领域模型、服务、工作流和测试
  frontend/                React + Vite 应用和自定义 A2UI catalog
  docs/                    架构、产品演示、安全和开发文档
  .github/                 CI、Issue 模板、PR 模板
  README.md                英文文档
  README.zh-CN.md          中文文档
```

## 技术栈

- 前端：React、Vite、TypeScript
- Agent UI：`@a2ui/react/v0_9`、`@a2ui/web_core/v0_9`、LoanPilot 自定义 A2UI catalog
- 后端：FastAPI、SQLAlchemy、Pydantic Settings
- 数据库：默认 SQLite，可通过 `DATABASE_URL` 配置外部数据库
- 测试：pytest、FastAPI TestClient、Vite production build

## 快速开始

### 后端

```bash
cd /mnt/d/1/LoanPilot
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8001 --reload
```

后端 API 地址：`http://127.0.0.1:8001`。OpenAPI 文档地址：`http://127.0.0.1:8001/docs`。

### 前端

```bash
cd /mnt/d/1/LoanPilot/frontend
npm install
VITE_API_BASE=http://127.0.0.1:8001/api npm run dev -- --host 0.0.0.0 --port 5173
```

前端访问地址：`http://localhost:5173`。

## 环境变量

如需本地覆盖配置，可以复制 `.env.example`：

```bash
cp .env.example .env
```

可用变量：

- `APP_NAME`：应用显示名称。
- `DATABASE_URL`：SQLAlchemy 数据库连接地址，默认使用本地 SQLite。
- `VITE_API_BASE`：前端 API 基础地址，通常为 `http://127.0.0.1:8001/api`。

不要提交 `.env`、本地数据库、日志、密钥、Token、生产数据库连接串。

## 演示场景

- 个人用户：咨询装修贷款、测算额度、创建申请、上传演示材料。
- 小微企业主：咨询经营周转贷款、查看经营贷推荐、了解材料清单。
- 存量贷款客户：查询本月账单、查看还款计划、发起提前还款试算。
- 理财客户：咨询短期流动性贷款并进行方案对比。

更多脚本见 [docs/product/demo-script.md](docs/product/demo-script.md)。

## A2UI 集成

后端输出 A2UI v0.9 消息：

- `createSurface`
- `updateDataModel`
- `updateComponents`

前端通过 `MessageProcessor` 处理消息，并使用 `A2uiSurface` 渲染 surface。LoanPilot 注册了自定义 A2UI catalog，包含 `LoanInsightCard`、`LoanInfoCard`、`LoanComparisonCard`、`LoanApplicationCard` 等金融业务组件。

## 验证

```bash
pytest -q
cd frontend && npm run build
```

## 安全说明

LoanPilot 是演示系统，不执行真实授信审批、身份核验、资金划转、证件存储或银行核心交易。连接真实银行系统前请先阅读 [SECURITY.md](SECURITY.md)。

## 贡献

欢迎贡献代码、文档和建议。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，再提交 Issue 或 Pull Request。

## 许可证

本项目基于 MIT License 开源，详见 [LICENSE](LICENSE)。
