# 三个 Workshop 的共享论文适配方案

核查日期：2026-08-23。官方政策与链接见 workshop_requirements_matrix.md。

## 单一事实源

继续维护一份共享 master：

- 主文：paper/neurips_2026.tex
- Bibliography：paper/references.bib
- 正式 supplement：paper/supplement_v2_formal.tex
- 正式结果来源：artifacts/v2/formal_v02_108/author_insight_review
- Publication figures：scripts/v2/generate_publication_figures_v02.py

三个版本不得改变标题、Research Question、abstract 数字、任务数量、condition 定义、append-only adjudication handling、uncertainty、结论或 limitations。Venue adaptation 只允许改变 Workshop 名称、OpenReview metadata、supplement 包装和轻量 framing emphasis。

## Venue wrapper

Master 现在通过 SubmissionWorkshopTitle 宏配置 Workshop 名称，三个薄 wrapper 为：

- paper/venue_ai4good.tex
- paper/venue_iaeval.tex
- paper/venue_verify_agents.tex

Wrapper 仅设置 workshoptitle 并输入同一 master，不复制正文。双盲 submission footer 在当前 NeurIPS style 中仍显示通用 NeurIPS submission notice；workshoptitle 会在适用的 final/workshop build 中生效。

推荐 build：

    cd paper
    tectonic venue_ai4good.tex
    tectonic venue_iaeval.tex
    tectonic venue_verify_agents.tex

主交付 PDF 仍由以下 master build 产生：

    tectonic neurips_2026.tex
    tectonic supplement_v2_formal.tex

## IAEval 适配

### 保持不变

- 标题与 abstract。
- Trustworthy Completion 四象限、12-task benchmark、三种 safeguard delivery 和全部正式结果。
- 8 页正文。

### 轻量 emphasis

- OpenReview abstract/cover metadata 中优先突出 trajectory-level evaluation、deterministic grading、repeated trials、task-cluster uncertainty 与 cost/latency。
- 不把工作改写成 user-simulator 论文；环境是 deterministic consumer sandbox，不是 human simulator。
- 推荐 metadata 关键词仅在允许字段中填写；当前 IAEval form 没有 keywords/TL;DR 字段。

### 包装

- Form 只有一个 PDF。若 chairs 确认 appendix 可随主 PDF 上传，可生成 main + references + supplement 的合并 submission PDF；否则只提交主 PDF，并把匿名 artifact 链接放在正文允许位置。
- 至少一位作者必须线下到 Atlanta 展示。

## AI4GOOD 适配

### 保持不变

- 标题、abstract 和所有正式结果。
- Consumer-only、one-agent、synthetic-task 和 no-neutral-control limitations。

### 轻量 emphasis

- General Track framing 优先突出 consumer financial/privacy interests、stakeholder-grounded boundaries、unintended harm 和 trustworthy deployment evidence。
- 不选择 Multi-Agent Safety and Security Track；本文不是 multi-agent 研究。
- 建议 keywords：trustworthy web agents; consumer protection; agent evaluation; deceptive interfaces; execution-time safeguards。
- 建议 TL;DR：Endpoint success can conceal unsafe consumer commitments; independent completion and safety scoring exposes the gap and shows that generic safeguards trade safety gains against completion loss.

### 包装

- 默认 master 已使用 AI4GOOD workshoptitle；venue_ai4good.tex 提供显式 wrapper。
- Form 没有独立 supplement 字段。向 chairs 确认是否将 supplement 合并为 appendix。
- 提前指定 reciprocal reviewer，完成 email sharing 和 accepted-work public-release consent。

## Verify-Agents 适配

### 保持不变

- 标题、abstract、framework、benchmark 和结果。
- 不把 deterministic scorer 描述成 formal proof system，也不声称 verifier performance。

### 轻量 emphasis

- OpenReview metadata 优先突出 environment-grounded verification、heterogeneous verifiable signals、monotonic unsafe boundaries 和 auditability。
- 建议 keywords：agent verification; environment-grounded evaluation; web agents; deterministic scoring; trustworthy completion。
- 建议 TL;DR：A deterministic environment-grounded benchmark separates whether a web agent finishes from whether it crosses a stakeholder-protecting unsafe boundary.

### 包装

- 使用 venue_verify_agents.tex。
- Portal 支持独立 supplementary PDF/ZIP；可上传 supplement_v2_formal.pdf，并在匿名 ZIP 中加入复现说明和必要代码。
- 不把 optional supplement 当作 reviewers 必读内容；主文必须自足。

## 同时投稿与出席

在提交前完成两项闸门：

1. 取得 IAEval 和 Verify-Agents 对 identical-core multi-workshop submission 的书面许可。AI4GOOD FAQ 已明确从其一方允许，但仍建议把三投计划完整告知。
2. 为 Atlanta、Paris、Sydney 分别指定可能出席的作者。若作者人数或差旅无法覆盖多地，应优先选择 scope 最匹配且最可执行的 venue，而不是提交后再解决。

推荐 scope 排序并非科学结论：

1. IAEval：最直接强调评价方法和 trajectory evidence。
2. Verify-Agents：最直接强调 environment-grounded verification。
3. AI4GOOD：stakeholder protection 和 consumer harm framing 很强，但需要更明确地解释其 AI-for-Good 外部意义。

## 不建议做的变体

- 不创建三套不同数据表或结果图。
- 不对 System/Interface 直接差异做 venue-specific 强结论。
- 不在某个版本隐藏 malformed-action adjudication、completion loss 或 one-agent/no-neutral limitations。
- 不为不同 Workshop 改标题。
- 不在未得到许可前把三投描述成合规既定事实。
