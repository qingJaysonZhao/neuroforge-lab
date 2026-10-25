"""
v1.30 COVERAGE-DIVERSITY PROBE -- attack the drift-world cascade by pre-spanning the neighborhood.

PREREG: poc/preregister/v130_coverage_diversity.yaml (committed 9fb94d8 BEFORE any result).

WHAT v128/v129 ESTABLISHED (第一档 measured)
    v128: paid-window gamma = 0.557 at drift 0.01 -- ABOVE the 0.4333 absolute floor -- and
          ER_paid = +0.342 POSITIVE, yet survival = 0.00. The mean economics PASS; agent dies.
          Trace: healthy ~350 steps (budget pinned 60), then 25 consecutive zero-success actions
          crash budget 52->19.7. Death is a CASCADE during a "no working coupler exists" window.
    v129: reprieve (more trials before purge) does NOT help -> purge rule is not the lever.
    ORACLE (perfect selection + reactive mint) survives only 0.35 -> selection is not the wall.
    => the missing piece is COVERAGE: the library fills with redundant copies of the current
       winner (认知2 big-not-deep) and has nothing for the drifted pattern.

THE FIX UNDER TEST -- Coverage-Directed Minting (CDM)
    When a combine-mint fires, with prob DIVERSITY_P steer it toward UNDER-COVERED channels
    (endogenous: library masks + sensed only, NEVER the true pattern, NEVER W) instead of always
    duplicating the sensed-overlap winner. DIVERSITY_P = 0 reproduces v129 PREDGUS EXACTLY
    (short-circuit: the rng is not consumed, so the control is bit-identical -- regression guard).

    Ladder {0.0 (control), 0.5, 1.0}. If survival rises monotonically or rises-then-saturates, it
    is a mechanism. A single-rung spike with no shape is tuning -> reported as null.

NEW DIAGNOSTIC INSTRUMENTS (frozen; read the true pattern ONLY to score, never feed back)
    D1 window_failure_mode : at each PAID step where the chosen op FAILS, classify
         coverage_fail  = NO op in the library (dormant or not) couples the TRUE pattern
         selection_fail = >=1 op couples it but the chosen one did not
       This is the pre-registered DISCRIMINATOR between "attack coverage" and "attack selection".
    D2 distinct_mask_ratio : distinct masks / |library|, mean over paid steps (diversity provenance)
    D3 neighbor_cover_frac : mean fraction of {current true pattern + its 16 one-drift neighbors}
       for which the library holds a coupler (proactive-coverage provenance). Sampled every 25
       steps, drift>0 arms only (bounds cost).
    D4 cascade_len : consecutive-zero-success run lengths in the paid window (max + distribution)

NOTHING HERE CHANGES A v1.17 CONSTANT. DECAY, GAIN, ACT_COST, B0, BUDGET_MAX, CONC_*, MAX_OPS,
VAR_P, SENSE_P, ACUTE_PUNISH, COMBINE_P, K_PRED, W_MAX_CAP all untouched. VAR_P (mint RATE) and
COMBINE_P (combine FRACTION) are NOT raised -- only the DIRECTION of mints that already happen
changes. This is the Stage3 §17.3 prescription: attack coverage, not by raising mutation prob.

HARD JUDGE (unchanged): full rent (state-grace THRESH=0.0), drift 0.01: survival > 0 AND
paid-window gamma > 0.4333. To BEAT the reactive-oracle ceiling: survival > 0.35.
"""
import json
import os
import random
import statistics
import sys

# ---------------- constants HELD IDENTICAL to v1.17 / v129 ---------------------------------
DECAY = 1.0
GAIN = 3.0
ACT_COST = 0.3
B0 = 25.0
BUDGET_MAX = 60.0
HORIZON = 4000

CONC_INIT = 0.6
CONC_UP = 1.0
CONC_DECAY = 0.997
CONC_MIN = 0.3
MAX_OPS = 40

N_BASE_OPS = 6
VAR_P = 0.20
SENSE_P = 0.30
ACUTE_PUNISH = 0.6

WORLDS = {"SMALL": 8, "OPEN": 64}

# ---------------- swept / held factors ---------------------------------------------------
OP_WEIGHT = 2
W_MAX_CAP = 6
COMBINE_P = 0.20

K_PRED = 6
EMA_A = 0.2
EMA_INIT = 0.5

BASE_GRACE = 200
PROBE_EVERY = 50
BLOCK = 500
D3_EVERY = 25          # neighbor-cover sampling cadence (cost bound)

DIVERSITY_LADDER = [0.0, 0.5, 1.0]     # 0.0 == exact PREDGUS control
CLEAR_LADDER = [1]                     # v129 showed clear_n=1 is best; held
DORM_LADDER = [3]                      # base honest config from v124/v129
COMBINE_MODES = ["PREDGUS", "ORACLE"]
DRIFT_LADDER = [0.0, 0.01, 0.02]
FORGET_LADDER = [400]
PARTIAL_LADDER = [0.5]
THRESH_LADDER = [0.0]                  # state-grace OFF -- FULL RENT per hard judge

BREAK_EVEN = 1.3 / 3.0                 # 0.4333
ORACLE_CEILING = 0.35                  # v128 measured, drift 0.01 reference


def pc(x):
    return bin(x).count("1")


class Op:
    __slots__ = ("mask", "conc", "fails", "dormant", "ov_ema", "dorm_since")

    def __init__(self, mask, conc=CONC_INIT):
        self.mask = mask
        self.conc = conc
        self.fails = 0
        self.dormant = False
        self.ov_ema = EMA_INIT
        self.dorm_since = None


def channels(x, n_ch):
    return [b for b in range(n_ch) if (x >> b) & 1]


def random_pair(rng, n_ch):
    a, b = rng.sample(range(n_ch), OP_WEIGHT)
    return (1 << a) | (1 << b)


def initial_pattern(rng, n_ch, w):
    m = 0
    for c in rng.sample(range(n_ch), w):
        m |= 1 << c
    return m


def step_env(pattern, drift, rng, n_ch):
    if drift and rng.random() < drift:
        active = channels(pattern, n_ch)
        inactive = [b for b in range(n_ch) if not ((pattern >> b) & 1)]
        if active and inactive:
            pattern = (pattern & ~(1 << rng.choice(active))) | (1 << rng.choice(inactive))
    return pattern


def sense(pattern, rng, n_ch):
    if rng.random() < SENSE_P:
        active = channels(pattern, n_ch)
        inactive = [b for b in range(n_ch) if not ((pattern >> b) & 1)]
        if active and inactive:
            pattern = (pattern & ~(1 << rng.choice(active))) | (1 << rng.choice(inactive))
    return pattern


def couples(mask, p, w):
    """UNCHANGED. The task stays binary."""
    if mask == 0:
        return False
    if (mask & p) != mask:
        return False
    return pc(mask) >= w - 1


def overlap(mask, p):
    k = pc(mask)
    return (pc(mask & p) / k) if k else 0.0


def score(mask, ref):
    k = pc(mask)
    return ((pc(mask & ref) / k) if k else 0.0) + 1e-3 * k


def local_variation(ops, rng, n_ch):
    parent = rng.choice(ops)
    bits = channels(parent.mask, n_ch)
    keep = rng.choice(bits)
    others = [b for b in range(n_ch) if b != keep]
    return Op((1 << keep) | (1 << rng.choice(others)))


def _best_union(cand, ref):
    best, bs = None, -1.0
    for i in range(len(cand)):
        for j in range(i + 1, len(cand)):
            u = cand[i].mask | cand[j].mask
            s = score(u, ref)
            if s > bs:
                bs, best = s, u
    if best is None:
        best = cand[0].mask | cand[1].mask
    return best


def coverage_directed_mint(ops, rng, n_ch, sensed):
    """CDM -- ENDOGENOUS. Reads ONLY ops masks + sensed. NEVER the true pattern, NEVER W.
    (K-HUMAN-DOOR: this function's signature structurally cannot see pattern/w.)"""
    pool = sorted(ops, key=lambda o: score(o.mask, sensed), reverse=True)[:K_PRED]
    if len(pool) < 2:
        return None
    cov = [0] * n_ch
    for o in ops:
        if not o.dormant:
            for b in channels(o.mask, n_ch):
                cov[b] += 1
    srt = sorted(cov)
    med = srt[len(srt) // 2]
    U = [c for c in range(n_ch) if cov[c] < med]
    if not U:
        half = max(1, n_ch // 2)
        U = sorted(range(n_ch), key=lambda c: cov[c])[:half]
    umask = 0
    for c in U:
        umask |= 1 << c
    best, bestkey = None, None
    for i in range(len(pool)):
        for j in range(i + 1, len(pool)):
            u = pool[i].mask | pool[j].mask
            if pc(u) > W_MAX_CAP:
                continue
            key = (pc(u & umask), pc(u))
            if bestkey is None or key > bestkey:
                bestkey, best = key, u
    return best


def mint_op(ops, rng, n_ch, mode, w, pattern, sensed, diversity_p):
    do_combine = (mode != "OFF") and len(ops) >= 2 and rng.random() < COMBINE_P
    if not do_combine:
        return local_variation(ops, rng, n_ch)

    nm = None
    if mode == "RANDOM":
        a, b = rng.sample(ops, 2)
        nm = a.mask | b.mask
    elif mode == "PREDGUS":
        # diversity_p == 0.0 short-circuits WITHOUT consuming rng -> bit-identical to v129 control
        if diversity_p > 0.0 and rng.random() < diversity_p:
            nm = coverage_directed_mint(ops, rng, n_ch, sensed)
        if nm is None:
            cand = sorted(ops, key=lambda o: score(o.mask, sensed), reverse=True)[:K_PRED]
            nm = _best_union(cand, sensed)
    elif mode == "ORACLE":
        act = channels(pattern, n_ch)
        k = min(w - 1, len(act))
        nm = 0
        for b in rng.sample(act, k):
            nm |= 1 << b

    if nm is None or nm == 0 or pc(nm) > W_MAX_CAP:
        return local_variation(ops, rng, n_ch)
    return Op(nm)


def _neighborhood(pattern, n_ch):
    """current pattern + all one-drift neighbors (swap one active channel for one inactive)."""
    act = channels(pattern, n_ch)
    inact = [b for b in range(n_ch) if not ((pattern >> b) & 1)]
    pats = [pattern]
    for a in act:
        base = pattern & ~(1 << a)
        for i in inact:
            pats.append(base | (1 << i))
    return pats


def run(world, drift, seed, mode, world_w, partial_max, dorm_n, clear_n,
        diversity_p, forget_after):
    n_ch = WORLDS[world]
    rng = random.Random(seed * 1000 + int(drift * 10000) + n_ch)
    pattern = initial_pattern(rng, n_ch, min(world_w, n_ch))

    ops = [Op(random_pair(rng, n_ch)) for _ in range(N_BASE_OPS)]
    seen, uniq = set(), []
    for o in ops:
        if o.mask not in seen:
            seen.add(o.mask)
            uniq.append(o)
    ops = uniq

    budget = B0
    alive = True
    steps = 0
    l_peak = 0

    all_steps = all_idle = all_act = all_succ = 0
    pd_steps = pd_idle = pd_act = pd_succ = 0
    full_paid = 0
    rescued = cleared = forgotten = 0
    # --- D1 window failure mode (paid steps where chosen op FAILED) ---
    d1_covfail = d1_selfail = d1_failsteps = 0
    # --- D2 distinct-mask ratio (paid steps) ---
    d2_sum = d2_n = 0
    # --- D3 neighbor coverage (sampled, drift>0 only) ---
    d3_sum = d3_n = 0
    # --- D4 cascade run lengths (paid window) ---
    cur_zero = 0
    d4_max = 0
    d4_lens = []
    blk_act = [0] * (HORIZON // BLOCK)
    blk_suc = [0] * (HORIZON // BLOCK)
    death = None

    for t in range(HORIZON):
        steps = t + 1
        pattern = step_env(pattern, drift, rng, n_ch)
        sensed = sense(pattern, rng, n_ch)
        probe_now = bool(dorm_n) and (t % PROBE_EVERY == 0)

        pool = [o for o in ops if (not o.dormant) or probe_now]
        triggered = [o for o in pool if (o.mask & sensed)]

        chosen = None
        if triggered:
            tot = sum(o.conc for o in triggered)
            if tot > 0:
                x = rng.random() * tot
                acc = 0.0
                for o in triggered:
                    acc += o.conc
                    if acc >= x:
                        chosen = o
                        break
                if chosen is None:
                    chosen = triggered[-1]
            else:
                chosen = rng.choice(triggered)
            if mode == "ORACLE":
                best = None
                for o in triggered:
                    if couples(o.mask, pattern, world_w):
                        if best is None or pc(o.mask) > pc(best.mask):
                            best = o
                if best is not None:
                    chosen = best

        ok = False
        if chosen is not None:
            ok = couples(chosen.mask, pattern, world_w)
            chosen.ov_ema = (1.0 - EMA_A) * chosen.ov_ema + EMA_A * overlap(chosen.mask, sensed)
            if ok:
                budget += GAIN
                chosen.conc += CONC_UP
                chosen.fails = 0
                chosen.dormant = False
                chosen.dorm_since = None
                k = pc(chosen.mask)
                if k > l_peak:
                    l_peak = k
            else:
                chosen.conc = max(0.0, chosen.conc
                                  + partial_max * overlap(chosen.mask, pattern) * CONC_UP
                                  - ACUTE_PUNISH)
                chosen.fails += 1
                if dorm_n and chosen.fails >= dorm_n:
                    if not chosen.dormant:
                        chosen.dorm_since = t
                    chosen.dormant = True
                    chosen.conc = max(chosen.conc, CONC_MIN)
                elif chosen.conc < CONC_MIN and chosen.fails < clear_n:
                    chosen.conc = CONC_MIN
                    rescued += 1

        acted = chosen is not None
        all_steps += 1
        if not triggered:
            all_idle += 1
        if acted:
            all_act += 1
            budget -= ACT_COST
        if ok:
            all_succ += 1

        bi = t // BLOCK
        if bi < len(blk_act):
            if acted:
                blk_act[bi] += 1
                if ok:
                    blk_suc[bi] += 1

        # ---------------- paid-window accounting + diagnostics ----------------
        if t >= BASE_GRACE:
            pd_steps += 1
            if len(ops) >= MAX_OPS:
                full_paid += 1
            if not triggered:
                pd_idle += 1
            if acted:
                pd_act += 1
            if ok:
                pd_succ += 1
            # D1: on a paid FAILED action, is the failure coverage or selection?
            if acted and not ok:
                d1_failsteps += 1
                exists = any(couples(o.mask, pattern, world_w) for o in ops)
                if exists:
                    d1_selfail += 1
                else:
                    d1_covfail += 1
            # D2: distinct-mask ratio
            if ops:
                d2_sum += len(set(o.mask for o in ops)) / len(ops)
                d2_n += 1
            # D4: cascade run lengths (zero-success actions in paid window)
            if acted:
                if ok:
                    if cur_zero:
                        d4_lens.append(cur_zero)
                        if cur_zero > d4_max:
                            d4_max = cur_zero
                        cur_zero = 0
                else:
                    cur_zero += 1
            # D3: neighbor coverage (sampled, drift>0 only)
            if drift > 0 and t % D3_EVERY == 0:
                pats = _neighborhood(pattern, n_ch)
                cov_cnt = 0
                for p in pats:
                    if any(couples(o.mask, p, world_w) for o in ops):
                        cov_cnt += 1
                d3_sum += cov_cnt / len(pats)
                d3_n += 1

        budget -= (0.0 if t < BASE_GRACE else DECAY)
        if budget > BUDGET_MAX:
            budget = BUDGET_MAX

        for o in ops:
            if not o.dormant:
                o.conc *= CONC_DECAY

        if forget_after:
            keep = []
            for o in ops:
                if o.dormant and o.dorm_since is not None and (t - o.dorm_since) >= forget_after:
                    forgotten += 1
                    continue
                keep.append(o)
            ops = keep

        before = len(ops)
        keep = []
        for o in ops:
            if o.dormant or o.fails < clear_n or o.conc >= CONC_MIN:
                keep.append(o)
            else:
                pass
        ops = keep
        cleared += before - len(ops)

        if not ops:
            ops = [Op(random_pair(rng, n_ch))]

        if rng.random() < VAR_P and len(ops) < MAX_OPS:
            ops.append(mint_op(ops, rng, n_ch, mode, world_w, pattern, sensed, diversity_p))
        if len(ops) > MAX_OPS:
            ops.sort(key=lambda o: o.conc)
            ops = ops[-MAX_OPS:]

        if budget <= 0:
            alive = False
            if cur_zero:
                d4_lens.append(cur_zero)
                if cur_zero > d4_max:
                    d4_max = cur_zero
            if ops:
                cs = [o.conc for o in ops]
                death = {"ops": len(ops), "dorm": sum(1 for o in ops if o.dormant),
                         "conc_max": max(cs), "distinct": len(set(o.mask for o in ops))}
            else:
                death = {"ops": 0, "dorm": 0, "conc_max": 0.0, "distinct": 0}
            break

    def rate(a, b):
        return (a / b) if b else None

    a_pd = rate(pd_idle, pd_steps)
    q_pd = rate(pd_act, pd_steps)
    g_pd = rate(pd_succ, pd_act)
    q_all = rate(all_act, all_steps)
    g_all = rate(all_succ, all_act)

    def er(q, g):
        return None if (q is None or g is None) else -1.0 + q * (3.0 * g - 0.3)

    blocks = [rate(blk_suc[i], blk_act[i]) for i in range(HORIZON // BLOCK)]
    return {
        "world": world, "drift": drift, "seed": seed, "W": world_w, "combine": mode,
        "diversity_p": diversity_p, "dorm_n": dorm_n, "clear_n": clear_n, "forget": forget_after,
        "alive": alive, "steps": steps, "L_peak": l_peak,
        "alpha_all": rate(all_idle, all_steps), "gamma_all": g_all,
        "alpha_paid": a_pd, "q_paid": q_pd, "gamma_paid": g_pd,
        "ER_all": er(q_all, g_all), "ER_paid": er(q_pd, g_pd),
        "paid_steps": pd_steps,
        "full_frac_paid": (full_paid / pd_steps) if pd_steps else 0.0,
        "rescued": rescued, "cleared": cleared, "forgotten": forgotten,
        # diagnostics
        "d1_failsteps": d1_failsteps, "d1_covfail": d1_covfail, "d1_selfail": d1_selfail,
        "d2_distinct_ratio": rate(d2_sum, d2_n),
        "d3_neighbor_cover": rate(d3_sum, d3_n),
        "d4_max_cascade": d4_max,
        "d4_mean_cascade": (sum(d4_lens) / len(d4_lens)) if d4_lens else 0.0,
        "death": death,
        "blocks": blocks,
    }


def aggregate(runs):
    keys = {}
    for r in runs:
        k = (r["combine"], r["diversity_p"], r["drift"])
        keys.setdefault(k, []).append(r)
    rows = []
    for k, rs in sorted(keys.items()):
        def avg(f):
            vs = [r[f] for r in rs if r[f] is not None]
            return (sum(vs) / len(vs)) if vs else None
        lifes = sorted(r["steps"] for r in rs)
        n = len(rs)
        covfail = sum(r["d1_covfail"] for r in rs)
        selfail = sum(r["d1_selfail"] for r in rs)
        failsteps = covfail + selfail
        nb = len(rs[0]["blocks"])
        curve = []
        for i in range(nb):
            vs = [r["blocks"][i] for r in rs if r["blocks"][i] is not None]
            curve.append((sum(vs) / len(vs)) if vs else None)
        deaths = [r["death"] for r in rs if r["death"]]
        rows.append({
            "combine": k[0], "diversity_p": k[1], "drift": k[2], "n": n,
            "survival": sum(1 for r in rs if r["alive"]) / n,
            "life_med": statistics.median(lifes),
            "life_iqr": (lifes[n // 4], lifes[(3 * n) // 4]),
            "life_max": lifes[-1],
            "alpha_paid": avg("alpha_paid"), "q_paid": avg("q_paid"),
            "gamma_paid": avg("gamma_paid"), "ER_paid": avg("ER_paid"),
            "full_frac_paid": sum(r["full_frac_paid"] for r in rs) / n,
            "coverage_fail_frac": (covfail / failsteps) if failsteps else None,
            "selection_fail_frac": (selfail / failsteps) if failsteps else None,
            "d1_failsteps": failsteps / n,
            "d2_distinct_ratio": avg("d2_distinct_ratio"),
            "d3_neighbor_cover": avg("d3_neighbor_cover"),
            "d4_max_cascade": avg("d4_max_cascade"),
            "d4_mean_cascade": avg("d4_mean_cascade"),
            "death_distinct": (sum(x["distinct"] for x in deaths) / len(deaths)) if deaths else None,
            "death_conc_max": (sum(x["conc_max"] for x in deaths) / len(deaths)) if deaths else None,
            "curve": curve,
        })
    return rows


def main():
    quick = "--quick" in sys.argv
    ws = [int(a.split("=")[1]) for a in sys.argv if a.startswith("--w=")] or [4]
    seeds = ([42, 43] if quick else list(range(101, 141)))
    runs = []
    for w in ws:
        for mode in COMBINE_MODES:
            # ORACLE is a ceiling reference: only the control rung (diversity does not apply to it)
            div_list = [0.0] if mode == "ORACLE" else DIVERSITY_LADDER
            for diversity_p in div_list:
                for clear_n in CLEAR_LADDER:
                    for dorm_n in DORM_LADDER:
                        for drift in DRIFT_LADDER:
                            for forget in FORGET_LADDER:
                                for partial in PARTIAL_LADDER:
                                    for seed in seeds:
                                        runs.append(run("SMALL", drift, seed, mode, w, partial,
                                                        dorm_n, clear_n, diversity_p, forget))
    rows = aggregate(runs)
    hdr = (f"{'combine':<9}{'divP':<6}{'drift':<7}{'n':<4}{'surv':<7}{'lifeMed':<8}{'IQR':<13}"
           f"{'a_paid':<8}{'g_paid':<8}{'ER_paid':<9}{'vs433':<7}{'covF%':<7}{'selF%':<7}"
           f"{'D2dist':<8}{'D3nbr':<7}{'D4max':<7}{'dthDist':<8}")
    print(hdr)
    print("-" * len(hdr))
    print(f"# gamma floor={BREAK_EVEN:.4f} | oracle ceiling@drift.01={ORACLE_CEILING} | divP=0 is exact PREDGUS control")
    for r in rows:
        def fm(v, d=3):
            return "-" if v is None else f"{v:.{d}f}"
        gp = r["gamma_paid"]
        vs = "-" if gp is None else ("OVER" if gp >= BREAK_EVEN else "under")
        iqr = f"{r['life_iqr'][0]}-{r['life_iqr'][1]}"
        print(f"{r['combine']:<9}{r['diversity_p']:<6}{r['drift']:<7}{r['n']:<4}"
              f"{r['survival']:<7.2f}{r['life_med']:<8.0f}{iqr:<13}"
              f"{fm(r['alpha_paid']):<8}{fm(r['gamma_paid']):<8}{fm(r['ER_paid']):<9}{vs:<7}"
              f"{fm(r['coverage_fail_frac'],2):<7}{fm(r['selection_fail_frac'],2):<7}"
              f"{fm(r['d2_distinct_ratio']):<8}{fm(r['d3_neighbor_cover']):<7}"
              f"{fm(r['d4_max_cascade'],1):<7}{fm(r['death_distinct'],1):<8}")

    print("\n# success rate by 500-step block (paid regime starts block 0 of t>=200)")
    for r in rows:
        cur = " ".join("-" if v is None else f"{v:.2f}" for v in r["curve"][:8])
        print(f"{r['combine']:<9} divP={r['diversity_p']:<4} drift={r['drift']:<6} surv={r['survival']:.2f} | {cur}")

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "v130_coverage_probe.json"), "w", encoding="utf-8") as f:
        json.dump({"runs": runs, "aggregate": rows, "break_even": BREAK_EVEN,
                   "oracle_ceiling": ORACLE_CEILING}, f, indent=2)
    print("\nwrote v130_coverage_probe.json")


if __name__ == "__main__":
    main()
