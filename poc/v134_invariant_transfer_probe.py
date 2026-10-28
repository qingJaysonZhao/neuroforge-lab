"""
v1.34 INVARIANT TRANSFER TEST -- is the library a TRANSFERABLE MODULE POOL or a LITERAL ANSWER TABLE?

PREREG: poc/preregister/v134_invariant_transfer.yaml (committed 43ebf26 BEFORE any result).

WHY THIS QUESTION IS NOT ANSWERED BY v130-v135
    Survival under drift measures adaptation to a target that moves by ONE channel swap at a time. A library of
    literal answers erodes slowly enough to keep up with 1-swap drift and looks IDENTICAL to a library of
    reusable modules on every metric collected so far. The two representation types are behaviourally
    indistinguishable under small drift and separable only under a JUMP. v133 (denoised confirmation inlet,
    survival 0.025 -> 0.500 at drift 0.01) and v135 (that win survives storage pricing: 0.425 at rung P1,
    priced net income +0.910/step) produced a LIVING, PAYING agent -- so there is finally something to test.

THE JUMP
    At t = SWITCH_AT = 2000 (fixed a priori; HORIZON 4000, paid regime 1800 steps old at the switch) the world
    pattern is replaced by one at Hamming distance D: D active channels swapped for D inactive ones. With W=4 on
    8 channels, D=4 is the DISJOINT pattern -- not one channel of the old target is lit. The agent is not told,
    gets no budget reprieve, no reset, no grace. Ordinary drift continues after the switch.

THE SWEPT STRUCTURAL VARIABLES = CARRY x D
    WARM   : library carried as-is, minting OPEN                 == the honest agent.
    COLD   : library WIPED to the 6 random weight-2 cold start    == the RE-LEARNING FLOOR.
    FROZEN : library carried, minting FROZEN after the switch     == THE DECODER TEST (is the carried structure
             ALONE sufficient?). The mint draw is still consumed and the op still built, then DISCARDED, so the
             random stream stays aligned with WARM: the only difference is whether the new op enters the library.
    NOSWITCH (D=0): switch machinery is a no-op consuming no rng  == regression anchor to v135 PERS K5 P1.
    D in {2, 4} only. NO third distance. PRIMARY = drift 0.01, D=4, WARM.

INSTRUMENT ARMS (labeled, cheating, NEVER an honest result -- K-INSTRUMENT-LABELED)
    LIT-HAND : handed {p0} plus the four weight-3 subsets p0-minus-one-channel (literal answers; reads the truth).
    MOD-HAND : handed all 28 weight-2 pairs of the 8 channels (full basis).
    Both keep the SAME generator as WARM (minting OPEN), so the pair brackets the seed representation type.
    If WARM lands near MOD-HAND and far from LIT-HAND, representation type decides transfer.

NEW PER-RUN STATE (no frozen constant touched)
    op.born = the step at which the op entered the library (0 for base and handed ops). Read only by the reuse
    metrics and by nothing in the decision path.

METRICS  (T1-T4, T6, T7 agent-side bookkeeping; T5 reads the truth and stays quarantined)
    T1 reuse_ratio      = fraction of post-switch SUCCESSFUL actions whose fired members were ALL born < SWITCH_AT
    T1b reuse_w2_ratio  = same, restricted to fired members that are ALL weight-2 (the generator makes a MIX:
                          v133/v135 measured w2_frac 0.83, w3+ 0.17, so T1 alone cannot separate carried
                          modules from carried composites)
    T2 recovery_lag     = steps to the first post-switch success; recovery_lag_80 = steps to the first 50-step
                          window with rate >= 0.8 x the pre-switch rate
    T3 post_survival    = alive at HORIZON                       PRIMARY OUTCOME
    T4 gamma_post       = coupling rate over post-switch actions
    T5 (INSTRUMENT)     = at the switch, reading p': does any op couple? pair_cover = how many of the 6
                          weight-2 subsets of p' are present as library masks
    T6 pre-switch snapshot: |L|, span, distinct, weight histogram
    T7 budget_at_switch : HONESTY CONTROL for the WARM-vs-COLD comparison

FORESEEN DIFFICULTY, REGISTERED BEFORE THE RUN
    span_end is 6.0 of 8 channels with |L| ~ 20, so the weight-2 subset is broad but THIN: the 6 specific pairs
    of a disjoint p' are unlikely to all be present, so T5 pair_cover is expected low and the jump is expected
    to be hard for every honest arm. Worse, carrying old ops can INTERFERE: a weight-2 op {a,b} with a in p'
    still triggers on sensed, gets selected, fails to couple and draws the penalty path -- so WARM could be
    WORSE than COLD. That outcome is preregistered as its own judgment (H-NEGATIVE-TRANSFER).

RENT is HELD at v135 rung P1 for every arm including the instruments, so the whole bracket is priced.
Everything else held at the v133/v135 winner: COMP=PAIR, CONF=PERS, K=5, retention R0 CLEAR, DORM_N=3,
CLEAR_N=1, FORGET_AFTER=400, BASE_GRACE=200, full rent THRESH=0.0.
NOTHING HERE CHANGES A v1.17 CONSTANT: DECAY, GAIN, ACT_COST, B0, BUDGET_MAX, CONC_*, MAX_OPS, N_BASE_OPS,
VAR_P, SENSE_P, ACUTE_PUNISH, COMBINE_P, K_PRED, W_MAX_CAP, DORM_N, CLEAR_N, FORGET_AFTER, BASE_GRACE,
RENT_UNIT (ACT_COST/MAX_OPS), couples() all untouched. Cold start = 6 RANDOM weight-2 features for every
honest arm; only the two instrument arms are handed anything.
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
CONF_HELD = ["INST", "PERS"]             # the two v133 arms being priced (BOTH/K-ladder not re-run here)
PRIMARY_K = 5                            # v133 primary K, carried over unchanged (a-priori there, held here)
DRIFT_LADDER = [0.0, 0.01, 0.02]
FORGET_AFTER = 400                       # R0 CLEAR keeps forget on, as v131/v132/v133
PARTIAL_MAX = 0.5
THRESH = 0.0                             # state-grace OFF -- FULL RENT per hard judge

# ---------------- v135 rent: HELD at rung P1 for every arm (the whole bracket is priced) --
RENT_UNIT = ACT_COST / MAX_OPS           # 0.3 / 40 = 0.0075 -- DERIVED from frozen constants, never searched
RUNGS = [("FREE", 0), ("P1", 1), ("P2", 2)]
RENT_HELD = dict(RUNGS)["P1"]            # v134 holds rent at rung P1; NOT swept here

# ---------------- v134 THE SWEPT STRUCTURAL VARIABLES: CARRY x D --------------------------
SWITCH_AT = 2000                         # fixed A PRIORI at the horizon middle (HORIZON 4000, BASE_GRACE 200)
CARRY_MODES = ["WARM", "COLD", "FROZEN"] # + NOSWITCH == D=0 (switch machinery a no-op, consumes no rng)
D_LADDER = [2, 4]                        # 2 distances ONLY, no third (K-NO-TUNE-TO-WIN)
PRIMARY_D = 4                            # disjoint pattern on 8 channels with W=4
N_POST_WIN = (HORIZON - SWITCH_AT) // 50 # 40 windows of 50 steps for recovery_lag_80

BREAK_EVEN = 1.3 / 3.0                   # 0.4333
ORACLE_CEILING = 0.075                   # v130 measured reactive-oracle survival @ drift .01
HANDED_UB_GAMMA = 0.70                   # verified full-basis union ceiling (instrument, not a target)
SPAN_CUT = 6                             # of 8 channels: a library is "spanning" if w2 features cover >= 6


def pc(x):
    return bin(x).count("1")


class Op:
    __slots__ = ("mask", "conc", "fails", "dormant", "ov_ema", "dorm_since", "conf_count", "conf_pers", "born")

    def __init__(self, mask, conc=CONC_INIT):
        self.mask = mask
        self.conc = conc
        self.fails = 0
        self.dormant = False
        self.ov_ema = EMA_INIT
        self.dorm_since = None
        self.conf_count = 0   # instantaneous-inlet confirmations (v132 definition kept for anchor fidelity)
        self.conf_pers = 0    # pooled-inlet confirmations (v133 diagnostic; NEVER drives anything here)
        self.born = 0         # v134: step at which the op entered the library (0 for base/handed ops).
                              # Read ONLY by the reuse metrics T1/T1b; never by the decision path.


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


def _cold_start(rng, n_ch):
    """the honest cold start: N_BASE_OPS RANDOM weight-2 features, deduplicated. Consumes rng."""
    ops = [Op(random_pair(rng, n_ch)) for _ in range(N_BASE_OPS)]
    seen, uniq = set(), []
    for o in ops:
        if o.mask not in seen:
            seen.add(o.mask)
            uniq.append(o)
    return uniq


def _handed(hand, p0, n_ch):
    """INSTRUMENT ONLY (K-INSTRUMENT-LABELED): a library given to the agent at t=0.
    LIT = the literal answers for the TRUE initial pattern p0: {p0} + the four weight-3 subsets p0-minus-one.
    MOD = all C(n_ch,2) weight-2 pairs (a full basis; reads nothing about p0 but is a hand-out anyway)."""
    if hand == "LIT":
        masks = [p0] + [p0 & ~(1 << b) for b in channels(p0, n_ch)]
    elif hand == "MOD":
        masks = [(1 << a) | (1 << b) for a in range(n_ch) for b in range(a + 1, n_ch)]
    else:
        return None
    out = []
    for m in masks:
        if m and pc(m) >= 2:
            out.append(Op(m))
    return out


def run(world, drift, seed, mode, world_w, comp_mode, ret, conf_mode, kw, rung,
        carry="WARM", dist=0, hand=None):
    n_ch = WORLDS[world]
    rng = random.Random(seed * 1000 + int(drift * 10000) + n_ch)
    pattern = initial_pattern(rng, n_ch, min(world_w, n_ch))

    ops = _cold_start(rng, n_ch)
    # ---- v134 instrument arms: the cold-start draws are STILL consumed, then the library is replaced,
    # so the environment/sensing random stream stays aligned with WARM (comparability, not fidelity).
    if hand:
        h = _handed(hand, pattern, n_ch)
        if h:
            ops = h

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
    i4_sum = 0                           # I4 held_units = mean (len(ops) + kw) over paid steps (bookkeeping)
    # ---- v134 jump state (bookkeeping only; nothing here enters the decision path) ----
    switched = False                     # True from t == SWITCH_AT onwards (set even when dist == 0)
    reached_switch = False
    frozen_mint = False                  # FROZEN: mint draw consumed + op built, then DISCARDED
    pre_act = pre_succ = 0               # pre-switch paid actions (denominator of recovery_lag_80)
    post_act = post_succ = 0             # T4
    t1_num = t1_den = 0                  # T1  reuse_ratio  (all fired members born < SWITCH_AT)
    t1b_num = t1b_den = 0                # T1b same restricted to all-weight-2 fired members
    post_wh = [0] * 5                    # weight histogram of post-switch fired members
    recovery_lag = None                  # T2
    recovery_lag80 = None
    post_win_act = [0] * N_POST_WIN
    post_win_suc = [0] * N_POST_WIN
    INSTR_any_couple = None              # T5 (reads the TRUTH p'; quarantined to the audit)
    INSTR_pair_cover = None              # T5
    pre_L = pre_span = pre_distinct = None   # T6
    pre_wh = None                        # T6
    budget_at_switch = None              # T7 honesty control
    carry_wiped = 0                      # how many ops the COLD wipe threw away
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

        # ================= v134 THE JUMP (t == SWITCH_AT; a no-op when dist == 0) =================
        # Placed BEFORE step_env/sense so the T5/T6/T7 snapshot reads the post-jump pattern p' pre-drift.
        # When dist == 0 NOTHING below consumes rng (regression anchor to v135 must stay bit-identical).
        if t == SWITCH_AT:
            switched = True
            reached_switch = True
            budget_at_switch = budget                    # T7 (identical across carry modes by construction)
            pre_L = len(ops)                             # T6 snapshot of the library AS IT ARRIVED
            pre_span = _span(ops, n_ch)
            pre_distinct = len(set(o.mask for o in ops))
            pre_wh = [0] * 5
            for o in ops:
                pre_wh[min(pc(o.mask), 4)] += 1
            if dist:
                # ---- environment-side jump: swap `dist` active channels for `dist` inactive ones ----
                act = channels(pattern, n_ch)
                inact = [b for b in range(n_ch) if not ((pattern >> b) & 1)]
                d = min(dist, len(act), len(inact))
                if d:
                    for b in rng.sample(act, d):
                        pattern &= ~(1 << b)
                    for b in rng.sample(inact, d):
                        pattern |= 1 << b
                # ---- T5 INSTRUMENT (reads the TRUTH p'; quarantined, never used by the agent) ----
                # measured on the library AS IT ARRIVED, i.e. BEFORE the carry handling below, so that
                # WARM / COLD / FROZEN are all diagnosed against the same carried structure.
                lib_masks = set(o.mask for o in ops)
                INSTR_any_couple = any(couples(o.mask, pattern, world_w) for o in ops)
                pb = channels(pattern, n_ch)
                subs = [(1 << pb[i]) | (1 << pb[j]) for i in range(len(pb)) for j in range(i + 1, len(pb))]
                INSTR_pair_cover = (sum(1 for s in subs if s in lib_masks) / len(subs)) if subs else None
                # ---- CARRY: what happens to the agent's own state at the jump ----
                if carry == "COLD":
                    carry_wiped = len(ops)
                    ops = _cold_start(rng, n_ch)         # the re-learning floor: 6 RANDOM weight-2 features
                elif carry == "FROZEN":
                    frozen_mint = True                   # the decoder test: carried structure ALONE
                # WARM: nothing happens to the library (the honest agent)

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

        # ---------------- v134 post-switch bookkeeping (T1/T1b/T2/T4; reads only ops.born/mask + ok) ----
        if acted and switched:
            post_act += 1
            if ok:
                post_succ += 1
            born_before = all(m.born < SWITCH_AT for m in fired_members)
            all_w2 = all(pc(m.mask) == OP_WEIGHT for m in fired_members)
            for m in fired_members:
                post_wh[min(pc(m.mask), 4)] += 1
            if ok:
                t1_den += 1
                if born_before:
                    t1_num += 1
                if all_w2:
                    t1b_den += 1
                    if born_before:
                        t1b_num += 1
                if recovery_lag is None:
                    recovery_lag = t - SWITCH_AT
            wi = (t - SWITCH_AT) // 50
            if 0 <= wi < N_POST_WIN:
                post_win_act[wi] += 1
                if ok:
                    post_win_suc[wi] += 1

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
            if not switched and acted:          # v134: pre-switch paid success rate (recovery_lag_80 baseline)
                pre_act += 1
                if ok:
                    pre_succ += 1
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
        # ---------------- v135 THE SWEPT VARIABLE: storage rent (paid steps only) ----------------
        # rung 0 == FREE == v133 exactly. RENT_UNIT is derived from frozen constants (ACT_COST/MAX_OPS),
        # not searched. Charge reads only len(ops) and kw -- K-HUMAN-DOOR safe.
        if t >= BASE_GRACE:
            i4_sum += len(ops) + kw          # I4 bookkeeping only (also collected on FREE, for comparability)
        if t >= BASE_GRACE and rung:
            budget -= RENT_UNIT * rung * (len(ops) + kw)
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
            new = mint_op(ops, rng, n_ch, mode, world_w, pattern, sensed, DIVERSITY_P)
            new.born = t                       # v134: provenance stamp (read only by T1/T1b)
            if not frozen_mint:
                ops.append(new)
            # FROZEN: the draw is consumed and the op is built exactly as in WARM, then DISCARDED, so the
            # random stream stays aligned with WARM and the only difference is whether it enters the library.
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

    # ---- v134 T2: recovery_lag_80 = steps from SWITCH_AT to the START of the first 50-step post window
    # whose success rate is >= 0.8 x the pre-switch paid success rate.
    pre_rate = (pre_succ / pre_act) if pre_act else None
    if reached_switch and pre_rate is not None:
        for wi in range(N_POST_WIN):
            if post_win_act[wi] and (post_win_suc[wi] / post_win_act[wi]) >= 0.8 * pre_rate:
                recovery_lag80 = wi * 50
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
        "comp_mode": comp_mode,
        "alive": alive, "steps": steps, "L_peak": l_peak,
        "alpha_all": rate(all_idle, all_steps), "gamma_all": g_all,
        "alpha_paid": a_pd, "q_paid": q_pd, "gamma_paid": g_pd,
        "ER_all": er(q_all, g_all), "ER_paid": er(q_pd, g_pd),
        "paid_steps": pd_steps,
        "full_frac_paid": (full_paid / pd_steps) if pd_steps else 0.0,
        "rescued": rescued, "cleared": cleared, "forgotten": forgotten,
        "comp_fires": comp_fires, "comp_fire_frac": rate(comp_fires, all_act),
        "ret": ret, "conf_mode": conf_mode, "K": kw, "rung": rung,
        "rung_name": dict((v, k) for k, v in RUNGS).get(rung, str(rung)),
        # ---------------- v134 fields ----------------
        "carry": carry, "dist": dist, "hand": hand or "NONE",
        "switch_at": SWITCH_AT, "reached_switch": reached_switch, "carry_wiped": carry_wiped,
        "post_survival": bool(alive and reached_switch),          # T3 PRIMARY OUTCOME
        "pre_rate": pre_rate,
        "post_act": post_act, "post_succ": post_succ,             # T4
        "gamma_post": rate(post_succ, post_act),
        "t1_num": t1_num, "t1_den": t1_den,                       # T1 raw counts (pooled at aggregate)
        "reuse_ratio": rate(t1_num, t1_den),
        "t1b_num": t1b_num, "t1b_den": t1b_den,                   # T1b raw counts
        "reuse_w2_ratio": rate(t1b_num, t1b_den),
        "recovery_lag": recovery_lag, "recovery_lag_80": recovery_lag80,   # T2
        "post_wh": post_wh,
        "budget_at_switch": budget_at_switch,                     # T7 honesty control
        "pre_L": pre_L, "pre_span": pre_span, "pre_distinct": pre_distinct, "pre_wh": pre_wh,   # T6
        "INSTR_any_couple": INSTR_any_couple, "INSTR_pair_cover": INSTR_pair_cover,             # T5 (truth)
        "conf_end_mean": (sum(o.conf_count for o in ops) / len(ops)) if ops else None,
        "confpers_end_mean": (sum(o.conf_pers for o in ops) / len(ops)) if ops else None,
        "conf_cleared_mean": (sum(cleared_conf) / len(cleared_conf)) if cleared_conf else None,
        "n_cleared_conf": len(cleared_conf),
        "INSTR_sens_err_inst": rate(i1_sum, i_n),
        "INSTR_sens_err_pers": rate(i2_sum, i_n),
        "INSTR_disagree_band": rate(i3_sum, i_n),
        "INSTR_held_units": rate(i4_sum, i_n),
        "INSTR_rent_paid": (RENT_UNIT * rung * rate(i4_sum, i_n)) if i_n else None,
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
        k = (r["combine"], r["comp_mode"], r["conf_mode"], r["K"], r["rung_name"],
             r["hand"], r["carry"], r["dist"], r["drift"])
        keys.setdefault(k, []).append(r)
    rows = []
    for k, rs in sorted(keys.items()):
        def avg(f):
            vs = [r[f] for r in rs if r[f] is not None]
            return (sum(vs) / len(vs)) if vs else None
        def med(f):
            vs = sorted(r[f] for r in rs if r[f] is not None)
            return statistics.median(vs) if vs else None
        def pooled(num, den):
            a = sum(r[num] for r in rs)
            b = sum(r[den] for r in rs)
            return (a / b) if b else None
        lifes = sorted(r["steps"] for r in rs)
        n = len(rs)
        reached = [r for r in rs if r["reached_switch"]]
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
        # v134: pooled weight histogram of POST-switch fired members
        pwh = [sum(r["post_wh"][i] for r in rs) for i in range(5)]
        pwh_tot = sum(pwh) or 1
        gops = [sum(r["growth_ops"][i] for r in rs) / n for i in range(len(rs[0]["growth_ops"]))]
        gspan = [sum(r["growth_span"][i] for r in rs) / n for i in range(len(rs[0]["growth_span"]))]
        rows.append({
            "combine": k[0], "comp_mode": k[1], "conf_mode": k[2], "K": k[3], "rung_name": k[4],
            "hand": k[5], "carry": k[6], "dist": k[7], "drift": k[8], "n": n,
            "survival": sum(1 for r in rs if r["alive"]) / n,
            "life_med": statistics.median(lifes),
            "life_iqr": (lifes[n // 4], lifes[(3 * n) // 4]),
            "alpha_paid": avg("alpha_paid"), "q_paid": avg("q_paid"),
            "gamma_paid": avg("gamma_paid"), "ER_paid": avg("ER_paid"),
            "comp_fire_frac": avg("comp_fire_frac"),
            # ---------------- v134 ----------------
            "reach_frac": len(reached) / n,
            "post_survival": sum(1 for r in rs if r["post_survival"]) / n,
            "post_surv_reached": (sum(1 for r in reached if r["post_survival"]) / len(reached)) if reached else None,
            "gamma_post": pooled("post_succ", "post_act"),
            "n_post_actions": avg("post_act"),
            "reuse_ratio": pooled("t1_num", "t1_den"),
            "reuse_ratio_mean": avg("reuse_ratio"),
            "reuse_w2_ratio": pooled("t1b_num", "t1b_den"),
            "reuse_w2_mean": avg("reuse_w2_ratio"),
            "recovery_lag_med": med("recovery_lag"),
            "recovery_lag80_med": med("recovery_lag_80"),
            "post_w2_frac": pwh[2] / pwh_tot, "post_w3plus_frac": (pwh[3] + pwh[4]) / pwh_tot,
            "INSTR_any_couple": avg("INSTR_any_couple"),
            "INSTR_pair_cover": avg("INSTR_pair_cover"),
            "budget_at_switch_med": med("budget_at_switch"),
            "pre_L": avg("pre_L"), "pre_span": avg("pre_span"), "pre_distinct": avg("pre_distinct"),
            # ---------------- carried over ----------------
            "conf_end_mean": avg("conf_end_mean"), "confpers_end_mean": avg("confpers_end_mean"),
            "conf_cleared_mean": avg("conf_cleared_mean"),
            "INSTR_sens_err_inst": avg("INSTR_sens_err_inst"),
            "INSTR_sens_err_pers": avg("INSTR_sens_err_pers"),
            "INSTR_disagree_band": avg("INSTR_disagree_band"),
            "INSTR_held_units": avg("INSTR_held_units"),
            "INSTR_rent_paid": avg("INSTR_rent_paid"),
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


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    sxy = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    return sxy / (sxx ** 0.5 * syy ** 0.5)


def get(rows, carry, dist, drift, hand="NONE"):
    for r in rows:
        if (r["carry"] == carry and r["dist"] == dist and r["hand"] == hand
                and abs(r["drift"] - drift) < 1e-12):
            return r
    return None


def main():
    quick = "--quick" in sys.argv
    ws = [int(a.split("=")[1]) for a in sys.argv if a.startswith("--w=")] or [4]
    seeds = ([42, 43] if quick else list(range(101, 141)))
    runs = []
    # 11 preregistered arms (v134_invariant_transfer.yaml). THE ONLY swept variables are CARRY x D.
    # Everything else held at the v133/v135 winner: PREDGUS x PAIR x PERS x K=5, retention R0 CLEAR,
    # rent rung P1. No 12th arm, no third distance, SWITCH_AT/primary fixed a priori.
    ARMS = [(None,  "WARM",   0),      # NOSWITCH: regression anchor == v135 PAIR x PERS x K5 x P1
            (None,  "WARM",   2),
            (None,  "WARM",   4),      # <-- PRIMARY JUDGE (with drift 0.01)
            (None,  "COLD",   2),
            (None,  "COLD",   4),      # re-learning FLOOR
            (None,  "FROZEN", 2),
            (None,  "FROZEN", 4),      # DECODER TEST
            ("LIT", "WARM",   2),      # INSTRUMENT (reads the truth)
            ("LIT", "WARM",   4),      # INSTRUMENT
            ("MOD", "WARM",   2),      # INSTRUMENT (full basis hand-out)
            ("MOD", "WARM",   4)]      # INSTRUMENT
    for w in ws:
        for hand, carry, dist in ARMS:
            for drift in DRIFT_LADDER:
                for seed in seeds:
                    runs.append(run("SMALL", drift, seed, "PREDGUS", w, "PAIR", RET_HELD, "PERS",
                                    PRIMARY_K, RENT_HELD, carry=carry, dist=dist, hand=hand))
    rows = aggregate(runs)

    hdr = (f"{'hand':<6}{'carry':<8}{'D':<3}{'drift':<7}{'n':<4}{'reach':<7}{'pSurv':<7}{'pSvR':<7}"
           f"{'lifeMed':<8}{'g_paid':<8}{'g_post':<8}{'reuse':<7}{'reuW2':<7}{'lag':<6}{'lag80':<7}"
           f"{'INSTRpc':<9}{'INSTRac':<9}{'budgSw':<8}{'preL':<6}{'preSpan':<8}")
    print(hdr)
    print("-" * len(hdr))
    print(f"# gamma floor={BREAK_EVEN:.4f} | rent HELD at rung P1 (RENT_UNIT={RENT_UNIT:.4f})"
          f" | SWITCH_AT={SWITCH_AT} | COMP=PAIR CONF=PERS K={PRIMARY_K} RET=CLEAR"
          f" | INSTRpc/INSTRac read the TRUTH p' at the switch (audit only)"
          f" | pSurv=alive at HORIZON over all seeds, pSvR=conditioned on reaching the switch")
    for r in rows:
        def fm(v, d=3):
            return "-" if v is None else f"{v:.{d}f}"
        print(f"{r['hand']:<6}{r['carry']:<8}{r['dist']:<3}{r['drift']:<7}{r['n']:<4}"
              f"{fm(r['reach_frac'],3):<7}{fm(r['post_survival'],3):<7}{fm(r['post_surv_reached'],3):<7}"
              f"{r['life_med']:<8.0f}{fm(r['gamma_paid']):<8}{fm(r['gamma_post']):<8}"
              f"{fm(r['reuse_ratio'],3):<7}{fm(r['reuse_w2_ratio'],3):<7}"
              f"{fm(r['recovery_lag_med'],0):<6}{fm(r['recovery_lag80_med'],0):<7}"
              f"{fm(r['INSTR_pair_cover'],3):<9}{fm(r['INSTR_any_couple'],3):<9}"
              f"{fm(r['budget_at_switch_med'],2):<8}{fm(r['pre_L'],1):<6}{fm(r['pre_span'],2):<8}")

    print("\n# GROWTH CURVE: library size / channel-span by 500-step block (switch at t=2000 = block 4)")
    for r in rows:
        o = " ".join(f"{v:.0f}" for v in r["growth_ops"][:8])
        s = " ".join(f"{v:.1f}" for v in r["growth_span"][:8])
        print(f"{r['hand']:<6}{r['carry']:<7}D={r['dist']:<3}drift={r['drift']:<6}"
              f"pSurv={r['post_survival']:.3f}")
        print(f"    |L| : {o}")
        print(f"    span: {s}")

    print("\n# success rate by 500-step block (blocks 0-3 pre-switch, 4-7 post-switch)")
    for r in rows:
        cur = " ".join("-" if v is None else f"{v:.2f}" for v in r["curve"][:8])
        print(f"{r['hand']:<6}{r['carry']:<7}D={r['dist']:<3}drift={r['drift']:<6}"
              f"pSurv={r['post_survival']:.3f} | {cur}")

    # ---------------- PREREGISTERED PREDICTIONS, scored ONCE (the audit is authoritative) -------------
    print("\n# PREDICTIONS (computed from this grid; primary = drift 0.01, D=4, WARM, hand NONE)")
    PD = 0.01
    w4, c4, f4 = get(rows, "WARM", 4, PD), get(rows, "COLD", 4, PD), get(rows, "FROZEN", 4, PD)
    w2, c2, f2 = get(rows, "WARM", 2, PD), get(rows, "COLD", 2, PD), get(rows, "FROZEN", 2, PD)
    lit4, mod4 = get(rows, "WARM", 4, PD, "LIT"), get(rows, "WARM", 4, PD, "MOD")
    d0 = get(rows, "WARM", 0, PD)
    if d0:
        print(f"  P-REGRESSION (anchor D=0, drift {PD}): survival={d0['survival']:.3f}"
              f" life_med={d0['life_med']:.0f} gamma_paid={d0['gamma_paid']:.3f}"
              f"  -> v135 committed target 0.425 / 2970 / 0.874 ; per-seed check in v134_regression_check.py")
    if lit4 and mod4:
        b1 = lit4["post_survival"] <= 0.10
        b2 = mod4["post_survival"] >= 0.80
        print(f"  P-BRACKET-SANE (INSTRUMENT): LIT-HAND pSurv={lit4['post_survival']:.3f} (<=0.10? {b1})"
              f" | MOD-HAND pSurv={mod4['post_survival']:.3f} (>=0.80? {b2})"
              f" -> bracket {'SANE' if (b1 and b2) else 'VOID/partial'}")
    if w4 and c4:
        diff = w4["post_survival"] - c4["post_survival"]
        ratio = (w4["post_survival"] / c4["post_survival"]) if c4["post_survival"] else float("inf")
        ok = (diff >= 0.10) and (ratio >= 2.0)
        neg = diff <= -0.10
        print(f"  P-TRANSFER (PRIMARY): WARM pSurv={w4['post_survival']:.3f} vs COLD={c4['post_survival']:.3f}"
              f" diff={diff:+.3f} ratio={ratio if ratio != float('inf') else -1:.2f}"
              f" (need >=2x AND >=+0.10) -> {'PASS' if ok else 'FAIL'}"
              f"{'  [H-NEGATIVE-TRANSFER condition met]' if neg else ''}")
        print(f"    reached-conditioned: WARM={w4['post_surv_reached']:.3f} COLD={c4['post_surv_reached']:.3f}"
              f" FROZEN={f4['post_surv_reached'] if f4 else float('nan'):.3f}"
              f" | reach_frac identical across carry modes by construction: "
              f"{w4['reach_frac']:.3f}/{c4['reach_frac']:.3f}/{f4['reach_frac'] if f4 else -1:.3f}")
    if w4:
        ru = w4["reuse_ratio"]
        print(f"  P-REUSE: T1 reuse_ratio(WARM,D4)={ru if ru is None else round(ru,3)}"
              f" (need >=0.50) -> {'PASS' if (ru is not None and ru >= 0.50) else 'FAIL'}"
              f" | T1b weight-2-only={w4['reuse_w2_ratio'] if w4['reuse_w2_ratio'] is None else round(w4['reuse_w2_ratio'],3)}"
              f" | post fired-member weights w2={w4['post_w2_frac']:.2f} w3+={w4['post_w3plus_frac']:.2f}")
    if f4:
        print(f"  P-DECODER: post_survival(FROZEN,D4)={f4['post_survival']:.3f} (need >0)"
              f" -> {'PASS' if f4['post_survival'] > 0 else 'FAIL'}"
              f" | gamma_post={f4['gamma_post'] if f4['gamma_post'] is None else round(f4['gamma_post'],3)}")
    print("  P-DOSE (D2 >= D4 per carry, drift 0.01):")
    for nm, a, b in (("WARM", w2, w4), ("COLD", c2, c4), ("FROZEN", f2, f4)):
        if a and b:
            print(f"    {nm:<7} D2 pSurv={a['post_survival']:.3f} g_post={a['gamma_post'] if a['gamma_post'] is None else round(a['gamma_post'],3)}"
                  f" | D4 pSurv={b['post_survival']:.3f} g_post={b['gamma_post'] if b['gamma_post'] is None else round(b['gamma_post'],3)}"
                  f" -> {'monotone' if a['post_survival'] >= b['post_survival'] else 'NON-MONOTONE'}")
    print("  P-BUDGET-CONFOUND (median T7 budget_at_switch, drift 0.01):")
    for nm, a in (("WARM", w4), ("COLD", c4), ("FROZEN", f4)):
        if a:
            print(f"    {nm:<7} budget_at_switch={a['budget_at_switch_med']:.3f} pre_L={a['pre_L']:.1f}"
                  f" pre_span={a['pre_span']:.2f}")
    # P-COVERAGE-PREDICTS: per-seed, among runs that REACHED the switch (the instrument exists there)
    sub = [r for r in runs if r["hand"] == "NONE" and r["carry"] == "WARM" and r["dist"] == 4
           and abs(r["drift"] - PD) < 1e-12 and r["reached_switch"] and r["INSTR_pair_cover"] is not None]
    if len(sub) >= 3:
        xs = [r["INSTR_pair_cover"] for r in sub]
        ys = [1.0 if r["post_survival"] else 0.0 for r in sub]
        r_pb = pearson(xs, ys)
        z = [y for x, y in zip(xs, ys) if x == 0]
        nz = [y for x, y in zip(xs, ys) if x > 0]
        print(f"  P-COVERAGE-PREDICTS (diagnostic, drift 0.01 D=4 WARM, n={len(sub)} reached-switch seeds;"
              f" seeds that died before the switch are EXCLUDED and reported as a bias):")
        print(f"    point-biserial r(pair_cover, post_survival) = {r_pb if r_pb is None else round(r_pb,3)}")
        print(f"    pair_cover==0: n={len(z)} pSurv={(sum(z)/len(z)) if z else float('nan'):.3f}"
              f" | pair_cover>0: n={len(nz)} pSurv={(sum(nz)/len(nz)) if nz else float('nan'):.3f}")
        ac = sum(1 for r in sub if r["INSTR_any_couple"])
        print(f"    INSTR any-op-couples-p' at the switch: {ac}/{len(sub)}")

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "v134_invariant_transfer_probe.json"), "w", encoding="utf-8") as f:
        json.dump({"runs": runs, "aggregate": rows, "break_even": BREAK_EVEN,
                   "oracle_ceiling": ORACLE_CEILING, "handed_ub_gamma": HANDED_UB_GAMMA,
                   "rent_unit": RENT_UNIT, "rent_held_rung": RENT_HELD,
                   "switch_at": SWITCH_AT, "d_ladder": D_LADDER, "primary_D": PRIMARY_D,
                   "primary_K": PRIMARY_K, "carry_modes": CARRY_MODES}, f, indent=2)
    print("\nwrote v134_invariant_transfer_probe.json")



if __name__ == "__main__":
    main()
