# Personal Intelligence System

**Status:** Vision defined, not yet built
**Created:** 2025-12-05
**Priority:** High — Core infrastructure

---

## Vision

A reliable extension of human observation:
- Daily curated intelligence feed
- Markets, events, predictions, insights
- All AI-generated BUT with cited sources
- Random audit capability at any time
- Trust earned through verification, not faith
- TEOF frameworks as filter for relevance

---

## Why This Matters

### The Problem

Governance system failure taught: AI hallucination compounds when AI observes AI.

**Cannot trust:**
- AI claims without sources
- AI building on AI outputs
- "Truth" that can't be verified

**Can trust:**
- AI curation with citations
- Claims verifiable against external sources
- System where hallucination is detectable

### The Solution

AI doesn't observe — it curates with citations. Human can audit any citation. Trust is earned through successful audits over time.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   YOUR OBSERVATION               │
│         (random audits, final decisions)         │
└─────────────────────────────────────────────────┘
                        ▲
                        │ audit any time
                        │
┌─────────────────────────────────────────────────┐
│              DAILY INTELLIGENCE FEED             │
│                                                  │
│  • World events    [source: Reuters, AP, etc]   │
│  • Market moves    [source: Bloomberg, Yahoo]   │
│  • Predictions     [source: analyst reports]    │
│  • TEOF insights   [source: your frameworks]    │
│  • Curated reads   [source: linked articles]    │
│                                                  │
│  Every claim → citation → you can verify        │
└─────────────────────────────────────────────────┘
                        ▲
                        │ generates
                        │
┌─────────────────────────────────────────────────┐
│              AI CURATION LAYER                   │
│                                                  │
│  • Fetches from sources                         │
│  • Summarizes with citations                    │
│  • Applies TEOF filters (what matters?)         │
│  • Flags uncertainty                            │
│  • Tracks prediction accuracy over time         │
│                                                  │
└─────────────────────────────────────────────────┘
                        ▲
                        │ pulls from
                        │
┌─────────────────────────────────────────────────┐
│                  DATA SOURCES                    │
│                                                  │
│  News: Reuters, AP, Bloomberg, FT               │
│  Markets: Yahoo Finance, TradingView, CoinGecko │
│  Analysis: Analyst reports, research papers     │
│  Social: Twitter/X, Reddit sentiment            │
│  Your frameworks: TEOF, source analyses         │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## Trust Mechanism

### How Trust Is Built

1. **Every AI claim has a citation**
   - "BTC up 3%" → [CoinGecko, timestamp]
   - "Fed expected to hold" → [Reuters, date]
   - "Per TEOF Layer 7..." → [/frameworks/power/power.md:line]

2. **Random audits**
   - Pick any claim, check the source
   - Source confirms → trust maintained
   - Source contradicts → flag, investigate

3. **Trust earned over time**
   - Track audit success rate
   - Build confidence through verification
   - Know system's reliability empirically

4. **Hallucination visible**
   - If AI hallucinates, citation won't match
   - Caught on audit
   - Pattern emerges: which claims reliable vs unreliable

---

## Daily Output Example

```markdown
# Morning Intelligence Brief — 2025-12-06

## Markets
- BTC: $97,450 (+2.3% 24h) [CoinGecko]
- SPY: $602.15 (+0.4%) [Yahoo Finance]
- Your portfolio: +$4,230 (est.) [calculated]

## Events
- Fed meeting next week, 73% probability hold [CME FedWatch]
- China PMI contracted 3rd month [Reuters]
- NVDA earnings beat, guidance raised [Bloomberg]

## TEOF-Filtered Insights
- Per Layer 2 (Energy): BTC approaching target allocation
- Per Power framework: Fed policy = Cantillon positioning

## Predictions (Trackable)
- BTC >$100k by Dec 31 (confidence: 65%) [Analyst consensus]
- Previous accuracy: 72% (18/25 this quarter)

## Curated Reads
- [Why the Fed is stuck](https://ft.com/...) — 8 min
- [AI chip shortage analysis](https://bloomberg.com/...) — 12 min

---
*Audit: Click any [source] to verify. System accuracy: 94%*
```

---

## Implementation Phases

### Phase 1: Manual Prototype (1 week)

**What:**
- Each morning, prompt Claude/GPT:
  - "Morning brief: markets, world events, cited sources"
  - "Apply TEOF filters to prioritize"
- Manually audit 2-3 citations per day
- Track audit results

**Deliverable:** Daily markdown brief, manual process

**Success criteria:** Audit success rate >90%

### Phase 2: Automated Feed (2-4 weeks)

**What:**
- Script that:
  - Fetches market data (APIs)
  - Fetches news headlines (RSS/APIs)
  - Sends to Claude API for summarization
  - Outputs structured markdown with citations
  - Logs to daily file

- Audit interface:
  - Citations are clickable links
  - Verification logged

**Deliverable:** Automated daily brief, audit logging

**Success criteria:** Runs daily without intervention

### Phase 3: Prediction Tracking (1-2 weeks)

**What:**
- Prediction logging:
  - AI makes predictions with confidence
  - Stored with timestamps
  - Outcomes recorded when known
  - Accuracy calculated

**Deliverable:** Prediction database, accuracy metrics

**Success criteria:** System proves its reliability over time

### Phase 4: TEOF Integration (ongoing)

**What:**
- Frameworks as filters:
  - "This affects Layer 7 (Power)"
  - "Per Stoicism, outside your control"
  - "Per value investing, this is noise"

**Deliverable:** TEOF-aligned intelligence curation

---

## Technical Components

| Component | Purpose | Difficulty | Status |
|-----------|---------|------------|--------|
| News aggregator | Pull from sources | Medium | Not started |
| Market data feed | Real-time prices | Easy (APIs) | Not started |
| AI summarization | Condense into brief | Easy (API) | Not started |
| Citation system | Every claim → source | Medium | Not started |
| Audit interface | Click to verify | Medium | Not started |
| Prediction tracker | Log and check | Medium | Not started |
| TEOF integration | Filter by framework | Easy | Not started |

---

## Why This vs Custom GPT

| Custom GPT (for others) | Personal Intelligence (for self) |
|------------------------|----------------------------------|
| Product for validation | Infrastructure for self |
| Requires verified foundation | Builds verified foundation |
| Can come later | Should come first |
| Tests market demand | Extends personal observation |

**The personal intelligence system is the foundation that makes everything else trustworthy.**

---

## Connection to Governance Failure

| Governance System (Failed) | Personal Intelligence (Proposed) |
|---------------------------|----------------------------------|
| AI generates truth | AI curates with citations |
| No verification path | Every claim auditable |
| AI observing AI | AI curating, human auditing |
| Hallucination compounds | Hallucination detectable |
| Trust assumed | Trust earned |

---

## Future Feature: Auto-Persistence Hook

**Idea (2025-12-07):** Post-session hook that automatically commits session learnings to git.

**Problem it solves:** Currently agents with file write access (Claude Code) can update identity.md/insights.md, but require ONBOARDING.md instruction to remember. Custom GPTs/Claude Projects can't write at all — requires manual copy-paste.

**Implementation sketch:**
1. API-based agent runs session
2. On session end, hook triggers:
   - Diff check: what files changed?
   - If identity.md or insights.md modified → `git add` + `git commit -m "Session update YYYY-MM-DD"`
   - Optional: push to remote
3. Full automation — no manual prompting needed

**Why this matters:** Closes the loop on memory persistence. Sessions compound automatically instead of requiring discipline to log.

**Prerequisites:** Personal intelligence system built on API (not Custom GPT/Claude Project).

---

## Next Action

**Phase 1, Step 1:** Create morning prompt template

Draft prompt for daily intelligence brief with:
- Market data request
- News summary request
- Citation requirement
- TEOF filter application
- Uncertainty flagging

Test manually for 1 week before automating.

---

*This is the reliable extension of observation. Build this first.*
