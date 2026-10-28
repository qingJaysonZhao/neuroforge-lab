"""
v134 K-REGRESSION: the NOSWITCH anchor (CARRY=WARM x D=0) must reproduce the COMMITTED v135 json
(PREDGUS x PAIR x PERS x K=5 x rung P1) PER SEED, PER FIELD.

The comparison key contains EVERY swept factor of both studies (the v133 script bug: omitting conf_mode
and K produced 119 false mismatches). Fields that exist only in v134 (jump bookkeeping) are listed
explicitly and excluded; anything else missing on either side is reported.
Reads only the two committed json files. No rng, no re-run.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

V134_ONLY = {
    "carry", "dist", "hand", "switch_at", "reached_switch", "carry_wiped", "post_survival", "pre_rate",
    "post_act", "post_succ", "gamma_post", "t1_num", "t1_den", "reuse_ratio", "t1b_num", "t1b_den",
    "reuse_w2_ratio", "recovery_lag", "recovery_lag_80", "post_wh", "budget_at_switch",
    "pre_L", "pre_span", "pre_distinct", "pre_wh", "INSTR_any_couple", "INSTR_pair_cover",
}


def key(r):
    # every factor that could distinguish two runs of either study
    return (r["world"], r["W"], r["drift"], r["seed"], r["combine"], r["comp_mode"], r["ret"],
            r["conf_mode"], r["K"], r["rung_name"])


def main():
    with open(os.path.join(HERE, "v134_invariant_transfer_probe.json"), encoding="utf-8") as f:
        a = json.load(f)["runs"]
    with open(os.path.join(HERE, "v135_storage_pricing_probe.json"), encoding="utf-8") as f:
        b = json.load(f)["runs"]

    # v134 anchor arm: no hand, WARM, D=0, rent rung P1, PAIR, PERS, K=5
    A = {}
    for r in a:
        if r["hand"] == "NONE" and r["carry"] == "WARM" and r["dist"] == 0 and r["rung_name"] == "P1" \
                and r["comp_mode"] == "PAIR" and r["conf_mode"] == "PERS" and r["K"] == 5:
            A[key(r)] = r
    # v135 primary arm
    B = {}
    for r in b:
        if r["comp_mode"] == "PAIR" and r["conf_mode"] == "PERS" and r["K"] == 5 and r["rung_name"] == "P1":
            B[key(r)] = r

    print(f"v134 anchor runs (WARM x D0 x P1)   : {len(A)}")
    print(f"v135 committed runs (PAIR PERS K5 P1): {len(B)}")
    only_a = set(A) - set(B)
    only_b = set(B) - set(A)
    print(f"keys only in v134: {len(only_a)}   keys only in v135: {len(only_b)}")
    if only_a:
        print("  e.g.", sorted(only_a)[:3])
    if only_b:
        print("  e.g.", sorted(only_b)[:3])

    mism = 0
    nfield = 0
    nrun = 0
    float_tol = 0.0          # exact equality demanded; floats are printed at full repr in json
    examples = []
    for k in sorted(set(A) & set(B)):
        ra, rb = A[k], B[k]
        nrun += 1
        fields = (set(rb) - V134_ONLY)          # score every v135 field
        missing_in_a = set(rb) - set(ra)
        if missing_in_a:
            mism += len(missing_in_a)
            examples.append((k, "MISSING_IN_V134", sorted(missing_in_a)[:4], None, None))
        for f in sorted(fields):
            if f not in ra:
                continue
            va, vb = ra[f], rb[f]
            nfield += 1
            if isinstance(vb, float) and isinstance(va, float):
                same = abs(va - vb) <= float_tol
            else:
                same = va == vb
            if not same:
                mism += 1
                if len(examples) < 12:
                    examples.append((k, f, vb, va, None))
    for e in examples:
        print("  MISMATCH", e[0], e[1], "v135=", e[2], "v134=", e[3])
    print(f"\nTOTAL runs={nrun} fields={nfield} mismatches={mism}")
    print("VERDICT:", "P-REGRESSION PASS (bit-identical to the committed v135 primary arm)"
          if (mism == 0 and not only_a and not only_b and nrun == len(B) == 120)
          else "P-REGRESSION FAIL -- see above")


if __name__ == "__main__":
    main()
