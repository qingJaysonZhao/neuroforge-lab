# -*- coding: utf-8 -*-
# 原始投影代数·Run1（2026-11-24）：洛书解空间 / 卦变换群 / 进制残差
import itertools, math
OUT = open('/root/.openclaw/workspace/research/oracle_verification/tools/primitive_algebra_run1.txt', 'w')
def log(s): print(s); OUT.write(s + '\n')

# === 1. 洛书：1..9填入3×3，八线和=15 的解与对称轨道 ===
lines = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
sols = []
for p in itertools.permutations(range(1,10)):
    if all(p[a]+p[b]+p[c]==15 for a,b,c in lines):
        sols.append(p)
log(f"[洛书] 八线和=15的解数: {len(sols)}")
def rot(p):  # 顺时针90°
    return (p[6],p[3],p[0], p[7],p[4],p[1], p[8],p[5],p[2])
def mirror(p): return (p[2],p[1],p[0], p[5],p[4],p[3], p[8],p[7],p[6])
base = sols[0]
orbit = {base, mirror(base)}
cur = base
for _ in range(3):
    cur = rot(cur); orbit.add(cur); orbit.add(mirror(cur))
log(f"[洛书] 首解在D4（旋转+镜像）下的轨道大小: {len(orbit)}  →  {'唯一解（八轨一）' if len(sols)==8 and len(orbit)==8 else '需查'}")

# === 2. 卦变换群：错(补)/综(逆)/互(核) 在64卦上生成的群 ===
def C(x): return x ^ 63
def R(x): return sum(((x>>i)&1)<<(5-i) for i in range(6))
F = [1,2,3,2,3,4]
def M(x): return sum(((x>>F[i])&1)<<i for i in range(6))
gens = [tuple(C(x) for x in range(64)), tuple(R(x) for x in range(64)), tuple(M(x) for x in range(64))]
def comp(g, h): return tuple(g[h[x]] for x in range(64))
ident = tuple(range(64))
G = {ident}; frontier = [ident]
while frontier:
    g = frontier.pop()
    for gen in gens:
        for ng in (comp(g, gen), comp(gen, g)):
            if ng not in G:
                G.add(ng); frontier.append(ng)
log(f"[卦群] 错/综/互生成的群阶: {len(G)}")
seen = set(); orbits = []
for x in range(64):
    if x in seen: continue
    orb = {g[x] for g in G}; seen |= orb; orbits.append(len(orb))
log(f"[卦群] 64卦轨道分解: {sorted(orbits)}  共{len(orbits)}轨")
log("[卦群] 生成元阶: 错=2 综=2 (由定义)；互阶见下方幂次:")
m = ident
for k in range(1,9):
    m = comp(m, gens[2])
    if m == ident:
        log(f"[卦群] 互卦算子阶 = {k}"); break

# === 3. 进制残差：2..72 约数密度 vs 文明实证进制 ===
def divisors(n): return sum(1 for d in range(1,n+1) if n%d==0)
def maxpf(n):
    m = 0
    for d in range(2, n+1):
        while n % d == 0: m = max(m, d); n //= d
    return m
rows = [(n, divisors(n), maxpf(n)) for n in range(2, 73)]
top = sorted(rows, key=lambda t: (-t[1], t[2]))[:10]
log(f"[进制] 2..72约数密度前十(基数,约数个数,最大素因子): {top}")
for att in (10, 12, 20, 60):
    r = rows[att-2]
    better = [t for t in rows if t[1] > r[1] and t[0] < att]
    log(f"[进制] 实证 {att}: 约数{r[1]}个, 光滑({r[2]})  比它小且约数更多的: {better if better else '无——局部最优'}")
log("[进制] 注：10进制约数仅4个，12有6个——纯数学12更优，10胜在手指信道。极值原理必须含信道代价项。")
OUT.close()
