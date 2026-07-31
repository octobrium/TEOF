# TEOF: A Personal Intelligence System

**TEOF helps people recover context, make better decisions, and direct attention toward their own goals.**

Modern life produces more personal information than human memory can reliably integrate. Decisions are scattered across messages, notes, documents, calendars, financial records, and conversations. The reasoning behind an action is often lost even when the action itself remains visible.

At the same time, many digital systems build increasingly accurate models of their users—but primarily to maximize engagement, retention, advertising, or consumption.

TEOF proposes a different use of personal data and adaptive technology:

> **Most platforms model you to capture your attention. TEOF models your life so you can direct your attention deliberately.**

## What TEOF Does

TEOF is a personal database and decision-support system. It preserves important parts of a person's history, keeps the sources attached, and retrieves relevant context when that context can change what the person does next.

### From a scattered history to a decision

Imagine someone evaluating a job offer that would require moving to another state.

The decision is not contained in the offer letter. Its real context is distributed across years of experience: notes from previous jobs, compensation records, messages with colleagues, financial goals, health patterns, relationship commitments, and memories of earlier moves. Some of that history is easy to find. Much of its significance is not.

A conventional search tool can locate a contract or message. TEOF is intended to reconstruct the decision around it. It can recover what the person previously valued in a workplace, why an earlier role became unsustainable, which compensation assumptions proved accurate, how geography affected important relationships, and what the person said they wanted before the new offer appeared.

The system then brings that history into the present. It distinguishes source material from later interpretation, identifies the constraints that are active now, and shows where the new opportunity supports or conflicts with the person's stated priorities. Instead of producing an unexplained answer, it helps construct a decision record: the evidence, the tradeoffs, the expected outcome, the confidence behind that expectation, and the next action required.

Suppose the person accepts the offer. Several months later, TEOF can return to the original reasoning and compare it with what actually happened. Was the compensation model accurate? Did the move improve the conditions it was meant to improve? Which concerns were justified, and which were projections from an earlier experience?

The result becomes part of the next decision. The database is therefore not only a record of the past. It is a growing calibration history—what the person believed, why they believed it, what they did, and what reality returned.

### From a decision to daily direction

The same record also helps at a smaller scale.

On an ordinary morning, the user may remember a dozen unfinished tasks but not the structure connecting them. A stressful message may feel more important than a quiet deadline. A new idea may displace a commitment made the previous week. After an interruption or low-energy period, even a well-formed plan can disappear from working memory.

TEOF reconstructs the current situation from the same underlying history. The job decision, financial constraints, health state, relationship commitments, active projects, and unresolved obligations are not separate dashboards competing for attention; they are parts of one life. The system uses their relationships to identify the next action most likely to matter.

The intended output is not more information. It is enough recovered context to act coherently.

## Attention Sovereignty

The modern attention economy is highly engineered. Platforms study behavior to predict what will cause a person to click, return, continue scrolling, or remain emotionally activated. These systems are often effective because their objectives are clear and measurable.

TEOF applies similar capabilities—behavioral modeling, feedback, visible progress, contextual recommendations, and adaptive interfaces—but changes the objective.

Consider the same morning. A conventional feed has learned which novelty, conflict, or social signal is most likely to capture the user. Its model may be accurate, but it serves the platform's objective: another interaction.

TEOF uses a model of the user on the user's behalf. It may recognize that the emotionally salient message is not the most consequential item, recover the reason a quiet deadline matters, and surface the twenty-minute action that advances the user's stated goal. Once the context has been restored and the action is clear, the system has done its job. It does not benefit from keeping the user inside it.

This is the core engineering problem of attention sovereignty: building technology that helps users allocate attention according to their considered goals rather than allowing external systems to allocate it for them.

TEOF can use quests, progress indicators, and feedback where these make real goals easier to understand and pursue. It rejects variable rewards, compulsory check-ins, streak preservation, and notifications designed primarily to manufacture engagement.

Success is not measured by time spent in TEOF. Success is measured by improved memory, better-calibrated decisions, completed external actions, and greater control over attention.

## How It Works

The basic process is:

```text
capture
→ organize
→ retrieve
→ interpret
→ prioritize
→ act
→ observe outcomes
→ update
```

TEOF preserves personal information in portable, inspectable formats such as Markdown, JSON, SQLite, and git. The underlying data belongs to the user and should survive changes in interfaces, AI models, and software platforms.

AI assists with retrieval, synthesis, pattern detection, and recommendation. Human review remains the authority for consequential interpretations and decisions.

> **AI may propose what the evidence means. The user decides what becomes part of their operating model. Reality determines whether that model survives.**

### Permissioned autonomy

TEOF can be maintained manually, but its larger potential comes from connecting it to the information systems a person already uses. With the user's permission, importers can gather data from selected sources such as messages, email, calendars, financial records, health exports, project tools, or browser history.

The user defines the boundary. One person might allow calendar and project data but exclude private messages. Another might permit a one-time archive import without ongoing access. A third might authorize scheduled updates while requiring approval before any interpretation changes their goals, personal record, or external systems. Permissions should be narrow, revocable, and visible rather than bundled into a single grant of access.

Consider the job-offer example. If the user has permitted access to the relevant sources, TEOF can detect the new offer, connect it to prior compensation records and relocation plans, recover earlier conversations about career priorities, and assemble a cited decision brief. It can notice that accepting the offer implies several dependent goals—review the contract, compare housing costs, complete licensing, plan the move—and surface them in an appropriate order.

The same process applies to ideas. A thought captured in a message or inbox can be routed to an existing project, linked to related observations, or proposed as a new goal. If the idea repeats, resolves an identified problem, or becomes time-sensitive, its priority can rise. If it duplicates an existing conclusion, the system can integrate it rather than creating another disconnected note.

This automation is intended to reduce maintenance without transferring authority. A typical governed cycle is:

```text
user-authorized sources
→ deterministic extraction and sorting
→ provenance-preserving storage
→ AI synthesis and proposed relationships
→ ranked goals, risks, and ideas
→ human approval where judgment or action is consequential
→ auditable update
```

Deterministic rules handle routine work where possible: parsing dates, matching known entities, detecting duplicates, checking deadlines, or refreshing derived metrics. AI is reserved for tasks that require interpretation, such as synthesizing several sources, explaining why an item may matter, or proposing how a new observation relates to an existing goal.

The interface can then surface what changed and why: a deadline approaching, a goal blocked by a prerequisite, an idea that connects two projects, or a prior prediction ready to be evaluated. The system may run automatically, but its reasoning remains inspectable and its consequential actions remain subject to the level of approval chosen by the user.

The objective is governed autonomy: less manual sorting, better synthesis, and timely direction without creating an opaque system that silently rewrites the user's priorities or acts beyond its authorization.

## Foundations

TEOF begins from a minimal observation: **observation is occurring**. From there, it adopts a practical method of recording differences, identifying patterns, testing interpretations, and revising models against outcomes.

The shortest version is:

```text
1. Observation is.
2. Observation registers difference.
3. Some patterns persist while others collapse.
4. Recursive observation enables refinement.
```

This foundation informs the system, but using TEOF does not require adopting a comprehensive metaphysical position. Its practical value should be judged by whether it improves retrieval, decisions, action, and correction.

## Present Status

TEOF currently exists as a working personal system built around one longitudinal life record. It has demonstrated practical value in memory retrieval, state reconstruction, decision support, relationship continuity, and attention allocation.

Its broader product thesis remains experimental. The next test is whether the architecture can produce comparable value for other users without requiring excessive maintenance or imposing one person's model of life on everyone else.

TEOF should ultimately be judged by concrete outcomes: whether it recovers context the user would otherwise have lost, improves consequential decisions, directs attention toward the user's stated goals, detects when its own model is wrong, and produces enough benefit to justify the effort of maintaining it.

## Start Here

For the shortest introduction:

1. Read [core/TEOF-core.md](core/TEOF-core.md).
2. Read [core/layers/L1 principles.md](core/layers/L1%20principles.md).
3. Read [core/TEOF.md](core/TEOF.md) for the full framework.

To begin building a personal system:

1. Read [ONBOARDING.md](ONBOARDING.md).
2. Read [memory/README.md](memory/README.md).
3. Use [seed/](seed/) to create a small personal record.
4. Apply the process to one consequential decision and evaluate it against the eventual outcome.

---

**TEOF is a personal intelligence system that turns a longitudinal life database into recoverable context, better decisions, and user-directed attention.**

Apache-2.0 · Evan Yu · BTC: bc1qxfg8m5tttz5u860f0j7cyhupgdcz25jku44s9c
