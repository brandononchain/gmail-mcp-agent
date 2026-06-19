# 🤖 Lead Nurturing & Automation

How the nurturing engine (`lead_nurturer.py`) works: automated follow-ups,
response tracking, and lead scoring. It's fully config- and template-driven, so
it carries no campaign-specific content of its own.

## ✅ What it does

- **Follow-up sequences** — automatic follow-ups on a configurable schedule
  (default: day 3 and day 7).
- **Response tracking** — incremental Gmail sync detects replies, idempotently
  (it won't reprocess the same message twice).
- **Lead scoring** — a simple points system based on engagement.
- **Smart responses** — optionally auto-replies to leads who sound interested.

## 📊 Lead lifecycle

```
new → contacted → responded → interested / not_interested
```

Status and scores are persisted to `lead_tracking.json` (git-ignored) after each
cycle, so progress survives restarts.

## 📁 Files

- `lead_nurturer.py` — the nurturing engine
- `run_nurturing.py` — standalone scheduler
- `lead_dashboard.py` — prints a status dashboard
- `nurturing_config.json` — configuration
- `templates/` — the email copy it sends
- `lead_tracking.json` — lead state (auto-created)
- `gmail_sync_state.json` — sync cursor for response checks (auto-created)

## 🛠️ Setup

```bash
pip install -r requirements.txt
```

Then set your identity and preferences in `nurturing_config.json`, and edit the
templates in `templates/`.

## 🎮 Usage

```bash
# Run a single nurturing cycle
python lead_nurturer.py

# Run continuously on a schedule (interval from config)
python run_nurturing.py

# View the dashboard
python lead_dashboard.py
```

## 📈 How it works

### 1. Response monitoring

- Incremental Gmail sync using `after:<timestamp>` plus pagination.
- Maintains `gmail_sync_state.json` to avoid reprocessing messages.
- Extracts the message body (prefers `text/plain`, falls back to stripped HTML).
- Matches against your `response_keywords` to categorize the reply.

### 2. Follow-up sequence

- **Day 0** — initial outreach (sent via `send_from_csv.py`).
- **Day N1** — first follow-up (`followup_1_days`, default 3).
- **Day N2** — second/final follow-up (`followup_2_days`, default 7).
- After the last follow-up, the lead is marked `not_interested` unless they
  reply. All timings are configurable.

### 3. Lead scoring

Point values come from the `lead_scoring` block in your config. Defaults:

- **+10** — a response is received
- **+5** — the response looks interested
- **+2** — any other response
- **-5** — the response looks not interested

### 4. Automated responses

- **Interested** → optional auto-reply using `templates/interested.txt`
  (toggle with `automation.auto_respond_to_interest`).
- **Not interested** → no further follow-ups.
- **Neutral** → continues the nurturing sequence.

## ⚙️ Configuration

See the [configuration reference in the README](README.md#️-configuration-reference)
for the full schema. Key blocks: `subjects`, `follow_up_schedule`,
`response_keywords`, `lead_scoring`, and `automation`.

## 🎯 Best practices

1. Run at least once per day (or use the MCP server / scheduler).
2. Tailor the templates and keywords to your audience.
3. Focus your attention on high-scoring leads.
4. Always honor unsubscribe/opt-out requests and applicable anti-spam laws.

## 🔧 Troubleshooting

- **No responses detected** — check Gmail API permissions/scopes.
- **Follow-ups not sending** — verify `sender_email` (or leave it blank to use
  the authenticated account) and that contacts have a `last_contact` set.
- **Dashboard empty** — run a nurturing cycle first to create
  `lead_tracking.json`.
- **Import errors** — install everything from `requirements.txt`.
