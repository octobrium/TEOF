# AI Trading System Architecture

**Objective:** AI-augmented swing trading / position trading for personal capital deployment

**Philosophy:** AI augments analysis and pattern recognition; you retain judgment and execution authority until system proves itself

**TEOF Derivation:** This system applies TEOF principles to capital deployment. Trading is Layer 2 (Energy) optimization with Layer 5 (Intelligence) methodology and Layer 4 (Defense) as the critical constraint.

---

## TEOF Framework Application

### Pattern C Architecture

The trading system implements Pattern C (stable core, adaptive periphery):

| Layer | Component | Stability | Change Frequency |
|-------|-----------|-----------|------------------|
| **Core** | Risk controls, position sizing rules, capital allocation limits | Stable | Rarely (only after major failures) |
| **Operational** | Strategy selection, signal generation framework, regime classification | Semi-stable | Monthly review |
| **Tactical** | Individual trades, entry/exit timing, specific indicators | Adaptive | Daily/weekly |

**Implication:** The Risk Controls section (lines 310-321) is the CORE — non-negotiable. Strategy selection is OPERATIONAL — can iterate. Individual trades are TACTICAL — highly adaptive.

### Layer Analysis

| TEOF Layer | Trading System Application | Status |
|------------|---------------------------|--------|
| **L1 Unity** | System coherence — all components aligned to single objective (positive expectancy) | Defined |
| **L2 Energy** | Capital preservation and growth — the point of the system | Primary focus |
| **L4 Defense** | Risk management — stops, position sizing, drawdown limits, diversification | Critical |
| **L5 Intelligence** | Signal generation, pattern recognition, regime detection, feedback loops | Core method |
| **L6 Truth** | Edge validation — does the system actually work? Paper trading, small capital tests | Gates |

### Degeneracy Principle (from TEOF §5.5)

**Critical for trading:** Multiple different mechanisms achieving the same defensive function.

The current risk management is partially degenerate but could be stronger:

| Risk Function | Current Mechanisms | Degeneracy Level |
|---------------|-------------------|------------------|
| **Loss limitation** | Stop losses | Low (single mechanism) |
| **Position protection** | Position sizing (1-2% risk) | Low (single mechanism) |
| **Portfolio protection** | Max drawdown trigger, correlation limits | Medium (two mechanisms) |
| **Edge validation** | Paper trading → small capital → scale | Medium (phased but not diverse) |

**Enhancement needed:** Add diverse mechanisms to critical functions:

**Loss Limitation (add degeneracy):**
- Stop loss (price-based)
- Time stop (exit if no movement after X days)
- Volatility stop (exit if volatility regime changes)
- Thesis invalidation (exit if original reason disappears)

**Position Protection (add degeneracy):**
- Position sizing by risk
- Maximum dollar exposure per position
- Maximum percentage of portfolio per position
- Sector/correlation limits

**Portfolio Protection (add degeneracy):**
- Max drawdown trigger (current)
- Correlation limits (current)
- Regime-based exposure reduction (add: reduce size in unfavorable regimes)
- Time-based circuit breaker (add: pause after 3 consecutive losses)

### Correction Mechanisms (from TEOF §5.6)

**Every surviving system has explicit error-detection and correction mechanisms.**

| Trading Component | Correction Mechanism | Frequency |
|-------------------|---------------------|-----------|
| Individual trades | Post-trade analysis | Each trade |
| Signal generation | Win rate / profit factor tracking | Weekly |
| Strategy | Paper → Small capital → Scale gates | Phase-based |
| System overall | Monthly review, edge validation | Monthly |
| Catastrophic | 15% drawdown pause + full review | Trigger-based |

**Current gap:** No explicit mechanism for detecting when edge has decayed. Add:

- **Edge decay detection:** If rolling 20-trade win rate drops below 40% or profit factor below 1.0, trigger strategy review
- **Regime mismatch detection:** If current regime differs from training regime, flag for manual review
- **Slippage monitoring:** If real execution differs from expected by >X%, investigate execution layer

---

## Market Selection

| Market | Inefficiency | Volatility | AI Edge Potential | Liquidity | Recommendation |
|--------|-------------|------------|-------------------|-----------|----------------|
| Crypto (BTC, ETH, majors) | High | High | High | High | Primary |
| Crypto (altcoins) | Very High | Very High | High | Variable | Secondary, smaller size |
| US Equities | Low | Medium | Low-Medium | Very High | Tertiary |
| Forex | Low | Low-Medium | Low | Very High | Skip |
| Options | Medium | High | Medium | High | Future (complexity) |

**Recommended focus:** Crypto majors (BTC, ETH, SOL) for primary system. More inefficient than traditional markets, AI edge more likely.

---

## Strategy Framework

### Timeframe
- **Swing trading:** Days to weeks
- **Not:** Day trading (time intensive, competes with dentistry), long-term hold (that's your asset allocation, not trading)

### Edge Hypothesis

Potential edges to test:

**1. Sentiment + Technical Confluence**
- AI monitors: Twitter/X sentiment, funding rates, on-chain flows, news
- Combines with: Technical levels (support/resistance, trend)
- Entry: When sentiment + technicals align
- Edge source: Processing more information faster than manual traders

**2. Volatility Regime Detection**
- AI classifies: Low vol / high vol / transitional regimes
- Strategy adapts: Different position sizing and targets per regime
- Edge source: Systematic regime awareness vs. emotional trading

**3. Mean Reversion on Overextension**
- AI detects: Extreme moves (RSI, Bollinger, funding rates)
- Fades: Overextended moves with defined risk
- Edge source: Systematic execution vs. FOMO/panic traders

**4. Trend Following with AI Filters**
- Core: Follow established trends
- AI adds: Entry timing, exit signals, regime filters
- Edge source: Not fighting trends + better timing

**Recommendation:** Start with #1 (Sentiment + Technical Confluence) — plays to AI strength in information processing.

**5. Copy Trading + Indicator Confluence (Shelved Idea)**

*Added: 2024-12-01*

- **Concept:** Layer copy trading signals on top of technical indicators (200 MA, RSI, MACD, etc.) to create multi-factor confluence-based buy signals. When multiple indicators align + copy trade signal from successful trader, stronger conviction.
- **Potential strengths:**
  - Confluence-based systems can outperform single-indicator systems
  - Adds "smart money" dimension to pure technicals
  - Can be systematized and automated
  - Reduces false signals by requiring multiple confirmations
- **Concerns:**
  - Technical indicators are largely backward-looking; academic literature (Fama 1970, Malkiel 1973) shows they don't reliably predict future returns
  - Copy trading assumes copied trader has edge — most don't persist (survivorship bias in leaderboards)
  - Overfitting risk: can always find indicator combinations that worked historically
  - Transaction costs eat into gains on frequent signals
  - "Strong historical indicators" is a red flag — past performance doesn't predict future in efficient markets
- **Verdict:** Medium-low potential. Would need rigorous out-of-sample backtesting, realistic transaction cost modeling, and honest edge assessment. Most people who pursue this discover they'd be better off in index funds.
- **Action if pursuing:** Research which indicators have any empirical support, create tier list, backtest combinations, model transaction costs before any real capital.
- **Status:** Shelved — revisit only if genuine quantitative edge hypothesis emerges.

---

## System Components

### 1. Data Ingestion

**Price Data:**
- Source: Exchange APIs (Binance, Coinbase), TradingView
- Frequency: 1-hour candles minimum, 4-hour for primary signals
- Store: Local database or cloud

**Sentiment Data:**
- Twitter/X: Keyword tracking, influencer monitoring
- Reddit: Subreddit sentiment
- News: Headlines, keyword frequency
- Tool: Custom scraping or APIs (LunarCrush, Santiment, or custom)

**On-Chain Data:**
- Exchange flows (inflows = selling pressure, outflows = accumulation)
- Whale wallets
- Funding rates
- Open interest
- Source: Glassnode, CryptoQuant, or free alternatives

**Technical Indicators:**
- Calculate locally: RSI, MACD, Bollinger, moving averages, volume
- Support/resistance levels
- Trend classification

### 2. AI Analysis Layer

**Signal Generation:**
```
Inputs:
- Price action (current + recent)
- Technical indicator values
- Sentiment score (aggregated)
- On-chain metrics
- Regime classification

Processing:
- Claude or local LLM analyzes confluence
- Scores opportunity (1-10)
- Identifies key levels (entry, stop, target)
- Flags concerns or conflicting signals

Output:
- Trade signal (long/short/neutral)
- Confidence level
- Suggested position size
- Key invalidation level
```

**Daily Briefing:**
- AI generates morning summary
- Key levels for the day
- Sentiment shifts
- Upcoming events/catalysts
- Active position status

### 3. Risk Management Layer

**Position Sizing:**
- Max risk per trade: 1-2% of trading capital
- Position size = (Risk Amount) / (Entry - Stop Loss)
- Never exceed max position regardless of conviction

**Stop Losses:**
- Every trade has defined stop before entry
- No moving stops to "give room" (ego trap)
- Trailing stops for winners only

**Portfolio Limits:**
- Max open positions: 3-5
- Max correlated exposure: 50% (e.g., not all in alts that move together)
- Max drawdown trigger: -15% → pause and review system

**Kelly Criterion (Adjusted):**
- Calculate optimal bet size based on win rate and payoff ratio
- Use half-Kelly or less (accounts for uncertainty in edge estimate)

### 4. Execution Layer

**Phase 1: Manual Execution**
- AI generates signal
- You review and approve
- You execute on exchange
- You log trade

**Phase 2: Semi-Automated**
- AI generates signal + sends alert (Telegram/Discord/SMS)
- You approve via quick response
- System executes
- You audit daily

**Phase 3: Fully Automated (Future)**
- AI executes within predefined parameters
- You review daily
- Override capability always available
- Only after 6+ months of validated edge

---

## Implementation Phases

### Phase 1: Infrastructure (Weeks 1-4)

**Week 1-2: Data Pipeline**
- [ ] Set up price data feed (TradingView or exchange API)
- [ ] Set up sentiment monitoring (Twitter API or manual tracking)
- [ ] Create simple database for logging
- [ ] Test data quality

**Week 3-4: Analysis Framework**
- [ ] Define signal generation prompts for Claude
- [ ] Create daily briefing template
- [ ] Build simple scoring system
- [ ] Paper trade manually using AI signals

Deliverable: AI can generate daily analysis and trade signals

### Phase 2: Paper Trading (Months 2-3)

**Process:**
1. AI generates signals each day
2. You log "paper" entries and exits
3. Track: win rate, avg win, avg loss, profit factor
4. Iterate on signal generation based on results

**Minimum sample size:** 30-50 trades before evaluating

**Success criteria:**
- Win rate > 45% with positive expectancy
- Profit factor > 1.3
- Drawdowns manageable
- Signals actionable (not too many, not too vague)

**If criteria not met:** Iterate on strategy, test alternatives, or conclude no edge

### Phase 3: Small Capital Deployment (Months 4-6)

**Entry criteria:** Paper trading success for 2+ months

**Allocation:** 5-10% of intended trading capital

**Process:**
1. Execute AI signals with real money
2. Position size 50% of calculated (extra conservative)
3. Track rigorously
4. Compare real results to paper results

**Watch for:**
- Slippage vs. paper
- Emotional interference
- Execution errors
- Results divergence from paper

### Phase 4: Scale (Months 6-12)

**If Phase 3 validates:**
- Increase to 50% → 100% of trading allocation
- Maintain position sizing discipline
- Consider semi-automation

**If Phase 3 disappoints:**
- Reduce to paper trading
- Diagnose: edge gone? Execution issues? Emotional trading?
- Iterate or conclude no edge

### Phase 5: Automation (Year 2+)

**Only if:**
- 12+ months of validated live trading
- Consistent edge demonstrated
- System is stable and understood

**Implementation:**
- Bot executes within strict parameters
- Daily audits
- Kill switch always available
- Start with small allocation to bot, scale up

---

## Trade Journal Template

```
Date:
Asset:
Direction: Long / Short
Signal source: [Sentiment confluence / Overextension / Trend / Other]
AI confidence: X/10

Entry price:
Stop loss:
Target(s):
Position size:
Risk amount: $X (X% of capital)

Rationale:
[Why this trade makes sense]

Concerns:
[What could go wrong]

Result:
Exit price:
Exit date:
P/L: $X (X%)
Outcome: Win / Loss / Breakeven

Post-trade analysis:
[What went right/wrong, what to learn]
```

---

## Tools & Tech Stack

| Function | Tool | Cost |
|----------|------|------|
| Charting | TradingView | $15-30/month (Pro) |
| Price Data | Exchange APIs (Binance, Coinbase) | Free |
| Sentiment | Twitter API + custom, or LunarCrush | Free - $50/month |
| On-chain | Glassnode, CryptoQuant free tier | Free - $50/month |
| AI Analysis | Claude (existing) | Existing |
| Alerts | Telegram bot or custom | Free |
| Trade Journal | Notion, Spreadsheet, or custom | Free |
| Execution | Exchange (Binance, Bybit) | Trading fees only |

**Starting cost: ~$30-50/month** (TradingView Pro + optional data)

---

## Risk Controls (Non-Negotiable)

1. **Never trade money you can't lose** — trading capital is separate from core asset allocation
2. **Stop loss on every trade** — defined before entry, honored without exception
3. **1-2% max risk per trade** — no exceptions for "high conviction"
4. **15% max drawdown trigger** — pause trading, review system
5. **No revenge trading** — after a loss, next trade must meet normal criteria
6. **No moving stops down** — only up (trailing)
7. **Daily audit** — review all positions, signals, results
8. **Weekly review** — aggregate stats, system performance
9. **Monthly review** — strategy assessment, edge validation

---

## Expected Outcomes

### Realistic Ranges (if edge exists)

| Metric | Poor | Acceptable | Good | Excellent |
|--------|------|------------|------|-----------|
| Win Rate | <40% | 40-50% | 50-60% | >60% |
| Profit Factor | <1.0 | 1.0-1.3 | 1.3-2.0 | >2.0 |
| Monthly Return | Negative | 2-5% | 5-10% | >10% |
| Max Drawdown | >30% | 20-30% | 10-20% | <10% |

### Honest Probability Assessment

| Outcome | Probability |
|---------|-------------|
| System has no edge, lose time | 40% |
| System has marginal edge, small profits | 30% |
| System has solid edge, meaningful profits | 20% |
| System is highly profitable | 10% |

This is a skill/research project with positive EV only if you're rigorous. Most retail traders lose money. The AI augmentation improves odds but doesn't guarantee success.

---

## Integration with Income Streams

**Priority:** Stream 1 (Content) > Stream 2 (Trading)

**Time allocation:**
- Trading system setup: 3-5 hrs/week initially
- Once running: 30-60 min/day for review + signals
- Does not compete with content creation time

**Capital allocation:**
- Trading capital is separate from core holdings (BTC, gold, etc.)
- Use only capital you've designated for active trading
- If system fails, core allocation is untouched

**Synergy:**
- Trading experience feeds content (what you learn, share)
- If system works, can become Stream 3 (advisory)
- If system fails, you've learned, can share that too

---

## Next Actions

### This Week
- [ ] Set up TradingView with key charts (BTC, ETH, SOL)
- [ ] Define initial signal generation prompt for Claude
- [ ] Create trade journal template
- [ ] Identify 3-5 Twitter accounts for sentiment tracking

### Next Week
- [ ] Generate first daily briefing with AI
- [ ] Paper trade first signals
- [ ] Set up basic tracking spreadsheet

### Month 1
- [ ] Refine signal generation based on paper results
- [ ] Build consistent daily routine
- [ ] 10+ paper trades logged and analyzed

---

## TEOF Audit Checklist

Before deploying capital, audit the system against TEOF principles:

### Pattern C (Stable Core / Adaptive Periphery)

- [ ] **Core defined:** Risk controls documented and non-negotiable
- [ ] **Core protected:** No mechanism exists to override core rules in the heat of trading
- [ ] **Operational layer clear:** Strategy framework defined, review cadence set
- [ ] **Tactical layer adaptive:** Individual trade decisions can vary without violating core

### Layer 4: Defense (Degeneracy)

- [ ] **Loss limitation:** 2+ different mechanisms (stop loss + time stop + thesis invalidation)
- [ ] **Position protection:** 2+ different mechanisms (% risk + max $ + max % portfolio)
- [ ] **Portfolio protection:** 2+ different mechanisms (drawdown trigger + correlation limits + regime adjustment)
- [ ] **No single point of failure:** System survives any single mechanism failing

### Layer 5: Intelligence (Correction Mechanisms)

- [ ] **Trade-level correction:** Post-trade analysis required for every trade
- [ ] **Strategy-level correction:** Weekly metrics review with defined thresholds
- [ ] **System-level correction:** Monthly edge validation review
- [ ] **Edge decay detection:** Explicit trigger for when rolling performance drops below threshold
- [ ] **Catastrophic correction:** Drawdown pause trigger defined and automated if possible

### Layer 6: Truth (Edge Validation)

- [ ] **Paper trading gate:** Minimum sample size before real capital
- [ ] **Small capital gate:** Minimum duration before scaling
- [ ] **Edge hypothesis explicit:** Can articulate why the system should work
- [ ] **Falsification criteria:** Know what evidence would prove the edge doesn't exist
- [ ] **No wishful thinking:** Probability assessment is honest (see Expected Outcomes)

### Anti-Patterns to Avoid

- [ ] **Not violating core for "special situations"** (Pattern A failure)
- [ ] **Not abandoning structure for "flexibility"** (Pattern B failure)
- [ ] **Not relying on single mechanism for critical functions** (Degeneracy failure)
- [ ] **Not ignoring correction signals** (Intelligence failure)
- [ ] **Not trading on hope rather than edge** (Truth failure)

---

*This system is experimental. Edge must be validated before real capital deployment. Update as learning accumulates.*

---

**TEOF Integration:** v1.0 (2025-12-03)
- Added TEOF Framework Application section
- Added Pattern C architecture mapping
- Added Degeneracy analysis and enhancement recommendations
- Added Correction Mechanisms mapping
- Added TEOF Audit Checklist
