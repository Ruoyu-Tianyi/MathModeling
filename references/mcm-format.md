# 美赛（MCM/ICM）格式与合规规范

`assets/mcm-template.docx` 由 `scripts/make_mcm_template.py` 按本规范生成；`build_docx.py --mcm` 一键产出合规 Word。

## 硬性规则（COMAP 官方）

- **页数限制**：正文（从 Summary Sheet 起）≤ 25 页；参考文献、附录、AI 使用报告不占页数
- **Summary Sheet**：第 1 页，含论文题目 + Summary（≤ 1 页，第一轮筛选唯一依据）
- **字体**：正文 ≥ 12 pt（推荐 Times New Roman 12 pt），1.5 倍行距
- **页面**：US Letter（21.59 × 27.94 cm），四边页边距 ≥ 1 inch（2.54 cm）
- **页码**：每页编页码（模板页脚 "Page X"）
- **匿名性**：论文内**不得出现队号以外任何身份信息**（姓名、学校、导师），队号写在 Summary Sheet 页眉
- **图表题注**："Figure 1: ..."（图下）/ "Table 1: ..."（表上），连续编号
- **语言**：全英文；公式、符号定义首次出现即给出

## AI 使用报告（2024 起强制）

- 位置：论文末尾（References 之后），标题 "Report on Use of AI"，不占 25 页
- 内容：用了哪些 AI 工具、用于什么（分析/建模/编程/写作）、如何验证
- 模板：`assets/ai-use-report.md`，写作时**如实填写**——本 skill 的使用本身就必须声明
- 关键表述：团队对 AI 产出的所有结果独立验证并负全责（verification statement）

## 与国赛流程的差异（skill 执行时）

| 环节 | 国赛 | 美赛 |
|---|---|---|
| 模板 | assets/cumcm-template.docx | assets/mcm-template.docx（`build_docx.py --mcm`） |
| 论文骨架 | assets/paper-template.md | assets/paper-template-en.md |
| 摘要 | 摘要 + 关键词（中文） | Summary + Keywords（英文，≤1 页） |
| precheck | `--lang zh` | `--lang en`（含 AI 报告检查） |
| 附录 | 代码附录 | 代码附录 + AI 使用报告 |
| 页数 | 无硬性限制（建议 ≤ 20） | ≤ 25 页（publish 应检查） |

## 评审关注点（与国赛的差异）

- Summary 权重更高（第一轮只看它）；强调故事线（problem → insight → impact）
- 创新性与假设合理性重于计算复杂度；结果必须落到现实建议（often a letter/memo required）
- 25 页预算管理：正文紧凑，细节全部推附录
