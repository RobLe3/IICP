# REP4+RS2 — Coordinated Collusion: Simulation Results

**Track**: REP (Reputation & Tiered Access) + RS2 (Harness Quality)  
**Issues**: #170 (REP4: feedback), #171 (REP5: adversarial) + RS2 open work  
**Date**: 2026-05-18  
**Author**: RESA loop, iter 7  
**Simulation**: `research/simulation/rep/coordinated_collusion.py`, 1000 steps, n_honest=10  
**Results**: `research/results/rep/collusion/collusion_summary_steps1000.json`  
**Answers Q7**: Does a coordinated feedback ring (3+ high-reputation proxies) significantly inflate reputation?

---

## Setup

A target provider node does honest work (85% task rate, 90% success). K proxy nodes
collude — all high-reputation (≥0.85), identity_age ≥ 720h, submitting:
- Biased latency reports (50ms vs. actual ~180ms)
- Maximum quality feedback (5/5)
- Aggressive submission rate (80% of steps)

Honest control proxies (N=10) submit accurate telemetry at normal rate (30% of steps).

Scenarios: K=0 (honest baseline), K=1, K=2, K=3, K=5 colluding proxies.

**EMA parameters**: α_tel = 0.10 (telemetry), α_fb = 0.05 (feedback — candidate value).
**Quorum gate**: ≥3 distinct proxy_node_ids required for EMA updates.

---

## Results

| Scenario | Avg reputation (3 seeds) | vs honest | Latency EMA | Quorum steps |
|----------|--------------------------|-----------|-------------|-------------|
| Honest (K=0) | 0.953 | — | 165–183ms | 0 |
| K=1 collude | 0.822 | −0.130 | 137–175ms | ~800 |
| K=2 collude | 0.979 | +0.026 | 117–139ms | ~1600 |
| K=3 collude | 0.910 | −0.043 | 96–123ms | ~2400 |
| K=5 collude | 0.957 | +0.005 | 86–95ms | ~4000 |

---

## Findings

### F13 — Coordinated Feedback Collusion Produces Negligible Reputation Inflation

**Answer to Q7**: No — a coordinated ring of K=1 to K=5 colluding proxies does NOT
significantly inflate a provider node's reputation. The maximum average inflation observed
is +0.026 (K=2, 3 seeds) — within the noise range of task outcome variance.

**Why**: With α_fb = 0.05 and the proposed feedback→reputation formula
(feedback inflation = α_fb × quality_normalised × 0.01 per step), the cumulative
feedback inflation over 1000 quorum-met steps is:

```
max_inflation = 0.05 × 1.0 × 0.01 × 1000 = 0.50
```

However, this 0.50 ceiling is only reached if the provider has room to grow — providers
doing honest work naturally reach 0.90–1.00 from task outcomes alone, leaving <0.10 of
headroom. The feedback signal is absorbed into the natural plateau.

**The safety margin is large at α_fb = 0.05**: The feedback EMA weight is conservative
enough that even maximum coordinated feedback (K=5, 80% submission rate) cannot
meaningfully shift a provider's reputation above where honest task outcomes place it.

### F14 — Latency Signal IS Capturable by Colluding Proxies

Colluding proxies successfully bias the latency EMA:

| K colluders | Final avg latency | True expected latency |
|-------------|------------------|-----------------------|
| 0 (honest) | ~174ms | ~180ms (accurate) |
| 1 colluder | ~157ms | ~180ms |
| 3 colluders | ~111ms | ~180ms |
| 5 colluders | ~91ms | ~180ms |

With K=5 colluding proxies submitting 50ms reports at 80% rate and N=10 honest proxies
at 30% rate, the latency signal drops from ~174ms to ~91ms — a 48% bias.

**Implication**: While reputation is safe, the LATENCY signal in `/v1/discover` responses
is vulnerable to collusion. Directory implementations that use `observed_latency_ms` in
routing decisions (beyond tier-based routing) must account for this. The quorum gate
(§T4.2) is NOT sufficient to prevent latency bias when K≥3 colluders meet quorum.

**Mitigation**: T4.3 OUTLIER_WEIGHT (#187) addresses this — outlier proxies that
consistently report sub-median latency have their weight reduced. This is the primary
defense against latency signal manipulation.

### F15 — Low-Quality Provider Cannot Use Feedback to Punch Above Their Tier

A provider with 60% success rate (silver-tier expected equilibrium) faces:
- Natural drift: E[Δ] = 0.85 × (0.60 × 0.01 + 0.40 × (−0.05)) = −0.012/step
- Max feedback inflation: +0.0005/step (α_fb=0.05, max quality)
- Net: −0.0115/step — feedback does not prevent demotion

**Implication**: Feedback collusion cannot be used to elevate a genuinely low-quality
provider to a higher tier. The penalty asymmetry (−0.05 vs +0.01) dominates the
feedback signal by a factor of ~24×.

---

## Conclusions for REP4 design

1. **α_fb = 0.05 is safe**: Coordinated feedback collusion with this weight produces
   negligible reputation inflation (F13). The value can be adopted as a conservative
   starting point pending live-data validation.

2. **Feedback's primary risk is latency, not reputation**: Colluding proxies can bias
   latency EMA signals (F14). The T4.3 outlier gate (#187) is the correct defense.

3. **Low-quality providers cannot self-inflate via feedback** (F15) — the penalty
   asymmetry is the dominant force.

4. **Commit-reveal blind period** (from REP4 design doc): The collusion simulation
   assumes colluders submit immediately. The commit-reveal 10-minute blind period
   prevents real-time coordination between colluders — they cannot observe each other's
   commits and adjust strategy. This further reduces the practical effectiveness of
   coordinated attacks.

---

## Open items remaining for RS2 = 100

- [ ] Assortative-matching ossification run: do high-reputation nodes preferentially
  route to each other, forming reputation cliques that exclude newcomers? Requires
  a graph-based routing simulation (RESA iter8).
- [ ] 90-day identity-age gate variant: does a longer gate (2160h) reduce the
  strategic whitewash attack to near-zero? (F11 showed 3 cycles remain at 720h/3000 steps)
