"""
v1.32 RETENTION x COMPOSITION with TWO-LAYER BOOKKEEPING -- attack the EROSION wall left by v131.

PREREG: poc/preregister/v132_retention_composition_twolayer.yaml (committed 19ae9bb BEFORE any result).

WHAT v131 LEFT (first-tier measured)
    PAIR composition = first honest survival>0 at drift 0.01 full rent (0.025, gamma 0.730, life 1334)
    but FAILS beat-oracle (0.075); EVERY arm (incl ORACLE) shows monotone spanning-basis erosion;
    ALL dies faster than PAIR (broad shared failure credit -> correlated mass clearing).
    Root hypothesis: the environment verdict is a signal about the COMPOSITION EVENT and carries almost
    no information about whether a MEMBER is cross-context reusable; v131 booked that verdict directly
    onto members (delete on low conc) = used a near-zero-information signal for member life/death.

THE FIX UNDER TEST: TWO-LAYER BOOKKEEPING + a 3-rung RETENTION ladder
    Event layer  : v131 PAIR credit EXACTLY (small, local; ALL held OFF per v131).
    Module layer : conf_count = times an op's mask was observation-confirmed (mask subset of sensed;
                   reads ONLY sensed, K-HUMAN-DOOR safe). Read-only diagnostic in CLEAR/RETAIN;
                   in SUPPRESS it drives the only unavoidable deletion (MAX_OPS eviction).
    R0 CLEAR    : v131 exactly (clear rule on, forget 400, evict lowest conc). Regression arm.
    R1 RETAIN   : clear rule OFF (failed features dorm at fails>=3 and stay); forget 400 on; evict conc.
    R2 SUPPRESS : clear OFF; forget OFF; dormancy floors conc at CONC_MIN (gate off firing weight);
                  eviction = lowest conf_count (module-layer invariant account).
    Composition in {OFF, PAIR}; ORACLE x OFF x CLEAR kept as the 0.075 ceiling reference.

HARD JUDGE (unchanged): full rent, drift 0.01: survival>0 AND gamma_paid>0.4333; beat oracle: >0.075.
"""
import json
import os
import random
import statistics
import sys

# ---------------- constants HELD IDENTICAL to v1.17 / v130 ---------------------------------
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
D3_EVERY = 25

COMP_MODES = ["OFF", "PAIR"]             # OFF == exact v131/v130 baseline (regression control); ALL held OFF per v131
DIVERSITY_P = 0.0                        # v130 CDM held OFF (it was falsified); pure composition test
CLEAR_N = 1
DORM_N = 3
COMBINE_MODES = ["PREDGUS", "ORACLE"]    # ORACLE = cheating point-storage ceiling, run OFF x CLEAR only
RET_LADDER = ["CLEAR", "RETAIN", "SUPPRESS"]   # R0/R1/R2 preregistered; NO fourth rung post hoc
DRIFT_LADDER = [0.0, 0.01, 0.02]
FORGET_AFTER = 400                       # applied in CLEAR and RETAIN; SUPPRESS holds forget OFF
PARTIAL_MAX = 0.5
THRESH = 0.0                             # state-grace OFF -- FULL RENT per hard judge

BREAK_EVEN = 1.3 / 3.0                   # 0.4333
ORACLE_CEILING = 0.075                   # v130 measured reactive-oracle survival @ drift .01
HANDED_UB_GAMMA = 0.70                   # verified full-basis union ceiling (instrument, not a target)
SPAN_CUT = 6                             # of 8 channels: a library is "spanning" if w2 features cover >= 6


def pc(x):
    return bin(x).count("1")


class Op:
    __slots__ = ("mask", "conc", "fails", "dormant", "ov_ema", "dorm_since", "conf_count")

    def __init__(self, mask, conc=CONC_INIT):
        self.mask = mask
        self.conc = conc
        self.fails = 0
        self.dormant = False
        self.ov_ema = EMA_INIT
        self.dorm_since = None
        self.conf_count = 0   # MODULE-LAYER account: cross-context observation confirmations (sensed only)


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


def mint_op(ops, rng, n_ch, mode, w, pattern, sensed, diversity_p):
    do_combine = (mode != "OFF") and len(ops) >= 2 and rng.random() < COMBINE_P
    if not do_combine:
        return local_variation(ops, rng, n_ch)

    nm = None
    if mode == "RANDOM":
        a, b = rng.sample(ops, 2)
        nm = a.mask | b.mask
    elif mode == "PREDGUS":
        if diversity_p > 0.0 and rng.random() < diversity_p:
            nm = None  # CDM held off in v131
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
    act = channels(pattern, n_ch)
    inact = [b for b in range(n_ch) if not ((pattern >> b) & 1)]
    pats = [pattern]
    for a in act:
        base = pattern & ~(1 << a)
        for i in inact:
            pats.append(base | (1 << i))
    return pats


def _span(ops, n_ch):
    """distinct channels covered by LIVE weight-2 features (representation-type instrument)."""
    s = set()
    for o in ops:
        if not o.dormant and pc(o.mask) == 2:
            s.update(channels(o.mask, n_ch))
    return len(s)


def run(world, drift, seed, mode, world_w, comp_mode, ret):
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
    comp_fires = 0                       # how many actions were composed unions (mechanism provenance)
    cleared_conf = []                    # conf_count of ops deleted by the CLEAR rule (P-CONFCOUNT-SIGNAL)
    d1_covfail = d1_selfail = d1_failsteps = 0
    d2_sum = d2_n = 0
    d3_sum = d3_n = 0
    cur_zero = 0
    d4_max = 0
    d4_lens = []
    blk_act = [0] * (HORIZON // BLOCK)
    blk_suc = [0] * (HORIZON // BLOCK)
    # growth curve: per-block library size + channel span (sampled at last step of each block)
    growth_ops = [0] * (HORIZON // BLOCK)
    growth_span = [0] * (HORIZON // BLOCK)
    death = None

    for t in range(HORIZON):
        steps = t + 1
        pattern = step_env(pattern, drift, rng, n_ch)
        sensed = sense(pattern, rng, n_ch)
        probe_now = bool(DORM_N) and (t % PROBE_EVERY == 0)

        pool = [o for o in ops if (not o.dormant) or probe_now]
        triggered = [o for o in pool if (o.mask & sensed)]

        # ---------------- SELECTION (composition vs single-op) ----------------
        composed_mask = None
        fired_members = []
        if comp_mode != "OFF":
            confirmed = [o for o in pool if (o.mask & sensed) == o.mask]
            if len(confirmed) >= 2:
                if comp_mode == "PAIR":
                    members = sorted(confirmed, key=lambda o: o.conc, reverse=True)[:2]
                else:  # ALL
                    members = confirmed
                u = 0
                for m in members:
                    u |= m.mask
                composed_mask = u
                fired_members = members
        if composed_mask is None:
            # OFF path OR composition fallback (fewer than 2 confirmed): single op, EXACTLY v130
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
            if chosen is not None:
                composed_mask = chosen.mask
                fired_members = [chosen]

        # ---------------- OUTCOME (one action, shared credit to fired members) ----------------
        acted = composed_mask is not None
        ok = False
        if acted:
            if comp_mode != "OFF" and len(fired_members) >= 2:
                comp_fires += 1
            ok = couples(composed_mask, pattern, world_w)
            if ok:
                budget += GAIN
                k = pc(composed_mask)
                if k > l_peak:
                    l_peak = k
            for m in fired_members:
                m.ov_ema = (1.0 - EMA_A) * m.ov_ema + EMA_A * overlap(m.mask, sensed)
                if ok:
                    m.conc += CONC_UP
                    m.fails = 0
                    m.dormant = False
                    m.dorm_since = None
                else:
                    m.conc = max(0.0, m.conc
                                 + PARTIAL_MAX * overlap(m.mask, pattern) * CONC_UP
                                 - ACUTE_PUNISH)
                    m.fails += 1
                    if DORM_N and m.fails >= DORM_N:
                        if not m.dormant:
                            m.dorm_since = t
                        m.dormant = True
                        if ret == "SUPPRESS":
                            m.conc = CONC_MIN          # gate OFF: floor the firing weight (suppress, not delete)
                        else:
                            m.conc = max(m.conc, CONC_MIN)
                    elif m.conc < CONC_MIN and m.fails < CLEAR_N:
                        m.conc = CONC_MIN
                        rescued += 1

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
            for o in ops:                       # module-layer account accrual (read-only in CLEAR/RETAIN)
                if (o.mask & sensed) == o.mask:
                    o.conf_count += 1
            pd_steps += 1
            if len(ops) >= MAX_OPS:
                full_paid += 1
            if not triggered:
                pd_idle += 1
            if acted:
                pd_act += 1
            if ok:
                pd_succ += 1
            if acted and not ok:
                d1_failsteps += 1
                exists = any(couples(o.mask, pattern, world_w) for o in ops)
                if exists:
                    d1_selfail += 1
                else:
                    d1_covfail += 1
            if ops:
                d2_sum += len(set(o.mask for o in ops)) / len(ops)
                d2_n += 1
            if acted:
                if ok:
                    if cur_zero:
                        d4_lens.append(cur_zero)
                        if cur_zero > d4_max:
                            d4_max = cur_zero
                        cur_zero = 0
                else:
                    cur_zero += 1
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

        forget_now = FORGET_AFTER if ret != "SUPPRESS" else 0
        if forget_now:
            keep = []
            for o in ops:
                if o.dormant and o.dorm_since is not None and (t - o.dorm_since) >= forget_now:
                    forgotten += 1
                    continue
                keep.append(o)
            ops = keep

        before = len(ops)
        if ret == "CLEAR":                      # R0: exactly the v131 clear rule (regression path)
            keep = []
            for o in ops:
                if o.dormant or o.fails < CLEAR_N or o.conc >= CONC_MIN:
                    keep.append(o)
                else:
                    cleared_conf.append(o.conf_count)
            ops = keep
        cleared += before - len(ops)

        if not ops:
            ops = [Op(random_pair(rng, n_ch))]

        if rng.random() < VAR_P and len(ops) < MAX_OPS:
            ops.append(mint_op(ops, rng, n_ch, mode, world_w, pattern, sensed, DIVERSITY_P))
        if len(ops) > MAX_OPS:
            if ret == "SUPPRESS":
                ops.sort(key=lambda o: (o.conf_count, o.conc))   # module-layer invariant drives eviction
            else:
                ops.sort(key=lambda o: o.conc)
            ops = ops[-MAX_OPS:]

        # growth-curve sampling at the last step of each block
        if (t + 1) % BLOCK == 0:
            gi = (t + 1) // BLOCK - 1
            if 0 <= gi < len(growth_ops):
                growth_ops[gi] = len(ops)
                growth_span[gi] = _span(ops, n_ch)

        if budget <= 0:
            alive = False
            if cur_zero:
                d4_lens.append(cur_zero)
                if cur_zero > d4_max:
                    d4_max = cur_zero
            wh = [0] * 5
            for o in ops:
                wh[min(pc(o.mask), 4)] += 1
            death = {"ops": len(ops), "dorm": sum(1 for o in ops if o.dormant),
                     "conc_max": max((o.conc for o in ops), default=0.0),
                     "distinct": len(set(o.mask for o in ops)),
                     "wh": wh, "span": _span(ops, n_ch)}
            break

    # end-of-horizon representation snapshot (survivors)
    wh_end = [0] * 5
    for o in ops:
        wh_end[min(pc(o.mask), 4)] += 1
    span_end = _span(ops, n_ch)

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
        "comp_mode": comp_mode,
        "alive": alive, "steps": steps, "L_peak": l_peak,
        "alpha_all": rate(all_idle, all_steps), "gamma_all": g_all,
        "alpha_paid": a_pd, "q_paid": q_pd, "gamma_paid": g_pd,
        "ER_all": er(q_all, g_all), "ER_paid": er(q_pd, g_pd),
        "paid_steps": pd_steps,
        "full_frac_paid": (full_paid / pd_steps) if pd_steps else 0.0,
        "rescued": rescued, "cleared": cleared, "forgotten": forgotten,
        "comp_fires": comp_fires, "comp_fire_frac": rate(comp_fires, all_act),
        "ret": ret,
        "conf_end_mean": (sum(o.conf_count for o in ops) / len(ops)) if ops else None,
        "conf_cleared_mean": (sum(cleared_conf) / len(cleared_conf)) if cleared_conf else None,
        "n_cleared_conf": len(cleared_conf),
        "d1_failsteps": d1_failsteps, "d1_covfail": d1_covfail, "d1_selfail": d1_selfail,
        "d2_distinct_ratio": rate(d2_sum, d2_n),
        "d3_neighbor_cover": rate(d3_sum, d3_n),
        "d4_max_cascade": d4_max,
        "d4_mean_cascade": (sum(d4_lens) / len(d4_lens)) if d4_lens else 0.0,
        "wh_end": wh_end, "span_end": span_end,
        "death": death,
        "growth_ops": growth_ops, "growth_span": growth_span,
        "blocks": blocks,
    }


def aggregate(runs):
    keys = {}
    for r in runs:
        k = (r["combine"], r["comp_mode"], r["ret"], r["drift"])
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
        curve = [(sum(r["blocks"][i] for r in rs if r["blocks"][i] is not None)
                  / max(1, sum(1 for r in rs if r["blocks"][i] is not None)))
                 if any(r["blocks"][i] is not None for r in rs) else None
                 for i in range(nb)]
        # representation-type snapshot: average end weight histogram (normalized) + span
        wh_avg = [0.0] * 5
        for r in rs:
            tot = sum(r["wh_end"])
            if tot:
                for i in range(5):
                    wh_avg[i] += r["wh_end"][i] / tot
        wh_avg = [x / n for x in wh_avg]
        gops = [sum(r["growth_ops"][i] for r in rs) / n for i in range(len(rs[0]["growth_ops"]))]
        gspan = [sum(r["growth_span"][i] for r in rs) / n for i in range(len(rs[0]["growth_span"]))]
        rows.append({
            "combine": k[0], "comp_mode": k[1], "ret": k[2], "drift": k[3], "n": n,
            "survival": sum(1 for r in rs if r["alive"]) / n,
            "life_med": statistics.median(lifes),
            "life_iqr": (lifes[n // 4], lifes[(3 * n) // 4]),
            "alpha_paid": avg("alpha_paid"), "q_paid": avg("q_paid"),
            "gamma_paid": avg("gamma_paid"), "ER_paid": avg("ER_paid"),
            "comp_fire_frac": avg("comp_fire_frac"),
            "conf_end_mean": avg("conf_end_mean"), "conf_cleared_mean": avg("conf_cleared_mean"),
            "coverage_fail_frac": (covfail / failsteps) if failsteps else None,
            "selection_fail_frac": (selfail / failsteps) if failsteps else None,
            "d1_failsteps": failsteps / n,
            "d2_distinct_ratio": avg("d2_distinct_ratio"),
            "d3_neighbor_cover": avg("d3_neighbor_cover"),
            "d4_max_cascade": avg("d4_max_cascade"),
            "w2_frac": wh_avg[2], "w3_frac": wh_avg[3], "w4plus_frac": wh_avg[4],
            "span_end": avg("span_end"),
            "death_distinct": (lambda d: (sum(x["distinct"] for x in d) / len(d)) if d else None)(
                [r["death"] for r in rs if r["death"]]),
            "growth_ops": gops, "growth_span": gspan,
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
            if mode == "ORACLE":
                arms = [("OFF", "CLEAR")]                 # ceiling reference arm only
            else:
                arms = [(c, r) for c in COMP_MODES for r in RET_LADDER]
            for comp_mode, ret in arms:
                for drift in DRIFT_LADDER:
                    for seed in seeds:
                        runs.append(run("SMALL", drift, seed, mode, w, comp_mode, ret))
    rows = aggregate(runs)
    hdr = (f"{'combine':<9}{'comp':<6}{'ret':<9}{'drift':<7}{'n':<4}{'surv':<7}{'lifeMed':<8}{'IQR':<12}"
           f"{'g_paid':<8}{'ER_paid':<9}{'vs433':<7}{'cmpFir':<8}{'covF%':<7}{'selF%':<7}"
           f"{'w2%':<7}{'w3+%':<7}{'span':<6}{'confEnd':<8}{'confClr':<8}")
    print(hdr)
    print("-" * len(hdr))
    print(f"# gamma floor={BREAK_EVEN:.4f} | oracle ceiling={ORACLE_CEILING} | handed-basis UB gamma={HANDED_UB_GAMMA}"
          f" | span cut={SPAN_CUT}/8 | OFF must == v130 baseline")
    for r in rows:
        def fm(v, d=3):
            return "-" if v is None else f"{v:.{d}f}"
        gp = r["gamma_paid"]
        vs = "-" if gp is None else ("OVER" if gp >= BREAK_EVEN else "under")
        iqr = f"{r['life_iqr'][0]}-{r['life_iqr'][1]}"
        w3p = r["w3_frac"] + r["w4plus_frac"]
        print(f"{r['combine']:<9}{r['comp_mode']:<6}{r['ret']:<9}{r['drift']:<7}{r['n']:<4}"
              f"{r['survival']:<7.2f}{r['life_med']:<8.0f}{iqr:<12}"
              f"{fm(gp):<8}{fm(r['ER_paid']):<9}{vs:<7}{fm(r['comp_fire_frac'],2):<8}"
              f"{fm(r['coverage_fail_frac'],2):<7}{fm(r['selection_fail_frac'],2):<7}"
              f"{r['w2_frac']:<7.2f}{w3p:<7.2f}{fm(r['span_end'],1):<6}"
              f"{fm(r['conf_end_mean'],1):<8}{fm(r['conf_cleared_mean'],1):<8}")

    print("\n# GROWTH CURVE (P-GROWTH-NOT-HANDED): library size / channel-span by 500-step block")
    for r in rows:
        o = " ".join(f"{v:.0f}" for v in r["growth_ops"][:8])
        s = " ".join(f"{v:.1f}" for v in r["growth_span"][:8])
        print(f"{r['combine']:<9}{r['comp_mode']:<5}{r['ret']:<9}drift={r['drift']:<6}surv={r['survival']:.2f}")
        print(f"    |L| : {o}")
        print(f"    span: {s}")

    print("\n# success rate by 500-step block (paid regime starts block 0 of t>=200)")
    for r in rows:
        cur = " ".join("-" if v is None else f"{v:.2f}" for v in r["curve"][:8])
        print(f"{r['combine']:<9}{r['comp_mode']:<5}{r['ret']:<9}drift={r['drift']:<6}surv={r['survival']:.2f} | {cur}")

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "v132_retention_composition_probe.json"), "w", encoding="utf-8") as f:
        json.dump({"runs": runs, "aggregate": rows, "break_even": BREAK_EVEN,
                   "oracle_ceiling": ORACLE_CEILING, "handed_ub_gamma": HANDED_UB_GAMMA}, f, indent=2)
    print("\nwrote v132_retention_composition_probe.json")


if __name__ == "__main__":
    main()
