# Trading Framework

Derived from TEOF principles. Maps to multiple layers with emphasis on **Layer 4: Defense** (risk management) and **Layer 5: Intelligence** (strategy refinement).

## Core Principle

Trading is applied observation under uncertainty. The market is a feedback system. Survival precedes profit. Edge comes from refined models, not prediction.

## TEOF Layer Mapping

| Layer | Trading Expression |
|-------|-------------------|
| Unity | Trading identity - what kind of trader are you? |
| Energy | Capital preservation - you can't trade with zero |
| Propagation | Compounding gains, scaling what works |
| Defense | Risk management, position sizing, stop losses |
| Intelligence | Strategy development, backtesting, refinement |
| Truth | Market reality - price is truth, opinions are noise |
| Power | Leverage, market access, execution capability |
| Ethics | No front-running, manipulation, or exploitation |

## Principles

### 1. Survival First
Risk of ruin = permanent exit from the game. Never risk enough to be knocked out. Kelly criterion as upper bound, fractional Kelly in practice.

### 2. Edge Before Size
No edge = gambling. Verify edge through backtesting before committing capital. Paper trade until statistically significant.

### 3. Process Over Outcome
Individual trades are noise. Evaluate the process, not the P&L of single trades. Did you follow the system?

### 4. Automate Decisions
Discretionary trading invites emotional interference. Algo execution removes in-the-moment bias. Code the rules.

### 5. Respect Uncertainty
Models are maps, not territory. Markets are non-stationary. What worked will eventually stop working. Continuous observation required.

### 6. Cut Losses, Let Winners Run
Asymmetry is the game. Small losses, large gains. This is psychologically hard - which is why it works.

## Risk Management

### Position Sizing
- Never risk more than 1-2% of capital per trade
- Adjust size to volatility (ATR-based sizing)
- Correlation matters - don't over-concentrate in correlated positions

### Drawdown Limits
- Daily loss limit: Stop trading after X% down
- Max drawdown threshold: Reduce size or pause after Y% peak-to-trough
- Recovery math: 50% loss requires 100% gain to recover

### Diversification
- Multiple uncorrelated strategies
- Multiple timeframes
- Multiple instruments (if applicable)

## Strategy Development

### The Loop (Minimal Loop Applied)
1. **Observe** - Identify potential pattern or inefficiency
2. **Hypothesize** - Formalize into testable rules
3. **Backtest** - Test against historical data
4. **Validate** - Out-of-sample testing, walk-forward analysis
5. **Deploy** - Paper trade, then small size, then scale
6. **Monitor** - Track performance, detect regime change
7. **Refine** - Adjust or retire based on evidence

### Backtest Hygiene
- No lookahead bias
- Account for transaction costs, slippage
- Sufficient sample size
- Out-of-sample holdout
- Be skeptical of curve-fitted results

## Failure Modes

- **Overconfidence**: Sizing up after wins (recency bias)
- **Revenge trading**: Increasing risk after losses to "get back"
- **Curve fitting**: Optimizing to past data, failing on new data
- **Ignoring costs**: Strategy looks good until fees eat the edge
- **Style drift**: Abandoning system during drawdown, then missing recovery
- **Survivorship bias**: Only seeing strategies that worked (ignoring failed attempts)

## Algo-Specific Considerations

### Infrastructure
- Execution latency (matters for some strategies, not others)
- Data quality and reliability
- Monitoring and alerting
- Failure modes: connection loss, API limits, exchange outages

### Code Discipline
- Version control all strategies
- Logging for post-trade analysis
- Paper trade environment mirrors live
- Kill switches and circuit breakers

## Decision Framework

Before any trade or strategy deployment:
1. What is the edge? (Layer 5: Intelligence)
2. What can I lose? (Layer 4: Defense)
3. Am I following the system or improvising? (Layer 6: Truth)
4. Can I survive being wrong 10 times in a row? (Layer 2: Energy)

## Related

- `finances.md` - Overall capital management
- Projects: Specific strategy implementations, backtests, trading journals
