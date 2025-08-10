# Core Equations — TEOF Unified Field Proposal (v2)

This file contains the essential definitions and equations required to work with the TEOF unification of QM and GR.

---

## 1. Total Action

\[
S_{\text{total}}[g,\rho] = S_{\text{GR}}[g] + S_{\text{QFT}}[g,\rho] + \lambda\,\mathcal{C}_1[g,\rho]
\]

Where:
- \(g_{\mu\nu}\) — spacetime metric
- \(\rho(x)\) — local quantum state (density operator)
- \(\lambda\) — coupling constant

---

## 2. Coherence-Penalty Functional

\[
\mathcal{C}_1 := \frac{1}{2} \lVert A \rVert_g^2
\]
\[
A_{\mu\nu} := G_{\mu\nu} - 8\pi G\,T_{\mu\nu} - \xi\,\mathcal{I}_{\mu\nu}(\rho)
\]

Where:
- \(G_{\mu\nu}\) — Einstein tensor
- \(T_{\mu\nu}\) — stress–energy tensor from QFT
- \(\xi\) — informational coupling constant
- \(\mathcal{I}_{\mu\nu}(\rho)\) — informational curvature

---

## 3. Informational Curvature

Let \(\pi:\mathcal{B} \to \mathcal{M}\) be a fiber bundle of state manifolds over spacetime.
\[
\mathcal{I}_{\mu\nu}(\rho) := (\partial_\mu \theta^a)(\partial_\nu \theta^b) I_{ab}(\rho)
\]
Where:
- \(\theta^a\) — local state parameters
- \(I_{ab}(\rho)\) — Fisher information metric on the state space

---

## 4. Field Variations

### Metric Variation
\[
\frac{c^3}{16\pi G} G_{\mu\nu} = T_{\mu\nu} + \lambda\,\Theta_{\mu\nu}[\rho,g]
\]
\[
\Theta_{\mu\nu} := -\frac{\delta \mathcal{C}_1}{\delta g^{\mu\nu}}
\]

### State Variation
\[
\frac{\delta S_{\text{QFT}}}{\delta \rho} + \lambda\,\frac{\delta \mathcal{C}_1}{\delta \rho} = 0
\]

---

## 5. Limits

- **\(\lambda = 0\)** → Standard GR + QFT
- **Flat \(g_{\mu\nu}\)** → QFT in flat spacetime
- **\(\mathcal{I}_{\mu\nu} \to 0\)** → Decoupling of informational effects

---

**Note:** Completing the scalar field example, the conservation proof, and first bounds on \(|\lambda\xi|\) will fully activate the framework for testable predictions.
