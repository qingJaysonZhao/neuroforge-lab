"""
v135 K-REGRESSION CHECK -- do the FREE (rung 0) arms reproduce the COMMITTED v133 json per-seed, per-field?

Why this file exists: the first attempt at the v133-vs-v132 regression comparison reported 119 FALSE mismatches
because the comparison key omitted conf_mode and K, so every PREDGUS/PAIR run collided into one bucket and the
last-written arm was compared against the wrong baseline. Lesson (also written into the v135 prereg guards):
THE COMPARISON KEY MUST INCLUDE EVERY SWEPT FACTOR. Here the key is
    (combine, comp_mode, conf_mode, K, drift, seed)
and the two FREE arms are matched to v133 arms of identical (combine, comp_mode, conf_mode, K).

Bonus check: v135 runs ORACLE x OFF x INST x K=5, v133 ran ORACLE x OFF x INST x K=1. ORACLE ignores comp_mode
path and conf_ref entirely, and the window maintenance consumes NO rng, so K must be behaviourally irrelevant
there. If these two agree per-seed, that is independent evidence that the window code is rng-neutral.

Fields compared: every key present in BOTH records except the v135-only additions
(rung, rung_name, INSTR_held_units, INSTR_rent_paid). Scalars must be exactly equal; lists elementwise equal.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = {"rung", "rung_name", "INSTR_held_units", "INSTR_rent_paid"}
# Fields that MEASURE the window and therefore MUST differ when K differs. Used only for the bonus arm below,
# where v135 ran K=5 and v133 ran K=1: they are excluded from the equality test and reported separately, so that
# a real behavioural difference could not hide behind them.
K_DEPENDENT = {"K", "INSTR_sens_err_pers", "INSTR_disagree_band", "confpers_end_mean"}

# v135 arm (combine, comp, conf, K)  ->  (v133 arm, extra fields to exclude)
PAIRS = [
    (("PREDGUS", "PAIR", "INST", 1), ("PREDGUS", "PAIR", "INST", 1), set()),
    (("PREDGUS", "PAIR", "PERS", 5), ("PREDGUS", "PAIR", "PERS", 5), set()),
    (("ORACLE", "OFF", "INST", 5), ("ORACLE", "OFF", "INST", 1), K_DEPENDENT),   # K must be irrelevant here
]


def load(name):
    with open(os.path.join(HERE, name), "r", encoding="utf-8") as f:
        return json.load(f)["runs"]


def key(r):
    return (r["combine"], r["comp_mode"], r["conf_mode"], r["K"], r["drift"], r["seed"])


def main():
    new = load("v135_storage_pricing_probe.json")
    old = load("v133_confirmation_inlet_probe.json")
    old_ix = {}
    for r in old:
        old_ix.setdefault(key(r), []).append(r)

    total_runs = total_fields = mism = missing = 0
    for new_arm, old_arm, extra_skip in PAIRS:
        sel = [r for r in new if r["rung"] == 0
               and (r["combine"], r["comp_mode"], r["conf_mode"], r["K"]) == new_arm]
        bad = []
        for r in sel:
            k = (old_arm[0], old_arm[1], old_arm[2], old_arm[3], r["drift"], r["seed"])
            cand = old_ix.get(k)
            if not cand:
                missing += 1
                bad.append((k, "NO v133 COUNTERPART"))
                continue
            o = cand[0]
            fields = sorted((set(r) | set(o)) - SKIP - extra_skip)
            for f in fields:
                total_fields += 1
                a, b = r.get(f, "<absent>"), o.get(f, "<absent>")
                if a != b:
                    mism += 1
                    bad.append((k, f, a, b))
            total_runs += 1
        note = f"  (excluded K-dependent measurement fields {sorted(extra_skip)})" if extra_skip else ""
        print(f"ARM v135{new_arm} FREE  vs  v133{old_arm}: runs={len(sel)} "
              f"mismatched_records={len(bad)}{note}")
        for b in bad[:20]:
            print("   MISMATCH", b)

    print(f"\nTOTAL per-seed runs compared={total_runs}  fields compared={total_fields}  "
          f"field mismatches={mism}  missing counterparts={missing}")
    print("VERDICT:", "P-REGRESSION PASS (bit-identical)" if (mism == 0 and missing == 0 and total_runs > 0)
          else "P-REGRESSION FAIL")


if __name__ == "__main__":
    main()
