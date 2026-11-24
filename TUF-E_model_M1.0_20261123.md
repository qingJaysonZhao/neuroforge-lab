# TUF-E Model
**Fingerprint: TUF-E-M1.0 · 2026-11-23 · External edition · 注释中英对照**
Scope note: design intent and derivation seeds; deeper implementation archives are shared on a milestone basis as collaboration deepens. Pre-registration and honest status are stated inside — we publish losses alongside results.

---

## Part 1 · The Model (EN)

### The story
The industry runs one experiment: scale. Bigger models, more data, more GPUs — knowledge frozen at the end of training, everyone else renting.

A public anomaly nobody organized: myoelectric prosthetic hands — worn by human amputees — work, in production, today. A 60-year-old amputee masters a 19-DoF bionic hand in half a day; training data: minutes. Dexterous hands on robots, carrying the world's best models, struggle: simulation 99% success, real hardware 60%; decision latency 1 s vs human 0.1 s; billions of simulation steps per task; a change of object material collapses the policy.

The lesson hides in plain sight. The human body already runs the architecture that makes skill cheap: reflexes compiled into muscle, habits crystallized by repetition, consciousness reserved for whatever is new. An infant spends a year learning to grasp; afterwards, grasping never costs a thought. A device plugged into that architecture inherits it. A robot built around one monolithic network does not. The field keeps spending billions making the network bigger. The missing engineering is the architecture the child already has — layered, compiled, habit-forming.

### The architecture
Three layers, each with its own timescale and representation regime:

| Layer | Biological analogue | Function | Representation | Timescale |
|---|---|---|---|---|
| **L0 Reflex** | spinal cord / muscle spindle | compliance, force limits, safety cutoffs | deterministic control code | 1 ms |
| **L1 Skill** | cerebellum / basal ganglia | habitual action primitives, ready to call | compiled instruction set | 10–100 ms |
| **L2 Deliberation** | prefrontal cortex | intent, planning, novel problem solving | learned model, expensive | 0.1–1 s |

Derivation chain — each step forced by a failure evidence:

1. *Latency forces the split.* Contact events resolve in milliseconds. Whatever must act at contact speed must be deterministic code. L0 is a physics deadline, not a preference.
2. *Data economics force crystallization.* Any solution an agent reaches repeatedly must be promoted out of expensive deliberation into L1 — a compiled, callable instruction set.
3. *Correctness forces the gate.* A wrongly promoted skill fires automatically and poisons behavior. Crystallization is therefore gated by cross-validation: replay, perturbation, independent-checker quorum. Crystallization without verification is hallucination transmission.
4. *Drift forces the eraser.* Environments drift; obsolete skills must dissolve, not accumulate. **What gets used grows stronger; what goes unused dissolves.** The dual valve — crystallize on verified success, dissolve on verified obsolescence — keeps the skill library alive.
5. *Physics must talk back.* Safety envelopes, joint limits, energy budgets — engineering constraints already written in code — must be compiled INTO the agent's viability conditions, not checked after the act. Everyone builds "AI writes code." Almost nobody builds "code constrains AI." The second direction is where this model works.

The two translation directions, precisely:
- **Forward (learned → executable):** validated behavior promoted into deterministic L0/L1 form, semantics preserved, verified by replay-and-perturb consensus.
- **Reverse (constraint → condition):** deterministic engineering constraints compiled into the agent's viability boundary — the agent's drive is to remain functional, so boundaries expressed as survival conditions are never forgotten.

### Status honesty
Framework v1.0 is published and externally reviewed; it does not beat baselines yet. All validation experiments are pre-registered with win/lose criteria published in advance. Negative results are data. In a field full of benchmark-chasing, integrity is a differentiator we intend to keep.

---

## Part 2 · Work Directions (derivation seeds)

Each direction is scoped for a competent AI agent or a small team. Acceptance gates stated; pre-registration is our standing rule.

**D1 — Three-layer stack on an open hand simulator.** L0/L1/L2 separation on an open-source dexterous hand (MuJoCo / IsaacGym, 9–20 DoF). Deliverable: contact-speed reflexes in deterministic code; deliberative layer above; measured latency budget per layer. Acceptance: 1 ms L0 budget met in hardware-in-the-loop replay; deliberation invoked only on novel events.

**D2 — Crystallization protocol.** Define the promotion gate: replay distribution, perturbation suite, independent-checker quorum, freeze format (versioned instruction set with provenance). Demonstrate on one repeated task (peg transfer). Acceptance: crystallized skill replays ≥1000 cycles with bounded error; reloadable after agent restart.

**D3 — Reverse-translation envelope.** Compile a written safety specification (force / temperature / joint limits) into viability boundary conditions inside an agent's decision loop. Acceptance: agent provably cannot emit an out-of-envelope action, under adversarial probing, at zero deliberation-time overhead.

**D4 — Forgetting-curve measurement.** Quantify the dual valve: inject controlled drift; measure dissolution against a frozen-library baseline. Acceptance: drift adaptation measurably faster with dissolution, at no cost to retained competence.

**Application domains:** dexterous manipulation (hardware); protein-structure-driven constraint design, where a learned model's outputs must survive translation into wet-lab protocols — the same translation seam, different substrate.

---

## Part 3 · Standard Prompts (frozen seeds)

Self-contained derivation seeds for English-speaking AI agents. Starting conditions, not oracles: every output must pass the Part 1 verification gates.

**Seed 1 — Architecture derivation.**
> You are a control-systems theorist. From first principles (latency budgets, data economics, failure isolation), derive the minimal layered architecture for a 20-degree-of-freedom dexterous manipulator whose deliberative layer runs at 1 Hz while contact events resolve at 1 kHz. For each layer, state what MUST live there and what must NEVER live there, with the forcing argument. Output: one-page architecture memo with responsibility matrix.

**Seed 2 — Crystallization gate design.**
> You are a verification engineer. Design a promotion protocol converting a repeatedly successful learned behavior into a frozen, callable instruction set, such that a wrong promotion cannot pass undetected. Specify replay distribution, perturbation suite, independent-checker quorum, freeze format, and dissipation rule for obsolete skills. Output: protocol document with acceptance gates.

**Seed 3 — Reverse translation.**
> You are a safety systems engineer. Given a written engineering constraint set (joint limits, force ceilings, thermal bounds), design a compilation path making these constraints part of an autonomous agent's viability conditions — conditions the agent treats as survival requirements, not external rules checked after acting. Demonstrate on one written specification. Output: compiled condition set plus adversarial test plan.

**Seed 4 — Forgetting as mechanism.**
> You are a learning-systems researcher. Design an experiment measuring whether designed forgetting (dissolution of unused or failed skills) improves adaptation to environment drift versus a frozen-library baseline, at equal library size. Specify drift model, metrics, pre-registered win/lose criteria. Output: pre-registration document.

**Seed 5 — The honest audit.**
> You are a hostile reviewer of the claim: "Layered architectures plus regulated crystallization beat monolithic learned policies for real-world dexterity." List the five strongest objections, the evidence that would answer each, and the cheapest experiment per objection. Output: audit memo.

---

## 注释 · Annotations（中英对照）

**A1 · 定义 Definition**
中文：TUF-E Model 是一套面向电气设备智能体控制泛化的标准与算法框架。它不针对任何单一设备或单一任务而设计；它定义的是"智能体如何获得可迁移、可固化、可验证的控制能力"这一层。
EN: The TUF-E Model is a standard-and-algorithm framework for generalized control of electrical-equipment intelligent agents. It is not designed for any single device or task; it defines the layer of *how an agent acquires transferable, crystallizable, verifiable control capability*.

**A2 · 三层与双阀 The three layers and the dual valve**
中文：L0/L1/L2 的分层不是工程偏好，而是被延迟、数据经济性、正确性、环境漂移四项硬约束逼出来的必然结构。固化（crystallization）与遗忘（dissolution）是同一枚硬币的两面：反复验证成功的行为结晶成可调用的指令集；被验证过时的技能溶解。验证门是唯一的入口——未经验证的固化比不固化更有害。
EN: The L0/L1/L2 split is not an engineering preference; it is forced by four hard constraints — latency, data economics, correctness, and environment drift. Crystallization and dissolution are two faces of one coin: repeatedly verified behavior freezes into callable instruction sets; verified-obsolete skills dissolve. The verification gate is the only door in — unverified crystallization is worse than none.

**A3 · 双向翻译 The two translation directions**
中文：前向翻译把"学到的"变成"能确定性执行的"，且语义不失真（以回放+扰动+独立观察者对拍为验收）。反向翻译把工程约束编译成智能体的生存条件——约束不再是被事后检查的规则，而是智能体维持自身功能的前提。行业人人做前向（AI生成代码），反向（代码约束AI）几乎无人做，是本框架的主攻方向之一。
EN: Forward translation turns *learned* into *deterministically executable* without semantic drift (verified by replay + perturbation + independent-observer consensus). Reverse translation compiles engineering constraints into the agent's viability conditions — constraints cease to be post-hoc rules and become prerequisites of the agent remaining functional. The industry works the forward direction (AI writes code); the reverse (code constrains AI) is nearly empty, and is one of this framework's primary directions.

**A4 · 定位与边界 Positioning and boundaries**
中文：本框架按科研级标准自我要求：预注册制（胜负标准事前公开）、与发布结果同步发布失败、承认尚未超越基线。框架刻意与任何具体部署场景解耦——它是设计层，不是产品说明书；应用形态由合作方在各自场景中定义。更深层的实现档案按合作里程碑逐步共享。
EN: The framework holds itself to research-grade standards: pre-registration (win/lose criteria published in advance), losses published alongside results, and an explicit admission that baselines are not yet beaten. It is deliberately decoupled from any specific deployment — a design layer, not a product manual; application forms are defined by partners in their own scenarios. Deeper implementation archives are shared progressively, by collaboration milestone.

**A5 · 给合作方的使用说明 Notes for collaborators**
中文：第三部分的五个种子提示词是给 AI 代理的推演起点，不是答案。每个提示词的产出都必须经过第一部分的验证门才算数——让智能体自行推导，让人类把关验收，这一分工本身即是本框架方法论的示范。建议用法：选一条工作方向（D1–D4），喂入对应种子，产出文档后回到验证门对拍。
EN: The five seeds in Part 3 are starting points for AI agents, not answers. Every seed output must pass the Part 1 gates to count — letting agents derive, letting humans gate-keep: this division of labor is itself a demonstration of the framework's methodology. Suggested use: pick one direction (D1–D4), feed the corresponding seed, and return the output to the verification gates.

---

*Change log: M1.0 (2026-11-23) — external edition. Positioned as the TUF-E Model with bilingual annotations; story re-anchored on the prosthetics-vs-robotics evidence; architecture derived as L0/L1/L2 with bidirectional translation and the crystallization/forgetting dual valve; five frozen prompt seeds. Supersedes the VC one-pager v1.1 (2026-11-03).*
