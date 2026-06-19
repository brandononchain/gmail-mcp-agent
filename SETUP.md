# 🚀 Quick Setup Guide

## 1. Clone the repository

```bash
git clone https://github.com/brandononchain/GMAIL-MCP-Agent.git
cd GMAIL-MCP-Agent
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure Gmail API

### Get Google OAuth2 credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select an existing one).
3. Enable the **Gmail API**.
4. Create **OAuth client ID** credentials of type **Desktop app**.
5. Download the JSON file.

### Install the credentials

```bash
# Save your downloaded OAuth client as credentials.json
cp /path/to/your/downloaded.json ./credentials.json
```

`credentials.example.json` shows the expected structure. The first time you run
a command, a browser opens to authorize access and a `token.json` is cached.

## 4. Configure your environment (optional)

```bash
cp env.example .env
# edit .env with your preferred editor
```

## 5. Set up your campaign

- Edit **`nurturing_config.json`** — set `sender_name`, `company_name`, and
  preferences. Leave `sender_email` blank to use the authenticated account.
- Edit the templates in **`templates/`** — `initial.txt`, `followup_1.txt`,
  `followup_2.txt`, `interested.txt`.
- Replace the sample rows in **`contacts.csv`** with your own list (a `to`
  column is required).

## 6. Test the system

```bash
# Send your initial outreach from the CSV
python send_from_csv.py contacts.csv --subject "Quick question" --body_file body.txt

# Run one nurturing cycle (checks replies, sends due follow-ups)
python lead_nurturer.py
```

## 7. Deploy 24/7 (optional)

```bash
./deploy.sh            # Docker
# or
docker-compose up -d
```

## 🔑 Files you provide

- `credentials.json` — your Gmail API credentials (git-ignored)
- `token.json` — auto-generated OAuth token (git-ignored)
- `.env` — your environment configuration (git-ignored)

## ⚠️ Security notes

- **Never commit** `credentials.json`, `token.json`, or `.env`. They're already
  in `.gitignore`.
- Use `credentials.example.json` and `env.example` as templates.
- Only email people who have opted in, and honor unsubscribe requests.

See [`README.md`](README.md) for full documentation.
