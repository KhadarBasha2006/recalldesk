# ✅ Submission Checklist — HackwithHyderabad (deadline Sept 29)

**Team: Legacy Legends** · Repo: https://github.com/KhadarBasha2006/recalldesk

**Roster:** Shaik Adil (leader) · Shaik Khadar Basha · Shaik Irfan · Syed Shahid Ahamed · Shaik Mohammad Murtuza Ayaan

> Content rule of thumb: **each of the 5 members** submits their own article + LinkedIn post (you may cover the same project from different angles); **one team** video total.

One submission per team. Every field of the final submission form, in order, with what to do.

---

## 0. Two forms exist — don't confuse them

| Form | Who | Status |
|---|---|---|
| **Profile Review Form** (https://forms.gle/AXWnanWsEEir6xSP9) | **EVERY team member, individually** | ⬜ Each member fills it. Teams are NOT reviewed for selection without it. |
| **Final Submission Form** (https://forms.gle/cD7fCnPnkdVm2sH78) | Team leader, once | ⬜ After the steps below |

---

## 1. GitHub Repository → the repo link

- [ ] Create the repo on your GitHub account (e.g. `recalldesk`), **public**
- [ ] Push this project (commands in "Push" section below)
- [ ] Edit `README.md` → replace `Team [your-team-name]`, member names, and the GitHub URL in the article/LinkedIn drafts
- [ ] Verify: a judge can run `docker hindsight → seed → api → web` from the README in < 10 minutes
- [ ] CI badge green (Actions run on push)

## 2. Demo Video → the video link

- [ ] Record with `content/video_script.md` (2–4 min, 1080p, OBS/Loom)
- [ ] Upload to **YouTube as public** (a Drive link is explicitly discouraged)
- [ ] Make a thumbnail (prompt provided at the bottom of the script)
- [ ] Paste the YouTube link in the form

## 3. Article (every member) → the article link

- [ ] Each member publishes their own article: Medium / Dev.to / Hashnode / LinkedIn Articles / Substack
- [ ] Base: `content/article.md` — **edit it into your own voice, add 2+ screenshots**
- [ ] **No mention of the hackathon anywhere in title or body (disqualifying)**
- [ ] Keep the three required links live: Hindsight GitHub, Hindsight docs, Vectorize agent-memory page
- [ ] Pre-submit checklist at the bottom of the content guide — verify all 9 items

## 4. LinkedIn Post (every member) → the social post link

- [ ] Each member posts: base in `content/linkedin_post.md` (under 800 chars)
- [ ] Article URL as **first comment**; Hindsight repo link as **second comment**
- [ ] Hashtags only on the last line; **no #hackathon-style tags (disqualifying)**
- [ ] Add your repo link in the main post body
- [ ] Tag Code.in (per content guide) if used

## 5. Reddit Post → the reddit link

- [ ] Submit the article as a **Link post** on ONE of: r/llmdevs, r/sideproject, r/aiagents, r/aimemory
- [ ] Title/body drafts: `content/reddit_post.md`
- [ ] Paste the Reddit thread URL in the form

## 6. FEEDBACK field

Write 2–3 honest sentences (what worked, what to improve). Example you can adapt:

> "The problem statement and content guide were unusually clear — the 25% memory weighting pushed us to make memory the product instead of a feature. What could be better: a sandboxed one-click Hindsight instance (or a longer cloud trial) would remove the biggest setup hurdle for judges reproducing projects, and earlier clarity on the live-demo format would help teams prepare."

---

## Push the repo (from this folder)

```bash
cd hindsight_support_agent
git init
git add .
git commit -m "RecallDesk: support agent with total recall — Hindsight memory + Groq"
git branch -M main
git remote add origin https://github.com/<your-username>/recalldesk.git
git push -u origin main
```

## Before you hit Submit — final sanity pass

- [ ] Repo link opens in an incognito window (public, not 404)
- [ ] Video is **public** on YouTube and starts with the problem, not a logo animation
- [ ] Every member has: article ✅ + LinkedIn post ✅ (+ Profile Review Form ✅)
- [ ] All four links open from a device you didn't post from
- [ ] Everyone on the team agrees — **one submission only**
- [ ] Submitted before **Sept 29 EOD** (don't wait for the last hour)
