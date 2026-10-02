# Chapter 4 Model Reference

Durable reference for the Chapter 4 two-phase model: what every symbol means, what it does **not**
mean, and the interpretation questions that came up while preparing the professor meetings.

Companion to `solve_chapter4.py`, `case_data.json`, and
`../chp4_models_multi_retailer_ev_battery_recycling_network_with_shapley_cost_sharing_v1.3.tex`.

**Provenance.** Consolidated 2026-09-07 from the 2026-08-11 working session. That session ended on a
network error before the notes could be saved, so this file completes it. All figures below were
re-checked against `generated/summary.json` on 2026-09-07.

**Units throughout:** volume in tons/year, variable costs in USD/ton, fixed costs and all reported
totals in thousand USD/year.

---

## 1. Symbol glossary

### 1.1 Sets

| Symbol | Meaning | Note |
|---|---|---|
| $I$ | Retailers, indexed by $i$ | 5 in the case: R1–R5 |
| $J$ | Candidate consolidation centers, indexed by $j$ | 4 candidates: NV, TN, MI, GA |
| $L$ | Candidate recovery processors, indexed by $l$ | 2: H (high-standard), L (standard) |
| $N$ | Cooperative-game players, $N=\{M\}\cup I$ | 6 players → $2^6=64$ coalitions |
| $S$ | A coalition, $S\subseteq N$ | Each $S$ gets its own MILP solve |
| $I(S)$ | Retailers inside coalition $S$, $I(S)=S\cap I$ | The Manufacturer contributes no return volume |

The Manufacturer $M$ is a player but is **not** in $I$: it has no return volume of its own. It enters
the physical model only by unlocking processor access and carrying platform cost.

### 1.2 Network parameters (given, not chosen)

| Symbol | Meaning | Unit |
|---|---|---|
| $d_i$ | Total end-of-life return volume reaching retailer $i$ | tons/yr |
| $c_i^R$ | Unit collection and initial handling cost at retailer $i$ — receiving, inspection, documentation, safe packaging, temporary storage, transport prep | USD/ton |
| $t_{ij}$ | Unit transport cost, retailer $i$ → center $j$ | USD/ton |
| $u_{jl}$ | Unit transport cost, center $j$ → processor $l$ | USD/ton |
| $f_j^C$ | Fixed cost of opening center $j$ — site, equipment, permits, safety systems, supervision | k USD/yr |
| $h_j$ | Unit handling cost at center $j$ — sorting, weighing, repackaging, inspection, batch prep | USD/ton |
| $K_j^C$ | Capacity of center $j$ | tons/yr |
| $f_l^P$ | Fixed cost of activating processor $l$ — contract setup, qualification audit, onboarding, access fee | k USD/yr |
| $p_l$ | Unit processing cost at processor $l$ | USD/ton |
| $K_l^P$ | Capacity of processor $l$ | tons/yr |
| $v_l$ | Value **per unit of recovered output** from processor $l$ — see §2 | USD/ton |
| $\rho_l$ | Recovery efficiency at processor $l$, $0<\rho_l\leq1$ | tons output / ton input |

The superscripts $C$, $P$, $R$, $G$ are **labels** (Center, Processor, Retailer, Governance), not
exponents.

Full flow path: $R_i \xrightarrow{t_{ij}} C_j \xrightarrow{u_{jl}} P_l$.

### 1.3 Stewardship / coalition-dependent parameters

These are what separate Chapter 4 from an ordinary reverse-logistics model.

| Symbol | Meaning |
|---|---|
| $\alpha(S)$ | Formal-service target: the share of returns coalition $S$ commits to route through the qualified network, $0<\alpha(S)\leq1$. See §3 |
| $D_i(S)$ | Volume retailer $i$ must formally process, $D_i(S)=\alpha(S)\,d_i$ |
| $e_l(S)\in\{0,1\}$ | Whether coalition $S$ is *permitted* to use processor $l$ — from contracts, certification, safety approval, audit, traceability capability, or Manufacturer platform access |
| $F^G(S)$ | Coalition-level fixed governance cost — shared reporting platform, traceability system, dealer training, audit, processor-contract administration, coordination |

$F^G(S)$ is a coalition-level fixed cost, **not** an external subsidy, and it can be positive even at
low volume. The Manufacturer's 500 k USD singleton cost is exactly this: the stand-alone cost of
maintaining platform readiness and processor relationships, **not** treatment cost for physical
volume.

### 1.4 Derived parameters

$$a_{ij}=c_i^R+t_{ij}+h_j \qquad\text{(upstream leg: collect + haul + handle)}$$

$$b_{jl}=u_{jl}+p_l-\rho_l v_l \qquad\text{(downstream leg, net of recovery credit)}$$

Worked example on the NV→H route: $u=40$, $p_H=410$, $\rho_H=0.90$, $v_H=330$, so
$b_{\mathrm{NV},H}=40+410-(0.90)(330)=40+410-297=\mathbf{153}$ USD per ton of returned input.

$b_{jl}$ is what lets the model trade off a costlier processor with higher recovery against a cheaper
one with lower recovery.

### 1.5 Allocation parameters (Phase II only — they never touch Phase I)

| Symbol | Meaning |
|---|---|
| $p_x$ | Baseline stewardship-responsibility share of player $x$, with $p_x\geq0$ and $\sum_{x\in N}p_x=1$. Can derive from return volume, EPR obligation, brand responsibility, regional risk, negotiated obligation, or platform control |
| $\theta$ | Weight on the Shapley component in the hybrid rule, $0\leq\theta\leq1$ |

> **Notation hazard:** $p_l$ (processor unit processing cost) and $p_x$ (player responsibility share)
> are different parameters that share a letter. Read $p_x$ as *responsibility proportion*.

### 1.6 Decision variables (what the MILP actually solves)

| Symbol | Meaning |
|---|---|
| $q_{ij}\geq0$ | Flow, retailer $i$ → center $j$. Constrained by $\sum_j q_{ij}=D_i(S)$ |
| $x_{jl}\geq0$ | Flow, center $j$ → processor $l$. Balance: $\sum_{i\in I(S)}q_{ij}=\sum_l x_{jl}$ |
| $y_j\in\{0,1\}$ | 1 if center $j$ is opened; triggers $f_j^C$ and enables $\sum_i q_{ij}\leq K_j^C y_j$ |
| $z_l\in\{0,1\}$ | 1 if processor $l$ is used; triggers $f_l^P$ and is capped by $z_l\leq e_l(S)$ |

> The $x$ in $x_{jl}$ is a flow variable. The $x$ in $\phi_x(c)$ is a generic player index. Unrelated.

### 1.7 Outputs

**$c(S)$ — optimized net stewardship cost of coalition $S$:**

$$c(S)=F^G(S)+\min\left[\sum_{i\in I(S)}\sum_{j\in J}a_{ij}q_{ij}+\sum_{j\in J}f_j^C y_j+\sum_{j\in J}\sum_{l\in L}b_{jl}x_{jl}+\sum_{l\in L}f_l^P z_l\right]$$

Five blocks: governance, upstream flow, center fixed, downstream net flow, processor fixed. "Net"
means the recovered-material credit is already deducted. $c(S)$ becomes the characteristic function
of the Phase II cost game.

**$\phi_x(c)$ — Shapley cost allocation.** Not a volume split. It is the average change in coalition
cost when $x$ joins, over all join orders. Satisfies $\sum_{x\in N}\phi_x(c)=c(N)$ — but budget
balance alone guarantees neither individual participation nor coalition stability.

**$\sigma(S;\phi)$ — core slack.** See §6.

### 1.8 The five easiest symbols to confuse

| Pair | Distinction |
|---|---|
| $d_i$ vs. $D_i(S)$ | All expected returns vs. returns that must enter the formal network |
| $e_l(S)$ vs. $z_l$ | *Permitted* to use a processor (parameter) vs. *actually* using it (variable) |
| $f_j^C$ vs. $h_j$ | Center fixed cost vs. variable handling cost |
| $p_l$ vs. $p_x$ | Processor processing cost vs. player responsibility share |
| $c(S)$ vs. $\phi_x(c)$ | Total cost of a coalition vs. the part one player is asked to pay |

**One-sentence summary for the committee:**

> The sets define who and what are available; the parameters describe volumes, costs, capacities,
> service commitments, and processor access; the Phase I variables choose facilities and flows;
> $c(S)$ records the least cost achievable by each coalition; and Phase II uses those coalition costs
> to calculate Shapley payments and test core stability.

---

## 2. What $v_l$ actually measures — and a known manuscript defect

This was re-derived from the solver's objective function rather than from the notation table, after
the table's wording was questioned.

**Conclusion:** $v_l$ is the value **per unit of recovered output**, *not* the market value of
unprocessed returned material. $\rho_l v_l$ is the realized credit per unit of **returned input**.

Derivation. Send $x_{jl}$ tons of returned input to processor $l$:

- recovered output $=\rho_l x_{jl}$
- recovery credit $=v_l(\rho_l x_{jl})=\rho_l v_l x_{jl}$
- net leg cost $=u_{jl}x_{jl}+p_l x_{jl}-\rho_l v_l x_{jl}=(u_{jl}+p_l-\rho_l v_l)\,x_{jl}$

which is exactly $b_{jl}$. This matches `solve_chapter4.py` (the objective coefficient is
`transport + processing - recovery_efficiency * base_recovery_value`) and is consistent with the
model computing recovered output as $\sum_{j,l}\rho_l x_{jl}$ — confirming $\rho_l$ is a *physical*
output ratio, not an abstract value-realization fraction.

**Why "returned material value before processing" is ambiguous.** Two readings:

- **Reading A — market price of unprocessed returns.** If a recycler would pay 330 USD/ton for
  untreated batteries, that 330 is already per ton of *input*, and the formula should be
  $b_{jl}=u_{jl}+p_l-v_l$. Multiplying by $\rho_l$ would discount an already-settled price twice.
- **Reading B — latent recoverable-material value.** Returned material does "contain" lithium,
  nickel, and cobalt value before processing, but only the successfully recovered fraction becomes a
  real credit. This reading is compatible with the current formula.

The current formula is only correct under Reading B — and even then, defining $v_l$ per unit of
recovered output is the cleaner statement.

### ⚠ Open defect (diagnosed 2026-08-11, not yet fixed)

The Chapter 4 notation table (line ~211 of the chapter `.tex`) still reads:

> `$v_l$ & Recovered-material value per processed unit at processor $l$`

"Per processed unit" suggests per unit of processed **input**, which makes the $\rho_l$ multiplication
look like a double discount. **The numbers are correct; only the definition is ambiguous.**

Prescribed fix (no numeric impact):

```latex
$v_l$ & Market value per unit of recovered output produced by processor $l$ \\
$\rho_l v_l$ & Realized recovered-material credit per unit of returned input processed at processor $l$ \\
```

with supporting prose after the equation:

> For each unit of returned input processed at processor $l$, the processor produces $\rho_l$ units of
> recovered output. Because each unit of recovered output has value $v_l$, the realized
> recovered-material credit is $\rho_l v_l$ per unit of returned input. Therefore, $b_{jl}$ is the
> second-leg transportation and processing cost net of this realized credit.

---

## 3. $\alpha(S)$ is an ex-ante commitment, not an outcome

$\alpha(S)$ is the share of returns the coalition **promises in advance** to route through the
qualified network. It is an input, not a decision variable.

**Why the model must not choose it.** If $\alpha(S)$ were optimized, the MILP would drive it toward
zero — handling less material is always cheaper. That would let the model manufacture savings by
quietly cutting formal-channel service, destroying the product-stewardship meaning of the results.
Fixing $\alpha(S)$ ex ante means Phase I answers a constrained question: *what is the cheapest network
that can deliver the promise we already made?*

**$\alpha(S)$ is not a recovery rate.** $\alpha(S)$ governs how much material *enters* the qualified
network. $\rho_l$ governs how much *is recovered* from what enters. Different stages, different
meanings.

**Why coalition-indexed.** Different coalitions can credibly commit to different service levels,
depending on their combined reach and capability.

**Current formulation is an exact target, not a floor.** The constraint is written
$\sum_j q_{ij}=D_i(S)$, an equality. Whether it should be $\geq$ (a minimum) is an open modeling
question worth raising with the professor.

In the baseline $\alpha(S)=1$, so $D_i(S)=d_i$ and the service rate is 100%.

> $\alpha(S)$ converts an abstract stewardship commitment into a concrete operating requirement. It
> specifies the share of each participating retailer's returns that must enter the qualified network.
> Phase I does not choose this commitment; it only identifies the least-cost network capable of
> delivering it.

---

## 4. Explicit responsibility share: $p_x$ vs. the 30% weight

These are two different percentages and conflating them is the single most likely misreading of the
hybrid rule.

$$\psi_x(\theta)=\theta\,\phi_x(c)+(1-\theta)\,p_x\,c(N)$$

- $1-\theta=0.30$ — the **weight** the responsibility rule carries in the blended allocation.
- $p_M=0.15$ — the Manufacturer's share **inside** the responsibility rule.

**The Manufacturer pays neither 30% nor 15% of total cost.** Working it through with baseline values
($c(N)=6{,}705.6$, $\phi_M=440.8$):

$$p_M\,c(N)=0.15\times6{,}705.6=1{,}005.8$$
$$\psi_M=0.70(440.8)+0.30(1{,}005.8)=308.6+301.7=\mathbf{610.3}$$

So the Manufacturer's actual share is $610.3/6{,}705.6\approx\mathbf{9.1\%}$.

The hybrid rule moves payments in **both** directions. For R1, whose responsibility share sits *below*
its Shapley allocation:

$$\psi_{R_1}=0.70(2{,}158.5)+0.30(1{,}930.6)=\mathbf{2{,}090.1}$$

— down from 2,158.5. The Manufacturer's payment rises; R1's falls.

**Why 0.70?** It is a stylized modeling assumption, not an estimate. Answer for the committee:

> The 30% weight is an illustrative negotiated adjustment rather than an empirically estimated
> parameter. It allows the case study to examine how adding explicit stewardship responsibility
> changes payments and coalition stability while retaining Shapley marginal contribution as the
> primary allocation principle.

Calibration would need EPR regulation, manufacturer–retailer contracts, stakeholder negotiation
records, managerial interviews, observed industry cost-sharing agreements, or behavioral experiments.

---

## 5. Marginal contribution vs. responsibility share

The two components answer genuinely different questions.

| Allocation logic | Question it answers |
|---|---|
| Shapley marginal contribution | How much cost did this player add to, or save, the system? |
| Explicit responsibility share | Given brand, legal, control, or negotiated obligation, how much *should* this player bear? |

**Shapley is cost-causation logic.** It reflects added volume, whether a new facility must open,
transport and processing effects, scale economies created, cheaper processors unlocked, and platform
cost carried.

**Responsibility is governance logic.** The Manufacturer collects no returns and may score a low
Shapley allocation precisely because its platform *lowers* everyone's cost — yet it designed and sold
the product, owns the brand, controls materials and channel, holds EPR obligations, and profits from
the original sale. A governance view may hold that it should not pay near-nothing just because its
marginal contribution is small.

**Why not 100% responsibility share?** Because responsibility weights can be subjective, unsupported
by data, blind to scale economies, punitive toward members who actually create savings, and are not
guaranteed to satisfy core stability.

**Most defensible position for the chapter:**

> Pure Shapley is the economic baseline because it allocates cost according to each player's average
> marginal contribution. The explicit responsibility component is introduced only as an optional
> governance adjustment when legal, brand-level, or negotiated stewardship obligations are not fully
> represented by physical network costs. It is not assumed to be fairer or more stable; those
> consequences must be evaluated separately.

Concretely: keep 100% Shapley as the primary baseline, present the hybrid as an illustrative
governance alternative, state plainly that 30% is stylized, and let core slack decide whether it
actually helps.

---

## 6. Core slack $\sigma(S;\phi)$

$$\sigma(S;\phi)=c(S)-\sum_{x\in S}\phi_x(c)$$

Comparing what a subgroup would pay operating alone against what it pays inside the grand coalition.

| Sign | Meaning |
|---|---|
| $\sigma>0$ | Staying is cheaper — no incentive to leave |
| $\sigma=0$ | Indifferent between staying and leaving |
| $\sigma<0$ | The subgroup is charged more than going alone — a **blocking incentive** |

**The −145.0 result.** The most dissatisfied subgroup is $S=\{M,R_1,R_3,R_4,R_5\}$:

$$\sigma(S;\phi)=c(S)-\sum_{x\in S}\phi_x(c)=5{,}240.4-5{,}385.4=\mathbf{-145.0}$$

These five players are allocated 5,385.4 k USD inside the grand coalition but could operate their own
network for 5,240.4 k USD — so leaving together saves them 145.0 k USD.

**Why "minimum".** Every proper subcoalition $\emptyset\neq S\subsetneq N$ has a slack. The reported
figure is the smallest:

$$\Sigma(a)=\min_{\emptyset\neq S\subsetneq N}\sigma(S;a)$$

It is the weakest link in the agreement — the subgroup with the strongest case for walking away.

**What −145.0 does *not* mean.** It does not mean the grand coalition loses money overall; that every
player wants out; that cooperation produced no savings; that all subgroups are unhappy; or that the
coalition must collapse in practice. In this case the grand coalition saves 21.5% overall and **every
individual player** prefers joining. The finding is precisely:

> Every member individually preferring to stay does not imply that every *group* of members prefers
> to stay.

**Everyday analogy.** Six people share a dinner; the group bill beats eating separately, so everyone
gains. But after splitting, five of them notice they were assigned \$538.54 while dining without the
sixth would cost \$524.04 — so those five can save \$14.50 by leaving together. That \$14.50 is the
blocking incentive.

**For the committee:**

> Core slack measures how much cheaper or more expensive it is for a subgroup to remain in the grand
> coalition rather than operate independently. A minimum core slack of −145.0 thousand USD means that
> the most dissatisfied subgroup could reduce its combined payment by 145.0 thousand USD by leaving
> together.

---

## 7. RQ2 vs. RQ3, and the four-concept boundary

**RQ2 — how is the total cost divided?** Budget balance ($\sum_x\phi_x(c)=c(N)$) plus individual
participation ($\phi_x(c)\leq c(\{x\})$ for each single player).

**RQ3 — will any subgroup walk away?** Every proper coalition must satisfy
$\sum_{x\in S}\phi_x(c)\leq c(S)$.

Individual rationality is just the special case of the core condition where $|S|=1$. Passing it says
nothing about larger subgroups — which is exactly what this case demonstrates.

> Cost sharing produces an allocation, but stability is a property that the allocation must
> subsequently pass. A balanced or individually acceptable allocation is not necessarily
> coalition-stable.

| Layer | Core question | How Chapter 4 handles it |
|---|---|---|
| EPR | Who is legally or institutionally assigned post-consumer responsibility? | Institutional context and source of obligation; the stylized model does **not** establish jurisdiction-specific compliance |
| Economic participation | Is joining cheaper than going alone, for each member? | Check $\phi_x(c)\leq c(\{x\})$ |
| Coalition stability | Would any subgroup be cheaper off on its own? | Check every core constraint |
| Normative fairness | Is the allocation just, transparent, and defensible? | **Not** guaranteed by the Shapley value; requires separate responsibility principles and procedural judgment |

> EPR tells us who is assigned post-consumer responsibility; the network model tells us how that
> responsibility can be implemented; economic participation tells us whether each firm prefers
> joining; coalition stability tells us whether any subgroup prefers leaving; and normative fairness
> asks whether the allocation is justifiable beyond economic incentives.

---

## 8. Current baseline results

From `generated/summary.json`, verified 2026-09-07. Costs in thousand USD/year.

| Quantity | Value |
|---|---|
| Grand-coalition cost $c(N)$ | 6,705.6 |
| Sum of stand-alone costs | 8,542.6 |
| Savings | 1,837.0 (21.5%) |
| Open centers | NV, MI, GA |
| Processors used | H, L |
| Required volume / recovered output | 12,400.0 / 10,560.0 tons |
| Service rate | 100% |
| Unit stewardship cost | 540.77 USD/ton |
| Minimum core slack (Shapley) | −145.0 |
| Least-core $\varepsilon$ | 52.875 |
| Coalitions solved per scenario | 64 |

**Shapley allocation:** M 440.8 · R1 2,158.5 · R2 1,320.2 · R3 1,045.9 · R4 852.0 · R5 888.2

### Allocation rules compared

| Rule | Manufacturer pays | Minimum core slack |
|---|---|---|
| Shapley baseline | 440.8 | −145.0 |
| Hybrid ($\theta=0.70$) | 610.3 | **−182.5** |
| Least-core L1 projection | 440.8 | −52.9 |
| Manufacturer responsibility shift | 500.0 | −157.5 |
| Proportional responsibility | 1,005.8 | **−505.8** |

**Key finding: making the Manufacturer pay more makes stability worse, not better.** Every rule that
raises the Manufacturer's payment above its Shapley value drives the minimum core slack *more*
negative. Pure proportional responsibility is worst at −505.8. So *"better aligned with a
responsibility principle" ≠ "more stable"* — a governance adjustment must always be re-tested against
all core constraints.

### Sensitivity

| Scenario | Grand cost | M allocation | Shapley min slack | Least-core ε* |
|---|---|---|---|---|
| Baseline | 6,705.6 | 440.8 | −145.0 | 52.9 |
| Service target 90% | 6,144.96 | 433.8 | −180.7 | 89.1 |
| Governance cost +25% | 6,874.35 | 565.8 | −142.5 | 49.8 |
| Recovery value +20% | 6,046.08 | 276.5 | −161.4 | 28.8 |
| Transportation +25% | 6,951.1 | 429.5 | −116.4 | 29.6 |
| Volume +20% | 7,648.32 | 420.0 | −88.8 | **−16.8** |
| Restricted processor access | 6,772.6 | 500.0 | **0.0** | 0.0 |

The two stability columns answer different questions. Shapley slack asks whether *this* allocation is
blocked; ε* asks whether *any* allocation can avoid being blocked (ε* ≤ 0 means the core is nonempty).

- **Restricted processor access** is the only scenario where the *Shapley* allocation is unblocked, and
  it gets there by making the grand coalition *more* expensive (6,772.6 vs. 6,705.6). Corrected
  2026-09-24: an earlier version of this note called this "removing the cheap outside option". That is
  wrong. The processor removed is H, the **Manufacturer-enabled** high-standard processor. It works
  because the Manufacturer-led subgroups can no longer run on H alone while the full coalition needs a
  second processor (see §9).
- **Volume +20%** has a *nonempty* core (ε* < 0) even though Shapley is still blocked: a stable allocation
  exists, so the instability there belongs to the rule, not to the network.

Efficiency and stability can trade off against each other.

---

## 9. Structural diagnosis — why the core is empty (added 2026-09-24)

Chapter 4 now explains the empty core with four standard analytical methods. The chapter's
propositions are general; the numbers below are for the stylized case and come from
`generated/summary.json` (`structural_diagnosis` block). In the chapter every number is a generated
macro.

**Convention.** ε* here is the *standard* least-core value, i.e. without the restriction aₓ ≥ 0. In
the case that restriction never binds (52.875 either way), so the core is empty under the standard
definition, not only under the chapter's convention.

### 9.1 Structural properties — *why*, and *which groups*

| Property | Result | Meaning |
|---|---|---|
| Monotone | 0 violations / 665 | Adding members never lowers cost |
| Subadditive | 0 / 301 | Two separate groups never do better apart |
| Concave (submodular) | **462 / 1,351 fail (34.2%)** | A member's marginal cost can *rise* as the group grows |
| — where the merged group needs both processors | 56.3% fail | vs. 25.2% otherwise |

- **Clearest case.** R2 joining {M,R1,R3} costs 1,007.8, because its volume fits into H's spare
  capacity. R2 joining {M,R1,R3,R4,R5} costs 1,465.2, because H is nearly full and L must be activated.
- **Why concavity matters, and why its failure is not the whole story.** For a concave cost game the
  core is nonempty and contains Shapley (Shapley 1971). But concavity is only *sufficient*, not
  necessary, so failing it does not by itself explain an empty core.
- **Certificate (Bondareva–Shapley).** Four coalitions with weight ⅓ each, every firm in exactly three:
  {M,R1,R2,R3}, {M,R1,R3,R4,R5}, {M,R2,R3,R4,R5}, {R1,R2,R4,R5}. Picture it as every firm splitting
  its year across three smaller partnerships: everyone is served, at ⅓ × 19,905.3 = **6,635.1 <
  6,705.6**. That single comparison proves no allocation can satisfy all four groups. The certificate is
  **unique**. Three of the four groups contain M and run on H alone.
- **Linear relaxation (Owen 1975).** If facilities could be opened "partly" (fixed cost paid per ton), the
  core is **nonempty**: ε̄* = −16.67, and Shapley lies inside it. This holds at all 77 parameter points
  tested. So **instability can only come from indivisible facilities**. Integrality gap = 471.0.
- **Additive costs are neutral.** Collection cost, platform cost, and per-retailer governance cost are
  carried by each firm regardless of partners. Setting them to zero leaves ε* and all 62 slacks unchanged.

### 9.2 Comparative statics — *how it responds*

Envelope formula: ∂ε*/∂θ = μ·c′(N) − Σ λ_S·c′(S), with μ = 0.75 and λ = 0.25 on each certificate group.
It is local (facility configurations fixed) and is checked against fully re-solved games:

| Input | Predicted ∂ε* | Re-solved |
|---|---|---|
| Coalition setup (base governance) cost | −0.25 | −0.25 |
| H capacity (per 1,000 t) | −13.875 | −13.875 |

- **Shared governance stabilizes**: any breakaway group would have to pay the setup cost again.
- **H capacity** (shadow price 18.5 USD/t in the grand coalition): the core is empty for 8,250–12,250 t,
  peaking at ε* = 145.8 at 11,000 t, and nonempty again from 12,400 t, where the full coalition fits on H
  alone. The response is not monotone; ε* jumps each time another large group first fits on H.
- **Service target α — the headline.** Stable at α = 0.80, where Shapley is inside the core (slack +92.4).
  Unstable from 0.81, peaking at ε* = 125.1 at α = 0.93. The threshold is α = K_H / total returns =
  0.806. **A stronger stewardship commitment is what destabilizes the collective.**

### 9.3 Heterogeneity — *is it the differences between retailers?*

No. Moving volumes from equal (2,480 t each) to actual, with the total fixed: equal volumes are the
**least** stable (ε* = 117.2, 8 blocking groups), and the most stable point lies in between (ε* = 22.1
at t = 0.375). With equal volumes, M plus any four retailers just fits in H. What matters is how closely
subgroups can fill the qualified processor, not asymmetry.

### 9.4 Bounds — *how much*

| Measure | Value | Relative size |
|---|---|---|
| Least-core ε* | 52.875 | 0.79% of c(N); 4.26 USD/t; 2.9% of savings |
| Worst Shapley blocking gain | 145.0 | 2.16% of c(N); 11.69 USD/t; 2.77% of that group's cost |
| **Cost of Stability** (external subsidy) | **70.5** | **3.8% of savings** |

Bounds: (n/(n−1))·ε* ≤ CoS ≤ min{n·ε*, integrality gap} → 63.45 ≤ 70.5 ≤ min{317.25, 471.0}. Here
CoS = ε* × 4/3, the certificate's total weight. Contrast with the responsibility shift: moving cost onto
M *inside* the coalition made stability worse (three of the four certificate groups contain M), while an
*external* 70.5 removes every blocking incentive.

**Terminology.** Say "Cost of Stability" (Bachrach et al. 2009) or "least-core value". Never say "price of
stability", which is a different, non-cooperative concept.

---

## 10. Reproducing

```bash
cd latex_code_active/chapter4_model
python solve_chapter4.py --data case_data.json --output generated --solver SCIP
```

Solves all 64 coalitions for the baseline and every sensitivity scenario, computes exact Shapley
allocations, checks all proper-coalition core constraints, solves the least-core/L1 projection, runs
the structural diagnosis (linear relaxation, certificate, Cost of Stability, envelope check, and the
capacity / service-target / dispersion sweeps), and writes CSV/JSON evidence plus LaTeX fragments. The
run takes about two minutes, and it **stops with an error** if any exported number would contradict a
Chapter 4 proposition. SCIP is primary; CBC is the fallback. Determinism is
checked via `generated/manifest.sha256`. **Do not hand-edit anything in `generated/`.**

The dataset is stylized — a reproducible illustration, **not** an industry-calibrated estimate.
Empirical calibration of regional volumes, facility costs, processor contracts, and coalition outside
options remains the identified next step.
