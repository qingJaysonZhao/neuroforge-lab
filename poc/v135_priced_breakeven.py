"""
v135 PRICED BREAK-EVEN -- the ER_paid / vs433 columns printed by the probe are STALE under storage rent.

er(q,g) = -1.0 + q*(3g - 0.3) hardcodes the unconditional rent DECAY = 1.0 and the per-action cost ACT_COST = 0.3;
it does NOT contain the v135 storage rent. Likewise BREAK_EVEN = 1.3/3 = 0.4333 is the q=1 rent-free break-even.
So a priced arm printing "OVER" has not been shown to be self-sustaining. This script recomputes both quantities
from the recorded per-arm averages, with the rent included:

    income/step  = GAIN * q * g                       (GAIN = 3.0, one successful action pays 3.0)
    cost/step    = DECAY + ACT_COST*q + RENT_UNIT*rung*units
    priced ER    = income - cost
    priced break-even gamma* = (DECAY + ACT_COST*q + rent) / (GAIN*q)

An arm is self-sustaining iff priced ER > 0, equivalently gamma_paid > gamma*.
Everything read here comes from the committed json; no new runs, no constant moved.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DECAY, GAIN, ACT_COST = 1.0, 3.0, 0.3
RENT_UNIT = ACT_COST / 40.0


def main():
    with open(os.path.join(HERE, "v135_storage_pricing_probe.json"), "r", encoding="utf-8") as f:
        rows = json.load(f)["aggregate"]
    hdr = (f"{'comp':<6}{'conf':<6}{'K':<3}{'rent':<6}{'drift':<7}{'surv':<7}{'q_paid':<8}{'gamma':<8}"
           f"{'units':<7}{'rent/st':<9}{'cost/st':<9}{'incom/st':<10}{'ER_priced':<11}{'gamma*':<8}{'verdict':<12}")
    print(hdr)
    print("-" * len(hdr))
    for r in sorted(rows, key=lambda x: (x["comp_mode"], x["conf_mode"], x["rung_name"], x["drift"])):
        q = r["q_paid"]
        g = r["gamma_paid"]
        units = r["INSTR_held_units"]
        rent = r["INSTR_rent_paid"] or 0.0
        if q is None or g is None or units is None:
            print(f"{r['comp_mode']:<6}{r['conf_mode']:<6}{r['K']:<3}{r['rung_name']:<6}{r['drift']:<7}"
                  f"{r['survival']:<7.3f}  (no paid actions)")
            continue
        cost = DECAY + ACT_COST * q + rent
        income = GAIN * q * g
        er = income - cost
        gstar = cost / (GAIN * q)
        verdict = "SELF-SUSTAIN" if er > 0 else "NET-NEGATIVE"
        print(f"{r['comp_mode']:<6}{r['conf_mode']:<6}{r['K']:<3}{r['rung_name']:<6}{r['drift']:<7}"
              f"{r['survival']:<7.3f}{q:<8.3f}{g:<8.3f}{units:<7.1f}{rent:<9.4f}{cost:<9.4f}"
              f"{income:<10.4f}{er:<+11.4f}{gstar:<8.4f}{verdict:<12}")


if __name__ == "__main__":
    main()
