# MatgModeling Skill（V1）

**把赛题交给Agent → 输出可直接提交、可继续编辑的建模论文（Word）**（含模型推导、可运行代码、规范图表、摘要与参考文献）。适用于国赛（CUMCM）、美赛（MCM/ICM）及同类赛事，面向 所有支持 SKILL.md 规范的 AI Agent 运行。

## 功能特性

- **五阶段流水线，各设质量门禁**：审题立项 → 数据获取 → 建模求解 → 论文写作 → 校验交付
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
│   ├── paper-structure.md        # 国赛/美赛论文结构、摘要写法、评审关注点
│   ├── format-spec.md            # 国赛排版规范（V1 新增）
│   └── data-sources.md           # 数据源路由与取数规范
├── scripts/
│   ├── scaffold.py               # 初始化比赛项目目录
│   ├── precheck.py               # 论文提交前自动检查
│   └── build_docx.py             # paper.md → 国赛规范 Word（V1 新增）
└── assets/
    └── paper-template.md         # 论文 Markdown 模板
```

## 安装

1、将整个文件夹复制到技能目录，或者直接下载 Release 中的 `math-modeling-contest.skill`（zip 格式）解压到上述目录。

2、或者直接交给你的Agent安装

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

> 规则：同一轮迭代合并为一条；跨天或大版本才新增条目；倒序排列。细粒度历史见 git tag（v1.0.0 ~ v1.4.0）。

### V1.4（2026-07-26）

- **C 型（数据驱动）赛题能力**：P0 新增"赛道判定"步骤——B 型（机理/优化）与 C 型（数据驱动）分流执行不同工作流；新增 `references/data-analysis-workflow.md` playbook（清洗 checklist → EDA 四图 → 统计检验选择 → 建模决策，含数据泄漏红线、常见坑、论文映射）
- **流程图工具**：`plot_setup.flow(layers, edges, ...)` 代码绘制技术路线图（分层自动布局、全离线、与论文图风格统一），问题分析节直接可用
- C 型工具链端到端验证：scaffold → 合成数据 → EDA → 流程图全部通过

### V1（2026-07-25/26）

- **交付管线**：Word（docx）优先交付；新增 `build_docx.py`（官方模板驱动）与 `publish.py` 一键出片（precheck → docx → Word 导 PDF → 清理临时文件）
- **排版与公式**：公式为 Word 原生 OMML（LaTeX → MathML → OMML，全离线，可编辑，失败回退图片）；官方模板 `assets/cumcm-template.docx` 为唯一格式来源；图片尺寸支持 `{w=..cm}` 标注 + 宽高比自动分档
- **表格**：三线表重写（顶/底线 1.5 磅、栏目线 0.5 磅、单元格直接画边框、首列居中内容列左对齐、垂直居中）
- **检查与脚手架**：`precheck.py` 增加图片存在性检查、摘要字数剥离 LaTeX 统计；`scaffold.py` 生成 `plot_setup.py` 绘图引导；论文模板标题去手工编号
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
