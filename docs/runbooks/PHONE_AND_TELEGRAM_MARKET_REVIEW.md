# Phone and Telegram Market Review Runbook

Status: manual phone workflow ready; Telegram integration not enabled  
Scope: V2 paper-only market reviews

## Recommended route now: private ChatGPT Project

1. On the ChatGPT phone app, create a private Project called
   `V2 Paper Market Review`.
2. Open the Project menu, choose Project settings, and paste the Project
   instructions from
   `docs/prompts/V2_PHONE_MULTI_TIMEFRAME_MARKET_REVIEW_PROMPT.md`.
3. Use project-only memory if available and keep the Project private.
4. Upload the 1h, 30m and 5m screenshots with the `+` button.
5. Paste the short phone prompt from the same file.
6. Save useful completed responses as Project sources, but refresh market and
   policy research for every new review.

This route needs no API, bot token, local scheduler or broker connection.

## Why Project instructions are preferable

- They apply only to the trading-review Project rather than every ChatGPT chat.
- The Project can retain the reusable methodology and prior non-sensitive
  reports while each new chat supplies fresh charts and research.
- The same Project can be opened on phone and web.

Do not upload screenshots containing balances, account identifiers, positions,
names or other private information.

## Telegram options

### Option A — manual share

Copy the finished review into a private Telegram message to yourself. This is
the safest Telegram route because no bot, token, listener or scheduler is
required.

### Option B — one-way manual bot sender

This could be built later as a small local script that sends one reviewed,
sanitised summary to an allowlisted Telegram chat when the operator manually
runs it.

Required controls:

- explicit approval before implementation and again before the first send;
- bot token held in macOS Keychain and injected only at runtime;
- no token, chat identifier or personal information in repository files;
- exact allowlist check before sending;
- one-way outbound summaries only;
- no inbound commands, no background listener and no scheduler;
- local preview and human confirmation before every send;
- no broker, exchange, MT5 or live-trading connection.

### Option C — automated Telegram intake/alerts

Not approved. V2 currently states that Telegram and heartbeat services are
disabled and tasks run manually. Enabling a bot listener, scheduler, remote
commands or unattended alerts would cross authentication, connector, external
messaging and automation gates and needs a separate security review and explicit
human approval.

## Recommended next decision

Use the private ChatGPT Project workflow first. If manual Telegram copying is
still too slow after several reviews, review and approve a one-way manual sender
as a separate task. Do not begin with an inbound bot or scheduler.

