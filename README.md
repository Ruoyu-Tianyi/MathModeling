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

> 倒序排列，最新版本在最上。

### V1.3.0（2026-07-26）

- 新增 `scripts/publish.py` 一键出片：precheck → docx → Word COM 导 PDF（无 Word 优雅跳过）→ 自动清理临时文件
- `scaffold.py` 现在生成 `code/plot_setup.py` 绘图引导模块（封装 managed runtime sys.path 与 CJK 字体），消除每个脚本手写样板代码的踩坑点
- `precheck.py` 增强：新增 md 引用图片的存在性检查；摘要字数统计先剥离 LaTeX 标记（修复误报）
- `assets/paper-template.md` 标题去手工编号（模板 Heading 样式自动编号，从源头消除编号重复）
- SKILL.md 增补：长仿真进度打印指引、图片尺寸标注语法、publish 工作流

### V1.2.1（2026-07-26）

- 图片尺寸灵活化：`![图 1](path.png){w=10cm}` 手动标注优先；无标注按宽高比自动分档（宽扁 ≥1.8:1 → 13.5 cm、方正 ≤1.2:1 → 10 cm、其余 → 12 cm），版面更紧凑（B 题论文 10 页 → 9 页）

### V1.2（2026-07-26）

- **公式升级为 Word 原生 OMML**：LaTeX → MathML（latex2mathml）→ OMML（Office 自带 MML2OMML.XSL），全部离线；公式在 Word 中可编辑（支持 LaTeX 输入法修改），转换失败自动回退 mathtext 图片。B 题论文 78/78 全部原生转换
- **三线表重写**（对标优秀作品）：顶线/底线 1.5 磅、栏目线 0.5 磅，单元格直接画边框（弃用 tblLook 样式引用）；首列居中、内容列左对齐，列宽按角色分配，垂直居中 + 0.2 cm 边距
- 修复标题自动编号与手工编号重复问题（模板 Heading 样式自带编号，builder 现自动剥离手工前缀）；行内 `code` 渲染为 Consolas

### V1.1（2026-07-26）

- 引入官方国赛论文模板 `assets/cumcm-template.docx`（用户提供），作为排版唯一格式来源
- `build_docx.py` 重写：直接在官方模板上生成论文，Heading 1/2/3、Normal、图表标题、三线表样式、页脚页码全部继承模板（此前为手写格式参数）
- `format-spec.md` 更新为模板实测参数（页边距左右 2.70 cm 等）；`paper-structure.md` 章节顺序对齐官方模板

### V1.0（2026-07-25）

- 交付物由 PDF 改为 **Word（docx）优先**，便于赛后编辑微调；PDF 保留为按需选项
- 新增 `references/format-spec.md`：国赛字体字号、页边距、三线表、题注、摘要页排版规范
- 新增 `scripts/build_docx.py`：离线 docx 生成（matplotlib mathtext 渲染公式嵌入、三线表、图表题注居中），经 2022 年 B 题实战验证
- 修复实战暴露的工具链问题：PDF/HTML 出片禁止使用公共 CDN（MathJax 必须本地化）

## License

MIT
