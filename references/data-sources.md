# 数据源路由（数模赛题取数）

P1 阶段用。原则：**赛题附件 > 专业数据库插件 > 官方公开统计 > 可复现仿真数据**。禁止编造；所有取数落盘 `data/` 并在 `data/SOURCES.md` 记录来源、接口、参数、时间。

## 目录
- [路由表](#路由表)
- [金融数据库插件用法](#金融数据库插件)
- [公开统计与宏观库](#公开统计与宏观库)
- [仿真数据规范](#仿真数据兜底)
- [失败处理](#失败处理)

## 路由表

| 赛题数据需求 | 首选 | 备选 |
|---|---|---|
| A 股/港股/美股行情、财务、股东 | Wind（`wind` skill） | Gildata、iFinD |
| 股票/基金多条件筛选、选股 | Gildata（自然语言筛选强） | Wind |
| 基金/ETF 净值、持仓、业绩 | Wind `fund_data` | Gildata |
| 债券、转债、发债主体 | Wind `bond_data` | — |
| 公告、年报、财经新闻 | Wind `financial_docs` / Gildata | SEC EDGAR（美股） |
| 中国宏观（GDP/CPI/PMI/社融/利率） | Wind `economic_data` (EDB) | iFinD |
| 全球宏观、国别对比 | World Bank Open Data | IMF（WEO 预测） |
| 美股估值/基本面/分析师预期 | S&P (`sp_data`) | Yahoo Finance |
| 美股官方财报 XBRL | SEC EDGAR | S&P |
| 企业工商/司法/关系（中国） | 天眼查 | — |
| 学术论文/方法调研 | scholar 插件 / web 搜索 | — |
| 行业统计（能源/人口/气象等） | 国家统计局、世行、行业年鉴（web 搜索定位） | 赛题附件 |

跨市场/拿不准时：先调对应插件的 datasource describe（如 Gildata 的 `get_data_source_desc`、Wind 的 tool-contracts.md），确认覆盖再取数。

## 金融数据库插件

- **Wind**：通过 `wind` skill 路由，`node skills/wind-mcp-skill/scripts/cli.mjs call <server_type> <tool> '<json>'`。门禁：单标的/单调用、日期 `yyyyMMdd`、参数逐字来自 tool-contracts.md。报错按 `error.code` 指引修，不跨域改。
- **Gildata**：优先 MCP 工具 `get_data_source_desc` / `call_data_source`（datasource 固定 `gildata`）；备选 `python3 scripts/gildata_tool.py`。自然语言 query 强，适合多条件筛选。
- **iFinD**：同花顺数据，覆盖 A 股/港美股基本面与行情；按 `ifind` skill 指引。
- **Yahoo Finance**：轻量美股行情/指标，仅在前三者不可用时用。
- **World Bank / IMF**：按各自 skill 指引取国别长序列与预测。

引用口径：论文数据表脚注写"数据来源：Wind，截至 YYYY-MM-DD"（用工具实际返回的口径，不杜撰）。

## 公开统计与宏观库

- 中国：国家统计局 (stats.gov.cn)、央行、行业主管部门公报——用 web 搜索定位具体表。
- 国际：World Bank indicators、IMF WEO、UN Comtrade、Our World in Data。
- 下载后统一转 CSV 存 `data/`，列名英文化，单位写入 SOURCES.md。

## 仿真数据（兜底）

数据库与公开渠道都拿不到时的合法方案，但必须满足：

1. 由明确机制生成（分布/随机过程/规则），代码存 `code/gen_data_*.py`，固定 seed，可复现。
2. 参数取值有依据（文献/常识量级），在论文假设中声明"数据为仿真生成，参数设定依据……"。
3. `data/SOURCES.md` 标注"SIMULATED"。

## 失败处理

- 插件报错：读错误码与提示，在错误域内修正（参数错改参数，网络错稍后重试一次）；不跨域乱试。
- 连续两次失败：换路由表中的备选源；再失败则转仿真数据并在论文中声明。
- 绝不把 web 搜索结果当作数据库返回值；论文中区分标注。
