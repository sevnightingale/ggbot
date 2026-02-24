# ggArena Season 1 Results: What Happened When 44 AI Bots Competed for 21 Days

**Status:** Revised draft, ready for Sev review
**Primary keyword:** ai trading competition
**Secondary keywords:** autonomous trading bots, ai agent performance, vibe trading, ai trading results
**Estimated length:** ~1,800 words
**Platform:** ggbots blog

**MDX frontmatter (for publishing):**
```
title: "ggArena Season 1 Results: What Happened When 44 AI Bots Competed for 21 Days"
description: "44 AI trading bots competed for 21 days in ggArena Season 1. The top 6 had manual intervention. Here's what the autonomous bots reveal about AI trading performance."
date: "2026-02-24"
author: "Sev"
authorTwitter: "@SevNightingale"
keywords:
  - ai trading competition
  - autonomous trading bots
  - ai agent performance
  - vibe trading results
  - crypto trading bots 2026
```

---

Season 1 of the ggArena is complete. 21 days, 44 AI trading bots, a $2,500 prize pool, and 1,156 trades.

The top of the leaderboard turned $10,000 into $126,965, a 1,169% return. The bottom turned $10,000 into $4,149, a loss of 58%.

Between those extremes: a dataset that reveals something the leaderboard alone doesn't show.

The six highest-returning bots all had manual intervention.

The numbers tell the real story.

---

## The Podium

**Overall:**

| # | Bot | Symbol | Trades | Win Rate | Return | Manual Closes |
|---|-----|--------|--------|----------|--------|---------------|
| 1 | denchik4 | ETH/USDT | 12 | 91.7% | +1,169.7% | 11 |
| 2 | Lil Shawty | SOL/USDT | 20 | 50.0% | +147.2% | 3 |
| 3 | THE MEG 7: Sharky's Revenge | SOL/USDT | 22 | 59.1% | +135.9% | 13 |
| 4 | CARROT | SOL/USDT | 71 | 47.9% | +100.8% | 2 |
| 5 | SOL Trader | SOL/USDT | 150 | 47.3% | +87.5% | 1 |

**Autonomous AI Leaderboard** (bots with zero manual intervention):

| # | Bot | Symbol | Trades | Win Rate | Return |
|---|-----|--------|--------|----------|--------|
| 1 | The Arbiter | BTC/USDT | 16 | 37.5% | +45.1% |
| 2 | SqueezePulse Marauder | SOL/USDT | 93 | 39.8% | +38.2% |
| 3 | Kdott | BTC/USDT | 33 | 24.2% | +14.4% |

The Autonomous leaderboard isolates pure AI performance. No manual trade closures, no mid-competition config changes, no human cherry-picking. Every number reflects exactly what the agent decided on its own.

If you're unfamiliar with how these agents work, we break down the core concept in [What is Vibe Trading?](/blog/what-is-vibe-trading).

**Competition summary stats:**
- 44 bots entered across 21 days (January 21 to February 11, 2026)
- 1,156 total trades executed during the competition window
- 16 bots finished profitable, 15 finished negative, 13 never placed a trade
- Best autonomous return: The Arbiter +45.1%
- Worst overall return: Moon boy -58.5% (107 trades)
- Spread between first and last: 1,228 percentage points

---

## What the Data Shows

### 1. The Manual Intervention Problem

This is the most important finding from Season 1.

The top six bots on the overall leaderboard all had manual intervention. Users changed their bots' settings mid-competition or manually closed trades outside the AI's decision engine.

| Bot | Rank | Return | Manual Closes | Max Leverage | Pattern |
|-----|------|--------|---------------|-------------|---------|
| denchik4 | 1st | +1,169.7% | 11 of 12 | 100x | Nearly all trades manual, human day-trading via bot |
| Lil Shawty | 2nd | +147.2% | 3 of 20 | 85x | One manual close at 85x accounted for most of the P&L |
| THE MEG 7 | 3rd | +135.9% | 13 of 22 | 50x | 50x day-trading (0-7 min holds), then switched to autonomous |
| CARROT | 4th | +100.8% | 2 of 71 | 75x | Mostly autonomous, but 2 manual closes at extreme leverage drove the return |
| SOL Trader | 5th | +87.5% | 1 of 150 | 75x | Borderline: genuine autonomous performance with one minor manual close |
| The FUNDER | 6th | +80.7% | 13 of 27 | 10x | Cherry-picked winners to close manually, losers hit stop loss |

The first genuinely autonomous bot, The Arbiter, sits at 7th overall with +45.1%.

This doesn't invalidate the overall results. These traders used the platform creatively. But the overall leaderboard measures something different from autonomous AI performance, and the competition was framed as the latter.

One user registered 7 bots, occupying positions #2 through #5 and beyond. Five of those seven had manual intervention. Another user registered 9 bots but only 2 actively traded. Season 2 addresses both issues.

### 2. Win Rate Is the Wrong Metric

The most counterintuitive signal in the data: win rate barely predicts returns.

The Arbiter won the Autonomous leaderboard with a 37.5% win rate, winning just 6 of 16 trades. Kdott came third with 24.2%. Meanwhile, denchik2 had a 57.1% win rate and lost 17.3% of its portfolio. MrJackson won 60.7% of trades and lost 36%.

What matters isn't how often you're right. It's whether your wins are larger than your losses. A bot that wins 37% of the time but lets profits run and cuts losses quickly will outperform one that wins 60% but closes gains too early.

The Arbiter's average winning trade was substantially larger than its average loss. The high-win-rate losers had the opposite profile: frequent small wins overwhelmed by occasional large losses.

This is the same principle that governs profitable human trading. The AI didn't change the underlying math. It made the patterns more visible. [Confidence-based position sizing](/blog/what-is-vibe-trading#confidence-scoring) is central to how vibe trading agents manage this tradeoff.

### 3. The Selectivity Question

The hypothesis going in: fewer trades, better results. The data is more nuanced than that.

The Arbiter won the autonomous leaderboard with 16 trades. Patient, selective, high-conviction entries only.

But SqueezePulse Marauder finished second with 93 trades, nearly six times as many. FENT REACTOR placed 128 trades and still finished positive (barely, at +1.5%). High activity isn't automatically the problem.

On the losing side, The Contrarian made 70 trades and lost 43.2%. Moon boy made 107 trades and lost 58.5%. LilStarScream made 94 trades and lost 9.7%.

The pattern isn't "fewer trades win." High frequency amplifies whatever edge, or lack of edge, a bot has. A well-configured high-frequency bot can work. A poorly configured one will lose faster.

The Compass made only 8 trades and lost 48.2%, going 0 for 8. Low frequency didn't save it from having no edge at all.

---

## The Storylines Worth Noting

**The Arbiter's genuine achievement.** +45.1% over 21 days with 16 trades, zero intervention, a 37.5% win rate, and maximum 10x leverage. A well-configured autonomous agent that outperformed through patience and disciplined risk management. It didn't need 100x leverage or manual saves. It won by being right enough, sized correctly, on the trades it chose to take.

**SqueezePulse Marauder's counterpoint.** 93 trades, 39.8% win rate, +38.2% return, 12x max leverage. The second-best autonomous bot took the opposite approach: high activity, moderate leverage. This proves there isn't one right way to build a profitable bot. The constraint is discipline, not style.

**The losing side.** The bottom five bots (Moon boy at -58.5%, The Compass at -48.2%, Rhoda at -46.2%, The Contrarian at -43.2%, MrJackson at -36.0%) collectively lost an average of 46% of their portfolios. Moon boy's 107 trades at a 40.2% win rate is the clearest illustration: close enough to break even on accuracy, but the losses were consistently larger than the wins.

---

## What We Learned

Season 1 gave us real data. Not a backtest, not a simulation. 44 bots making live decisions in live markets across 21 days.

The clearest takeaways:

**Manual intervention dominated the leaderboard.** The top 6 bots all had human involvement, from outright manual day-trading at 100x leverage to strategic cherry-picking of winning exits. Season 2 locks this down in code.

**Win rate is the wrong goal.** Optimize for risk/reward, not accuracy. The two best autonomous bots won 37.5% and 39.8% of their trades respectively. Multiple bots with 55%+ win rates finished deep in the red.

**Configuration matters more than model.** Every bot in this competition had access to the same class of AI models. The difference between +45% and -58% wasn't the model. It was how the bot was configured to use it: position sizing, confidence thresholds, and patience.

**There's no single winning style.** The Arbiter won with patience (16 trades). SqueezePulse Marauder nearly matched it with activity (93 trades). What they shared: disciplined execution and zero manual intervention.

---

## Season 2

Season 2 is coming. We'll announce dates and format once confirmed.

What's changing: enforcement in code. Config locks on registration. No manual closes. Leverage caps. Per-user bot limits. An audit trail badge distinguishing fully autonomous bots from anything else.

Season 1 showed us what autonomous AI trading looks like, and exactly where the rules need to be tighter. Season 2 is built on those lessons.

If you want to compete, start building now. The Autonomous AI Leaderboard is where we'll be watching most closely. That's where pure AI performance gets tested.

**[Build your bot at app.ggbots.ai](https://app.ggbots.ai)**

---

*ggArena Season 1 ran January 21 to February 11, 2026. 44 AI trading bots. $2,500 prize pool. All bots started with $10,000 in paper capital. Results based on competition-end snapshot captured February 12, 2026.*
