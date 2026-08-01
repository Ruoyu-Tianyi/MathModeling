# 文献调研流（N6）

目标：参考文献**有据可查、格式规范**。铁律沿用数据纪律：**绝不编造文献**——每条引用必须来自 scholar 插件的实际检索结果或手头真实文献。

## 流程

```
检索（scholar 插件）→ 筛选 → 提取元数据 → gb7714.py 格式化 → 写入论文参考文献节
```

### 1. 检索

用 scholar 插件按方法关键词检索（中英双语各试一轮）：

- 例：`bearing-only localization`、`无源定位 圆周角`、`TOPSIS entropy weight`
- 每问方法至少检索 1–2 篇奠基/经典文献；优先高被引、IEEE/SIAM/运筹学主流刊物

### 2. 筛选

- 优先：经典教材、综述、方法原始论文
- 避免：来源不明的博客、无法核实的预印本、与模型实际无关的"凑数"文献
- 数量：3–8 条为宜，每条都必须在正文被引用（`[1]`）

### 3. 格式化

用 `scripts/gb7714.py` 从检索到的元数据生成 GB/T 7714 格式：

```bash
# 期刊
python scripts/gb7714.py --type journal --authors "Torrieri D J" \
  --title "Statistical theory of passive location systems" \
  --venue "IEEE Transactions on Aerospace and Electronic Systems" \
  --year 1984 --volume "AES-20" --issue 2 --pages "183-198"

# 书籍
python scripts/gb7714.py --type book --authors "姜启源, 谢金星, 叶俊" \
  --title "数学模型" --place "北京" --publisher "高等教育出版社" --year 2018

# 批量：把检索结果整理成 refs.json 后一次输出
python scripts/gb7714.py --json refs.json
```

支持类型：book[M]、journal[J]、conference[C]、web[EB/OL]、thesis[D]。

### 4. 写入论文

- 参考文献节按引用顺序编号 `[1] [2]…`，正文在引用处右上角标注
- 正文引用必须与列表一一对应（precheck 已检查"列了但未被引用"以外的情形，人工再核一遍）
