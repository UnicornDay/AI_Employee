# Stop Building AI Chatbots. Here’s How I Built My First Autonomous AI Employee with Antigravity.

### *Why prompt engineering is already obsolete, and how to build a zero-touch digital worker that monitors markets, reads financial news, and files executive reports without you touching a screen.*

---

Imagine hiring a real human assistant. 

On their first day, they sit at your desk, stare at you blankly, and wait. Every thirty minutes, you have to tap them on the shoulder and say: *“Hey, could you check the stock price now?”* Then they check it, report back, and freeze again until you give another command.

If an assistant did that, you’d fire them before lunchtime. 

Yet, this is exactly how 99% of people use Artificial Intelligence today. We open a browser tab, type into a rectangular chat box, press Enter, wait for tokens to stream across the screen, and copy-paste the output. 

We called it **“Generative AI.”** Then we chained prompts together and called it **“AI Agents.”** 

But neither is an employee. 

Recently, inside Google DeepMind’s **Antigravity** coding environment, I set out to cross the chasm between an *AI Agent* and a true *AI Employee*. I wanted to build an autonomous financial analyst named **Ava** to monitor Australia’s biotech giant **CSL Limited (ASX: CSL)**. 

The rule was simple: **Zero human interaction.** No terminal windows open on my screen. No prompt boxes. No babysitting. She had to wake up every 30 minutes, inspect the market, record structured data, read the day's financial news, synthesize executive briefings with an LLM, and log it all silently in the background while I lived my life.

Here is the difference between an AI Agent and an AI Employee—and the exact blueprint of how we built one using Antigravity.

---

## The Fatal Distinction: AI Agent vs. AI Employee

The tech industry throws around the term “Agent” loosely. But in production, there is a massive conceptual divide:

| Dimension | AI Agent (The Tool) | AI Employee (The Worker) |
| :--- | :--- | :--- |
| **Trigger Mechanism** | **Reactive**: Awaits a user prompt or API trigger. | **Proactive**: Driven by time, events, and business cadences. |
| **Execution Realm** | Trapped in a chat UI, browser tab, or open terminal. | Embedded into the OS kernel or cloud daemon (headless, silent). |
| **Deliverable** | Ephemeral conversational text in a chat bubble. | Tangible, persistent business artifacts (logs, ledgers, briefs). |
| **Resilience** | Dies when you close the tab, sleep your laptop, or click away. | Self-recovering, handles network drops, survives computer reboots. |
| **Human Role** | **Operator**: You are constantly micromanaging the loop. | **Manager**: You review the finished work when you choose. |

An **AI Agent** is a capable intern sitting next to you waiting for instructions.  
An **AI Employee** is a team member with a job description who gets things done whether you're at your desk or asleep.

---

## The Job Description: Hiring “Ava”

We assigned Ava a dual mandate:
1. **The Clockwork Ledger**: Every 30 minutes during market trading, fetch real-time market metrics for `CSL.AX` (price, previous close, day range, volume, change %) and record it to a clean ledger without flashing any windows.
2. **The Executive Synthesis**: Every day at 16:30 (shortly after the Australian Securities Exchange closes), scan Google News RSS feeds for CSL Limited, cross-reference market movements, pipe the data into **Gemini 3.6 Flash**, and write an executive briefing evaluating catalysts and sentiment (Bullish / Neutral / Bearish).

## The Twist: I Didn't Write a Single Line of Code

Here is the most incredible part of this entire experiment: **I didn't write a single line of Python, configure Windows Task Scheduler XML, or debug API headers by hand.**

I acted strictly as the **Executive Manager**, communicating pure human intent in conversational English. **Antigravity** acted as the **Lead Systems Architect and Engineer**, writing the code, diagnosing OS-level console freezes, finding background runtimes, and configuring Windows services.

If you look through the conversation thread, the entire system was built using just four conversational prompts:

### Prompt 1: The Initial Hire
> *"can I create an AI employee? She will check the stock price of CSL.AX from internet every half hour without I asking her to do it and then create a log file to record that price with all permision to the current folder"*

Antigravity immediately validated the market API, scaffolded the core Python daemon, and configured the CSV and activity log ledgers.

### Prompt 2: The Course Correction (Demanding True Zero-Touch)
When the first prototype launched with a standard command-prompt window, I rejected the complexity:
> *"this is not what I want, I want sth simple every half hour it logs updated csl.ax stock price in the log file automatically without I touching the screen."*

Antigravity took that raw feedback, recognized that open terminal windows and mouse clicks freeze Windows console processes, completely redesigned the architecture, banished the terminal using headless `pythonw.exe`, and registered a background Windows Task Scheduler job.

### Prompt 3: Giving Her a Brain
Once the clockwork was proven, I gave her an intelligence upgrade:
> *"can you allow her to read financial news and summarize every day about CSL.AX? same as you did for stock price checking, no interaction with human, fully automated."*

Antigravity detected my system's `GEMINI_API_KEY`, hooked up Google News RSS feeds, integrated the latest **Gemini 3.6 Flash** model, and scheduled a daily market-close briefing at 16:30 AEST.

### Prompt 4: The 48-Hour Check-in
> *"tell me if Ava is working today?"*

Antigravity inspected the background OS tasks, checked the live ledgers, and confirmed that Ava had already executed three pre-market checks while I was asleep.

---

## How Antigravity Engineered Her Behind the Scenes

Antigravity gives AI assistants direct tool-use capabilities to manipulate files, execute background commands, and inspect system environments. Here is how it architected the solution:

### 1. The Zero-Dependency Engine
Rather than bloating the project with heavy external libraries, we wrote the core engine in lightweight Python using native standard libraries (`urllib.request`, `json`, `xml.etree.ElementTree`). 

She queries Yahoo Finance’s live feed and parses Google News RSS directly. This means instant cold-starts, zero package conflicts, and sub-second execution.

### 2. Banishing the Terminal (`pythonw.exe`)
The quickest way to ruin an automation project is to leave a black command prompt window open on your screen. If you click inside a Windows console window, the OS enters "QuickEdit selection mode" and silently freezes the process until you hit Enter. Close the window, and your agent dies.

To solve this, we decoupled the script from the console using Windows’ built-in **`pythonw.exe`** (*Python Windowless*). It executes code with absolute invisibility—no command prompt, no taskbar icons, no screen flickering.

### 3. The Autonomous Heartbeat (Windows Task Scheduler)
Instead of keeping an infinite Python `while True: time.sleep(1800)` loop running—which can stall if a laptop goes into Modern Standby or sleep—we offloaded the heartbeat to the operating system's native **Task Scheduler**.

Using PowerShell scripts orchestrated through Antigravity, we registered two native scheduled tasks:
- **`CSL_Auto_Price_Logger`**: Runs every 30 minutes (`PT30M`) with headless `pythonw.exe`.
- **`CSL_Daily_News_Briefing`**: Triggers daily at 16:30 AEST.

Because Task Scheduler runs at the OS level, Ava wakes up on battery, catches up if the machine was asleep, and survives reboots.

### 4. Giving the Employee a Brain (Gemini 3.6 Flash)
Logging numbers is just robotic automation. To make Ava an *analyst*, we wired her to Google’s **Gemini 3.6 Flash** via its REST API, passing her existing environment credentials.

Every afternoon, she feeds the day's raw news headlines and closing figures into a structured financial prompt:

```python
prompt = f"""You are Ava, an executive AI financial analyst monitoring CSL Limited (ASX: CSL).
Here is today's market performance: {stock_summary}
Here are the latest news headlines: {news_headlines}

Provide an executive briefing:
1. Executive Summary (2 sentences on price action & news)
2. Key News & Catalysts (3-4 concise bullets explaining why it matters)
3. Market Sentiment & Outlook (Bullish / Neutral / Bearish with rationale)
Sign off as Ava."""
```

---

## The Result: Work That Happens While You Sleep

When you open the project folder, there are no chaotic consoles. There are just quiet, updating deliverables:

### The 30-Minute Price Ledger (`csl_price_log.txt`)
```text
[2026-09-07 14:27:32] CSL.AX: $173.66 AUD | Change: -0.83 (-0.48%) | Day Range: [$173.58 - $176.15] | Vol: 337,109 | Market: OPEN
[2026-09-07 14:29:20] CSL.AX: $173.54 AUD | Change: -0.96 (-0.55%) | Day Range: [$173.54 - $176.15] | Vol: 338,622 | Market: OPEN
[2026-09-07 15:14:43] CSL.AX: $173.53 AUD | Change: -0.96 (-0.55%) | Day Range: [$173.27 - $176.15] | Vol: 388,561 | Market: OPEN
```

### The Daily AI Intelligence Briefing (`csl_daily_briefing.txt`)
```text
================================================================================
DAILY FINANCIAL BRIEFING: Monday, 07 September 2026
================================================================================

### 1. Executive Summary
CSL Limited traded slightly lower today at $173.41 AUD (-0.62%) as the stock consolidates following its FY26 reporting cycle. Market sentiment remains constructively anchored after recent regulatory agreements in the U.S. helped ease policy uncertainty surrounding drug pricing and manufacturing.

### 2. Key News & Catalysts
* U.S. Pricing & Manufacturing Agreements: Mitigates major policy overhangs in CSL's largest market, enhancing revenue predictability for core therapies.
* FY26 Operational Reset: Major research houses noted that worst margin pressures are likely over, signaling an operational bottom.
* Dividend Attention: Market commentary advised long-term fundamental focus ahead of the upcoming ex-dividend date.

### 3. Market Sentiment & Outlook
* Sentiment: Bullish
* Rationale: Mitigated U.S. regulatory risks combined with an earnings inflection point position the stock well for long-term recovery.

Ava - AI Financial Analyst
```

---

## 48 Hours Later: The Real-World Test

The true test of any employee is what happens after the excitement of Day 1 wears off. 

Two days later—on Wednesday, 9 September 2026—I sat down with my morning coffee at 7:40 AM and wondered: *“Did she keep working, or did she crash in the middle of the night?”*

I didn't open a terminal. I navigated straight to the ledger:
`C:\Users\willi\AI_Employee\csl_price_log.txt`

There it was. While I had been asleep, Ava had quietly clocked in before the market open:

```text
[2026-09-09 06:54:20] CSL.AX: $174.80 AUD | Change: +1.62 (+0.94%) | Market: PRE-MARKET
[2026-09-09 07:11:41] CSL.AX: $174.80 AUD | Change: +1.62 (+0.94%) | Market: PRE-MARKET
[2026-09-09 07:29:07] CSL.AX: $174.80 AUD | Change: +1.62 (+0.94%) | Market: PRE-MARKET
```

She had correctly identified that the ASX was in `PRE-MARKET` mode, standing by for the 10:00 AM opening bell.

Next, I opened her executive briefing report:  
👉 **`C:\Users\willi\AI_Employee\csl_daily_briefing.txt`**

Waiting inside was an intelligence report from Tuesday afternoon that I hadn't even read on the news yet:

> **Key Discovery by Ava (Tuesday, 8 September):**  
> * **A$1.15 Billion On-Market Buy-Back:** CSL appointed J.P. Morgan to execute an on-market share buy-back of up to A$1.15 billion, signaling balance sheet strength and driving shares up **+0.94%** to **$174.80 AUD**.  
> * **Market Sentiment:** **Bullish**

She didn't just log a price tick. She identified an A$1.15B corporate buy-back, explained why the price rallied, and filed the briefing cleanly to disk—without a single human prompt.

---

## What This Means for the Future of Software

The most profound moment in building an AI Employee is not writing the code. 

It’s walking away from your laptop, living your life for 48 hours, and opening a file at `C:\Users\willi\AI_Employee\csl_daily_briefing.txt` to find that an artificial intelligence checked the market every thirty minutes, read breaking corporate filings, synthesized an A$1.15 billion market catalyst, and filed executive reports—**without you touching the screen once**.

Prompting is the command line of the 2020s. It was the first interface, but it won't be the final one. 

The future doesn't belong to people who know how to ask ChatGPT questions. The future belongs to people who know how to architect autonomous digital employees that do the work for them.

---

#ArtificialIntelligence #AIAgents #AIEmployee #Automation #Python #SoftwareEngineering #FutureOfWork #MachineLearning #TechTrends #Antigravity
