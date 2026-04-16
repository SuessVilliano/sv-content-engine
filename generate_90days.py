#!/usr/bin/env python3
"""
SV Content Engine — 90-Day Script Library Generator
Creates day_XX_vox_ready.txt and day_XX_social.txt for days 6-90
Follows SV voice rules: no contractions, '...' pauses, short sentences, calm/certain tone.
Pillar rotation: Mindset (1-14) → Discipline (15-28) → Strategy (29-42) → Reality (43-56) → repeat
"""
import os

BASE = "/Users/jamaurjohnson/Documents/SV_Content_Engine/scripts"
os.makedirs(BASE, exist_ok=True)

TAGS = "#trading #trader #daytrader #forex #stocks #tradermindset #discipline #patience #psychology #consistency #hybridfunding #sourcevessele #wealth #financialfreedom #mindset #growthmindset #tradinglife #marketsmastery #funded #proptrading"

# Days 6-90 content data
# Format: (day, pillar, hook, vox_script, ig_caption)
DAYS = [

# ═══════════════════════════════════════════════════════
# MINDSET — Days 6-14
# ═══════════════════════════════════════════════════════

(6, "MINDSET",
"Confidence does not come from belief. It comes from evidence.",
"""Pay attention.

Confidence in trading is not something you decide to have.

It is something you earn.

You earn it from data.
From a track record.
From proof that your process works.

Most traders are waiting to feel confident before they follow their rules.

That is backwards.

Follow the rules first.
Document the results.
Let the evidence build the confidence.

Belief without evidence is hope.
You are not trading hope.

Source Vessel. Hybrid Funding.""",
"""Confidence in trading is not a feeling you wait for.

It is a record you build.

Follow the rules. Document the results. Let the evidence do the work.

That is the only confidence worth trading on."""),

(7, "MINDSET",
"The work you do alone determines what you become in public.",
"""Most people want results in public.

They want the wins. The recognition. The proof.

But the work happens alone.

Before the market opens. After it closes.
In the journal. In the review. In the silence.

There is no shortcut to the work.
There is no audience for most of it.

That is the point.

The trader who does the private work...
becomes the trader who produces public results.

Do the work nobody sees.

Source Vessel. Hybrid Funding.""",
"""The wins happen in public. The work happens alone.

Before the market opens. In the journal. In the review. In the silence.

Most people want the results without the private work. Do the work nobody sees."""),

(8, "MINDSET",
"You are not a trader who needs to make money today. You are a trader who follows a plan.",
"""Pay attention.

There are two versions of you at the chart.

The first version needs the money.
That version is scared. Impatient. Willing to break rules.

The second version follows the plan.
That version is calm. Selective. Trusts the process.

The market can feel which version showed up.

Your job is not to make money today.
Your job is to execute correctly today.

The money is the outcome.
Execution is the input.

Control what you can control.

Source Vessel. Hybrid Funding.""",
"""Two versions show up to the chart.

One needs the money. One follows the plan.

They make completely different decisions.

Your job is execution. The money is the outcome of that — not the goal of it."""),

(9, "MINDSET",
"Process score versus P&L score. One of these you control.",
"""Here is a shift that changes everything.

Stop scoring yourself on your P&L.
Start scoring yourself on your process.

Did you follow your entry criteria?
Did you honor your stop?
Did you stick to your session hours?
Did you journal every trade?

That is your real score.

A green day with broken rules is a loss in disguise.
A red day with perfect process is evidence your edge works.

Score the process.
Let the P&L take care of itself.

Source Vessel. Hybrid Funding.""",
"""Score your process. Not your P&L.

A green day with broken rules is a warning.
A red day with clean execution is proof your edge is working.

One of these scores you actually control."""),

(10, "MINDSET",
"How you start the session determines how you trade the session.",
"""The first ten minutes before you trade are more important than most traders realize.

Not chart analysis.
Not signal hunting.

Mental preparation.

What is your intention for this session?
What is your maximum acceptable loss?
Are you clear? Rested? Present?

Or are you distracted? Anxious? Carrying yesterday?

The market responds to the version of you that showed up.

Start the session correctly.
Everything else follows from that.

Source Vessel. Hybrid Funding.""",
"""The first ten minutes before you trade determine the quality of every trade after.

Not chart analysis. Mental preparation.

Intention. Loss limit. Mental state. These come before the chart."""),

(11, "MINDSET",
"After a loss, there is one rule. Twenty minutes before your next trade.",
"""Here is a rule that has saved traders from their worst sessions.

After a significant loss...
do not trade for twenty minutes.

Walk away from the screens.
Let the emotion move through you.
Reset your state.

Because the trade you take in the first five minutes after a loss...
is not a trade.
It is a reaction.

Reactions are expensive.
Responses are profitable.

Twenty minutes. Every time. No exceptions.

Source Vessel. Hybrid Funding.""",
"""After a significant loss: twenty minutes away from the screens. Every time.

The trade you take in the first five minutes after a loss is not a trade. It is a reaction.

Reactions are expensive. Responses are profitable."""),

(12, "MINDSET",
"Structure outlasts willpower every time. That is why funded traders win.",
"""Willpower runs out.

Every trader has felt it.
The discipline that holds for three weeks...
and then breaks on a Tuesday for no clear reason.

Structure does not run out.

A funded account with daily loss limits, maximum drawdown rules, and set risk parameters...
gives you external structure when your internal structure fails.

This is not a weakness.
This is intelligent design.

Build structure. Then trade inside it.

Source Vessel. Hybrid Funding.""",
"""Willpower runs out. Structure does not.

A funded account with loss limits and drawdown rules gives you external structure when your internal discipline fails.

Build structure. Trade inside it. That is intelligent design."""),

(13, "MINDSET",
"One undisciplined session can erase three weeks of work. That is the real cost.",
"""Most traders calculate the cost of a bad session in dollars.

That is not the full cost.

One session where you broke every rule...
sends a signal to your brain.
That rule-breaking is acceptable.
That your system is optional.
That emotions can override structure.

That signal takes weeks to undo.

The real cost of one undisciplined session is not the loss.
It is the permission it gives your future self.

Guard every session.

Source Vessel. Hybrid Funding.""",
"""The real cost of one undisciplined session is not the dollar loss.

It is the permission it gives your brain to break rules again next time.

One bad session can take weeks to undo. Guard every session."""),

(14, "MINDSET",
"Consistency is not a strategy. It is the proof that your strategy is real.",
"""Everyone talks about consistency.

But consistency is not a thing you decide to have.
It is the output of a hundred small correct decisions.

The consistent pre-market routine.
The consistent risk per trade.
The consistent post-session review.

Consistency is not the destination.
It is the proof you arrived.

When your results are consistent...
it means your process is consistent.

Build the process first.
Consistency appears on its own.

Source Vessel. Hybrid Funding.""",
"""Consistency is not something you decide to have.

It is the output of a hundred small correct decisions made the same way every single day.

Build the process. Consistency is the proof it is working."""),

# ═══════════════════════════════════════════════════════
# DISCIPLINE — Days 15-28
# ═══════════════════════════════════════════════════════

(15, "DISCIPLINE",
"The journal is not optional. It is the strategy.",
"""Most traders are looking for a better strategy.

The better strategy is already in front of them.

It is the journal.

Your journal contains the patterns you cannot see in the moment.
The setups that cost you. The sessions you should have skipped.
The entries that keep working. The exits that keep failing.

The market gives you feedback every single day.
The journal is how you collect it.

No journal means no feedback loop.
No feedback loop means no improvement.

Write it down. Every session.

Source Vessel. Hybrid Funding.""",
"""The journal is not a habit for disciplined traders.

It is the reason they are disciplined.

It contains the patterns you cannot see in the moment. Write every session."""),

(16, "DISCIPLINE",
"One rule. Followed completely. That is the standard.",
"""You do not need a hundred rules.

You need one rule...
followed without exception.

Pick your highest-value rule.
The one you break most often.
The one that costs you the most when you break it.

Now follow it completely.
Not most of the time.
Not when it is convenient.
Every single time.

One rule honored completely is worth more than ten rules followed loosely.

Start there.

Source Vessel. Hybrid Funding.""",
"""You do not need more rules. You need to honor the ones you have.

Pick the rule you break most often. The one that costs you the most.

Now follow it without exception. One rule honored completely changes everything."""),

(17, "DISCIPLINE",
"The trade you deliberately skip is a trade you won. Learn to count it.",
"""There is a trade in every session that does not quite fit.

The setup is almost there.
The conditions are almost right.
The conviction is almost present.

Most traders take this trade.

The disciplined trader does not.

And then they count the skip.
They write it in the journal.
'Saw it. Passed it. Correct.'

The skip is a win.
Start counting it as one.

Source Vessel. Hybrid Funding.""",
"""The trade you deliberately pass is a trade you won.

Write it in the journal. 'Saw it. Passed it. Correct.'

The skip is a discipline win. Start counting it as one."""),

(18, "DISCIPLINE",
"Position sizing is discipline made visible in a single number.",
"""You can say you are disciplined.

Or you can show your position size.

An oversized position exposes every break in your discipline.
The fear. The greed. The need to recover fast.

A correctly sized position is calm.
It does not need the trade to work.
It can take the loss cleanly and move forward.

Position sizing is where discipline becomes real.

Not in a rule book.
In the actual number you type before you press enter.

Source Vessel. Hybrid Funding.""",
"""Your position size is a direct measurement of your discipline.

Oversized = fear, greed, or desperation. Correctly sized = calm, clean, process-driven.

The number you type before every trade tells the truth."""),

(19, "DISCIPLINE",
"The pre-session routine is where professional traders are made.",
"""By the time the market opens, the preparation should be complete.

Key levels marked.
High-impact news noted.
Position size calculated.
Mental state checked.

The professional trader is not making decisions at open.
The professional trader is executing decisions made before open.

Build a pre-session routine so consistent...
that when price hits your level, you react without hesitation.

The routine is the edge.

Source Vessel. Hybrid Funding.""",
"""By the time the market opens, the decisions should already be made.

Levels. News. Risk. Mental state.

The routine that happens before the session is where professional trading is built."""),

(20, "DISCIPLINE",
"The emotional reset is part of the trading process. Build it deliberately.",
"""Before you trade, you need to be in a specific mental state.

Calm. Present. Detached from outcome.

If you are carrying stress from outside the market...
carry it to a walk, not to the chart.

If you are carrying the last session's loss...
carry it to the journal, not to the next trade.

The emotional reset is not weakness.
It is preparation.

Build it into your process as deliberately as you build your chart analysis.

Source Vessel. Hybrid Funding.""",
"""Before the chart: the mental reset.

Stress, frustration, yesterday's loss — carry those to a walk or a journal. Not to the next trade.

The reset is preparation. Build it deliberately."""),

(21, "DISCIPLINE",
"Discipline on a winning day is just as important as discipline on a losing one.",
"""Winning days are when discipline gets broken most often.

Three wins in a row and the brain starts negotiating.
'I know what I am doing today. Let me add one more.'
'I am feeling it. Let me size up slightly.'

The winning streak creates the biggest drawdown.

Your rules do not change because the session is going well.

Honor the system on green days.
That is the real test.

Source Vessel. Hybrid Funding.""",
"""The biggest drawdowns come after winning streaks.

Because discipline breaks when confidence is highest.

Your rules do not change because the session is going well. Honor the system on green days especially."""),

(22, "DISCIPLINE",
"The end-of-session review is not optional. It is when the next session is built.",
"""Most traders close the platform and walk away.

The disciplined trader sits down first.

What happened today?
What worked and why?
What did not work and why?
What would I do differently?

This takes fifteen minutes.
And it changes everything about tomorrow.

The next session is built in the review of this one.

If you skip the review, you skip the improvement.

Source Vessel. Hybrid Funding.""",
"""The end-of-session review is where the next session is built.

What worked. What didn't. What you would do differently.

Fifteen minutes. Every session. That is where the improvement lives."""),

(23, "DISCIPLINE",
"The stop-loss is not doubt. It is the most disciplined thing you do.",
"""Placing a stop-loss is not an expression of doubt.

It is the most disciplined act in the trade.

You are saying:
'I know where I am wrong. And I have defined the price I am willing to pay for it.'

That is not weakness.
That is precision.

The trader who removes stops is not confident.
That trader is undisciplined.

Set the stop. Honor it completely.
Never move it against yourself.

Source Vessel. Hybrid Funding.""",
"""Setting a stop-loss is not doubt. It is precision.

You have defined exactly where you are wrong and exactly what that will cost you.

Never remove it. Never move it against yourself. That is discipline, not doubt."""),

(24, "DISCIPLINE",
"Knowing when to walk away is one of the highest-value skills in trading.",
"""There is a skill most traders never develop.

The skill of walking away.

When you have hit your daily max loss.
When three consecutive stop-outs have happened.
When your mind is clearly not in the right place.

Walking away is not losing.
It is protecting what remains.

The discipline to stop is harder than the discipline to start.
But it is worth infinitely more.

Know when the session is done.

Source Vessel. Hybrid Funding.""",
"""Knowing when the session is done is a high-value skill.

Max loss hit. Three stop-outs. Mind not right.

Walking away in those moments is not losing. It is protecting what remains."""),

(25, "DISCIPLINE",
"Discipline in a drawdown is the most important discipline you will ever practice.",
"""Drawdowns test everything.

Your system. Your sizing. Your process.
But most importantly, your discipline.

The urge to abandon the strategy that is underperforming.
The urge to size up to recover faster.
The urge to take trades outside your plan.

Every one of these urges, if acted on, converts a temporary drawdown into a permanent loss.

Stay the process.
Size correctly.
Let the edge play out.

Discipline in a drawdown defines careers.

Source Vessel. Hybrid Funding.""",
"""Drawdowns test discipline more than any other condition.

The urge to abandon strategy, size up, or break rules — if acted on, converts a temporary drawdown into a permanent one.

Stay the process. Discipline in a drawdown defines careers."""),

(26, "DISCIPLINE",
"Screen time is not the same as productive time. Know the difference.",
"""Sitting in front of the charts for eight hours is not work.

It is exposure.

Productive trading time is defined.
Pre-session analysis. The actual session. Post-session review.

Everything beyond that is noise consumption.
Watching price move for no reason. Second-guessing closed trades. Looking for reasons to stay in the market.

Define your productive hours.
Work within them.
Close everything else.

More screen time creates worse decisions.
Not better ones.

Source Vessel. Hybrid Funding.""",
"""Eight hours at the charts is not work. It is exposure.

Productive trading time has a start, a purpose, and an end.

Define your session hours. Work within them. Close everything else."""),

(27, "DISCIPLINE",
"Doing nothing is a trade. The most underrated one in the market.",
"""The market will always present something that looks like an opportunity.

That is its design.

Your job is not to take every opportunity.
Your job is to take the specific opportunities that fit your edge.

Everything else is noise.

Doing nothing — deliberately, consciously, with a reason — is a trade.
It is the trade of choosing not to act.

The most disciplined traders in the world are masters of doing nothing.

Source Vessel. Hybrid Funding.""",
"""Doing nothing is a trade. The most underrated one.

The market always looks like it is offering something. Your job is to take only what fits your edge.

Deliberate inaction is a skill. Master it."""),

(28, "DISCIPLINE",
"Accountability is structure. Structure outlasts motivation.",
"""Most traders rely on motivation.

Motivation runs out. Accountability does not.

Having someone who reviews your journal.
A rule set you cannot quietly break without record.
A daily loss limit you have committed to in writing.

These are external accountability structures.

They work when your internal discipline fails.
And your internal discipline will fail.
Not always. Not often if you train it.
But it will fail.

Build external structures now.
They will carry you when everything else runs out.

Source Vessel. Hybrid Funding.""",
"""Motivation runs out. Accountability structures do not.

A journal reviewed by someone else. A loss limit written and committed to. External structures.

Build them now. They will carry you when internal discipline fails."""),

# ═══════════════════════════════════════════════════════
# STRATEGY — Days 29-42
# ═══════════════════════════════════════════════════════

(29, "STRATEGY",
"One setup. Mastered completely. That is a trading career.",
"""Most traders know ten setups moderately well.

The profitable trader knows one setup completely.

Every condition it works in. Every condition it fails in.
The ideal entry. The ideal exit. The confluence that makes it A-grade.

One setup, traded with that depth of understanding...
produces more consistency than ten setups traded with moderate understanding.

Pick your setup.
Study it until you know it better than anyone.

That depth is the edge.

Source Vessel. Hybrid Funding.""",
"""Most traders know ten setups moderately well.

Profitable traders know one setup completely — every condition, every confluence, every failure mode.

One setup mastered is a trading career. Pick yours."""),

(30, "STRATEGY",
"Confluence is not about more indicators. It is about independent confirmation.",
"""Adding more indicators does not create confluence.

It creates noise.

True confluence means the same signal appears from independent sources.

Price structure and volume.
Session timing and key level.
Higher timeframe direction and lower timeframe entry.

When multiple independent factors align...
the probability of the setup increases.

When indicators all measure the same thing differently...
you have one signal in three windows.

Learn the difference.

Source Vessel. Hybrid Funding.""",
"""True confluence is independent confirmation — not more indicators measuring the same thing.

Price structure, session timing, volume, higher timeframe direction. These are independent inputs.

When they align, probability increases. That is the real meaning of confluence."""),

(31, "STRATEGY",
"Trade your session. The market is always open. Your edge is not.",
"""The market runs twenty-four hours.

Your edge does not.

Every setup has an optimal session.
London open. New York open. Overlap.
The hours when volume and volatility match your strategy.

Trading outside your session does not expand your opportunities.
It dilutes your edge.

Know your session.
Trade within it only.
Close the platform outside of it.

Your edge is session-specific.
Honor that.

Source Vessel. Hybrid Funding.""",
"""The market is always open. Your edge is not.

Every setup has an optimal session — the hours where volume and volatility match your strategy.

Trading outside your session dilutes your edge. Know it. Stay inside it."""),

(32, "STRATEGY",
"A risk-reward ratio only works if your entries are selective enough to achieve it.",
"""A 1:2 risk-reward sounds excellent in theory.

In practice, it requires patience.

You cannot force a 1:2 setup.
You must wait for the entry that gives the market enough room to reach target 2 before it can reach your stop.

That means being selective.
That means passing B-grade setups.
That means waiting for the exact entry, not the approximate one.

Risk-reward is not a goal.
It is the result of precise entry discipline.

Source Vessel. Hybrid Funding.""",
"""A 1:2 risk-reward ratio only works if your entry is precise enough to achieve it.

You cannot force the ratio. You must wait for the exact entry that gives price room to run before it can reach your stop.

Risk-reward is the result of disciplined entry — not a target you set."""),

(33, "STRATEGY",
"Market structure shows you where price wants to go. Everything else is commentary.",
"""Before any indicator. Before any signal.

Read the structure.

Higher highs and higher lows — price is in an uptrend.
Lower highs and lower lows — price is in a downtrend.
Consolidation between clear levels — price is ranging.

This tells you the direction before you look at anything else.

The simplest read in trading is often the most powerful.

Read the structure.
Let everything else confirm it.

Source Vessel. Hybrid Funding.""",
"""Before any indicator: read the structure.

Higher highs and higher lows. Lower highs and lower lows. Clear ranging levels.

Market structure tells you where price wants to go before any signal confirms it."""),

(34, "STRATEGY",
"The fake breakout is not a trap for everyone. For the patient trader, it is the setup.",
"""The fake breakout is the market's most common trap.

Price breaks above resistance.
Retail traders enter long.
Price reverses immediately and hunts their stops.

But for the patient trader...
the fake breakout is the entry.

Wait for the breakout. Watch it fail.
Then enter in the direction of the reversal.
The stops of the trapped traders become the fuel for your trade.

Learn to trade the trap instead of falling into it.

Source Vessel. Hybrid Funding.""",
"""The fake breakout is a trap for impatient traders and a setup for patient ones.

Watch the break. Watch it fail. Enter the reversal as trapped traders' stops become fuel for the move.

Learn to use the trap."""),

(35, "STRATEGY",
"News events are not the enemy. Trading them without a plan is.",
"""High-impact news creates volatility.

Volatility is not the enemy.
Unplanned volatility is.

There are two valid approaches to news.

One: step aside completely. Mark it on the calendar. Skip the session.
Two: trade the post-news structure. Wait for the initial reaction to settle, then trade the confirmed direction.

There is no valid third approach.
Trading through news without a plan is speculation.

Know your news approach before the event.

Source Vessel. Hybrid Funding.""",
"""News is not the enemy. Trading it without a plan is.

Two valid approaches: step aside completely, or trade the post-news structure after the initial reaction settles.

Know your approach before the event — not during it."""),

(36, "STRATEGY",
"Time-based exits remove emotion from the trade. Price-based exits maximize efficiency.",
"""There are two exit philosophies.

Time-based: close all positions at the end of the session regardless of where they are.
This removes the overnight risk. It removes emotional attachment to position.

Price-based: exit when your target is hit or your stop is reached.
This is cleaner in theory. It requires stronger discipline in practice.

Most traders benefit from combining both.
A stop and target in place. Plus a session close rule.

The exit strategy is as important as the entry.
Design it before the trade opens.

Source Vessel. Hybrid Funding.""",
"""Time-based exits remove emotion. Price-based exits maximize efficiency.

Most traders benefit from both: a stop and target in place, plus a session hard close.

Design the exit strategy before the trade opens — not while you are in it."""),

(37, "STRATEGY",
"Backtesting tells you what your setup has done. Forward testing tells you if you can execute it.",
"""Most traders backtest to find confidence in their setup.

That is the wrong use of backtesting.

Backtesting tells you what the setup did in historical data.
Forward testing tells you if you can execute the setup in live conditions.

They are different skills.

The setup that looks perfect in backtest...
will challenge your discipline in real-time.

Backtest to understand the edge.
Forward test to develop the execution.
Live trade to produce the results.

Each phase has a specific purpose.

Source Vessel. Hybrid Funding.""",
"""Backtesting tells you what a setup has done historically.

Forward testing tells you if you can execute it in real conditions.

They are different skills. Use each for its specific purpose."""),

(38, "STRATEGY",
"Scaling into a position is not averaging down. It is building on confirmation.",
"""There is an important distinction.

Averaging down is adding to a losing position because you believe it will come back.
That is hope-based risk management. It is dangerous.

Scaling in is adding to a position as it confirms your thesis.
Price moves in your direction. Structure holds. You add with confirmation.

One adds to failure.
One builds on success.

If you are going to add to positions...
only do it when the trade is proving you right.

Source Vessel. Hybrid Funding.""",
"""Averaging down adds to failure. Scaling in builds on confirmation.

Only add to a position when price is proving you right — structure holding, direction confirmed.

Never add because you believe a losing position will come back."""),

(39, "STRATEGY",
"The partial take-profit is not indecision. It is intelligent risk management.",
"""Taking partial profits at the first target is not weak.

It is removing risk from the trade while maintaining participation in the move.

Take fifty percent off at target one.
Move your stop to breakeven on the remainder.

Now you have secured a gain.
Your remaining position costs you nothing.
And you are still in the trade if it continues.

You do not have to choose between securing profit and letting winners run.
The partial exit lets you do both.

Source Vessel. Hybrid Funding.""",
"""Partial take-profit at target one is not indecision. It is intelligent management.

Take half off. Move stop to breakeven. The remaining position costs you nothing.

You secure profit and stay in the move. Both at once."""),

(40, "STRATEGY",
"Two correlated positions are one position with double exposure. Never forget that.",
"""You can think you are diversified when you are not.

Two USD-denominated pairs moving on dollar sentiment.
Two risk assets responding to the same macro event.
Two positions that rise and fall together.

That is not diversification.
That is one trade with twice the risk.

Before you add a second position, ask one question.
Are these trades independent of each other?

If they are not independent, they are correlated.
Correlated positions compound your exposure without compounding your edge.

Source Vessel. Hybrid Funding.""",
"""Two correlated positions are one trade with double exposure.

If they move on the same underlying factor — dollar sentiment, risk-on flows, central bank decisions — they are not diversified.

Ask: are these trades independent? If not, they are one trade."""),

(41, "STRATEGY",
"The market phases dictate the strategy. The strategy does not dictate the phase.",
"""Your strategy is not designed for all market conditions.

No strategy is.

Trend-following strategies fail in ranges.
Mean-reversion strategies fail in trends.
Breakout strategies fail in choppy conditions.

The successful trader identifies the current phase first.
Then selects the strategy appropriate to that phase.
Then executes.

If the phase changes, the strategy changes with it.

The market always leads.
The strategy always follows.

Source Vessel. Hybrid Funding.""",
"""No strategy works in all market conditions.

Trend-following fails in ranges. Mean-reversion fails in trends.

Identify the phase first. Then select the strategy that fits. The market leads. The strategy follows."""),

(42, "STRATEGY",
"The A-plus setup has specific criteria. If it does not meet all of them, it is not A-plus.",
"""The A-plus setup is not a feeling.

It is a checklist.

Your specific conditions that define the highest-probability version of your setup.
Session timing. Structure confirmation. Volume. Level precision.

When all boxes are checked, you execute with full size.
When one box is missing, you pass.

The A-minus setup is not worth full size.
The B-plus setup is not worth taking.

Define your A-plus criteria in writing.
Refuse everything below it.

Source Vessel. Hybrid Funding.""",
"""The A-plus setup is not a feeling. It is a checklist.

Specific conditions that define the highest-probability version of your setup.

If one box is missing, it is not A-plus. Pass it. Only full criteria gets full execution."""),

# ═══════════════════════════════════════════════════════
# REALITY — Days 43-56
# ═══════════════════════════════════════════════════════

(43, "REALITY",
"Most traders do not fail at strategy. They fail at staying long enough to succeed.",
"""Here is the truth most people will not say.

The strategy was probably fine.

The market knowledge was adequate.
The setups were reasonable.
The entries were close enough.

What failed was the staying.

Most traders quit before their edge has had time to produce.
Before the sample size is large enough to evaluate.
Before the learning curve bends.

The filter in this industry is not intelligence.
It is the willingness to stay through the difficult phases.

Source Vessel. Hybrid Funding.""",
"""Most traders do not fail at strategy. They fail at staying long enough.

The market knowledge was there. The setups were close.

What failed was the willingness to stay through the difficult phases. That is the only real filter."""),

(44, "REALITY",
"The funded account path is not a shortcut. It is a structure that forces the correct behavior.",
"""People ask why funded trading exists.

The answer is accountability.

When you trade with your own money without rules...
you make emotional decisions.
You move stops. You average down. You overtrade.

A funded account has hard rules.
A daily loss limit you cannot override.
A maximum drawdown that stops you from destroying yourself.

It is not a shortcut to profits.
It is a structure that forces professional behavior.

And professional behavior is how you eventually get the profits.

Source Vessel. Hybrid Funding.""",
"""A funded account is not a shortcut. It is a structure.

Hard loss limits. Maximum drawdown. Rules you cannot quietly ignore.

That structure forces professional behavior. Professional behavior is what produces professional results."""),

(45, "REALITY",
"Losing is not failure. Losing the same way twice is.",
"""Every professional trader has taken losses.

Many losses. Hundreds of them.
Thousands across a career.

That is not failure.

Failure is taking the same loss twice because you did not examine the first one.

The loss that teaches you nothing...
is the only loss that is truly wasted.

Every other loss is tuition.
Every other loss builds the edge.

Pay attention to what you are paying for.

Source Vessel. Hybrid Funding.""",
"""Losing is not failure. Losing the same way twice is.

Every loss that teaches you something is tuition.

The only truly wasted loss is the one you take again because you did not examine the first one."""),

(46, "REALITY",
"The market is not your enemy. Your own behavior inside it is.",
"""The market does not know your name.

It does not target your stops specifically.
It does not move against you personally.
It does not want you to fail.

It is a mechanism. An aggregate of decisions by millions of participants.

Your enemy is not the market.
Your enemy is the version of you that overrides the plan.
That moves the stop. That sizes up emotionally.
That trades outside the session.

Fix the behavior. The market will cooperate.

Source Vessel. Hybrid Funding.""",
"""The market is not your enemy.

It does not target you personally. It is a mechanism — an aggregate of millions of decisions.

Your enemy is the version of you that overrides the plan. Fix the behavior."""),

(47, "REALITY",
"Profits are not the first goal. Surviving long enough to learn is.",
"""New traders focus entirely on profits.

That is not the first goal.

The first goal is survival.

Staying in the game long enough to collect enough data to understand your edge.
Long enough to recognize your psychological patterns.
Long enough to execute the same plan with consistency.

Profits follow from that.
They cannot precede it.

Trade small first. Survive. Learn. Grow.
The profits are already waiting on the other side of that work.

Source Vessel. Hybrid Funding.""",
"""Profits are not the first goal. Survival is.

Staying in the game long enough to learn your edge, understand your psychology, and build consistent execution.

Profits follow from that work. They cannot precede it."""),

(48, "REALITY",
"A profitable month looks quieter than people expect. It is mostly waiting.",
"""People imagine profitable trading as constant action.

Screens full of positions. Decisions every minute.

A real profitable month looks different.

Three to five quality trades per week.
Most sessions spent observing rather than executing.
A clear daily loss limit that creates a natural stop to the day.
A journal that takes longer to fill than the trading session.

Quiet. Deliberate. Selective.

Profitability is calm in practice.
It is only exciting in the highlight reel.

Source Vessel. Hybrid Funding.""",
"""A profitable month looks quieter than most people expect.

Three to five quality trades per week. Most sessions spent watching, not trading.

Quiet. Deliberate. Selective. Profitability is calm in practice."""),

(49, "REALITY",
"Nobody watches your losing trades. Stop performing for an audience that is not there.",
"""You are performing.

Not always consciously.
But you are.

You hold a losing trade longer than your plan allows...
because walking away with a loss feels like admitting failure.

You do not take the entry that appears at an inelegant time...
because it does not feel like a quality trade.

Nobody is watching.

Take the clean loss.
Take the slightly imperfect entry.
Honor the plan.
Perform for your process — not for an imaginary audience.

Source Vessel. Hybrid Funding.""",
"""You are performing for an audience that is not there.

Holding losers too long because a clean loss feels like failure. Skipping valid entries because they are not elegant enough.

Nobody is watching. Honor the plan. Perform for your process."""),

(50, "REALITY",
"Comparing your chapter two to someone else's chapter twenty is the fastest way to quit.",
"""The trader you see posting results online...

You do not know their starting point.
You do not know their loss history.
You do not know the years of invisible work.
You do not know how many times they almost quit.

You are looking at chapter twenty and comparing it to your chapter two.

That comparison is designed to make you feel behind.
You are not behind.

You are at the beginning of the correct path.

Stay on your path.

Source Vessel. Hybrid Funding.""",
"""The trader posting results online is at chapter twenty. You are at chapter two.

You do not see their starting point, their loss history, or the years of invisible work.

Stay on your path. The comparison is designed to make you quit."""),

(51, "REALITY",
"The overnight account and the five-year account are built by completely different behaviors.",
"""Two accounts.

The overnight account is built on big size, high risk, aggressive entries.
It either blows up or produces a highlight-reel week.

The five-year account is built on consistent process, proper risk, patience, and compound growth.
It survives every difficult phase.
It is still running when everything else has stopped.

Which account are you building?

The behaviors are different.
The decisions are different.
Make the choice deliberately.

Source Vessel. Hybrid Funding.""",
"""Two accounts: overnight and five-year.

The overnight account is built on big risk and produces a highlight week or a blown account.

The five-year account is built on consistent process and is still running when everything else has stopped."""),

(52, "REALITY",
"Ego has a market price. It is always higher than traders expect.",
"""Ego in trading shows up in specific ways.

Not taking a stop because you refuse to be wrong.
Sizing up after wins because you are feeling invincible.
Refusing to follow a rule that your less-experienced self wrote.

Every one of these costs real money.

Ego is the most expensive component in most losing accounts.

Trade with a blank mind.
Let the setup decide. Let the plan execute.
Leave the ego outside the door.

Source Vessel. Hybrid Funding.""",
"""Ego in trading has a specific market price.

Not taking stops. Sizing up after wins. Refusing rules written by a wiser version of yourself.

These cost real money. Leave the ego outside the session. Every time."""),

(53, "REALITY",
"The trader who over-explains their losses is still in the learning phase. That is okay.",
"""Pay attention to how you talk about your losses.

'The market was rigged today.'
'Spread manipulation hit my stop.'
'It would have worked if not for the news event.'

These explanations protect the ego.
They also prevent learning.

When you over-explain a loss, you avoid the real question.

What in my process failed?

The trader who asks that question is building something.
The trader who explains it away is staying still.

Source Vessel. Hybrid Funding.""",
"""The way you talk about losses tells you where you are in the process.

'The market was rigged' protects the ego and prevents learning.

The real question after every loss: what in my process failed? That question builds something."""),

(54, "REALITY",
"A small account teaches discipline in ways a large account cannot.",
"""Starting with a large account sounds like an advantage.

In practice, it often produces reckless behavior.

When the size is large enough that losses do not sting...
the lessons do not stick.

A small account where every trade matters...
creates precision.
Forces correct sizing.
Demands patience for the right setup.

The small account constraints are not limitations.
They are the curriculum.

Master the small account.
The large account follows naturally.

Source Vessel. Hybrid Funding.""",
"""A small account teaches discipline in ways a large one cannot.

When every trade matters, precision follows naturally. Correct sizing. Patience for the right setup.

The small account constraints are the curriculum. Master them."""),

(55, "REALITY",
"Real progress in trading looks like fewer mistakes. Not more winners.",
"""Most traders measure progress by the winning percentage.

Real progress looks different.

Less overtrading this month than last.
Fewer rules broken this week than the week before.
One fewer revenge trade this session.

The mistakes are decreasing.
The process is tightening.
The edge is becoming more reliable.

Progress in trading is visible in the reduction of errors.
The wins follow the errors down.

Source Vessel. Hybrid Funding.""",
"""Real trading progress is visible in fewer mistakes — not more winners.

Less overtrading. Fewer broken rules. One fewer revenge trade.

The process tightens. The errors decrease. The wins follow."""),

(56, "REALITY",
"Natural talent in trading does not exist in the way people think it does.",
"""People talk about natural talent in trading.

There is none.

What looks like talent is pattern recognition developed through thousands of hours of screen time.
What looks like calm is emotional training built through hundreds of difficult sessions.
What looks like confidence is a track record built over years.

Nobody was born to trade.

The 'talented' traders you see...
are the ones who stayed long enough for the skill to appear.

Stay long enough.

Source Vessel. Hybrid Funding.""",
"""Natural talent in trading does not exist.

What looks like talent is pattern recognition from thousands of hours. What looks like calm is trained emotional control.

Nobody was born to trade. They stayed long enough for the skill to appear."""),

# ═══════════════════════════════════════════════════════
# MINDSET CYCLE 2 — Days 57-70
# ═══════════════════════════════════════════════════════

(57, "MINDSET",
"Coming back after a break is a skill. Return with intention, not urgency.",
"""The break ended.

You are back at the chart.

This moment matters.

Not because the market changed.
Because you did.

Rest creates perspective.
Perspective reveals what was unclear before.

Return with intention, not urgency.
Set your session parameters before the open.
Ease back into full size over two or three sessions.

The urge to make up for missed time is the first thing to resist.
The market was open while you were gone.
It will be open tomorrow.

Source Vessel. Hybrid Funding.""",
"""Returning after a break requires intention, not urgency.

The urge to make up for missed time is the first thing to resist.

Ease back in. Reduce size for the first two sessions. Let the perspective the break gave you work for you."""),

(58, "MINDSET",
"A drawdown period is not punishment. It is a recalibration phase.",
"""When the drawdown comes — and it will come — there is a choice.

You can interpret it as punishment.
Evidence that you are not good enough. That the strategy is broken.

Or you can interpret it as recalibration.

The market is showing you something.
A condition your strategy does not handle well.
A timing issue. A sizing issue. A mindset leak.

Go find the signal in the drawdown.
It is always there.

Recalibration, not punishment.

Source Vessel. Hybrid Funding.""",
"""A drawdown is not punishment. It is information.

The market is showing you something your strategy does not handle well.

Go find the signal. Recalibration, not punishment."""),

(59, "MINDSET",
"Know why you are doing this. The reason determines how you behave under pressure.",
"""Under pressure, the reason becomes the anchor.

Why are you trading?

If the answer is money alone... every loss feels like a step away from survival.
That creates desperation decisions.

If the answer is mastery... every loss is a lesson.
That creates learning decisions.

If the answer is freedom... every correct session is progress.
That creates process decisions.

Know your reason.
Write it down.
Read it on your worst days.

The reason is the foundation.

Source Vessel. Hybrid Funding.""",
"""Under pressure, the reason becomes the anchor.

If you trade for money alone, every loss feels like a step away from survival.

Know why you are really doing this. Write it down. Read it on the worst days."""),

(60, "MINDSET",
"Day sixty. The compound effect of sixty consistent sessions is already working beneath the surface.",
"""Day sixty.

Sixty sessions of showing up.
Sixty reviews. Sixty journal entries.
Sixty opportunities to break rules... and not breaking them.

This is not a midpoint.
It is proof.

Proof that you are capable of the sustained work.
That the process is becoming your process.
That the trader you are becoming is already present in how you approach each session.

The compound effect is not visible yet.
But it is working.

Trust it.

Source Vessel. Hybrid Funding.""",
"""Day sixty. Sixty sessions of sustained work.

The compound effect of consistent daily practice is not always visible early.

But it is working beneath the surface. The trader you are becoming is already present in how you approach each session."""),

(61, "MINDSET",
"You are not the same trader who started this. Own the upgrade.",
"""Something has shifted.

You do not take every trade that looks interesting.
You do not hold losers as long as you used to.
You review the session instead of closing and walking away.
The rules feel more natural than they did at the start.

These are not small changes.
These are identity changes.

The trader you were sixty sessions ago made different decisions than the trader you are today.

Own the upgrade.
The improvement is real.

Source Vessel. Hybrid Funding.""",
"""Something has shifted in you as a trader.

The rules feel more natural. The losses are cleaner. The journal is consistent.

These are identity changes, not skill changes. Own the upgrade. It is real."""),

(62, "MINDSET",
"Emotional neutrality is not indifference. It is the ability to respond instead of react.",
"""The goal is not to feel nothing.

Emotions in trading are information.
Anxiety before a trade is a signal to check your size.
Excitement about a setup is a signal to slow down and verify.

Emotional neutrality means you do not act on the emotion immediately.
You note it. You assess it. Then you respond based on your plan.

That pause between emotion and action...
is where professional trading lives.

Build the pause.

Source Vessel. Hybrid Funding.""",
"""Emotional neutrality is not feeling nothing. It is the pause between emotion and action.

Anxiety signals: check your size. Excitement signals: slow down and verify.

Note the emotion. Assess it. Then respond from the plan — not from the feeling."""),

(63, "MINDSET",
"Certainty is not available in trading. Clarity is. Know the difference.",
"""New traders want certainty.

The certain entry. The certain winner. The certain outcome.

Trading does not offer certainty.
The market is probabilistic by nature.

What trading offers is clarity.

Clarity about your edge. Clarity about your risk.
Clarity about the conditions your setup requires.
Clarity about what you will do when you are wrong.

Pursue clarity.
Stop waiting for certainty.
It was never available.

Source Vessel. Hybrid Funding.""",
"""Certainty is not available in trading. Clarity is.

Certainty about outcome does not exist. Clarity about edge, risk, and process does.

Pursue clarity. Stop waiting for certainty. It was never on the table."""),

(64, "MINDSET",
"Treat the trading session like a practice session. The performance takes care of itself.",
"""The best athletes do not perform during practice.
They practice during practice.
The performance happens during competition, drawing on what was built in practice.

Trading works the same way.

Each session is practice.
You are practicing execution. Practicing the pre-market routine.
Practicing emotional management. Practicing disciplined exits.

Stop trying to perform each session.
Start practicing correctly.

The results — the performance — emerge from the accumulated practice.

Source Vessel. Hybrid Funding.""",
"""Each trading session is practice, not performance.

Practice correct execution. Practice the routine. Practice emotional management.

The results emerge from the accumulated practice. Stop trying to perform. Start practicing correctly."""),

(65, "MINDSET",
"Smart people struggle in trading because intelligence is not the primary skill required.",
"""Intelligence helps in trading.
It does not guarantee success.

The primary skills in trading are emotional — not intellectual.

Patience when you want to act.
Discipline when you want to deviate.
Calm when the trade is going against you.
Acceptance when the loss hits your stop.

These are not intelligence skills.
They are character skills.

Many intelligent people have blown accounts.
Many average learners have built consistent careers.

The deciding variable is character.

Source Vessel. Hybrid Funding.""",
"""Intelligence does not guarantee trading success.

The primary skills are emotional: patience, discipline, calm under pressure, acceptance of loss.

These are character skills, not intellectual ones. The deciding variable is character."""),

(66, "MINDSET",
"Let a bad trade go fast. The longer you carry it, the more it costs you.",
"""The losing trade is closed.

The position is gone.
The money is gone.
The opportunity cost of carrying it mentally is just beginning.

Every minute you spend replaying the loss...
is a minute you are not present for the next setup.

Let it go fast.

Write one line in the journal.
'Stopped out at X. Reason: Y. Next.'

That is the complete process.
The trade is done.
Move forward.

Source Vessel. Hybrid Funding.""",
"""Let a bad trade go fast.

One line in the journal: stopped out at X, reason Y, next.

The position is closed. The mental replay costs you the next setup. Move forward."""),

(67, "MINDSET",
"Your self-talk after a loss directly determines the quality of your next decision.",
"""After a loss, the internal conversation starts.

Most traders say things to themselves they would never say to another trader.

Critical. Harsh. Permanent-sounding.

'I am terrible at this.' Not: 'That trade did not work.'
'I always do this.' Not: 'I deviated from the plan this time.'

The self-talk creates the next trade.

After a clean loss, one that was within the plan...
the correct internal response is simply:
'Within parameters. Next.'

Protect that narrative.

Source Vessel. Hybrid Funding.""",
"""Self-talk after a loss creates the next trade.

'I am terrible at this' becomes fear and hesitation.
'Within parameters. Next.' becomes clean execution.

After a plan-aligned loss: within parameters. Next. Protect that narrative."""),

(68, "MINDSET",
"The focus state is not found. It is built. Deliberately, before every session.",
"""You cannot wait for focus to arrive.

You have to build it.

The pre-session routine is not a checklist.
It is a process of building the focused state before the market opens.

The same sequence. Every session.
Chart review. Risk parameters set. Intention stated.
Distractions closed. Mind settled.

By the time the market opens, focus is already present.
Not found. Built.

The same way every day.

Source Vessel. Hybrid Funding.""",
"""Focus is not found. It is built before every session through a consistent routine.

Chart review. Risk set. Intention stated. Distractions closed.

By the time the market opens, focus is already present because you built it deliberately."""),

(69, "MINDSET",
"Patience is not passive. It is the active practice of choosing the right moment.",
"""Patience in trading is not waiting.

Passive waiting is simply not trading.
Active patience is continuously evaluating conditions and choosing not to act...
until the specific moment when all conditions are met.

It is not absence of action.
It is the active decision to not act until the edge is fully present.

That distinction matters.

You are not waiting.
You are choosing.
Choosing to trade only the highest-probability moment.

That is patient precision.

Source Vessel. Hybrid Funding.""",
"""Patience in trading is not passive. It is an active choice.

Not waiting until something happens. Continuously evaluating conditions and choosing not to act until the edge is fully present.

You are not waiting. You are choosing. That is patient precision."""),

(70, "MINDSET",
"The compounding mind grows at the same rate as the compounding account.",
"""Your account compounds.
That is the financial result of consistent correct behavior.

Your mind compounds too.

Each session of correct process builds on the last.
Each lesson retained compounds into pattern recognition.
Each discipline decision builds the neural pattern that makes the next one easier.

The mind and the account grow together.
Or they fail together.

Invest in the mind as deliberately as you invest in the account.

They are the same investment.

Source Vessel. Hybrid Funding.""",
"""Your account compounds. So does your mind.

Each session of correct process builds on the last. Each lesson retained compounds into pattern recognition.

Invest in the mind as deliberately as you invest in the account. They are the same investment."""),

# ═══════════════════════════════════════════════════════
# DISCIPLINE CYCLE 2 — Days 71-84
# ═══════════════════════════════════════════════════════

(71, "DISCIPLINE",
"The professional checklist is not bureaucracy. It is the last line of defense before the trade.",
"""Before every trade, the same questions.

Does this setup meet my entry criteria?
Is my position size correct for this volatility?
Is my stop placed at the correct structural level?
Is there a news event in the next thirty minutes?
Am I in the correct mental state?

This checklist takes sixty seconds.
It has prevented more losing trades than any analysis system.

The checklist is not bureaucracy.
It is the last line of defense.

Build yours. Use it every time.

Source Vessel. Hybrid Funding.""",
"""The pre-trade checklist takes sixty seconds.

Does this meet my criteria? Is size correct? Is stop structural? Any news? Right mental state?

It is the last line of defense before the trade. Build yours. Use it every time."""),

(72, "DISCIPLINE",
"No exceptions. Not even once. The moment you make one exception, the rule means nothing.",
"""The most dangerous words in trading:

'Just this once.'

The moment you make one exception to your rules...
the rules become negotiable.
And negotiable rules are not rules.
They are suggestions.

The brain files the exception as evidence that rule-breaking is permissible.
It will return to that evidence the next time the urge arises.

No exceptions.
Not when you are confident.
Not when the setup looks perfect.
Not when it worked last time.

The rule is the rule.

Source Vessel. Hybrid Funding.""",
"""'Just this once' is the most dangerous phrase in trading.

The moment you make one exception, the rules become suggestions.

No exceptions. Not when confident. Not when the setup looks perfect. The rule is the rule."""),

(73, "DISCIPLINE",
"The second month of discipline is harder than the first. Stay with it.",
"""The first month of a new approach, everything feels fresh.

The discipline is energized by novelty.
The process is interesting because it is new.

The second month is different.

The novelty is gone.
The wins have not arrived in the volume you expected.
The rules feel restrictive, not liberating.

This is the critical phase.

Most traders reset at month two.
Find a new strategy. Start over.
And stay stuck in the pattern of monthly resets.

Stay with the process. Month two is where real discipline is built.

Source Vessel. Hybrid Funding.""",
"""The second month of a new approach is harder than the first.

Novelty is gone. Results have not caught up. The rules feel restrictive.

This is the critical phase. Most traders reset here and stay stuck. Stay with the process."""),

(74, "DISCIPLINE",
"The habits that survive your worst losing streak are your real habits.",
"""It is easy to maintain good habits during winning streaks.

The test comes during losing streaks.

When the journal feels pointless because everything is going wrong anyway.
When the pre-session routine feels unnecessary because confidence is low.
When the rules feel like they are working against you.

The habits you maintain through the losing streak...
those are your real habits.

Everything else is conditional behavior.

Build habits that survive the worst conditions.
Those are the only ones worth having.

Source Vessel. Hybrid Funding.""",
"""Good habits are easy to maintain during winning streaks.

The ones you maintain during losing streaks are your real habits.

Build habits that survive the worst conditions. Everything else is conditional behavior."""),

(75, "DISCIPLINE",
"Time-blocking for trading is not structure for structure's sake. It is protection.",
"""Trading without defined hours is dangerous.

Without a session end time, you stay in the market too long.
Without a defined preparation window, you rush into sessions unprepared.
Without a review block, the feedback loop disappears.

Block three specific windows in your trading day.

Preparation. Session. Review.

Outside those windows, the platform is closed.
The market continues.
You do not.

Protect your time. It is how you protect your edge.

Source Vessel. Hybrid Funding.""",
"""Three time blocks in every trading day: preparation, session, review.

Outside those windows, the platform is closed. The market runs. You do not participate.

Time-blocking is not rigidity. It is protection for your edge."""),

(76, "DISCIPLINE",
"The weekly data review is where patterns become visible that single sessions cannot show.",
"""Single sessions are too small to show patterns.

One bad day does not indicate a problem.
Three bad Mondays in four weeks indicates something worth examining.

The weekly review reveals what the daily review misses.

What setups performed and what underperformed this week?
What sessions produced versus which sessions were costly?
What emotional states correlated with the best and worst outcomes?

This is the data layer.
Review it weekly without exception.

Source Vessel. Hybrid Funding.""",
"""Single sessions are too small to reveal patterns.

Three bad Mondays in four weeks is a pattern. One losing day is not.

The weekly review reveals what daily journals miss. Do it without exception."""),

(77, "DISCIPLINE",
"Eliminate the setups that consistently lose. They are not in a bad phase. They do not work for you.",
"""Every trader has a setup in their repertoire that consistently underperforms.

Not bad luck. Consistent underperformance.
Session after session. Month after month.

That setup is telling you something.
It does not work with your execution style.
Or your session. Or your timeframe.

It is not in a bad phase.
It does not work for you.

Remove it from the playbook.
Replacing it with nothing is better than trading it.

Discipline includes knowing what not to trade.

Source Vessel. Hybrid Funding.""",
"""Every trader has a setup that consistently underperforms.

Not bad luck — consistent, documented underperformance across months.

Remove it from the playbook. Discipline includes knowing what not to trade."""),

(78, "DISCIPLINE",
"Consistency when results lag is the highest form of trust in your process.",
"""The results have not arrived yet.

You have been executing correctly.
The journal confirms clean process.
The setups are sound.
The risk is managed.

And the results are still lagging.

This is where most traders break.

Continuing to execute with discipline when results lag...
is the highest expression of trust in your process.

The edge works over sample size.
Sample size requires patience.
Patience requires trust.

Stay the process.

Source Vessel. Hybrid Funding.""",
"""Executing correctly when results are lagging is the highest form of trust in your process.

The journal confirms clean execution. The setups are sound. Results have not arrived yet.

Stay the process. The edge works over sample size."""),

(79, "DISCIPLINE",
"The notebook is slower than the screen. That is exactly why it works.",
"""There is something about writing by hand in a trading journal that the digital version cannot replicate.

Slowing down.
Committing the observation to words before it disappears.
Physically forming the letters that describe the mistake or the insight.

The slowness is the feature.

The screen rewards speed.
The notebook rewards reflection.

Carry a physical notebook for your key observations.
The act of slowing down enough to write by hand...
changes how deeply you process the trade.

Source Vessel. Hybrid Funding.""",
"""The notebook is slower than the screen. That is exactly why it works.

The act of slowing down enough to write by hand changes how deeply you process the trade.

Keep a physical notebook for key observations. The slowness is the feature."""),

(80, "DISCIPLINE",
"Name your worst habit. Write the rule that stops it. Follow it without negotiation.",
"""You know your worst trading habit.

It shows up in your journal. Month after month.
The same pattern. Different days.

Name it out loud.

Now write the specific rule that stops it.
Not a general guideline. A specific, absolute rule.

'I will not trade in the thirty minutes after a stop-out.'
'I will not increase size after two consecutive losses.'
'I will not hold positions through high-impact news.'

Specific. Absolute. Non-negotiable.

One rule at a time. That is how discipline gets built.

Source Vessel. Hybrid Funding.""",
"""Name your worst habit. Write it. Then write the exact rule that stops it.

Not a guideline. A specific, absolute, non-negotiable rule.

One rule at a time. That is how discipline compounds."""),

(81, "DISCIPLINE",
"The morning preparation is your competitive advantage over every trader who skips it.",
"""While other traders are opening the market without preparation...
you are reviewing the structure.
Marking the key levels.
Noting the high-impact events.
Setting your max risk for the session.
Checking your mental state.

By the time the market opens, you are already ahead.

Not because you know what will happen.
But because you know what you will do when it happens.

Preparation does not guarantee outcomes.
It guarantees readiness.

That is a significant competitive advantage.

Source Vessel. Hybrid Funding.""",
"""While other traders open the chart cold, you are finishing your preparation.

Structure reviewed. Levels marked. Risk set. Mental state checked.

By the open, you know what you will do when price moves. That readiness is a real competitive advantage."""),

(82, "DISCIPLINE",
"Exit discipline separates the traders who get in right from the ones who profit from it.",
"""The entry gets you positioned.

But the exit determines whether you made money.

Half the traders who read the direction correctly still lose.
Because they exit too early when fear takes over.
Or too late when greed takes over.

Exit discipline means: you know your target before you enter.
You know your stop before you enter.
You know your partial-exit level before you enter.

The plan is complete before the trade opens.
Then you execute the exit exactly as planned.

No adjustments based on emotion.

Source Vessel. Hybrid Funding.""",
"""Entry gets you positioned. Exit determines profit.

Half the traders who read direction correctly still lose — because fear or greed disrupts the exit.

Know your exit before you enter. Execute it exactly as planned. No emotion-based adjustments."""),

(83, "DISCIPLINE",
"The no-new-strategy month is one of the most valuable experiments a trader can run.",
"""Here is an experiment worth trying.

For thirty days, no new strategies.

No new indicators.
No new timeframes.
No new setups.

Trade only what you have been trading.
With the same rules. The same session hours.

What you will discover in thirty days...
is either that your current strategy works when executed consistently...
or that your execution is the problem — not the strategy.

Either discovery is valuable.

Run the experiment.

Source Vessel. Hybrid Funding.""",
"""Run a no-new-strategy month.

For thirty days: same strategy, same rules, same session hours. No modifications.

You will discover either that consistent execution works — or that execution is the problem. Either discovery is valuable."""),

(84, "DISCIPLINE",
"Discipline is not effort. Eventually it becomes identity. That is the goal.",
"""At first, discipline is effort.

You have to force yourself to follow the rules.
You have to resist the urge to deviate.
You have to consciously choose the plan over the emotion.

Over time, with enough repetition...
discipline becomes identity.

You do not choose to follow your rules.
You follow them because that is who you are.

The goal is not disciplined effort.
The goal is disciplined identity.

Work toward it every session.

Source Vessel. Hybrid Funding.""",
"""At first, discipline is effort. You force yourself to follow the rules.

Over time, discipline becomes identity. You follow the rules because that is who you are.

Work toward disciplined identity. That is the real goal."""),

# ═══════════════════════════════════════════════════════
# STRATEGY CYCLE 2 — Days 85-90
# ═══════════════════════════════════════════════════════

(85, "STRATEGY",
"The optimal entry is not the earliest entry. It is the entry with the most confirmation.",
"""Most traders want to get in as early as possible.

They want the best price.
They want the maximum reward.

Early entries have the least confirmation.
They are often before the setup has fully formed.

The optimal entry is not the earliest.
It is the most confirmed.

Wait for the candle close.
Wait for the level to hold.
Wait for the volume to confirm.

A slightly less optimal price with higher confirmation...
produces better outcomes than an early entry that has not yet proved itself.

Source Vessel. Hybrid Funding.""",
"""The optimal entry is not the earliest entry. It is the most confirmed one.

Wait for candle close. Wait for level to hold. Wait for volume to confirm.

A slightly worse price with high confirmation beats an early entry that has not yet proved itself."""),

(86, "STRATEGY",
"Patience within the setup is a separate skill from patience waiting for the setup.",
"""You waited for the setup.

It appeared. All criteria confirmed.
You entered correctly.

Now a different patience is required.

The patience within the trade.

Not closing the trade because it stalled.
Not taking profits too early because of anxiety.
Not moving the stop because the trade is uncomfortable.

The trade is performing within normal parameters.
Let it develop.

This is a different practice than waiting for the setup.
And it is just as important.

Source Vessel. Hybrid Funding.""",
"""Patience to wait for the setup and patience within the trade are two separate skills.

Once you are in a correctly entered trade, the second patience begins.

Not closing early. Not moving stops from anxiety. Letting the trade develop as planned."""),

(87, "STRATEGY",
"The higher timeframe shows where price wants to go. The lower timeframe shows when to enter.",
"""Use multiple timeframes, but use them correctly.

The higher timeframe is for direction.
Where is the overall structure? Where is price in the larger trend?

The lower timeframe is for entry.
The precise moment price reaches the level. The confirmation candle. The entry trigger.

These are different questions that require different timeframes.

Do not use the higher timeframe to make entry decisions.
Do not use the lower timeframe to make directional decisions.

Each timeframe has a specific role. Honor it.

Source Vessel. Hybrid Funding.""",
"""Higher timeframe shows direction. Lower timeframe shows the entry.

Do not use the higher timeframe to time entries. Do not use the lower timeframe to determine direction.

Each timeframe has a specific role. Use them correctly."""),

(88, "STRATEGY",
"Adding to a winner is only valid when structure supports the addition.",
"""Adding to a winning position is a skill.

But it has a specific criterion.

You add to a winner only when price action gives you structural confirmation that the move is continuing.

A higher low forming in an uptrend.
Price retesting and holding a broken level.
Volume confirming the continuation.

You do not add simply because the trade is in profit.
Being in profit is not confirmation of continuation.

Add when structure confirms continuation.
Not when profit confirms your ego.

Source Vessel. Hybrid Funding.""",
"""Adding to a winning position requires structural confirmation — not just being in profit.

A higher low. A retest of a broken level. Volume confirming continuation.

Add when structure confirms the move is continuing. Not when profit feels good."""),

(89, "STRATEGY",
"The trade plan is your contract with yourself before price moves. Honor every clause.",
"""Before the market opens, write the trade plan.

This pair. This session. This setup.
Entry criteria. Stop placement. Target levels.
Partial exit levels. Maximum size. Conditions to pass.

This is your contract.

When price moves and emotions rise...
the plan is the only valid reference.

Not your current feeling.
Not what looks like it is happening now.
The plan you wrote with a clear mind before it mattered.

Honor every clause.

Source Vessel. Hybrid Funding.""",
"""The trade plan is a contract written with a clear mind before price moves.

When price moves and emotions rise, the plan is the only valid reference.

Honor every clause. Not your current feeling. The plan you wrote before it mattered."""),

(90, "MINDSET",
"Day ninety. The foundation is built. Now the real work begins.",
"""Day ninety.

Think about the distance from day one.

The rules that felt restrictive now feel like protection.
The patience that felt impossible now feels natural.
The journal that felt like a chore now feels essential.

You did not just complete ninety days.
You built a foundation.

This is not a finish line.
It is a starting line.

The trader who shows up for day ninety-one...
with the same discipline, the same patience, the same process...
that trader is already where most traders never get.

Keep going.

Source Vessel. Hybrid Funding.""",
"""Day ninety.

The rules feel like protection now. Patience feels natural. The journal feels essential.

You did not complete ninety days. You built a foundation.

This is not a finish line. Day ninety-one is where it gets real. Keep going."""),

]

# ─────────────────────────────────────────────────────────────
# Write all files
# ─────────────────────────────────────────────────────────────
created = 0
skipped = 0

for (day, pillar, hook, vox, caption) in DAYS:
    pad = str(day).zfill(2)

    vox_path     = os.path.join(BASE, f"day_{pad}_vox_ready.txt")
    social_path  = os.path.join(BASE, f"day_{pad}_social.txt")

    # Write vox_ready (skip if APPROVED version already exists and has content)
    approved_flag = os.path.join(BASE, f"day_{pad}_vox_ready_APPROVED.flag")
    if os.path.exists(vox_path) and os.path.exists(approved_flag):
        print(f"SKIP Day {day} vox (already approved)")
        skipped += 1
    elif not os.path.exists(vox_path):
        with open(vox_path, "w", encoding="utf-8") as f:
            f.write(vox.strip())
        print(f"  WROTE Day {day} vox: {vox_path}")
        created += 1
    else:
        # File exists but not approved — overwrite only if content is thin
        existing = open(vox_path, encoding="utf-8", errors="replace").read()
        if len(existing.strip()) < 100:
            with open(vox_path, "w", encoding="utf-8") as f:
                f.write(vox.strip())
            print(f"  UPDATED Day {day} vox (was thin)")
            created += 1
        else:
            print(f"  KEEP Day {day} vox (has content)")
            skipped += 1

    # Always write social if it does not exist
    if not os.path.exists(social_path):
        ig_caption = caption.strip()
        social_content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DAY {day} — {pillar}
HOOK: {hook}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTAGRAM CAPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{ig_caption}

{TAGS}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TWITTER / X THREAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{ig_caption.split(chr(10))[0]}

#trading #tradermindset #hybridfunding
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUTUBE TITLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{hook} (Day {day}) — Source Vessel · Hybrid Funding

YOUTUBE DESCRIPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{ig_caption}

Hybrid Funding → hybridfunding.co
Source Vessel → @sourcevessele

{TAGS}
"""
        with open(social_path, "w", encoding="utf-8") as f:
            f.write(social_content)
        print(f"  WROTE Day {day} social: {social_path}")
        created += 1
    else:
        print(f"  KEEP Day {day} social (exists)")
        skipped += 1

print(f"\n{'='*50}")
print(f"COMPLETE: {created} files created, {skipped} skipped")
print(f"Scripts directory: {BASE}")
print(f"Days covered: {DAYS[0][0]} → {DAYS[-1][0]}")
print(f"{'='*50}")
