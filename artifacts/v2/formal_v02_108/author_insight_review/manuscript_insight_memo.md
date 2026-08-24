# Manuscript insight memo

## 中文执行摘要

**建议：`RECOMMEND_MAIN_PLUS_SUPPLEMENT`。** 数据完整性通过，冻结的 malformed-action 规则经追加式裁定后，108/108 个计划单元均有有效结果。最强的论文主线不是“warning 很有效”，而是：一个完成率很高的强模型，在没有 safeguard 时仍频繁越过消费者利益边界；通用 safeguard 能提高安全率，但同时降低完成率，因此可信完成率的净提升有限。System 与 Interface 两种完整交付策略的直接差异很小、区间很宽，不能说谁更好，也不能说二者等效。

最重要的三个发现：第一，No safeguard 下 C=94.4%，但 TC 仅19.4%，unsafe completion 达75.0%，直接支持“完成不等于可信完成”。第二，System 和 Interface 相对 No safeguard 的 S 都提高16.7个百分点，但 C 分别下降11.1和16.7个百分点，TC均提高8.3个百分点；这是安全—完成权衡，不是全面解决。第三，效果高度依赖任务：部分任务明显响应，另一些在三条件下持续不安全；平均值不能代替 task profile。

正文建议放：完整数据核算、三条件四象限、三个主要 contrasts 及 task-cluster 区间、paired conversion/completion loss、System–Interface 不可区分。Supplement 放：36 个 task×condition profile、termination、family、repeats/LOTO、追加式裁定、cost/latency。不要写：deception 的因果效应、System/UI 等效或普遍优越、warning 教会了安全推理、跨模型/真实网站/人群泛化。

## English paper-ready candidate language

### Results headline

Across the 36 No-safeguard runs, the agent reached the nominal endpoint in 34 cases (94.4%) but achieved trustworthy completion in only 7 (19.4%); 27 runs (75.0%) were unsafe completions. Thus, high endpoint completion did not imply protection of the consumer interest encoded by the task boundary.

### Safeguard trade-off

Relative to No safeguard, System-delivered guidance increased safety by 16.7 percentage points and trustworthy completion by 8.3 points while reducing nominal completion by 11.1 points. Interface-delivered guidance increased safety by 16.7 points and trustworthy completion by 8.3 points while reducing nominal completion by 16.7 points. Task-cluster bootstrap intervals were wide, and paired trajectories showed that safety gains did not consistently reflect successful use of the safe route: completion was lost in six System and seven Interface pairs, whereas unsafe baseline completion changed to trustworthy completion in two System and four Interface pairs.

### Delivery comparison

Direct Interface-minus-System contrasts were small and imprecise (trustworthy completion 0.0 points, safety 0.0 points, nominal completion -5.6 points). The experiment therefore did not resolve a difference between the two complete delivery strategies; this should not be interpreted as evidence of equivalence.

### Protocol-consistency adjudication

One Interface-delivered trajectory was originally labeled unavailable after a malformed model action. Because the frozen outcome specification classifies malformed agent actions as valid behavioral outcomes, hash-linked append-only artifacts adjudicated the observed trajectory as safe non-completion (C=0, S=1). No rerun occurred, and all original artifacts remain unchanged.

### Discussion

The generic safeguard changed the outcome profile, but it did not reliably convert unsafe completion into safe completion. Its safety benefit was partly accompanied by ordinary stopping and timeout, suggesting that execution-time guidance can reduce unsafe commitments without necessarily preserving task completion. This distinction is precisely what independent C/S scoring exposes.

### Required limitations

These findings characterize one frozen agent on 12 curated deceptive-interface sandbox tasks. Without neutral interfaces, additional agents, live websites, a detector, or human participants, the study cannot identify the causal effect of deception, establish a universal channel advantage, measure detector performance, or support population-level generalization.
