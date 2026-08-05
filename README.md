# MathModeling Skill（V3.6）

**把赛题交给Agent → 输出可直接提交、可继续编辑的建模论文（Word）**（含模型推导、可运行代码、规范图表、摘要与参考文献）。适用于国赛（CUMCM）、美赛（MCM/ICM）及同类赛事，面向 所有支持 SKILL.md 规范的 AI Agent 运行。

## 功能特性

- **五阶段流水线，各设质量门禁**：审题立项 → 数据获取 → 建模求解 → 论文写作 → 校验交付
- **B/C 双赛道分流（V3）**：P0 判定清单逐问计分 + 用户确认后进入专属路径——B 型（机理/优化）走无噪声验证、多解性枚举、噪声地板等检验武器；C 型（数据驱动）走一键 EDA + 评价/预测/统计/优化决策树
- **题型→模型路由**：评价 / 预测 / 优化 / 机理 / 数据分析五大类，每问"主模型 + 对比基线"，拒绝模型堆砌
- **真实数据接入**：内置数据源路由表，金融/宏观数据自动路由到 Wind、Gildata、iFinD、World Bank、IMF、SEC、Yahoo Finance 等数据插件；取不到的数据走可复现仿真并在论文中声明，**严禁编造数据**
- **强制质量项**：每问必须含模型检验与灵敏度分析；摘要最后定稿且必须含具体数值结果
- **国赛排版规范内置**：字体字号、页边距、三线表、图表题注、摘要页格式封装为 `references/format-spec.md`，一键生成合规 Word
- **Word 优先交付**：`build_docx.py` 全离线将 paper.md 转为规范 docx（公式 mathtext 渲染嵌入、表格三线表、图片居中题注），可直接在 Word 中编辑微调；PDF 按需经本地 MathJax + Chrome 无头出片
- **自动化工具**：项目脚手架一键生成目录；提交前检查器自动拦截章节缺失、图表未引用、占位符残留等问题

## 目录结构

```
├── SKILL.md                      # 技能主入口（AI 加载此文件启动工作流）
├── references/
│   ├── problem-types.md          # 题型识别与模型选择路由表
│   ├── track-b-modeling.md       # B 赛道理工方法论（V3 新增）
│   ├── track-c-modeling.md       # C 赛道数据方法论（V3 新增）
│   ├── data-analysis-workflow.md # C 型赛题数据工作流 playbook
│   ├── deep-reasoning.md         # 深度推理协议（推导稿/六检查/红队）
│   ├── math-writing.md           # 数学写作与公式深度规范
│   ├── paper-structure.md        # 国赛/美赛论文结构、摘要写法、评审关注点
│   ├── format-spec.md            # 国赛排版规范
│   ├── data-sources.md           # 数据源路由与取数规范
│   └── literature.md             # 文献调研流（GB/T 7714）
├── scripts/
│   ├── scaffold.py               # 初始化比赛项目目录（含 plot_setup 绘图引导）
│   ├── eda.py                    # C 赛道一键数据探查报告（V3 新增）
│   ├── precheck.py               # 论文提交前自动检查（含查重自检）
│   ├── sensitivity.py            # 灵敏度分析自动化
│   ├── gb7714.py                 # GB/T 7714 参考文献格式化
│   ├── stats_utils.py            # 零 scipy 统计兜底库（p 值/聚类/CLR，scaffold 自动分发）
│   ├── build_docx.py             # paper.md → 国赛规范 Word
│   └── publish.py                # 一键出片（precheck → docx → PDF）
└── assets/
    ├── cumcm-template.docx       # 官方国赛论文标准模板
    └── paper-template.md         # 论文 Markdown 模板
```

## 安装

本技能兼容所有支持 SKILL.md 规范的 AI Agent 运行时（Kimi Work / Kimi Code / Claude Code 等），三种方式任选：

### 方式一：交给 Agent 安装（推荐）

克隆本仓库后，对你的 Agent 说：

> 把 math-modeling-contest 技能安装到我的技能目录

Agent 会自动识别当前运行时的技能目录并完成复制。

### 方式二：手动复制

将整个文件夹（或下载 Release 中的 `math-modeling-contest.skill` 解压）复制到任一技能目录：

| 运行时 | 技能目录 |
|---|---|
| Kimi Work（Windows） | `C:\Users\<用户名>\AppData\Roaming\kimi-desktop\daimon-share\daimon\skills\math-modeling-contest\` |
| Kimi Code / 通用 agents | `~/.config/agents/skills/math-modeling-contest/` 或 `~/.kimi/skills/math-modeling-contest/` |
| Claude Code | `~/.claude/skills/math-modeling-contest/` |
| 项目级（仅当前项目可用） | `<项目>/.agents/skills/math-modeling-contest/` |

### 方式三：Git 直接克隆到技能目录

```bash
git clone https://github.com/RuoYu-Tianyi/MathModeling.git <技能目录>/math-modeling-contest
```

### 依赖环境

- **必需**：Python ≥ 3.9，`pip install python-docx matplotlib latex2mathml lxml pillow numpy`
- **可选**：本机安装 Microsoft Word（用于公式 OMML 转换与一键导出 PDF；无 Word 时公式自动回退为图片渲染、PDF 步骤自动跳过）
- Wind / Gildata 等数据插件仅金融赛题需要，非必需

### 验证安装

对 Agent 说"用数模技能做这道题"，技能被触发即安装成功；或运行：

```bash
python math-modeling-contest/scripts/precheck.py --help
```

## 使用

安装后对 AI 说：

> 用数模技能做这道题 + [赛题文本/PDF]

工作流产出：

```
<项目名>/
├── problem/      # 赛题原文
├── data/         # 原始数据 + SOURCES.md（来源可溯）
├── code/         # q1_*.py, q2_*.py ... 每问独立可运行
├── figures/      # 规范图表
├── results/      # 数值结果
└── paper/paper.md → paper.docx (+ paper.pdf 按需)   # 可提交论文
```

脚本独立用法：

```bash
# 初始化比赛项目（美赛用 --lang en）
python scripts/scaffold.py --name my-contest --lang zh

# 提交前检查（0 error 才通过）
python scripts/precheck.py paper/paper.md --lang zh

# 生成国赛规范 Word
python scripts/build_docx.py paper/paper.md
```

## 设计原则

- 先计划后动手：P0 的《问题分析》是唯一计划来源
- 优先级：摘要质量 > 模型检验/灵敏度 > 图表规范 > 模型复杂度
- 数据铁律：不编造数据、不编造文献、不编造数据库返回值

## 更新日志

> 规则：同一轮迭代合并为一条；跨天或大版本才新增条目；倒序排列。细粒度历史见 git tag（v1.0.0 ~ v3.6.0）。

### V3.6（2026-08-05，贝叶斯与软聚类：C 赛道"深刻档"补全）

源自回测复盘 D 级观察——此前"贝叶斯个体化预测 / 混合模型聚类"只能写进论文"改进"节，现已落成 skill 原生能力：

- **贝叶斯不确定性量化**：`stats_utils.bayes_linreg()`（NIG 共轭闭式解，纯 numpy，弱先验下后验均值≈OLS）+ `bayes_predict()`（t 预测分布逐样本可信区间）；截距模型即"类均值预测的贝叶斯升级版"。合成数据 200 次重复平均覆盖率 0.942（名义 0.95）；玻璃数据留一实测：高钾 0.935、铅钡 0.923 达标
- **GMM 软聚类**：`gmm()` EM 实现（full/diag 双协方差模式，空簇重置 + 协方差正则化）+ `gmm_select()` BIC 选 k；输出逐样本后验归属概率，max 后验 <0.7 即"过渡样本"——"存疑"从定性词变定量结论
- **小样本协方差纪律**（实测教训）：n ≲ k·d²/2 时全协方差过参数化、BIC 选出病态 k；`cov_type="diag"` 为小样本默认——diag 模式下高钾 BIC 与轮廓系数同选 k=2，训练集类型分离 ARI=1.0
- **第三证据角色**：规则法与距离法冲突时（2022 C 题 A5：规则→铅钡 vs 质心→高钾），GMM 后验作独立量化裁决（A5 后验 1.000 支持规则判定，分歧源于质心法受风化漂移影响）
- **track-c-modeling.md 新增两节**：预测类"贝叶斯不确定性量化"（先验纪律/区间覆盖率检验写法）、聚类节"软聚类路线"（协方差纪律/BIC vs 轮廓系数并列报告/后验过度自信警示）

### V3.5（2026-08-05，C 题回测复盘加固）

源自 2022 C 题（古代玻璃）全流程回测的九项观察（O1~O9）复盘，分工具 / 方法论 / 质检三层修复：

- **A1 `stats_utils.py` 收编进 skill**：零 scipy 统计兜底库（chi2/t/F 分布生存函数与 p 值、KMeans、CLR 变换等 330 行，数值校验 chi2_sf(3.841,1)=0.05、KMeans ARI=1.0）；`scaffold.py` 自动分发到 `code/`，C 题环境无 scipy 不再手写兜底
- **A2 运行环境探针 + 降级映射表**：`track-c-modeling.md` 新增探针代码与降级映射（sklearn RF → 决策桩/质心、scipy.stats → stats_utils、缺失库逐一给出替代路线），建模前先探明环境
- **B precheck 三项误报修复**：薄小节判定改按字符量（<120 散文 chars，排除表格/图/公式行）；关键词只按分号/逗号切分（不再把空格当分隔符误报）；摘要上限 600→800 字符。回测论文 WARN 从 8 条降到 3 条（误报清零，保留真实提示）
- **B publish 错误透明化**：Word COM 出片失败时打印 stderr 首行 + 自动重试一次 + 自查提示，不再静默
- **C1 EDA 跑两次**：workflow 阶段 2 明确 raw 一次（摸清底数）+ clean/join 后一次（正式分析基准）
- **C2 小簇纪律**：聚类簇 n<5 不作正式亚类结论，只作提示
- **C3 画像图纪律**：只画关键成分（贡献度排序前几项），拒绝全成分蜘蛛网图

### V3.1（2026-08-05，xlsx 实战接入增强）

源自 2022 C 题（古代玻璃）回测前测的四项观察（多表关联 / 成分数据语义 / 复合编号 / 高缺失噪音）：

- **eda.py 多表单遍历**：xlsx 默认全 sheet 扫描，报告含多表单概览 + 表间共同列（疑似关联键，按表对两两求交）+ 无共同列时的编号前缀关联提示；`--sheet` 可单表分析
- **eda.py 成分数据模式**：`--blank-as-zero`（空白=未检出→0，低检出列改报"检出率"并抑制无意义的偏度/异常点噪音）+ `--row-sum-range LO,HI`（行和有效性检查，输出无效行清单）；编号/id 类列自动排除出图、统计与行和（修掉单数值列元信息表全表误报）
- **track-c-modeling.md 新增"成分数据纪律"**：闭合效应三档对策（声明 → CLR 变换 → 0 值替换规则）、CLR 空间聚类、比例反演建模范式
- **data-analysis-workflow.md 常见坑 +2**：多表单关联 join 时机、复合编号解析（`03部位1` → 主体 id + 部位标签）
- 实测：2022 C 题附件一次跑出 3 表 9 图 + 报告，无效行（行和 79.47 / 71.89 两条）精确命中

### V3（2026-08-04，B/C 双赛道分流工作流）

- **双路径路由（不开分支，单仓库维护）**：P0 赛道判定升级为"判定清单逐问计分 + 命中信号举证 + 用户确认"三步；判定后分流到专属方法论文件——B 型走 `references/track-b-modeling.md`，C 型走 `references/track-c-modeling.md` + `data-analysis-workflow.md`，混合型逐问分流
- **`track-b-modeling.md`（B 题实战沉淀）**：无噪声先验验证（机器精度证明实现正确）、多解性/镜像解枚举（解个数随约束数变化成表）、误差传播链与噪声地板（解析 + Monte Carlo 双证据）、迭代收敛曲线规范、退化检验当定理用、B 题灵敏度对象（物理参数/测量精度/构型/分布假设）
- **`track-c-modeling.md`（C 题方法论深化）**：评价/预测/统计推断/数据驱动优化四类决策树；熵权/TOPSIS/AHP 完整公式链；时序（ADF→ARIMA→残差白噪声）与回归（VIF 共线性、防数据泄漏）路线纪律；C 题灵敏度与检验清单；EDA 发现编号回引的论文写法
- **`scripts/eda.py` 一键数据探查**：读 Excel/CSV 自动产出分布网格图、相关系数热力图、时序面板（含滑动平均）、分组箱线图 + 缺失/统计三线表 + 自动发现列表（高缺失、共线对、偏态、异常点、重复行），合成数据自测全部命中预埋异常
- **流程图能力增强**：`plot_setup.flow()` 新增 `orientation="lr"` 横向布局（数据→参数→优化链条图）与 `phases=[...]` 阶段泳道标签，旧调用完全兼容

### V2.5（2026-08-01，自动化工具链补强）

- **N4 灵敏度分析自动化**：新增 `scripts/sensitivity.py`——`sweep()` ±5%~20% 参数扫描重解，`report()` 输出扰动曲线图 + 变化表（支持多指标），`sweep_multi()` + `tornado()` 多参数龙卷风图；评审硬指标零借口
- **N5 查重自检**：`precheck.py` 新增问题重述与 `problem/` 原文的 8-gram 重合度检测（>40% ERROR 拦截、>25% WARN），支持 `--problem` 指定目录；正/负向测试通过（原创 0 误报、抄题 100% 拦截）
- **N6 文献调研流**：新增 `references/literature.md`（scholar 检索 → 筛选 → 格式化流程）与 `scripts/gb7714.py`（GB/T 7714 五类文献格式化，单条/批量）

### V2（2026-08-01，深度推理能力升级）

- **推导稿制度（R2）**：P0 后强制纸面推导先行——`scaffold.py` 生成 `analysis/derivations.md` 骨架（定义与符号 → 引理 → 推导 → 可解形式），代码只许实现推导稿结论
- **六检查协议（R1）**：新增 `references/deep-reasoning.md`，模型建立后逐项过"量纲 / 退化检验 / 不变量 / 界与误差 / 良态性 / 反例压力测试"并留证据，写进 P2 门禁
- **分题型深化阶梯（R3）**：优化 / 统计 / 机理 / 评价 / 预测 / 几何六类题的"能用 → 扎实 → 深刻"升级路径，交卷前对照升级
- **模型红队门禁（R4）**：≥3 个对抗场景（退化输入、极端比例、边界样本、噪声注入、对抗构造），发现的问题写入论文检验节
- **严谨性检查（R5）**：`precheck.py` 新增假设数量与引用检查、符号表符号正文使用率检查
- SKILL.md：P0 新增推导稿步骤，P2 门禁升级为"跑通 + 检验 + 六检查 + 红队"

### V1.5（2026-07-27，对标一等奖范文 B030）

- **公式深度**：新增 `references/math-writing.md`（公式链条、双解法互验、解析讨论、段落三件套）；`precheck.py` 增加公式密度/过薄小节/附录无代码三项 WARN
- **附录代码**：`build_docx.py` 支持 ` ``` ` 代码块与 `--appendix-code DIR`（行号 + Consolas + 注释着色 + 浅灰底框）；`publish.py` 同名参数透传
- **图专业化**：`plot_setup` 新增 `paper_style()`（白底去顶/右边框、浅灰细网格、300 dpi）与几何示意图助手 `draw_circle`/`mark_point`/`mark_angle`
- **格式对齐范文**：摘要独占一页（自动分页）、页眉 = 论文题目 + 页码右对齐 + 分隔线、H1 居中且编号改空格无顿号、公式编号右 tab 贴页边、题注半角冒号、关键词空格分隔
- **可视化多样化**：规范"核心结果图 + 表双呈现"；B 题对照版新增收敛过程表
- B 题论文对照版验证：摘要独占页、范文式页眉、公式 (1)–(9) 编号体系、附录 7 个代码文件全部渲染通过（29 页）

### V1（2026-07-25/26）

- **交付管线**：Word（docx）优先交付；新增 `build_docx.py`（官方模板驱动）与 `publish.py` 一键出片（precheck → docx → Word 导 PDF → 清理临时文件）
- **排版与公式**：公式为 Word 原生 OMML（LaTeX → MathML → OMML，全离线，可编辑，失败回退图片）；官方模板 `assets/cumcm-template.docx` 为唯一格式来源；图片尺寸支持 `{w=..cm}` 标注 + 宽高比自动分档
- **表格**：三线表重写（顶/底线 1.5 磅、栏目线 0.5 磅、单元格直接画边框、首列居中内容列左对齐、垂直居中）
- **检查与脚手架**：`precheck.py` 增加图片存在性检查、摘要字数剥离 LaTeX 统计；`scaffold.py` 生成 `plot_setup.py` 绘图引导；论文模板标题去手工编号
- **C 型赛题能力**：P0 新增"赛道判定"（B 型机理 / C 型数据驱动分流）；新增 `references/data-analysis-workflow.md`（清洗 → EDA → 统计 → 建模决策 playbook）；`plot_setup.flow()` 代码绘制技术路线图
- **规范文档**：`format-spec.md`（模板实测参数）、`paper-structure.md`（章节对齐官方模板）、长仿真进度打印指引、出片禁用公共 CDN 规则
- 修复：标题自动编号重复、`daimon_runtime` 导入踩坑、MathJax CDN 超时、`\le`/`\tag` 兼容等实战问题

## 赞助支持

如果这个技能对你有帮助，欢迎请我喝杯咖啡 ☕
这会支持我持续维护和迭代它。

<p align="center">
  <img src="docs/sponsor-qr.jpg" width="220" alt="赞赏码">
</p>

## License

MIT
