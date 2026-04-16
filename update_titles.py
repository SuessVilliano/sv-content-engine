#!/usr/bin/env python3
"""
SV Content Engine — Title & Caption Upgrader
Rewrites YouTube titles, IG first lines, and Twitter hooks across all 90 day social files.
Replaces boring "Day XX — PILLAR — Topic" format with compelling, curiosity-driven hooks.
"""
import os, re

BASE = "/Users/jamaurjohnson/Documents/SV_Content_Engine/scripts"

# Compelling YouTube titles — benefit-driven, curiosity-first, no "Day XX" prefix
TITLES = {
    1:  "Why Your Mind Costs You More Than Any Losing Trade",
    2:  "The Trade You Don't Take Is Your Best Trade",
    3:  "Fear Is Information — Here's How to Read It",
    4:  "Why the Best Traders Take the Fewest Trades",
    5:  "The Market Is Your Mirror — What It's Really Showing You",
    6:  "Confidence Without a Track Record Is Just Hope",
    7:  "The Work Nobody Sees Is the Work That Pays",
    8:  "Stop Trading Like You Need the Money Today",
    9:  "Your P&L Is the Wrong Scoreboard",
    10: "The Ten Minutes Before You Trade That Determine Everything",
    11: "The Twenty-Minute Rule That Saves Accounts",
    12: "Why Funded Traders Last Longer Than Solo Traders",
    13: "One Undisciplined Session Can Erase Three Weeks of Work",
    14: "Consistency Is the Output of a Hundred Small Correct Decisions",
    15: "The Trading Journal Is Not a Habit — It Is the Strategy",
    16: "One Rule Followed Completely Is Worth Ten Rules Followed Loosely",
    17: "The Trade You Skip Deliberately Is a Trade You Won",
    18: "Your Position Size Is a Direct Measurement of Your Discipline",
    19: "The Work That Happens Before the Market Opens Is the Real Edge",
    20: "Reset Your Emotional State Before You Reset Your Charts",
    21: "Discipline on a Winning Day Is the Real Test",
    22: "The End-of-Session Review Is Where Tomorrow Gets Built",
    23: "Your Stop-Loss Is Not Doubt — It Is the Most Disciplined Thing You Do",
    24: "Knowing When to Walk Away Is One of the Highest-Value Skills in Trading",
    25: "Discipline in a Drawdown Is What Defines a Trading Career",
    26: "Eight Hours at the Charts Is Not Work — It Is Exposure",
    27: "Doing Nothing Is a Trade. The Most Underrated One in the Market.",
    28: "Accountability Structures Work When Internal Discipline Fails",
    29: "One Setup Mastered Completely Is an Entire Trading Career",
    30: "True Confluence Is Independent Confirmation — Not More Indicators",
    31: "The Market Is Always Open. Your Edge Is Not.",
    32: "Risk-Reward Only Works If Your Entries Are Selective Enough",
    33: "Market Structure Tells You Where Price Wants to Go Before Any Signal Does",
    34: "The Fake Breakout Is Not a Trap for Everyone — For Patient Traders It's the Setup",
    35: "How to Handle News Events Without Getting Destroyed",
    36: "Design the Exit Before You Enter — Not While You Are in the Trade",
    37: "Backtesting and Forward Testing Are Two Different Skills",
    38: "Scaling In Is Not Averaging Down — Learn the Difference",
    39: "How to Secure Profit and Still Ride the Move at the Same Time",
    40: "Two Correlated Positions Are One Trade With Double Exposure",
    41: "The Market Phase Dictates the Strategy — Not the Other Way Around",
    42: "The A-Plus Setup Is Not a Feeling — It Is a Checklist",
    43: "Most Traders Don't Fail at Strategy — They Fail at Staying Long Enough",
    44: "Why Funded Accounts Force the Professional Behavior That Solo Accounts Don't",
    45: "Every Loss That Teaches You Something Has Already Paid for Itself",
    46: "The Market Is Not Your Enemy — Your Own Behavior Inside It Is",
    47: "Survival First. Profits Are the Reward for Surviving Long Enough.",
    48: "What a Truly Profitable Month Actually Looks Like Day to Day",
    49: "Nobody Is Watching Your Losing Trades — Stop Performing for Them",
    50: "Stop Comparing Your Chapter Two to Someone Else's Chapter Twenty",
    51: "The Overnight Account and the Five-Year Account Are Built on Different Behaviors",
    52: "Ego Has a Market Price — It Is Always Higher Than Traders Expect",
    53: "The Way You Explain Your Losses Tells You Where You Are in the Process",
    54: "What a Small Account Teaches You That a Large Account Cannot",
    55: "Real Trading Progress Is Visible in Fewer Mistakes — Not More Wins",
    56: "Natural Talent in Trading Does Not Exist the Way People Think",
    57: "How to Return After a Break Without Losing What You Built",
    58: "A Drawdown Period Is Not Punishment — It Is a Recalibration Phase",
    59: "Know Why You Are Trading — The Reason Determines How You Behave Under Pressure",
    60: "Day 60: The Compound Effect of Consistent Daily Discipline Is Already Working",
    61: "You Are Not the Same Trader Who Started This — Own the Upgrade",
    62: "Emotional Neutrality Is Not Indifference — It Is the Pause Between Emotion and Action",
    63: "Certainty Is Not Available in Trading — Clarity Is. Know the Difference.",
    64: "Stop Trying to Perform Each Session — Start Practicing Correctly",
    65: "Why Smart People Struggle in Trading More Than They Expect",
    66: "Let a Bad Trade Go Fast — The Longer You Carry It the More It Costs",
    67: "The Way You Talk to Yourself After a Loss Determines Your Next Trade",
    68: "The Focus State Is Not Found — It Is Built Before Every Session",
    69: "Patience Is Not Passive — It Is the Active Choice of the Right Moment",
    70: "The Compounding Mind Grows at the Same Rate as the Compounding Account",
    71: "The Professional Pre-Trade Checklist — 60 Seconds That Change Everything",
    72: "No Exceptions. Not Even Once. Here Is Why.",
    73: "The Second Month of Discipline Is Harder Than the First — Stay With It",
    74: "Build Trading Habits That Survive Your Worst Losing Streak",
    75: "Why Time-Blocking Is One of the Most Underrated Edges in Trading",
    76: "The Weekly Data Review Shows Patterns the Daily Review Cannot",
    77: "Some Setups Just Don't Work for You — Eliminate Them Permanently",
    78: "How to Stay Consistent When the Results Are Not There Yet",
    79: "Why a Physical Notebook Changes How Deeply You Process Trades",
    80: "Name Your Worst Habit — Then Build the Exact Rule That Stops It",
    81: "The Morning Preparation Is Your Competitive Advantage Over Every Trader Who Skips It",
    82: "Exit Discipline Separates the Traders Who Get In Right From the Ones Who Profit",
    83: "The No-New-Strategy Month Is the Most Valuable Experiment You Can Run",
    84: "From Disciplined Effort to Disciplined Identity — That Is the Goal",
    85: "The Optimal Entry Is Not the Earliest Entry — It Is the Most Confirmed One",
    86: "Patience Within the Trade Is a Separate Skill From Patience Waiting for the Trade",
    87: "The Right Way to Use Multiple Timeframes — Most Traders Get This Backwards",
    88: "When to Add to a Winner — And When Adding Is Just Ego Talking",
    89: "Write the Trade Plan Before Price Moves — Then Honor Every Clause",
    90: "Day 90: The Foundation Is Built. Now the Real Work Begins.",
}

# Short, punchy IG hook lines (first line of caption — what stops the scroll)
IG_HOOKS = {
    1:  "Your mind is costing you more than your losses are.",
    2:  "The best trade you took today might be the one you didn't take.",
    3:  "Fear is not a stop sign. It is a signal. Learn to read it.",
    4:  "The most profitable traders take the fewest trades.",
    5:  "The market is showing you something about yourself. Pay attention.",
    6:  "Confidence without a track record is just hope dressed up as skill.",
    7:  "The work nobody sees is the only work that produces real results.",
    8:  "If you are trading like you need the money today, you are already losing.",
    9:  "Stop scoring yourself on your P&L. Score yourself on your process.",
    10: "The ten minutes before you trade determine the quality of everything after.",
    11: "After a loss, 20 minutes away from the screen is the highest-value trade you can make.",
    12: "Willpower runs out. Structure does not. That is why funded traders last.",
    13: "One undisciplined session sends a message to your brain you spend weeks undoing.",
    14: "Consistency is not a decision. It is the output of a hundred small correct ones.",
    15: "The journal is not the discipline habit. It is the discipline strategy.",
    16: "One rule, followed every single time, is worth ten rules followed when convenient.",
    17: "Write this in your journal tonight: saw it, passed it, correct.",
    18: "Your position size tells the truth about your discipline before your results do.",
    19: "By the time the market opens, the preparation should already be done.",
    20: "The emotional reset is part of the process — not a break from it.",
    21: "The real test of discipline is not the losing day. It is the winning one.",
    22: "The session is not over until the review is written.",
    23: "Your stop-loss is not doubt. It is the most precise thing you do in a trade.",
    24: "The most profitable exit in your career might be the one you never placed.",
    25: "In a drawdown, the only thing that matters is what you do next.",
    26: "If screens are open and you are not in your session window, close them.",
    27: "The most disciplined trade you made today is the one where you did nothing.",
    28: "External accountability structures work when internal discipline fails. Build both.",
    29: "Master one setup completely. That is a trading career.",
    30: "Confluence is not more indicators. It is independent signals saying the same thing.",
    31: "Know your session. Trade inside it only. Close the platform outside of it.",
    32: "A 1:2 risk-reward requires patience, not just intention.",
    33: "Read the structure before you read any indicator. It tells you everything first.",
    34: "Learn to trade the fake breakout trap instead of falling into it.",
    35: "Your approach to news events should be decided before the event — not during it.",
    36: "Design the exit before the trade opens. Not while you are in it.",
    37: "Backtesting tells you what happened. Forward testing tells you if you can execute it.",
    38: "Scaling in is building on confirmation. Averaging down is building on hope.",
    39: "You do not have to choose between securing profit and riding the move.",
    40: "Two positions on the same catalyst are one trade. Know your real exposure.",
    41: "The market phase is not a suggestion. It determines which strategy belongs.",
    42: "The A-plus setup is not something you feel. It is something you confirm.",
    43: "Most traders fail not at strategy but at staying long enough to let it work.",
    44: "A funded account does not just give you capital. It gives you the structure to survive.",
    45: "Examine every loss. The one you learn nothing from is the only truly wasted one.",
    46: "The market has no opinion of you. Your behavior inside it does all the damage.",
    47: "The first goal is not profit. The first goal is staying in the game long enough to earn it.",
    48: "A profitable month looks quieter than people expect. Mostly patience. Few trades.",
    49: "Nobody is watching your losing trades. Stop performing for an audience that isn't there.",
    50: "You are comparing your chapter two to their chapter twenty. Stop.",
    51: "The five-year account is not built faster. It is built on completely different behaviors.",
    52: "Ego has a market price. Check your trade history to see what you have paid.",
    53: "The way you explain your losses tells you more about where you are than your P&L does.",
    54: "The constraints of a small account are the curriculum. Master them.",
    55: "Progress in trading is visible in fewer mistakes before it is visible in more wins.",
    56: "Nobody was born to trade. The talented ones just stayed long enough for skill to appear.",
    57: "Coming back after a break requires intention, not urgency.",
    58: "A drawdown is information. Go find the signal in it.",
    59: "Know the real reason you are doing this. It will anchor you when nothing else does.",
    60: "60 sessions of consistent process. The compound effect is already working beneath the surface.",
    61: "You are a different trader than when this started. Own it.",
    62: "Emotional neutrality is not feeling nothing. It is the pause between emotion and action.",
    63: "Stop waiting for certainty. Pursue clarity instead. Certainty was never available.",
    64: "The performance takes care of itself when you practice correctly, every session.",
    65: "Intelligence is helpful in trading. It is not the deciding variable. Character is.",
    66: "One line in the journal. Stopped out. Reason noted. Move forward.",
    67: "The self-talk after a loss creates the next trade. Make it clean.",
    68: "Focus is not found. It is built — the same way, before every session.",
    69: "Patience is not waiting. It is actively choosing to act only at the right moment.",
    70: "Your mind compounds at the same rate as your account. Invest in both.",
    71: "The pre-trade checklist takes sixty seconds and has saved more money than any indicator.",
    72: "The moment you make one exception, the rule means nothing.",
    73: "The second month is harder than the first. It is also where real discipline is built.",
    74: "The habits you maintain during your worst losing streak are your real habits.",
    75: "Time-blocking for trading is not rigidity. It is protection for your edge.",
    76: "The pattern you see after four Mondays in a row is more valuable than any single day's data.",
    77: "Some setups consistently lose for you. They are not in a bad phase. Eliminate them.",
    78: "Consistency when results lag is the highest form of trust in your process.",
    79: "The notebook is slower. That is exactly why it works.",
    80: "Name the worst habit. Write the specific rule. Follow it without negotiation.",
    81: "Your morning preparation is a competitive advantage over every trader who opens cold.",
    82: "Half the traders who read direction correctly still lose because of how they exit.",
    83: "Commit to one strategy for thirty days. No modifications. Then evaluate what you find.",
    84: "The goal is not disciplined effort. The goal is disciplined identity.",
    85: "The best entry is not the earliest one. It is the most confirmed one.",
    86: "Two different patience skills — waiting for the setup, and staying in the trade.",
    87: "Higher timeframe for direction. Lower timeframe for entry. Most traders reverse this.",
    88: "Add to a winner only when structure confirms continuation — not when profit feels good.",
    89: "Write the trade plan before price moves. Then honor every clause of it.",
    90: "The foundation is built. Everything that comes next is built on what you did here.",
}

def update_social_file(day):
    pad = str(day).zfill(2)
    path = os.path.join(BASE, f"day_{pad}_social.txt")
    if not os.path.exists(path):
        return False

    try:
        content = open(path, encoding="utf-8").read()
    except UnicodeDecodeError:
        content = open(path, encoding="latin-1").read()

    title = TITLES.get(day, "")
    hook  = IG_HOOKS.get(day, "")

    if not title:
        return False

    # Replace YouTube title line
    # Pattern: "YOUTUBE TITLE" section followed by content
    yt_pattern = re.compile(
        r'(YOUTUBE TITLE\s*\n[━=\-]+\s*\n)([^\n━=]+)',
        re.MULTILINE
    )
    if yt_pattern.search(content):
        content = yt_pattern.sub(
            lambda m: m.group(1) + title,
            content, count=1
        )
    else:
        # Add YouTube title section if missing
        if "YOUTUBE TITLE" not in content:
            content += f"\nYOUTUBE TITLE\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{title}\n"

    # Update IG caption hook (first non-empty line after INSTAGRAM CAPTION header)
    if hook and "INSTAGRAM CAPTION" in content:
        ig_idx = content.index("INSTAGRAM CAPTION")
        # Find the separator after the header
        rest = content[ig_idx + len("INSTAGRAM CAPTION"):]
        # Skip past the separator line
        sep_match = re.search(r'━+\s*\n', rest)
        if sep_match:
            after_sep = rest[sep_match.end():]
            # Replace first non-empty line
            lines = after_sep.split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    lines[i] = hook
                    break
            new_after_sep = '\n'.join(lines)
            rest_new = rest[:sep_match.end()] + new_after_sep
            content = content[:ig_idx + len("INSTAGRAM CAPTION")] + rest_new

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True

# Run for all 90 days
updated = 0
for day in range(1, 91):
    if update_social_file(day):
        print(f"  Updated Day {day}: {TITLES.get(day,'')[:60]}")
        updated += 1
    else:
        pad = str(day).zfill(2)
        if not os.path.exists(os.path.join(BASE, f"day_{pad}_social.txt")):
            print(f"  MISSING Day {day} social file")

print(f"\n{'='*50}")
print(f"Updated {updated} social files with compelling titles")
print(f"{'='*50}")
