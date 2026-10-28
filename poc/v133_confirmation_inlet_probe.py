"""
v1.33 HETEROGENEOUS CONFIRMATION INLET -- attack the SAME-SOURCE confirmation that v132 proved is recency in disguise.

PREREG: poc/preregister/v133_heterogeneous_confirmation_inlet.yaml (committed 7825771 BEFORE any result).

WHAT v131/v132 LEFT (first-tier measured)
    v131: PAIR composition = the only honest survival>0 at drift 0.01 full rent (0.025, gamma 0.730, life 1334),
          FAILS beat-oracle (0.075); spanning basis erodes monotonically (span 6.2 -> 0.1 over 8 blocks).
    v132: retention cannot fix erosion (4th retention falsification; H-NO-RET-RESCUE). Mechanism 3 measured:
          the module-layer account conf_count -- how often an op's mask is a subset of the CURRENT sensed --
          is RECENCY IN DISGUISE, because the confirmation test carries NO context-distinction: one op
          re-confirmed N times inside one pattern neighbourhood counts as N independent confirmations.
          Used as the eviction key it kept junk and evicted fresh features (span_end 0.8, worst rung).

THE SINGLE SWEPT STRUCTURAL VARIABLE = CONF_MODE x window K (the confirmation inlet)
    v131/v132 compute EVERY confirmation, union-membership test and minting score against ONE instantaneous
    noisy read: sense() corrupts the pattern with prob SENSE_P=0.30 by swapping one active channel for one
    inactive channel. A union assembled from features confirmed by a corrupted read can contain a channel that
    is not lit, so it fails to couple even when the library spanned the right channels.
    The agent keeps its OWN observation history: a rolling window of the last K `sensed` values (new state;
    no frozen constant moved). Persistent set P = channels lit in a MAJORITY (>K/2) of the reads in the window.
      INST : confirmed iff mask subset sensed_t              == v131/v132 exactly (regression anchors A/B).
      PERS : confirmed iff mask subset P                     == temporally pooled inlet (K independent draws).
      BOTH : confirmed iff mask subset sensed_t AND subset P == agreement of two discretizations (conservative).
    K=1 makes PERS bit-identical to INST (majority of one read = that read) = regression anchor C.
    Downstream is v131 PAIR UNCHANGED: union of confirmed features (PAIR = 2 highest conc; fallback to the v130
    single-op conc-weighted path when fewer than 2 confirmed), shared credit to fired members, retention R0 CLEAR.

WHY THIS IS NOT THE SAME-SOURCE FALLACY (and why it is also a test of my critique of Hy's Theorem C)
    The DPI ceiling I(Y;gate) <= I(Y;A^N) <= I(Y;B) is N-free ONLY when the N samples resample the agent's own
    belief B (chain Y -> B -> A^N). Here the samples are independent noisy observations of the WORLD
    (chain Y -> A^N, noise draws independent across time), and the state changes on a timescale (1/drift ~ 100
    steps) >> K. Pooling K such reads reduces per-channel estimation error; the question v133 answers is whether
    that reduction REACHES the viability space. Instruments I1/I2 measure it directly (see below).

INSTRUMENTS (oracle-side; printed with an INSTRUMENT tag; NEVER read by the agent -- K-INSTRUMENT-LABELED):
    I1 sens_err_inst = mean Hamming(sensed_t, true pattern) over paid steps.
    I2 sens_err_pers = mean Hamming(P, true pattern) over paid steps, at the arm's K.
    I3 disagree_band = mean |P symmetric-difference sensed_t| over paid steps (where the two inlets differ).

HARD JUDGE (unchanged): full rent, drift 0.01: survival>0 AND gamma_paid>0.4333; beat oracle: survival>0.075.
PRIMARY judge is scored on PAIR x PERS x K=5 (K fixed a priori at the ladder middle, before any result).
NOTHING HERE CHANGES A v1.17 CONSTANT. DECAY, GAIN, ACT_COST, B0, BUDGET_MAX, CONC_*, MAX_OPS, N_BASE_OPS,
VAR_P, SENSE_P, ACUTE_PUNISH, COMBINE_P, K_PRED, W_MAX_CAP, DORM_N, CLEAR_N, FORGET_AFTER, BASE_GRACE, couples()
all untouched. Cold start = 6 RANDOM weight-2 features.
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
COMBINE_MODES = ["PREDGUS", "ORACLE"]    # ORACLE = cheating point-storage ceiling, run OFF x INST only
RET_HELD = "CLEAR"                       # v132 falsified RETAIN/SUPPRESS: retention held at R0 = v131 exact
CONF_MODES = ["INST", "PERS", "BOTH"]    # the swept confirmation inlet
K_LADDER = [1, 3, 5, 9]                  # observation-window ladder; K=1 makes PERS == INST (anchor C)
PRIMARY_K = 5                            # primary judge fixed A PRIORI at the ladder middle (K-NO-TUNE-TO-WIN)
DRIFT_LADDER = [0.0, 0.01, 0.02]
FORGET_AFTER = 400                       # R0 CLEAR keeps forget on, as v131/v132
PARTIAL_MAX = 0.5
THRESH = 0.0                             # state-grace OFF -- FULL RENT per hard judge

BREAK_EVEN = 1.3 / 3.0                   # 0.4333
ORACLE_CEILING = 0.075                   # v130 measured reactive-oracle survival @ drift .01
HANDED_UB_GAMMA = 0.70                   # verified full-basis union ceiling (instrument, not a target)
SPAN_CUT = 6                             # of 8 channels: a library is "spanning" if w2 features cover >= 6


def pc(x):
    return bin(x).count("1")


class Op:
    __slots__ = ("mask", "conc", "fails", "dormant", "ov_ema", "dorm_since", "conf_count", "conf_pers")

    def __init__(self, mask, conc=CONC_INIT):
        self.mask = mask
        self.conc = conc
        self.fails = 0
        self.dormant = False
        self.ov_ema = EMA_INIT
        self.dorm_since = None
        self.conf_count = 0   # instantaneous-inlet confirmations (v132 definition kept for anchor fidelity)
        self.conf_pers = 0    # pooled-inlet confirmations (v133 diagnostic; NEVER drives anything here)


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


def run(world, drift, seed, mode, world_w, comp_mode, ret, conf_mode, kw):
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
    cleared_conf = []                    # conf_count of ops deleted by the CLEAR rule (continuity with v132)
    # ---- v133 observation window (NEW STATE; no frozen constant touched) ----
    hist = []                            # rolling window of the last kw `sensed` values (agent's own history)
    cnt = [0] * n_ch                     # incremental per-channel lit counts inside the window
    pers = 0                             # persistent set P = channels lit in a MAJORITY (>len/2) of window reads
    i1_sum = i2_sum = i3_sum = i_n = 0   # INSTRUMENTS (oracle-side; never read by the agent)
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

        # ---- v133: push this read into the agent's own window, maintain the persistent set P ----
        # incremental counts: no rng consumed, no frozen constant touched. kw=1 => P == sensed exactly.
        hist.append(sensed)
        for b in channels(sensed, n_ch):
            cnt[b] += 1
        if len(hist) > kw:
            old = hist.pop(0)
            for b in channels(old, n_ch):
                cnt[b] -= 1
        need = len(hist) // 2 + 1            # strict majority of the reads currently held
        pers = 0
        for b in range(n_ch):
            if cnt[b] >= need:
                pers |= 1 << b

        pool = [o for o in ops if (not o.dormant) or probe_now]
        triggered = [o for o in pool if (o.mask & sensed)]

        # ---------------- SELECTION (composition vs single-op) ----------------
        composed_mask = None
        fired_members = []
        if comp_mode != "OFF":
            # THE SWEPT INLET: which estimate decides that a live op is a confirmed composition member.
            # INST = the single instantaneous noisy read (v131/v132 exactly).
            # PERS = the temporally pooled persistent set (K independent noise draws).
            # BOTH = agreement of the two discretizations (mask subset of sensed AND of P).
            if conf_mode == "PERS":
                conf_ref = pers
            elif conf_mode == "BOTH":
                conf_ref = sensed & pers
            else:
                conf_ref = sensed
            confirmed = [o for o in pool if (o.mask & conf_ref) == o.mask]
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
            for o in ops:                       # both confirmation accounts are DIAGNOSTIC ONLY in v133
                if (o.mask & sensed) == o.mask:
                    o.conf_count += 1
                if (o.mask & pers) == o.mask:
                    o.conf_pers += 1
            # INSTRUMENTS (oracle-side; K-INSTRUMENT-LABELED: quarantined from the decision path)
            i1_sum += pc(sensed ^ pattern)      # I1 estimation error of the instantaneous inlet
            i2_sum += pc(pers ^ pattern)        # I2 estimation error of the pooled inlet at this arm's K
            i3_sum += pc(pers ^ sensed)         # I3 disagreement band between the two discretizations
            i_n += 1
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
        "ret": ret, "conf_mode": conf_mode, "K": kw,
        "conf_end_mean": (sum(o.conf_count for o in ops) / len(ops)) if ops else None,
        "confpers_end_mean": (sum(o.conf_pers for o in ops) / len(ops)) if ops else None,
        "conf_cleared_mean": (sum(cleared_conf) / len(cleared_conf)) if cleared_conf else None,
        "n_cleared_conf": len(cleared_conf),
        "INSTR_sens_err_inst": rate(i1_sum, i_n),
        "INSTR_sens_err_pers": rate(i2_sum, i_n),
        "INSTR_disagree_band": rate(i3_sum, i_n),
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
        k = (r["combine"], r["comp_mode"], r["conf_mode"], r["K"], r["drift"])
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
            "combine": k[0], "comp_mode": k[1], "conf_mode": k[2], "K": k[3], "drift": k[4], "n": n,
            "survival": sum(1 for r in rs if r["alive"]) / n,
            "life_med": statistics.median(lifes),
            "life_iqr": (lifes[n // 4], lifes[(3 * n) // 4]),
            "alpha_paid": avg("alpha_paid"), "q_paid": avg("q_paid"),
            "gamma_paid": avg("gamma_paid"), "ER_paid": avg("ER_paid"),
            "comp_fire_frac": avg("comp_fire_frac"),
            "conf_end_mean": avg("conf_end_mean"), "confpers_end_mean": avg("confpers_end_mean"),
            "conf_cleared_mean": avg("conf_cleared_mean"),
            "INSTR_sens_err_inst": avg("INSTR_sens_err_inst"),
            "INSTR_sens_err_pers": avg("INSTR_sens_err_pers"),
            "INSTR_disagree_band": avg("INSTR_disagree_band"),
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
    # 9 preregistered arms (v133_heterogeneous_confirmation_inlet.yaml). Retention HELD at R0 CLEAR (v132 falsified
    # RETAIN/SUPPRESS). No 10th arm, no post-hoc K.
    ARMS = [("ORACLE", "OFF", "INST", 1),                    # A2 ceiling reference
            ("PREDGUS", "OFF", "INST", 1),                   # A1 regression anchor A (== v132 OFF CLEAR)
            ("PREDGUS", "PAIR", "INST", 1),                  # A3 regression anchor B (== v132 PAIR CLEAR = v131 winner)
            ("PREDGUS", "PAIR", "PERS", 1),                  # A4 regression anchor C (majority of 1 read == that read)
            ("PREDGUS", "PAIR", "PERS", 3),                  # A5 ladder
            ("PREDGUS", "PAIR", "PERS", 5),                  # A6 PRIMARY (K fixed a priori)
            ("PREDGUS", "PAIR", "PERS", 9),                  # A7 ladder (lag cost)
            ("PREDGUS", "PAIR", "BOTH", 3),                  # A8 consensus inlet
            ("PREDGUS", "PAIR", "BOTH", 5)]                  # A9 consensus inlet at primary K
    for w in ws:
        for mode, comp_mode, conf_mode, kw in ARMS:
            for drift in DRIFT_LADDER:
                for seed in seeds:
                    runs.append(run("SMALL", drift, seed, mode, w, comp_mode, RET_HELD, conf_mode, kw))
    rows = aggregate(runs)
    hdr = (f"{'combine':<9}{'comp':<6}{'conf':<6}{'K':<3}{'drift':<7}{'n':<4}{'surv':<7}{'lifeMed':<8}{'IQR':<12}"
           f"{'g_paid':<8}{'ER_paid':<9}{'vs433':<7}{'cmpFir':<8}{'covF%':<7}{'selF%':<7}"
           f"{'w2%':<7}{'w3+%':<7}{'span':<6}{'confEnd':<8}{'confPE':<8}{'INSTRi1':<9}{'INSTRi2':<9}{'INSTRi3':<9}")
    print(hdr)
    print("-" * len(hdr))
    print(f"# gamma floor={BREAK_EVEN:.4f} | oracle ceiling={ORACLE_CEILING} | handed-basis UB gamma={HANDED_UB_GAMMA}"
          f" | span cut={SPAN_CUT}/8 | INST rows must == v132 rows | INSTR columns read the TRUTH (audit only)")
    for r in rows:
        def fm(v, d=3):
            return "-" if v is None else f"{v:.{d}f}"
        gp = r["gamma_paid"]
        vs = "-" if gp is None else ("OVER" if gp >= BREAK_EVEN else "under")
        iqr = f"{r['life_iqr'][0]}-{r['life_iqr'][1]}"
        w3p = r["w3_frac"] + r["w4plus_frac"]
        print(f"{r['combine']:<9}{r['comp_mode']:<6}{r['conf_mode']:<6}{r['K']:<3}{r['drift']:<7}{r['n']:<4}"
              f"{r['survival']:<7.3f}{r['life_med']:<8.0f}{iqr:<12}"
              f"{fm(gp):<8}{fm(r['ER_paid']):<9}{vs:<7}{fm(r['comp_fire_frac'],2):<8}"
              f"{fm(r['coverage_fail_frac'],2):<7}{fm(r['selection_fail_frac'],2):<7}"
              f"{r['w2_frac']:<7.2f}{w3p:<7.2f}{fm(r['span_end'],1):<6}"
              f"{fm(r['conf_end_mean'],1):<8}{fm(r['confpers_end_mean'],1):<8}"
              f"{fm(r['INSTR_sens_err_inst'],2):<9}{fm(r['INSTR_sens_err_pers'],2):<9}"
              f"{fm(r['INSTR_disagree_band'],2):<9}")

    print("\n# GROWTH CURVE: library size / channel-span by 500-step block (P-EROSION-FLAT judge material)")
    for r in rows:
        o = " ".join(f"{v:.0f}" for v in r["growth_ops"][:8])
        s = " ".join(f"{v:.1f}" for v in r["growth_span"][:8])
        print(f"{r['combine']:<9}{r['comp_mode']:<5}{r['conf_mode']:<5}K={r['K']:<3}drift={r['drift']:<6}surv={r['survival']:.3f}")
        print(f"    |L| : {o}")
        print(f"    span: {s}")

    print("\n# success rate by 500-step block (paid regime starts block 0 of t>=200)")
    for r in rows:
        cur = " ".join("-" if v is None else f"{v:.2f}" for v in r["curve"][:8])
        print(f"{r['combine']:<9}{r['comp_mode']:<5}{r['conf_mode']:<5}K={r['K']:<3}drift={r['drift']:<6}"
              f"surv={r['survival']:.3f} | {cur}")

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "v133_confirmation_inlet_probe.json"), "w", encoding="utf-8") as f:
        json.dump({"runs": runs, "aggregate": rows, "break_even": BREAK_EVEN,
                   "oracle_ceiling": ORACLE_CEILING, "handed_ub_gamma": HANDED_UB_GAMMA,
                   "primary_K": PRIMARY_K, "k_ladder": K_LADDER}, f, indent=2)
    print("\nwrote v133_confirmation_inlet_probe.json")


if __name__ == "__main__":
    main()
