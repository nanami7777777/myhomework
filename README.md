# HotpotQA Redis Dashboard

一个适合作业展示的最小可用系统：使用 Redis 管理 `hotpotqa/hotpot_qa` 数据，提供多跳检索、简单聚类和可视化，并支持将静态前端托管到 GitHub Pages。

## 功能概览

- 使用 Redis 存储 HotpotQA 样本、分类索引和 token 倒排索引
- 支持按 `question / title / sentence` 进行简单检索
- 支持查看 supporting facts 对应的多跳路径图
- 支持对检索结果做轻量聚类并绘制柱状图
- 支持双模式展示：
  - **本地 API 模式**：连接 FastAPI + Redis
  - **静态 Demo 模式**：直接读取 `docs/data/demo_samples.json`

## 目录结构

- `app/core/`: 核心数据模型、标准化、聚类、多跳图构建
- `app/services/`: Redis 仓储层
- `app/tests/`: pytest 测试
- `scripts/import_hotpotqa.py`: 导入 HotpotQA 到 Redis
- `scripts/export_demo.py`: 从 Redis 导出演示 JSON
- `docs/`: GitHub Pages 静态前端

## 环境准备

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 启动 Redis

本项目默认连接 `redis://localhost:6379/0`。

如果你本机已安装 Redis，可直接启动：

```bash
redis-server
```

如果你使用其他地址，可通过环境变量覆盖：

```bash
export REDIS_URL=redis://localhost:6379/0
```

## 导入 HotpotQA 数据

先导入一小部分样本用于作业演示：

```bash
source .venv/bin/activate
python scripts/import_hotpotqa.py --subset distractor --split validation --limit 200
```

说明：
- `--subset` 可选 `distractor` 或 `fullwiki`
- `--split` 可选 `train` / `validation` / `test`
- `--limit` 建议作业演示时先用 100~500

## 启动后端 API

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

启动后接口默认位于：`http://127.0.0.1:8000/api`

主要接口：
- `GET /api/health`
- `GET /api/search?q=...`
- `GET /api/sample/{id}`
- `GET /api/path/{id}`
- `GET /api/cluster?q=...`
- `GET /api/stats`

## 启动静态前端

直接在项目根目录启动静态服务器：

```bash
python3 -m http.server 4173
```

然后访问：`http://127.0.0.1:4173/docs/`

页面会优先尝试连接本地 `http://127.0.0.1:8000/api`。如果 API 不可用，会自动切换到静态 Demo 模式。

## 导出演示数据

如果你想把 Redis 中的真实样本导出成 GitHub Pages 可直接使用的静态文件：

```bash
source .venv/bin/activate
python scripts/export_demo.py --limit 50 --output docs/data/demo_samples.json
```

## GitHub Pages 托管

推荐步骤：

1. 创建 GitHub 仓库并推送本项目
2. 进入仓库 `Settings -> Pages`
3. 选择从分支部署
4. 选择当前分支和 `/docs` 目录
5. 保存后等待 GitHub Pages 发布

托管后：
- 默认可直接展示仓库中已提交的 `demo_samples.json`
- 如果你只需要课程答辩演示，这已经足够
- 如果你想展示 Redis 实时结果，建议本地运行 API 并录制演示

## 运行测试

```bash
source .venv/bin/activate
pytest -q
```

## 作业可讲解点

你答辩时可以强调这几个点：

- **数据管理**：使用 Redis 保存样本和索引，而不是只读 JSON 文件
- **多跳检索**：通过 supporting facts 重建问题到答案的证据链
- **简单聚类**：对检索结果用 Jaccard 相似度做轻量聚类
- **可视化**：前端展示统计、结果列表、证据路径图和聚类图
- **工程落地**：同一套前端同时支持本地 API 模式和 GitHub Pages 静态模式
