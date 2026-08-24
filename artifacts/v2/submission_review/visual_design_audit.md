# 论文视觉设计审计

审计日期：2026-08-23。

## 结论

主文和 Protocol v2 supplement 的数据图已切换到一套独立、可复现、vector-first 的 publication figure pipeline。冻结的 author-insight 分析图片及其哈希没有被修改；新版图直接读取同一组已审计 CSV，不重新计算或改写任何实验结果。

## 统一视觉规范

### Condition palette

- No safeguard：#7A7A7A，中性灰，无纹理。
- System-delivered safeguard：#0072B2，Okabe-Ito 系列蓝色，斜线纹理或圆形 marker。
- Interface-delivered safeguard：#E69F00，Okabe-Ito 系列橙色，交叉纹理或方形 marker。

条件比较图在颜色以外继续使用 hatch、marker shape、边框、直接数值标签和明确 legend，因此黑白打印时仍可区分。四象限 outcome 图是例外：为避免大面积纹理噪声，它使用有明显亮度差的纯色、细白分隔线和直接标签；如投稿流程要求专门的黑白版本，应另行生成稀疏纹理版本，而不是增加当前彩色图的纹理密度。

### Outcome palette

四象限图表达的是 outcome 而不是 condition，因此使用独立但克制的 palette：

- Trustworthy completion：沉稳蓝 #4C78A8。
- Unsafe completion：低饱和陶土橙 #D97941。
- Safe non-completion：浅蓝灰 #B8C4CE。
- Unsafe failure：炭灰 #555B66。

该图不再依赖红绿对立或密集网纹。彩色版本采用纯色填充、细白分隔线和基于底色亮度自动选择的黑/白标签；足够大的分段同时显示原始 count 和 percentage。浅灰 #E6E8EB 网格与纯白背景降低了视觉噪声。

### Typography and line work

- 所有新数据图使用 DejaVu Sans，PDF 内嵌 TrueType subset。
- 统一轴线 0.8 pt、数据线 1.4 pt、误差线 1.6 pt、浅灰 grid 0.6 pt。
- 图例去除重边框，标题、轴标签和直接数值采用一致层级。
- 误差图用蓝色圆形和橙色方形，同时显示点估计标签与 95% interval。
- Task profile 不再使用 RdYlGn；改为离散灰阶、直接 rate 标签和彩色 condition header。所有单元现均为三个有效 repeats，无需 unavailable dagger。

## Figure inventory

| LaTeX 用途 | 新 publication figure | 数据源 | 非颜色编码 |
|---|---|---|---|
| Main C/S outcome distribution | paper/figs/protocol_v2_cs_quadrants_publication.pdf | condition_summary.csv | 亮度对比、白色分隔线、count、percentage、denominator |
| Main safeguard contrasts | paper/figs/protocol_v2_tradeoff_publication.pdf | contrast_bootstrap.csv | circle/square marker、直接 estimate、error bar |
| Supplement task profiles | paper/figs/protocol_v2_task_profiles_publication.pdf | task_condition_summary.csv | 离散灰阶、直接 rate、dagger |
| Supplement paired transitions | paper/figs/protocol_v2_paired_transitions_publication.pdf | paired_transitions.csv | hatch、边框、bar labels |
| Generated cost/latency diagnostic (not included in compact supplement) | paper/figs/protocol_v2_cost_latency_publication.pdf | cost_summary.csv | hatch、边框、直接 labels |
| Main framework | paper/figs/trustworthy_completion_cs_pipeline.pdf | framework/scoring specification | 直接 quadrant labels；无红绿对立 |

生成器为 scripts/v2/generate_publication_figures_v02.py。它写入 publication_figure_manifest.json，其中记录输入 CSV 和输出 PDF 的 SHA-256、condition palette、vector_output=true 和 data_modified=false。

## 冻结分析图保护

artifacts/v2/formal_v02_108/author_insight_review/review_manifest.json 中的原分析图哈希仍由 manuscript verifier 检查。原始文件包括：

- fig_cs_quadrants_by_condition.png
- fig_tradeoff_contrasts.png
- fig_task_condition_heatmap.png
- fig_paired_transitions.png
- fig_cost_latency_supplement.png

新版脚本没有写入 author_insight_review。旧 PNG 仍可用于审计对照，但 LaTeX 已改用 publication PDF。

## Task screenshots

三张任务截图没有裁色、重着色、内容编辑或生成式处理，只在 LaTeX 中统一加 0.4 pt 边框并保持等宽对齐：

- forced action：1280x720，SHA-256 1e05c4c8b066a976c9aa5d7062115308f766dcc8cdceb4d647d6c4d04cafe07e。
- sneaking：1280x720，SHA-256 21c13958a0752ddadf550d5c23569550acb9a29f8ce698d5778ca50dd92d54de。
- interface interference：1280x720，SHA-256 eed227211c402ecf6f6f69d9d5efb9b0afb9c712efec3b7dace26ac790138a6b。

在 5.5-inch 正文宽度下，每张图显示宽度约 1.74 inch，有效分辨率约 736 dpi，高于 300 dpi 要求。

## LaTeX and wrapper changes

- paper/neurips_2026.tex 和 paper/supplement_v2_formal.tex 已更新为引用 publication PDF。
- paper/figs/task_family_examples_v02.tex 只增加统一边框与对齐。
- 主文 workshoptitle 现在通过 SubmissionWorkshopTitle 宏配置。
- 三个 wrapper 只设置 Workshop 名称，不复制或改写正文。

## 验证

- 主 PDF：10 页，正文 8 页，References 在第 8 页 Conclusion 后开始。
- Supplement：10 页；保留完整数值表和关键诊断图，移除了与表格重复的 task-rate 表及 cost/latency 图。
- Tectonic 编译无 LaTeX error、无 undefined citation/reference、无 overfull box。
- Publication figures 和 framework figure 的字体均为嵌入式字体。
- Manuscript verifier 从原始 formal attempts 和 hash-linked adjudication 重建全部 108 行并核对 108 个有效 C/S outcomes；结果通过。
- Version 1 supplement 源文件和 PDF 哈希保持不变。
- 本轮没有调用模型/实验 API，没有上传、提交、commit 或 push。
