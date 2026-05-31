# HotpotQA Redis Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个使用 Redis 管理 HotpotQA 数据、提供多跳检索与可视化，并支持 GitHub Pages 静态展示的课程作业项目。

**Architecture:** 使用 Python/FastAPI 作为 API 层，Redis 保存样本与倒排索引，静态前端通过 API 或预导出 JSON 展示检索、多跳图和简单聚类。系统采用双模式：本地完整模式依赖 Redis 与 API，GitHub Pages 演示模式依赖静态 JSON。

**Tech Stack:** Python 3.11+, FastAPI, redis-py, pytest, vanilla JS, Chart.js, Cytoscape.js

---

### Task 1: 初始化项目结构与依赖

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `README.md`
- Create: `app/__init__.py`
- Create: `app/core/__init__.py`
- Create: `app/services/__init__.py`
- Create: `app/tests/__init__.py`
- Create: `docs/index.html`
- Create: `docs/styles.css`
- Create: `docs/app.js`

- [ ] 写入依赖、忽略规则、项目说明和基础目录
- [ ] 明确本地运行与 GitHub Pages 演示模式

### Task 2: 先写核心单元测试

**Files:**
- Create: `app/tests/test_processing.py`
- Create: `app/tests/test_clustering.py`
- Create: `app/tests/test_graph.py`

- [ ] 先为 tokenizer、样本标准化、聚类、多跳图构建写失败测试
- [ ] 运行 pytest，确认测试先失败

### Task 3: 实现数据处理核心逻辑

**Files:**
- Create: `app/core/models.py`
- Create: `app/core/processing.py`
- Create: `app/core/clustering.py`
- Create: `app/core/graph.py`

- [ ] 实现通过测试所需的最小逻辑
- [ ] 运行 pytest，确认核心测试通过

### Task 4: 实现 Redis 仓储与导入脚本

**Files:**
- Create: `app/services/repository.py`
- Create: `scripts/import_hotpotqa.py`
- Create: `scripts/export_demo.py`

- [ ] 封装 Redis 读写、索引写入、样本检索接口
- [ ] 实现从 Hugging Face 导入和向静态 JSON 导出

### Task 5: 编写 API 层及测试

**Files:**
- Create: `app/main.py`
- Create: `app/tests/test_api.py`

- [ ] 先写 API 失败测试
- [ ] 实现 `/api/health`、`/api/search`、`/api/sample/{id}`、`/api/path/{id}`、`/api/cluster`、`/api/stats`
- [ ] 再运行 pytest，确认通过

### Task 6: 构建静态前端

**Files:**
- Modify: `docs/index.html`
- Modify: `docs/styles.css`
- Modify: `docs/app.js`
- Create: `docs/data/.gitkeep`

- [ ] 实现搜索表单、结果列表、样本详情、多跳图、聚类图、模式切换说明
- [ ] 优先走 API，失败时回退到静态 demo 数据

### Task 7: 联调与收尾

**Files:**
- Modify: `README.md`
- Modify: `docs/app.js`
- Modify: `docs/styles.css`

- [ ] 补充运行步骤、GitHub Pages 部署说明、导入导出命令
- [ ] 检查 lint/test，并修复明显问题
