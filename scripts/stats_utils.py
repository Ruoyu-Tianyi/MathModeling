"""纯 numpy 统计/机器学习工具（无 scipy/sklearn 环境的自实现）

分布生存函数（Numerical Recipes 风格连分式/级数）：
  gammq(a,x)  正则化上不完全伽马 -> chi2_sf, t_sf, f_sf
  betai(a,b,x) 正则化不完全贝塔
统计检验：
  chi2_contingency(table) -> chi2, p, dof, expected
  cramers_v(chi2, n, r, c)
  mannwhitney(x, y) -> U, z, p（正态近似 + 连续性修正）
  rankdata(a)（平均秩，处理结）
  spearman(x, y) -> rho, p（t 近似）
  bh_fdr(pvals) -> 校后 p
机器学习：
  zscore(X), clr(X, zero_repl=half-min-positive)
  kmeans(X, k, seed, n_init) -> labels, inertia（k-means++ 初始化）
  silhouette_score(X, labels)
  ari(labels1, labels2)
  cart_gini(X, y, max_depth, min_leaf) -> 规则列表 + predict 函数
  f_ratios(X, y) -> 单变量类间/类内方差比（特征重要性旁证）
"""
import math

import numpy as np

EPS = 1e-300


# ---------------------------------------------------------------- 特殊函数
def gammq(a, x):
    """Regularized upper incomplete gamma Q(a,x) = P(a,x) 的补。"""
    if x < 0 or a <= 0:
        return float("nan")
    if x == 0:
        return 1.0
    if x < a + 1.0:  # 级数表示 P，再取补
        ap, s, d = a, 1.0 / a, 1.0 / a
        for _ in range(1000):
            ap += 1
            d *= x / ap
            s += d
            if abs(d) < abs(s) * 1e-14:
                break
        p = s * math.exp(-x + a * math.log(x) - math.lgamma(a))
        return max(0.0, 1.0 - p)
    # 连分式表示 Q
    tiny = 1e-300
    b, c, d = x + 1 - a, 1 / tiny, 1 / (x + 1 - a)
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return max(0.0, h * math.exp(-x + a * math.log(x) - math.lgamma(a)))


def betai(a, b, x):
    """Regularized incomplete beta I_x(a,b)（连分式）。"""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1 - x))
    front = math.exp(lbeta)

    def cf(a_, b_, x_):
        tiny = 1e-300
        qab, qap, qam = a_ + b_, a_ + 1, a_ - 1
        c, d = 1.0, 1.0 - qab * x_ / qap
        if abs(d) < tiny:
            d = tiny
        d = 1 / d
        h = d
        for m in range(1, 1000):
            m2 = 2 * m
            aa = m * (b_ - m) * x_ / ((qam + m2) * (a_ + m2))
            d = 1 + aa * d
            if abs(d) < tiny:
                d = tiny
            c = 1 + aa / c
            if abs(c) < tiny:
                c = tiny
            d = 1 / d
            h *= d * c
            aa = -(a_ + m) * (qab + m) * x_ / ((a_ + m2) * (qap + m2))
            d = 1 + aa * d
            if abs(d) < tiny:
                d = tiny
            c = 1 + aa / c
            if abs(c) < tiny:
                c = tiny
            d = 1 / d
            delta = d * c
            h *= delta
            if abs(delta - 1) < 1e-14:
                break
        return h

    if x < (a + 1) / (a + b + 2):
        return front * cf(a, b, x) / a
    return 1 - front * cf(b, a, 1 - x) / b


def chi2_sf(x, df):
    return gammq(df / 2.0, x / 2.0)


def t_sf(t, df):
    """双侧 |T| > |t| 的概率。"""
    x = df / (df + t * t)
    return betai(df / 2.0, 0.5, x)


def f_sf(f, d1, d2):
    x = (d1 * f) / (d1 * f + d2)
    return 1.0 - betai(d1 / 2.0, d2 / 2.0, x)


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


# ---------------------------------------------------------------- 检验
def chi2_contingency(table):
    obs = np.asarray(table, dtype=float)
    n = obs.sum()
    rs, cs = obs.sum(1, keepdims=True), obs.sum(0, keepdims=True)
    exp = rs @ cs / n
    mask = exp > 0
    chi2 = float(((obs - exp) ** 2 / np.where(mask, exp, 1))[mask].sum())
    dof = (obs.shape[0] - 1) * (obs.shape[1] - 1)
    return chi2, chi2_sf(chi2, dof), dof, exp


def cramers_v(chi2, n, r, c):
    return math.sqrt(chi2 / (n * max(1, min(r - 1, c - 1))))


def mannwhitney(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    n1, n2 = len(x), len(y)
    r = rankdata(np.concatenate([x, y]))
    r1 = r[:n1].sum()
    u1 = r1 - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    # 结的修正
    _, counts = np.unique(np.concatenate([x, y]), return_counts=True)
    tie = (counts ** 3 - counts).sum()
    sigma = math.sqrt(n1 * n2 / 12 * (n1 + n2 + 1 - tie / ((n1 + n2) * (n1 + n2 - 1))))
    z = (u1 - mu - 0.5 * np.sign(u1 - mu)) / sigma
    return u1, z, 2 * norm_sf(abs(z))


def rankdata(a):
    a = np.asarray(a, float)
    order = a.argsort(kind="mergesort")
    ranks = np.empty(len(a))
    sa = a[order]
    i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and sa[j + 1] == sa[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    n = len(x)
    rx, ry = rankdata(x), rankdata(y)
    rx, ry = rx - rx.mean(), ry - ry.mean()
    denom = math.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    rho = float((rx * ry).sum() / denom) if denom > 0 else 0.0
    if abs(rho) >= 1:
        return rho, 0.0
    t = rho * math.sqrt((n - 2) / (1 - rho ** 2))
    return rho, t_sf(t, n - 2)


def bh_fdr(pvals):
    p = np.asarray(pvals, float)
    n = len(p)
    order = p.argsort()
    ranked = p[order] * n / (np.arange(n) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(ranked, 1.0)
    return out


# ---------------------------------------------------------------- 变换与 ML
def zscore(X):
    X = np.asarray(X, float)
    sd = X.std(0)
    sd[sd == 0] = 1
    return (X - X.mean(0)) / sd


def clr(X):
    """Centered log-ratio；0 值替换为该列最小正值的一半。"""
    X = np.asarray(X, float).copy()
    for k in range(X.shape[1]):
        col = X[:, k]
        pos = col[col > 0]
        repl = pos.min() / 2 if len(pos) else 1e-3
        col[col <= 0] = repl
        X[:, k] = col
    lg = np.log(X)
    return lg - lg.mean(1, keepdims=True)


def kmeans(X, k, seed=0, n_init=10, max_iter=300):
    X = np.asarray(X, float)
    best = None
    for init in range(n_init):
        rng = np.random.default_rng(seed * 1000 + init)
        idx = [rng.integers(len(X))]
        for _ in range(k - 1):
            d2 = np.min(((X[:, None, :] - X[idx][None]) ** 2).sum(-1), 1)
            idx.append(rng.choice(len(X), p=d2 / d2.sum()))
        C = X[idx].copy()
        for _ in range(max_iter):
            lab = ((X[:, None, :] - C[None]) ** 2).sum(-1).argmin(1)
            Cn = np.array([X[lab == i].mean(0) if (lab == i).any() else C[i]
                           for i in range(k)])
            if np.allclose(Cn, C):
                break
            C = Cn
        inertia = float(((X - C[lab]) ** 2).sum())
        if best is None or inertia < best[2]:
            best = (lab, C, inertia)
    return best


def silhouette_score(X, labels):
    X = np.asarray(X, float)
    D = np.sqrt(((X[:, None, :] - X[None]) ** 2).sum(-1))
    s = np.zeros(len(X))
    for i in range(len(X)):
        same = (labels == labels[i])
        same[i] = False
        a = D[i, same].mean() if same.any() else 0.0
        b = min(D[i, labels == c].mean() for c in set(labels) if c != labels[i])
        s[i] = (b - a) / max(a, b) if max(a, b) > 0 else 0.0
    return float(s.mean())


def ari(a, b):
    a, b = np.asarray(a), np.asarray(b)
    n = len(a)

    def comb2(x):
        return x * (x - 1) / 2

    tab = np.zeros((a.max() + 1, b.max() + 1))
    for i in range(n):
        tab[a[i], b[i]] += 1
    sum_c = comb2(tab).sum()
    sa, sb = comb2(tab.sum(1)).sum(), comb2(tab.sum(0)).sum()
    total = comb2(n)
    expected = sa * sb / total
    maxi = (sa + sb) / 2
    return (sum_c - expected) / (maxi - expected) if maxi != expected else 1.0


def cart_gini(X, y, max_depth=3, min_leaf=3):
    """二分类 CART（gini），返回规则列表与预测函数。"""
    X, y = np.asarray(X, float), np.asarray(y)
    rules = []

    def gini(idx):
        if len(idx) == 0:
            return 0.0
        p = (y[idx] == y[0]).mean()
        # 二分类通用：两类比例
        classes, counts = np.unique(y[idx], return_counts=True)
        ps = counts / len(idx)
        return float(1 - (ps ** 2).sum())

    def split(idx, depth, path):
        maj = y[idx][0] if (y[idx] == y[0]).mean() >= 0.5 else [c for c in np.unique(y) if c != y[0]][0]
        counts = {c: int((y[idx] == c).sum()) for c in np.unique(y)}
        node = {"path": list(path), "n": len(idx), "counts": counts,
                "label": max(counts, key=counts.get)}
        if depth >= max_depth or len(idx) < 2 * min_leaf or len(counts) == 1:
            rules.append(node)
            return node["label"]
        best = None
        for k in range(X.shape[1]):
            vals = np.unique(X[idx, k])
            if len(vals) < 2:
                continue
            thr_cand = (vals[:-1] + vals[1:]) / 2
            for t in thr_cand:
                l, r = idx[X[idx, k] <= t], idx[X[idx, k] > t]
                if len(l) < min_leaf or len(r) < min_leaf:
                    continue
                g = len(l) / len(idx) * gini(l) + len(r) / len(idx) * gini(r)
                if best is None or g < best[0]:
                    best = (g, k, t)
        if best is None:
            rules.append(node)
            return node["label"]
        _, k, t = best
        l, r = idx[X[idx, k] <= t], idx[X[idx, k] > t]
        left = split(l, depth + 1, path + [(k, "<=", t)])
        right = split(r, depth + 1, path + [(k, ">", t)])
        return node["label"]

    split(np.arange(len(X)), 0, [])
    return rules


def f_ratios(X, y):
    """单变量类间/类内方差比（越大区分度越高）。"""
    X, y = np.asarray(X, float), np.asarray(y)
    out = []
    for k in range(X.shape[1]):
        grand = X[:, k].mean()
        between = sum(((y == c).sum()) * (X[y == c, k].mean() - grand) ** 2
                      for c in np.unique(y))
        within = sum(((X[y == c, k] - X[y == c, k].mean()) ** 2).sum()
                     for c in np.unique(y))
        out.append(between / within if within > 0 else np.inf)
    return np.array(out)
