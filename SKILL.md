---
name: math-modeling-contest
description: 数学建模竞赛（国赛 CUMCM、美赛 MCM/ICM 及同类赛事）全流程求解技能：输入赛题文本/PDF，输出可直接提交的完整建模论文（含模型推导、可运行代码、规范图表、摘要与参考文献）。当用户给出数模赛题、要求"做题/建模/写数模论文/准备国赛美赛"，或提及 CUMCM、MCM、ICM、数模国赛/美赛、数学建模论文时使用。赛题需要真实数据（经济金融、宏观、行业、人口等）时，按 references/data-sources.md 路由到 Wind、Gildata、iFinD、World Bank、IMF、Yahoo Finance 等已安装数据插件取数，禁止编造数据。
---

# 数学建模竞赛全流程

目标：赛题 → 可提交论文。默认在当前 workspace 下建立比赛项目目录（用 `scripts/scaffold.py`），全部产出落盘。

## 总流程（五阶段，按门禁推进）

```
P0 审题立项 → P1 数据获取 → P2 建模求解 → P3 论文写作 → P4 校验交付
```

每阶段有完成门禁（Gate），未过门禁不进入下一阶段。默认一次会话内完成全链路；若赛题复杂，按阶段分段交付并汇报进度。

### P0 审题立项（Gate：产出《问题分析》）

1. 读取赛题全文（用户给的文本 / PDF / 图片先转为文本）。
2. 拆解为子问题 Q1…Qn，每问标注：题型（评价/预测/优化/机理/数据分析）、拟用模型候选、所需数据及来源。
3. 查 `references/problem-types.md` 做题型→模型路由；确定整体技术路线。
4. 输出《问题分析》小节（每问：重述 + 思路 + 模型选择理由 + 数据计划）。若用户在线，简明确认后再进 P1；用户不在线则按最合理方案继续。
5. 运行 `python scripts/scaffold.py --name <项目名> --lang zh`（美赛用 `en`）生成目录与模板。

### P1 数据获取（Gate：数据落盘 data/ 且来源可溯）

- 按 `references/data-sources.md` 选择数据源：金融/宏观/行业真实数据走已安装数据库插件（Wind、Gildata、iFinD、World Bank、IMF、Yahoo 等），其余用公开统计或赛题附件。
- **铁律：不编造数据。** 取不到的真实数据，改为可复现的仿真/假设数据，并在论文"模型假设"中显式声明；数据库报错如实记录，不跨域乱改参数。
- 所有原始数据保存到 `data/`，文件名带来源与日期；在 `data/SOURCES.md` 逐条记录：来源、接口、查询参数、取数时间、字段含义。
- 同一数据集只取一次，复用不落重复请求。

### P2 建模求解（Gate：每问模型跑通 + 有检验）

- 每问独立脚本 `code/q1_*.py`、`code/q2_*.py`……从 `data/` 读数，结果图存 `figures/`（编号 fig1, fig2…），数值结果同时打印并写入 `results/`。
- 图表规范：managed Python 下先 `from daimon_runtime import setup_plot; setup_plot()`，统一字体与配色；`fig.savefig("figures/figN_描述.png", bbox_inches="tight")`。
- 每问必须包含**模型检验**（残差/拟合优度/收敛性/对比基线）和**灵敏度或稳健性分析**（至少一个关键参数扰动）。这是评奖硬指标，不可省略。
- 模型跑通一个就立刻进入 P3 写对应小节，写作与求解交错推进，不等全部跑完。
- 代码风格：脚本顶部注释写明输入/输出/运行方式；随机过程固定 seed；单次运行 < 5 分钟。
- 绘图统一从脚手架的引导模块开始：`from plot_setup import plt, savefig`（`code/plot_setup.py` 已封装 managed runtime 的 sys.path 插入与 CJK 字体，禁止每个脚本手写 sys.path 模板代码）。
- 超过 30 秒的仿真（Monte Carlo 等）每若干次迭代打印一次进度（如 `if m % 100 == 0: print(...)`），避免调用方误判超时；默认把长循环次数写成常量，便于先小规模试跑再放大。

### P3 论文写作（Gate：结构完整 + 摘要定稿）

- 按 `references/paper-structure.md` 与 `assets/paper-template.md` 写作，产出 `paper/paper.md`。
- 写作顺序：先写模型建立与求解各节 → 检验与灵敏度 → 优缺点 → **最后打磨摘要**。摘要是评奖第一权重：问题→方法→结果（具体数字）→结论，一段式，200–400 字（美赛 1 页内）。
- 公式用 LaTeX；符号表统一符号，全文一致；图表有编号有题注，正文必引用（"如图 1 所示"）。
- 标题不写手工编号（模板 Heading 样式自动编号）；图片尺寸可用 `![图 1](path){w=10cm}` 标注，无标注按宽高比自动分档。
- 语言：国赛中文（术语保留英文），美赛英文。

### P4 校验交付（Gate：precheck 通过 + 成稿 docx）

1. **一键出片**：运行 `python scripts/publish.py paper/paper.md`——自动完成 precheck → 生成规范 docx → Word 可用时导出 PDF → 清理临时文件，任一步失败即停。需要分步时：先 `precheck.py` 修全部 ERROR（WARN 逐条确认），再 `build_docx.py`。
2. 人工复核清单：摘要含具体结果数字；每问都有检验与灵敏度；假设合理且被引用；参考文献格式统一；无 TODO/占位符残留。
3. 排版规范见 `references/format-spec.md`（基于 `assets/cumcm-template.docx` 官方模板）：公式为 Word 原生 OMML（可编辑，失败回退图片），三线表顶/底线 1.5 磅、栏目线 0.5 磅。
4. 无 Office 环境需 HTML 出片时：用 markdown-it + **本地** MathJax 生成 HTML，再经系统 Chrome/Edge 无头模式 `--print-to-pdf`（**禁止依赖 CDN**——jsdelivr 等公共 CDN 可能超时）。
5. 交付清单：`paper.docx`（主交付，可编辑）、`paper_word.pdf`（按需）、`code/`（支撑材料）、`data/SOURCES.md`（数据溯源）、`figures/`。

## 效率规则

- **先计划后动手**：P0 的《问题分析》是唯一计划来源，模型选定后不随意更换；换模型要回写问题分析。
- **并行能并行的**：数据下载、文献调研、模板填充可并行；模型求解按问独立、互不阻塞。
- **不重复造轮子**：取数脚本、绘图框架跨问复用；每问脚本只写差异部分。
- **时间盒**：默认预算内优先级 = 摘要质量 > 模型检验/灵敏度 > 图表规范 > 模型花哨度。宁用简单模型+完整检验，不用复杂模型+无检验。

## 反模式（禁止）

- ❌ 编造数据、编造文献、编造数据库返回值
- ❌ 论文出现"模型A/B/C都试了"，但正文只有结果没有检验与对比理由
- ❌ 只有模型没有灵敏度分析；只有图没有正文引用
- ❌ 摘要从正文复制句子凑数，无具体数值结果
- ❌ 为炫技堆模型：每问一个主模型 + 至多一个对比基线

## 资源索引

- `references/problem-types.md` — 题型识别与模型选择路由表（评价/预测/优化/机理/数据分析）
- `references/paper-structure.md` — 国赛/美赛论文结构、摘要与图表规范、评审关注点
- `references/format-spec.md` — 国赛排版规范（字体字号、页边距、三线表、题注、摘要页）
- `references/data-sources.md` — 数据库与公开数据源路由（Wind/Gildata/iFinD/World Bank/IMF/Yahoo/SEC 及取数口径）
- `scripts/scaffold.py` — 初始化比赛项目目录：论文模板 + data/SOURCES.md + code/plot_setup.py（绘图引导）
- `scripts/precheck.py` — 提交前自动检查（章节完整性、图表编号引用、图片存在性、摘要、占位符）
- `scripts/build_docx.py` — paper.md → 国赛规范 docx（基于官方模板；公式 Word 原生 OMML，失败回退 mathtext 图片；三线表直接画边框；图片尺寸标注/自动分档）
- `scripts/publish.py` — 一键出片：precheck → docx → Word COM 导出 PDF → 清理临时文件
- `assets/cumcm-template.docx` — 官方国赛论文标准模板（页面/样式/页脚页码/三线表的唯一格式来源）
- `assets/paper-template.md` — 论文 Markdown 模板（无手工编号标题，zh/en 双版内嵌）
