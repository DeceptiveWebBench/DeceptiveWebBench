# 投稿缺漏检查清单

核查日期：2026-08-23。政策证据见 workshop_requirements_matrix.md；其中每个条目均链接到官方 CFP、OpenReview 或 NeurIPS 官方政策。

## 共同基线

### 已满足

- [x] 主文 8 页正文，三个 Workshop 的 full-paper 页数均合规。
- [x] 使用 NeurIPS 2026 dblblindworkshop style。
- [x] PDF 中作者与单位为匿名占位符，无致谢和作者身份链接。
- [x] 标题、Research Question、实验结果和结论在所有 venue 共享。
- [x] 108 个计划单元均有有效结果；malformed-action cell 依据冻结规则完成 append-only adjudication，未重跑、未插补。
- [x] 主文与 supplement 都有可复现的模型、浏览器、scorer、uncertainty 和费用说明。
- [x] 新图来自已审计 CSV；冻结分析图片未被覆盖。
- [x] Version 1 supplement 的源文件和 PDF 保持原哈希。

### 尚缺

- [ ] 匿名 artifact URL。GitHub/Hugging Face 上传后必须在登出状态测试，且 repository、release、文件元数据和 commit history 都不能泄露作者身份。
- [ ] 最终作者列表、顺序、单位、OpenReview profile IDs 和每位作者的可用邮箱。
- [ ] Venue submission metadata：keywords、TL;DR、track、reviewer nominee 等。
- [ ] 明确的 supplement 打包决定。
- [ ] IAEval 与 Verify-Agents 对 same-paper multi-workshop submission 的书面确认。
- [ ] 三地同期录用时的线下出席分工。

### 存在风险

- [ ] 三个官网截止均为 2026-08-29 AoE，但 live OpenReview form 的内部 duedate 与官网不同。应按官网较早时间提交，不能依赖 portal grace period。
- [ ] 只有 AI4GOOD 明确写明可同时投其他 NeurIPS Workshop；另外两方需确认。
- [ ] AI4GOOD 在 Paris、IAEval 在 Atlanta、Verify-Agents 在 Sydney，Workshop 日期重叠。
- [ ] Workshop CFP 没有统一说明是否要求 NeurIPS paper checklist、AI-writing disclosure 或独立 ethics statement。
- [ ] 当前 supplement 是独立 10 页 PDF；IAEval 和 AI4GOOD OpenReview form 没有独立 supplement 字段。

### 必须修改或确认后才能投稿

- [ ] 用对应 venue wrapper 编译，避免 camera-ready 或后续版本出现错误 Workshop 名称。
- [ ] 插入并验证匿名 artifact 链接，或在确认不提交 artifact 后删除所有 placeholder/comment 中的上传计划。
- [ ] 确认 supplement 上传方式；不要在 IAEval/AI4GOOD form 中假设存在第二文件槽。
- [ ] 检查所有作者是否与目标 Workshop organizer 存在 NeurIPS 定义的 personal/organizational conflict。
- [ ] 若多投，先取得 IAEval 和 Verify-Agents 书面许可。

### 仅投稿时处理

- [ ] 在 OpenReview 中填写所有作者 profile；不要在 PDF 中解除匿名。
- [ ] 粘贴与 PDF 一致的 title 和 abstract。
- [ ] 上传 PDF 后重新下载，检查页数、字体、链接和匿名性。
- [ ] 完成 portal 中的 email sharing、public release、review commitment 等确认。
- [ ] 保存 submission ID、上传时间和最终 SHA-256。

## IAEval

### 已满足

- [x] 8 页正文低于 full paper 9 页上限。
- [x] 论文直接覆盖 trajectory-level evaluation、deterministic grading、repeated runs、cost/latency 与 safety。
- [x] 双盲 PDF 和 NeurIPS workshop template 合规。

### 尚缺 / 必须确认

- [ ] OpenReview form 仅含 title、authors、abstract 和单一 PDF；询问 10 页 supplement 是否应拼接为 appendix。
- [ ] 向 iaeval2026-pc@googlegroups.com 确认同一核心论文同时投 AI4GOOD 与 Verify-Agents 是否允许。
- [ ] 指定至少一名能够到 Atlanta 线下展示的作者。
- [ ] 确认是否要求 checklist、ethics statement 或 AI-writing disclosure。

### 仅投稿时处理

- [ ] 使用 paper/venue_iaeval.tex 进行最终 venue build。
- [ ] 2026-08-29 23:59 AoE 前提交，不依赖 OpenReview 晚一小时的内部 duedate。

## AI4GOOD

### 已满足

- [x] 8 页正文位于 2--9 页范围。
- [x] Trustworthy Completion、consumer protection 和 stakeholder harm framing 与 General Track 高度匹配。
- [x] AI4GOOD FAQ 从其一方明确允许其他 NeurIPS Workshop 投稿。

### 尚缺 / 必须确认

- [ ] 不选择 Multi-Agent Safety and Security Track。
- [ ] 指定至少一名 reciprocal reviewer，并确认其 OpenReview profile、时间和 conflicts。
- [ ] 确认 10 页 supplement 是否合并在单一 PDF 后；portal 没有独立 supplement 字段。
- [ ] 公开官网与 OpenReview duedate 相差两天多；除非收到公开延期，按官网日期提交。
- [ ] 确认 accepted paper public release 和 author email sharing。
- [ ] 确认是否需要独立 ethics statement/checklist。

### 仅投稿时处理

- [ ] 使用 paper/venue_ai4good.tex 或默认 master build。
- [ ] 填写 keywords、可选 TL;DR、General Track、reviewer nominee。
- [ ] 安排 Paris 出席作者；展示形式目前尚未公布。

## Verify-Agents

### 已满足

- [x] 8 页正文位于 4--9 页普通论文范围。
- [x] Environment-grounded verification、deterministic signals、benchmark design 和 reliability framing 与 Workshop 三个 pillars 高度匹配。
- [x] Portal 有独立 optional supplementary PDF/ZIP 字段，当前 supplement 可作为单独 PDF 上传。

### 尚缺 / 必须确认

- [ ] 向 verify-agents-workshop@googlegroups.com 确认 same-paper multi-workshop submission。
- [ ] 确认未公布的 camera-ready deadline、出席要求、checklist 和 AI-writing disclosure。
- [ ] 准备 accepted-submission public release 确认。
- [ ] 作者可能被要求评审，需提前确认工作量与 conflicts。

### 仅投稿时处理

- [ ] 使用 paper/venue_verify_agents.tex 进行最终 venue build。
- [ ] 填写 keywords、可选 TL;DR，上传主 PDF 和可选 supplement。
- [ ] 安排 Sydney poster/oral 展示作者。
