"""
v134 ANALYSIS -- reads ONLY v134_invariant_transfer_probe.json (no re-run, no rng).
Produces the numbers quoted in poc/audit/2026-10-29_v134_invariant-transfer.md:
  A. how the jump kills: death timing relative to SWITCH_AT
  B. recovery: never-recovered fraction, censored lag, lag-to-80%
  C. the priced handicap direction (post-switch rent WARM vs COLD)
  D. literal answer vs modular basis at the switch (INSTR, truth-reading, quarantined)
  E. instrument-arm behaviour (LIT-HAND defect, MOD-HAND jump-insensitivity)
  F. reuse by carry mode and distance (the invariant measure)
"""
import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
SW = 2000
RENT_UNIT = 0.0075


def sel(runs, drift, dist, carry="WARM", hand="NONE"):
    return [r for r in runs if abs(r["drift"] - drift) < 1e-12 and r["dist"] == dist
            and r["carry"] == carry and r["hand"] == hand]


def med(vs):
    vs = [v for v in vs if v is not None]
    return statistics.median(vs) if vs else None


def main():
    with open(os.path.join(HERE, "v134_invariant_transfer_probe.json"), encoding="utf-8") as f:
        J = json.load(f)
    runs = J["runs"]

    print("=" * 100)
    print("A. HOW THE JUMP KILLS -- death step relative to SWITCH_AT=2000 (drift 0.01, n=40 per arm)")
    print(f"{'arm':<22}{'died<SW':<9}{'0-100':<8}{'100-500':<9}{'500-1000':<10}{'1000+':<8}{'alive':<8}")
    for dist in (0, 2, 4):
        for carry in ("WARM", "COLD", "FROZEN"):
            rs = sel(runs, 0.01, dist, carry)
            if not rs:
                continue
            b = [0] * 6
            for r in rs:
                if r["alive"]:
                    b[5] += 1
                elif r["steps"] <= SW:
                    b[0] += 1
                else:
                    d = r["steps"] - SW
                    b[1 if d <= 100 else (2 if d <= 500 else (3 if d <= 1000 else 4))] += 1
            n = len(rs)
            print(f"D={dist} {carry:<17}" + "".join(f"{x/n:<9.3f}" if i == 0 else f"{x/n:<8.3f}"
                                                   for i, x in enumerate(b[:5])) + f"{b[5]/n:<8.3f}")

    print("\n" + "=" * 100)
    print("B. RECOVERY (only runs that REACHED the switch are eligible; 'never' = no post-switch success)")
    print(f"{'arm':<22}{'reached':<9}{'never%':<9}{'lag_med':<9}{'lag_mean':<10}{'lag80_med':<11}{'g_post':<8}")
    for dist in (0, 2, 4):
        for carry in ("WARM", "COLD", "FROZEN"):
            rs = [r for r in sel(runs, 0.01, dist, carry) if r["reached_switch"]]
            if not rs:
                continue
            n = len(rs)
            never = sum(1 for r in rs if r["recovery_lag"] is None)
            lags = [r["recovery_lag"] for r in rs if r["recovery_lag"] is not None]
            l80 = [r["recovery_lag_80"] for r in rs if r["recovery_lag_80"] is not None]
            ps = sum(r["post_succ"] for r in rs)
            pa = sum(r["post_act"] for r in rs)
            print(f"D={dist} {carry:<17}{n:<9}{never/n:<9.3f}{med(lags) if lags else -1:<9.0f}"
                  f"{(sum(lags)/len(lags)) if lags else -1:<10.1f}"
                  f"{(med(l80) if l80 else -1):<11.0f}{(ps/pa if pa else -1):<8.3f}")

    print("\n" + "=" * 100)
    print("C. PRICED HANDICAP DIRECTION -- post-switch library size => storage rent per step (drift 0.01)")
    print("   growth_ops blocks 4..7 are the post-switch block-end |L| (switch at t=2000 = block 4 start)")
    for dist in (0, 2, 4):
        for carry in ("WARM", "COLD", "FROZEN"):
            rs = sel(runs, 0.01, dist, carry)
            if not rs:
                continue
            n = len(rs)
            post = [sum(r["growth_ops"][i] for r in rs) / n for i in (4, 5, 6, 7)]
            span = [sum(r["growth_span"][i] for r in rs) / n for i in (4, 5, 6, 7)]
            rent = [RENT_UNIT * (v + 5) for v in post]
            print(f"D={dist} {carry:<8}|L| post=" + " ".join(f"{v:5.1f}" for v in post)
                  + "  span post=" + " ".join(f"{v:4.1f}" for v in span)
                  + "  rent/step=" + " ".join(f"{v:.3f}" for v in rent))
    print("   => COLD carries ~6 units post-switch, WARM ~20-40: the rent handicap FAVOURS COLD,")
    print("      so a WARM > COLD survival gap is measured AGAINST WARM's own higher price.")

    print("\n" + "=" * 100)
    print("D. LITERAL ANSWER vs MODULAR BASIS AT THE SWITCH (INSTRUMENT: reads the truth p', quarantined)")
    print(f"{'arm':<22}{'any_couple':<12}{'pc=0':<8}{'0<pc<=.5':<10}{'pc>.5':<9}{'pc_mean':<9}{'pSurv|pc=0':<12}"
          f"{'pSurv|pc>0':<11}")
    for dist in (2, 4):
        for carry, hand in (("WARM", "NONE"), ("COLD", "NONE"), ("FROZEN", "NONE"),
                            ("WARM", "LIT"), ("WARM", "MOD")):
            rs = [r for r in sel(runs, 0.01, dist, carry, hand) if r["reached_switch"]]
            if not rs:
                continue
            n = len(rs)
            ac = sum(1 for r in rs if r["INSTR_any_couple"])
            z = [r for r in rs if r["INSTR_pair_cover"] == 0]
            lo = [r for r in rs if 0 < r["INSTR_pair_cover"] <= 0.5]
            hi = [r for r in rs if r["INSTR_pair_cover"] > 0.5]
            nz = [r for r in rs if r["INSTR_pair_cover"] > 0]

            def sv(g):
                return (sum(1 for r in g if r["post_survival"]) / len(g)) if g else None
            tag = f"D={dist} {(hand + '-' if hand != 'NONE' else '') + carry:<15}"
            print(f"{tag:<22}{ac/n:<12.3f}{len(z)/n:<8.3f}{len(lo)/n:<10.3f}{len(hi)/n:<9.3f}"
                  f"{sum(r['INSTR_pair_cover'] for r in rs)/n:<9.3f}"
                  f"{(sv(z) if z else float('nan')):<12.3f}{(sv(nz) if nz else float('nan')):<11.3f}")
    print("   any_couple = a STORED op literally couples p' at the switch (the 'answer table' reading).")
    print("   pair_cover = how many of the 6 weight-2 subsets of p' are in the library (the modular reading).")

    print("\n" + "=" * 100)
    print("E. INSTRUMENT ARMS -- did LIT-HAND behave as a literal table? did MOD-HAND behave as a basis?")
    for drift in (0.0, 0.01, 0.02):
        line = []

        def snap(rs):
            got = [r for r in rs if r["pre_L"] is not None]
            if not got:
                return None
            n = len(got)
            pcs = [r["INSTR_pair_cover"] for r in got if r["INSTR_pair_cover"] is not None]
            return (f"pSurv={sum(1 for r in rs if r['post_survival'])/len(rs):.3f}"
                    f" preL={sum(r['pre_L'] for r in got)/n:.1f}"
                    f" preSpan={sum(r['pre_span'] for r in got)/n:.2f}"
                    f" pc={(sum(pcs)/len(pcs)) if pcs else float('nan'):.3f}"
                    f" (n_reached={n})")
        for hand in ("LIT", "MOD"):
            for dist in (2, 4):
                rs = sel(runs, drift, dist, "WARM", hand)
                if rs:
                    line.append(f"{hand} D{dist}: " + (snap(rs) or "-"))
        warm = []
        for dist in (2, 4):
            rs = sel(runs, drift, dist, "WARM", "NONE")
            if rs:
                warm.append(f"WARM D{dist}: " + (snap(rs) or "-"))
        print(f" drift={drift}")
        for s in line + warm:
            print("   " + s)

    print("\n" + "=" * 100)
    print("H. DISSOCIATION -- does the LITERAL answer or the MODULAR basis predict transfer?")
    print("   reached-switch runs, drift 0.01, D=4; INSTR reads the truth (quarantined)")
    print(f"{'arm':<18}{'n':<5}{'pSurv|any_couple=T':<20}{'pSurv|any_couple=F':<20}"
          f"{'pSurv|pc>0.5':<15}{'pSurv|pc<=0.5':<15}")
    for carry, hand in (("WARM", "NONE"), ("COLD", "NONE"), ("FROZEN", "NONE"),
                        ("WARM", "LIT"), ("WARM", "MOD")):
        rs = [r for r in sel(runs, 0.01, 4, carry, hand) if r["reached_switch"]]
        if not rs:
            continue

        def sv(g):
            return (sum(1 for r in g if r["post_survival"]) / len(g)) if g else None
        T = [r for r in rs if r["INSTR_any_couple"]]
        F = [r for r in rs if not r["INSTR_any_couple"]]
        hi = [r for r in rs if r["INSTR_pair_cover"] > 0.5]
        lo = [r for r in rs if r["INSTR_pair_cover"] <= 0.5]
        f2 = lambda v: "  n/a " if v is None else f"{v:.3f}"
        tag = f"{(hand + '-' if hand != 'NONE' else '') + carry}"
        print(f"{tag:<18}{len(rs):<5}{f2(sv(T)) + f' (n={len(T)})':<20}"
              f"{f2(sv(F)) + f' (n={len(F)})':<20}{f2(sv(hi)) + f' (n={len(hi)})':<15}"
              f"{f2(sv(lo)) + f' (n={len(lo)})':<15}")

    print("\n" + "=" * 100)
    print("F. REUSE (T1) BY CARRY MODE AND DISTANCE, drift 0.01 -- pooled over runs")
    print(f"{'arm':<22}{'reuse':<9}{'reuseW2':<9}{'t1_den':<9}{'post_w2':<9}{'post_w3+':<10}")
    for dist in (0, 2, 4):
        for carry in ("WARM", "COLD", "FROZEN"):
            rs = sel(runs, 0.01, dist, carry)
            if not rs:
                continue
            num = sum(r["t1_num"] for r in rs)
            den = sum(r["t1_den"] for r in rs)
            n2 = sum(r["t1b_num"] for r in rs)
            d2 = sum(r["t1b_den"] for r in rs)
            pw = [sum(r["post_wh"][i] for r in rs) for i in range(5)]
            tot = sum(pw) or 1
            print(f"D={dist} {carry:<17}{(num/den if den else -1):<9.3f}{(n2/d2 if d2 else -1):<9.3f}"
                  f"{den:<9}{pw[2]/tot:<9.3f}{(pw[3]+pw[4])/tot:<10.3f}")
    for hand in ("LIT", "MOD"):
        for dist in (2, 4):
            rs = sel(runs, 0.01, dist, "WARM", hand)
            if not rs:
                continue
            num = sum(r["t1_num"] for r in rs)
            den = sum(r["t1_den"] for r in rs)
            n2 = sum(r["t1b_num"] for r in rs)
            d2 = sum(r["t1b_den"] for r in rs)
            print(f"D={dist} {hand + '-HAND':<17}{(num/den if den else -1):<9.3f}{(n2/d2 if d2 else -1):<9.3f}"
                  f"{den:<9}")

    print("\n" + "=" * 100)
    print("G. THE JUMP TAX -- survival lost by jumping, per carry mode (all drifts, over all 40 seeds)")
    for drift in (0.0, 0.01, 0.02):
        base = sel(runs, drift, 0, "WARM")
        b = (sum(1 for r in base if r["alive"]) / len(base)) if base else None
        out = [f"drift={drift} NOSWITCH survival={b:.3f}"]
        for carry in ("WARM", "COLD", "FROZEN"):
            for dist in (2, 4):
                rs = sel(runs, drift, dist, carry)
                if rs:
                    s = sum(1 for r in rs if r["alive"]) / len(rs)
                    out.append(f"{carry}D{dist}={s:.3f}({s-b:+.3f})")
        for hand in ("LIT", "MOD"):
            for dist in (2, 4):
                rs = sel(runs, drift, dist, "WARM", hand)
                if rs:
                    s = sum(1 for r in rs if r["alive"]) / len(rs)
                    out.append(f"INSTR-{hand}D{dist}={s:.3f}")
        print("  " + "  ".join(out))

    print("\n" + "=" * 100)
    print("I. PAIRED SIGNIFICANCE -- WARM vs COLD / WARM vs FROZEN on post_survival, paired by seed")
    print("   McNemar exact (two-sided binomial on the discordant pairs); all 40 seeds per cell")
    from math import comb
    for drift in (0.0, 0.01, 0.02):
        for dist in (2, 4):
            for other in ("COLD", "FROZEN"):
                A = {r["seed"]: r for r in sel(runs, drift, dist, "WARM")}
                B = {r["seed"]: r for r in sel(runs, drift, dist, other)}
                seeds = sorted(set(A) & set(B))
                b = sum(1 for s in seeds if A[s]["post_survival"] and not B[s]["post_survival"])
                c = sum(1 for s in seeds if B[s]["post_survival"] and not A[s]["post_survival"])
                n = b + c
                if n == 0:
                    p = 1.0
                else:
                    k = min(b, c)
                    tail = sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n)
                    p = min(1.0, 2 * tail)
                print(f"  drift={drift:<5} D={dist} WARM vs {other:<7} discordant WARM-only={b} "
                      f"{other}-only={c}  McNemar exact p={p:.4f}")

    print("\n" + "=" * 100)
    print("J. SPECIALIZATION TRAP (post-hoc, THIRD-TIER: not preregistered, hypothesis only)")
    print("   does a STATIC world make the library less jump-robust than a mildly drifting one?")
    print(f"{'drift':<8}{'WARM D4 pc':<13}{'WARM D4 pSurv':<15}{'WARM D4 pSvR':<14}{'COLD D4 pSurv':<15}"
          f"{'MOD D4 pc':<12}{'MOD D4 pSurv':<13}")
    for drift in (0.0, 0.01, 0.02):
        w = sel(runs, drift, 4, "WARM")
        c = sel(runs, drift, 4, "COLD")
        m = sel(runs, drift, 4, "WARM", "MOD")

        def m_(rs, f):
            vs = [r[f] for r in rs if r[f] is not None]
            return (sum(vs) / len(vs)) if vs else float("nan")
        reached = [r for r in w if r["reached_switch"]]
        psvr = (sum(1 for r in reached if r["post_survival"]) / len(reached)) if reached else float("nan")
        print(f"{drift:<8}{m_(w,'INSTR_pair_cover'):<13.3f}"
              f"{sum(1 for r in w if r['post_survival'])/len(w):<15.3f}{psvr:<14.3f}"
              f"{sum(1 for r in c if r['post_survival'])/len(c):<15.3f}"
              f"{m_(m,'INSTR_pair_cover'):<12.3f}{sum(1 for r in m if r['post_survival'])/len(m):<13.3f}")
    print("   pc = pair_cover of the disjoint p' measured at the switch (INSTRUMENT, reads the truth).")


if __name__ == "__main__":
    main()
