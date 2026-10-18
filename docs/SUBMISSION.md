# Submission kit

Deadline: **Fri Oct 30, 2026, 10:00 am PT** (9:00 pm Mauritius time). Submit by Oct 29.

## 12-day plan

| Day | Date | Goal |
|---|---|---|
| 1 | Sun 18 | Join the hackathon on Devpost and apply to the Nebius Builder Program for credits. Get Token Factory and Tavily keys |
| 2 | Mon 19 | Run locally with keys. `python -m app.check_models`, fix any model ids in `.env` |
| 3–4 | Tue 20–Wed 21 | Live runs on 4–5 different denials (MRI, out-of-network ER, prior-auth drug, Medicare Advantage). Tune prompts where output is weak |
| 5 | Thu 22 | Push to a public GitHub repo, confirm the MIT license shows in the About panel |
| 6 | Fri 23 | Deploy (docs/DEPLOY.md). Test from your phone |
| 7 | Sat 24 | Talk to 2–3 real people who've had a denial; get one quote you can use with permission. This is your "Impact" evidence |
| 8 | Sun 25 | Record the video |
| 9 | Mon 26 | Edit the video, upload to YouTube as **Public** |
| 10 | Tue 27 | Fill in the Devpost form (text below) and the feedback section |
| 11 | Wed 28 | Buffer: fix anything broken; re-test the live URL |
| 12 | Thu 29 | **Submit.** Don't wait for the 30th |

## Devpost text (edit into your own words)

**Tagline:** Your insurer said no. Appeal writes the letter that gets a yes.

**Inspiration:** [Your story here: why you care. A personal or family experience with a denial is the strongest opening you can have.]

**What it does:** Snap a photo of a health-insurance denial. Appeal reads it, explains in plain English what the insurer is claiming, researches the insurer's own coverage policy, clinical guidelines and appeal rules, and drafts a ready-to-send appeal letter. Every claim is cited and verified. You also get your deadline with a calendar reminder, an evidence checklist and a letter-of-medical-necessity template for your doctor.

**How we built it:** A six-step agent that sends each step to the right-sized NVIDIA Nemotron model on Nebius Token Factory. Nemotron 3.5 Super VL reads scanned letters. Nemotron 3.5 Lightning handles triage and research planning. Tavily gathers evidence from authoritative domains. Nemotron 3 Ultra does the one hard reasoning step: building the argument from numbered sources only. Nemotron 3 Super drafts the letter and verifies each citation. Progress streams live to the UI, and a per-step ledger shows tokens and latency per model.

**Challenges:** Keeping a persuasive letter honest. We restricted the strategy model to retrieved sources, strip citations to ids that don't exist in code, and run a separate verification pass. Unknown facts become placeholders instead of being invented.

**What's next:** External-review packet generation, fax/mail sending, tracking an appeal through each level, and Spanish-language support.

**Where Token Factory accelerated the workflow:** One OpenAI-compatible API gave us four Nemotron sizes, so model routing was a config change, not a new integration. [Add a real observation from your testing, e.g. latency per step.]

## Video script (under 3:00)

| Time | Show | Say |
|---|---|---|
| 0:00–0:20 | A real-looking denial letter on a table | "When a health insurer denies care, most people never appeal. The process is confusing, and the deadline is buried in a letter like this one." |
| 0:20–0:35 | Home page | "Appeal turns this letter into a winning appeal in about a minute." |
| 0:35–1:20 | Upload the photo and add a note; steps stream live | Narrate each step and name the model: "Nemotron Super VL reads the scan… Lightning classifies it… Tavily finds the insurer's own policy and the clinical guidelines… Nemotron 3 Ultra builds the argument…" |
| 1:20–2:05 | Result: deadline, strength, letter; click a citation | "Here's the deadline and a calendar reminder. The letter cites every claim, and every citation was checked by a second model. Placeholders mark facts only you know, so nothing is invented." |
| 2:05–2:30 | Checklist, doctor tab, "How it was built" ledger | "Here's what to gather and a template for your doctor. And here's the routing: small models for the easy parts, Ultra only for the reasoning." |
| 2:30–2:50 | You on camera, or a quote from someone you interviewed | Impact: who this is for, and why it matters. |
| 2:50–3:00 | Logo + repo URL | "Appeal. Open source, built on Nemotron and Nebius." |

Record a **live** run, not sample mode. Use no copyrighted music.

## Feedback section (there's a separate $100 prize)

Write specific, actionable notes from your real experience. Examples: how model discovery and ids worked, structured-output/JSON reliability across Nemotron sizes, vision input limits, rate limits, latency of Ultra and how you worked around it, docs gaps (e.g. env vars for Serverless Endpoints). Specific notes beat praise.

## Final checklist

- [ ] Track: Best Apps and Agents
- [ ] Public repo with MIT license visible in About
- [ ] README explains Nemotron + Token Factory + Tavily usage (done)
- [ ] Live demo URL works logged-out
- [ ] YouTube video public, under 3 min
- [ ] Feedback section completed
- [ ] Bonus: Best Use of Tavily qualifies automatically (runtime Tavily call)
