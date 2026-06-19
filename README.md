# 📬 Gmail MCP Agent

An open-source, plug-and-play toolkit for running **personalized Gmail outreach
and automated follow-ups** — controllable over the [Model Context
Protocol](https://modelcontextprotocol.io/) (MCP) so you can drive it from any
MCP-compatible client or run it as a 24/7 background service.

Everything that's specific to a campaign — sender identity, subject lines, email
copy, and your contact list — lives in **config files and the `templates/`
directory**. The code itself ships with no business, industry, or personal data
baked in. Clone it, drop in your credentials, edit a few text files, and go.

> ⚠️ **Send responsibly.** Only email people who have agreed to hear from you,
> honor unsubscribe/opt-out requests, respect Gmail's
> [sending limits](https://support.google.com/a/answer/166852), and comply with
> anti-spam laws (e.g. CAN-SPAM, GDPR, CASL) in your jurisdiction.

## ✨ Features

- **CSV-driven outreach** — send templated, personalized emails to a contact list.
- **Automated follow-up sequences** — configurable timing (default: day 3 and day 7).
- **Response tracking** — incremental, idempotent Gmail sync detects replies.
- **Keyword-based lead scoring** — categorize replies as interested / not interested.
- **Auto-replies** — optionally respond to interested leads automatically.
- **MCP server** — start/stop/monitor the agent from any MCP client.
- **Runs anywhere** — locally, via Docker, or as a systemd service.

## 📁 Project structure

```
├── send_from_csv.py          # One-shot CSV email sender (initial outreach)
├── lead_nurturer.py          # Follow-up sequences, response tracking, scoring
├── mcp_server.py             # MCP server exposing control tools
├── mcp_client.py             # Simple CLI client for the MCP server
├── lead_dashboard.py         # Prints a status dashboard
├── run_nurturing.py          # Standalone scheduler (no MCP needed)
├── templates/                # Your email copy (Jinja2) — edit these
│   ├── initial.txt
│   ├── followup_1.txt
│   ├── followup_2.txt
│   └── interested.txt
├── contacts.csv              # Sample contact list — replace with your own
├── body.txt                  # Body template for send_from_csv.py
├── nurturing_config.json     # Sender identity, schedule, scoring, automation
├── credentials.example.json  # Template for your Gmail OAuth client
├── env.example               # Template for environment variables
├── Dockerfile / docker-compose.yml / deploy.sh
└── gmail-mcp-agent.service   # systemd unit template
```

Files generated at runtime (git-ignored): `token.json`, `lead_tracking.json`,
`gmail_sync_state.json`, `send_log.csv`, `mcp_server.log`.

## 🚀 Quick start

### 1. Install

```bash
git clone https://github.com/brandononchain/GMAIL-MCP-Agent.git
cd GMAIL-MCP-Agent
pip install -r requirements.txt
```

### 2. Get Gmail API credentials

1. Open the [Google Cloud Console](https://console.cloud.google.com/) and create
   (or select) a project.
2. Enable the **Gmail API**.
3. Create an **OAuth client ID** of type **Desktop app**.
4. Download the JSON and save it as `credentials.json` in the project root.
   (See `credentials.example.json` for the expected shape.)

The first time you run a command, a browser window opens for you to authorize
access; a `token.json` is then cached locally for reuse.

### 3. Configure your campaign

- **`nurturing_config.json`** — set `sender_name`, `company_name`, follow-up
  timing, scoring, and automation toggles. Leave `sender_email` blank to use the
  address of the authenticated Gmail account.
- **`templates/`** — edit `initial.txt`, `followup_1.txt`, `followup_2.txt`, and
  `interested.txt`. They're Jinja2 templates; any CSV column is available
  (e.g. `{{ first_name }}`, `{{ company }}`), plus `{{ sender_name }}` and
  `{{ company_name }}`.
- **`contacts.csv`** — replace the sample rows with your list. A `to` column is
  required; `first_name` and `company` are optional but used for personalization.

### 4. Send your initial outreach

```bash
# Send the body.txt template to everyone in contacts.csv
python send_from_csv.py contacts.csv --subject "Quick question" --body_file body.txt
```

### 5. Run automated nurturing

```bash
# One cycle: check for replies, send any due follow-ups, print a report
python lead_nurturer.py

# Or keep it running on a schedule (interval from config)
python run_nurturing.py
```

## 🤖 MCP server

Run the agent as an MCP server so any MCP-compatible client can control it:

```bash
python mcp_server.py
```

It exposes these tools:

| Tool                | Description                                  |
| ------------------- | -------------------------------------------- |
| `start_nurturing`   | Start the background loop (`interval_hours`) |
| `stop_nurturing`    | Stop the background loop                      |
| `run_single_cycle`  | Run one nurturing cycle now                   |
| `get_status`        | System status and lead statistics             |
| `get_lead_report`   | Detailed lead report                          |
| `update_config`     | Update `nurturing_config.json` (hot-reloaded) |
| `send_test_email`   | Send a test email to an address               |
| `get_logs`          | Tail recent server logs                       |

A minimal CLI client is included:

```bash
python mcp_client.py start 4      # start, every 4 hours
python mcp_client.py status
python mcp_client.py report
python mcp_client.py test you@example.com
python mcp_client.py stop
```

To register the server with an MCP client (e.g. Claude Desktop), point it at
`python /absolute/path/to/mcp_server.py`.

## ⚙️ Configuration reference

```jsonc
{
  "sender_email": "",            // blank = use the authenticated Gmail account
  "sender_name": "Your Name",
  "company_name": "Your Company",
  "contacts_file": "contacts.csv",
  "templates_dir": "templates",
  "subjects": {                  // Jinja2 subject lines per stage
    "followup_1": "Following up, {{ first_name }}",
    "followup_2": "One last note",
    "interested": "Re: Great to hear from you"
  },
  "follow_up_schedule": {
    "followup_1_days": 3,
    "followup_2_days": 7,
    "max_follow_ups": 2
  },
  "response_keywords": {
    "interested": ["interested", "yes", "demo", "call"],
    "not_interested": ["not interested", "no thanks", "stop", "unsubscribe"]
  },
  "lead_scoring": {
    "response_bonus": 10,
    "interest_bonus": 5,
    "follow_up_penalty": -1
  },
  "automation": {
    "check_responses_interval_hours": 4,
    "auto_respond_to_interest": true,
    "auto_send_follow_ups": true
  }
}
```

Environment variables (see `env.example`) configure `send_from_csv.py` —
credentials/token paths, default sender, rate limiting (`PER_MINUTE`), and the
log file.

## 🚢 Deployment

**Docker (recommended):**

```bash
./deploy.sh                 # build + run with docker-compose
# or
docker-compose up -d
```

`docker-compose.yml` mounts your `credentials.json`, `contacts.csv`, `body.txt`,
`templates/`, and `nurturing_config.json` into the container, so you can edit
copy without rebuilding.

**systemd:** edit the paths/user in `gmail-mcp-agent.service`, then:

```bash
sudo cp gmail-mcp-agent.service /etc/systemd/system/
sudo systemctl enable --now gmail-mcp-agent
```

## 🔒 Security & privacy

- OAuth2 is used for Gmail access — no passwords are stored.
- `credentials.json`, `token.json`, `.env`, and all runtime state files are
  git-ignored. Never commit them.
- All data stays local; nothing is sent to third parties.

## 📚 More docs

- [`SETUP.md`](SETUP.md) — step-by-step setup
- [`NURTURING_README.md`](NURTURING_README.md) — how nurturing & scoring work
- [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) — production deployment & ops
- [`templates/README.md`](templates/README.md) — writing email templates

## 🤝 Contributing

Contributions are welcome — open an issue or submit a pull request.

## 📄 License

Released under the [MIT License](LICENSE).
