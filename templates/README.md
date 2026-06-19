# Email Templates

These files define the messages the agent sends. They are
[Jinja2](https://jinja.palletsprojects.com/) templates, so any column in your
`contacts.csv` is available as a variable (e.g. `{{ first_name }}`,
`{{ company }}`), along with `{{ sender_name }}` and `{{ company_name }}` from
your config.

| File             | When it's used                                                |
| ---------------- | ------------------------------------------------------------- |
| `initial.txt`    | First-touch outreach (used by `send_from_csv.py` via `body.txt`, or as a reference) |
| `followup_1.txt` | First automated follow-up (default: 3 days after contact)     |
| `followup_2.txt` | Second / final automated follow-up (default: 7 days)          |
| `interested.txt` | Auto-reply sent when a lead's response looks interested        |

## Customizing

1. Edit the text in each file. Replace the bracketed `[ ... ]` placeholders.
2. Add or remove `{{ variable }}` tags to match the columns in your CSV.
3. Change which directory is loaded with the `templates_dir` key in
   `nurturing_config.json` (default: `templates`).

If a template file is missing, the agent falls back to a built-in generic
version so it always has something to send.
