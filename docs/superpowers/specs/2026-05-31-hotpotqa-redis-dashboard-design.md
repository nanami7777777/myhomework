# HotpotQA Redis 多跳检索展示系统设计

## 目标
构建一个适合作业展示的最小可用系统：使用 Redis 管理 `hotpotqa/hotpot_qa` 数据，提供问题检索、多跳过程查看、简单聚类和可视化；前端为静态页面，可部署到 GitHub Pages。

## 范围
- 支持从 Hugging Face `hotpotqa/hotpot_qa` 导入样本到 Redis
- 支持基于问题、上下文标题、句子内容的简单检索
- 支持查看样本的多跳证据链与答案路径
- 支持对检索结果做轻量聚类并可视化展示
- 支持导出静态演示数据，使 GitHub Pages 页面在无后端时也能运行

## 非目标
- 不实现训练或模型推理
- 不依赖 RediSearch、向量数据库或复杂流式计算
- 不追求全量数据高性能检索，优先保证结构清晰和功能完整

## 架构
系统分为三层：
1. 数据层：Python 导入脚本将 HotpotQA 样本标准化后写入 Redis，建立 token 倒排索引与分类集合索引。
2. 服务层：FastAPI 提供检索、详情、多跳图、聚类、统计接口。
3. 展示层：静态 HTML/CSS/JS 页面，优先请求 API；若 API 不可用，则回退到预导出的静态 JSON 演示数据。

## 数据设计
每条样本在 Redis 中保存为一个 Hash：
- `hotpot:sample:{id}`
- 关键字段：`id`、`subset`、`split`、`question`、`answer`、`type`、`level`、`context_docs_json`、`supporting_facts_json`

索引设计：
- 集合索引：`hotpot:index:split:{split}`、`hotpot:index:type:{type}`、`hotpot:index:level:{level}`
- 倒排索引：`hotpot:index:token:{token}`，成员为样本 `id`
- 全量 ID 集：`hotpot:index:all`

## 检索设计
- 使用统一 tokenizer 处理 query、question、title、sentence
- 检索时对 query token 命中的倒排集合做聚合
- 对候选样本按命中 token 数、supporting facts 数、context 文档数做简单打分排序
- 可按 split/type/level 过滤

## 多跳可视化设计
对单条样本构建图结构：
- 节点：Question、Context Title、Supporting Sentence、Answer
- 边：question->title、title->supporting sentence、supporting sentence->answer
- 对 comparison 类问题支持并行证据链展示，对 bridge 类问题支持串联展示

## 聚类设计
- 采用轻量的基于 token Jaccard 相似度的贪心聚类
- 输入为当前检索结果或导出样本子集
- 输出 cluster 列表：`label`、`size`、`keywords`、`sample_ids`
- 前端将 cluster size 绘制为柱状图，并显示聚类关键词摘要

## 部署设计
- 后端本地运行：`uvicorn app.main:app --reload`
- 前端静态目录放在 `docs/`，可直接通过 GitHub Pages 托管
- 提供 `scripts/export_demo.py` 将 Redis 中的样本导出到 `docs/data/demo_samples.json`

## 测试策略
- 对标准化、tokenize、图构建、聚类函数编写 pytest 单元测试
- 对 API 关键路由编写最小接口测试
- 静态前端以手动验证为主，并提供运行说明

## 作业交付物
- 可运行后端代码
- 可部署静态前端
- Redis 导入与导出演示脚本
- README 使用说明
- 基本测试
