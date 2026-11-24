# TUF-E Derivation Prompt Pack v2.0 (EN · frozen seeds · self-contained)
# 2026-11-24 · 供 V.C. Tran 用国外前沿大模型复现推导 · v1.0 Part 3 之升级版
# How to run: P1→P2→P3→P4 顺序；每个 prompt 开新会话；temperature=0；人工审阅门=Tran本人
# 回传物：四个输出的原文+模型自述的失败点

---

## P1 — Derive the Principle (逆问题)
**Context pack (paste verbatim):**
- Three civilizations independently built cyclic time codes: Chinese sexagenary cycle (lcm 10,12 = 60, coprime CRT self-check), Maya base-20, Mesopotamia base-60. Divisor counts: 10→4, 12→6, 20→6, 60→12. All four are local optima of divisor density per symbol cost.
- Yijing: 64 binary trigram-pairs; closes under flip (错) and invert (综) to a 12-element group; 64 configs = 16 orbits.
- Lo Shu 3×3 magic square: all 8 solutions = one D4 symmetry orbit.
**Task:** These are projections of an unknown rule onto human media (fingers, knots, bone). Formulate the optimization problem P whose solution class contains all three. P must include an explicit channel-cost term (the physical actuator: finger/notation/burning) — a pure-math objective alone cannot explain why Maya pays for 20 while China pays for 10.
**Output contract:** (1) formal statement of P; (2) identification of each cost term with a physical channel; (3) one prediction P makes about a fourth, unseen civilization; (4) what evidence would falsify P.
**Acceptance:** P must have fewer free parameters than the three data points it explains.

## P2 — Derive the Architecture (从原理到三层栈)
**Task:** An agent must act through a low-bandwidth lossy channel (latency 100× spread: contact events at 1 ms, planning at 1 s). Derive — do not assume — the minimal agent architecture as the solution of P1's optimization. Show that any architecture lacking compiled reflex/skill layers pays a quantifiable cost in bandwidth, latency, or error rate.
**Output contract:** (1) derivation chain, each step forced by a named failure mode (latency / data economics / correctness / drift); (2) the dual-valve rule (crystallize on verified success, dissolve on verified obsolescence) derived as optimality, not aesthetics; (3) the cost of violating each step, quantified; (4) state what would change your mind.
**Acceptance:** no biological analogy may appear as a premise — biology may only appear as corroboration.

## P3 — Design the Protocol (灵巧手指令协议)
**Task:** Design a layered command protocol for a dexterous hand (underactuated, fewer motors than DoF): L0 semantic intent / L1 grasp-taxonomy+params / L2 finger-level / L3 joint trajectory. Requirements: (a) cross-layer algebraic checksums in the style of CRT self-checking (a corrupted L1 field must be detectable at L2/L3 wire-check); (b) exposure-layer adaptation: one interface serves operators of different bandwidth ( ℓ* = argmin bandwidth s.t. task distortion ≤ ε_environment ); (c) versioning + provenance per compiled skill.
**Output contract:** (1) JSON schema per layer + checksum construction; (2) validation matrix (every interactive element: expected behavior / test / evidence); (3) corruption-injection test plan (bit flips, field swaps, stale versions); (4) bandwidth accounting: bytes on the wire vs plain JSON equivalent.
**Acceptance:** the corruption-injection plan must name which corruptions are detectable, which are correctable, which escape — honesty about the escape set is mandatory.

## P4 — Red Team (攻击P3)
**Task:** Attack the P3 protocol. Find corruption classes its checksum misses; find environments where the exposure-layer adaptation picks the wrong layer; estimate the protocol's overhead vs its error-detection value at realistic bit-error rates.
**Output contract:** (1) attack list ranked by severity; (2) for each: fix, or honest acceptance with residual-risk statement; (3) overall verdict: build / revise / abandon — with numbers.
**Acceptance:** an "abandon" verdict correctly argued is a successful run. We publish losses.

---
*Frozen-seed discipline: these are starting conditions, not oracles. Every output must pass its acceptance gates. Honesty clause (verbatim in every prompt): "State what would change your mind. Publish negative results."*
