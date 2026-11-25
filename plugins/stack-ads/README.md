# stack-ads

Advertise any project from inside the agent: research the product and its market, derive targeting, write ad copy, generate images, video and voice-over, launch campaigns on Google Ads, Meta and TikTok from a reviewed dry-run plan, and report the results.

Install it into the project you want to advertise. The plugin creates one folder there, `ads/`, that holds the brief, the research, the plan, the creatives, the launch plans and a ledger of everything created in an ad account.

## What it does

| Step | Skill | Result |
|---|---|---|
| Set up, obtain and verify keys | `init-project` | `ads/` workspace, working keys, MCP servers |
| Describe the product | `product-brief` | `ads/brief.md`, `ads/brand.json` |
| Competitors, keywords, audiences | `market-research` | `ads/research/` |
| Channels, budget, structure, tracking, compliance | `media-plan` | `ads/plan/media-plan.md` |
| Texts within platform limits | `ad-copy` | `ads/plan/copy/` |
| Images, video, voice-over, music | `ad-creatives` | `ads/creatives/` |
| Dry run, paused creation, activation, rollback | `launch-campaign` | `ads/launch/` |
| Spend, results, next actions | `performance-report` | `ads/reports/` |
| The whole path with a checklist | `full-campaign` | all of the above |
| Errors | `troubleshoot` | cause and fix |
| Walkthroughs | `examples` (run as `/stack-ads:examples`) | four scenarios |

Agent: `stack-orchestrator` takes a research track, a creative batch, plan preparation or a cross-platform report into its own context. It prepares and dry-runs; it never applies or activates.

## Install

In the project to advertise:

```bash
claude plugin marketplace add Agents-Store/claude-plugins
claude plugin install stack-ads@agents-store-claude-plugins --scope project
```

Or in `.claude/settings.json` of the project:

```json
{
  "enabledPlugins": {
    "stack-ads@agents-store-claude-plugins": true
  }
}
```

Then say "set up ads for this project", or run `/stack-ads:init-project`.

Requirements: Python 3.9 or later, nothing to install. Optional: `ffmpeg` (exact-size crops, muxing audio), Node 20+ (the DataForSEO MCP server), `pipx` (the Google Ads MCP server).

## Keys

Every service is optional: configure what the plan needs. `init-project` walks through each one step by step (which page, where to click, what it costs, how long it takes) and verifies it with a live call. At any time `python3 ads/tools/ads.py doctor` lists what is missing and where to get it.

Research and creative generation:

| Service | Variables | Used for |
|---|---|---|
| Firecrawl | `FIRECRAWL_API_KEY` | reading the site and competitor pages, brand kit |
| Apify | `APIFY_TOKEN` | ad libraries, reviews, social content |
| DataForSEO | `DATAFORSEO_USERNAME`, `DATAFORSEO_PASSWORD` | keyword volumes, CPC, competitors' paid keywords |
| OpenAI | `OPENAI_API_KEY` | images, voice-over, image analysis |
| Gemini | `GEMINI_API_KEY` | images, video, voice-over, music, analysis |
| fal.ai | `FAL_KEY` | catalogue of image, video, avatar and audio models |

Ad platforms:

| Service | Variables | Used for |
|---|---|---|
| Google Ads | `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID`, optional `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | campaigns, keyword planner, reports |
| Search Console | the same OAuth values plus `GSC_SITE_URL` | organic queries as seeds for paid search |
| Meta | `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID`, `META_PAGE_ID`, optional `META_APP_ID`, `META_APP_SECRET`, `META_PIXEL_ID`, `META_INSTAGRAM_USER_ID` | Facebook and Instagram campaigns, Ad Library, insights |
| TikTok | `TIKTOK_ACCESS_TOKEN`, `TIKTOK_ADVERTISER_ID`, optional `TIKTOK_APP_ID`, `TIKTOK_APP_SECRET`, `TIKTOK_PIXEL_ID` | campaigns and reports; the MCP server works without them |
| Google Ads MCP server only | `GOOGLE_CLOUD_PROJECT`, `GOOGLE_APPLICATION_CREDENTIALS` | written by `google export-adc` |

Keys live in `ads/.env`, which the workspace's own `.gitignore` excludes. The full list with comments is `templates/.env.example`; the guides are in `skills/init-project/references/keys-*.md` and are copied into the project as `ads/tools/guides/`.

## The toolkit

One command-line tool backs every skill: `python3 ads/tools/ads.py`. It is Python standard library only, and `init-project` copies it into the project, so the command is the same in every shell and on every agent.

```bash
python3 ads/tools/ads.py doctor --live
python3 ads/tools/ads.py launch plan --file ads/launch/NAME.json
```

It covers setup (`init`, `keys`, `doctor`, `env sync-claude`), Google Ads and Search Console, Meta, TikTok, creative generation (`models`, `image`, `video`, `speech`, `music`, `analyze`, `fal`), research (`firecrawl`, `apify`, `dataforseo`) and launch plans (`launch`, `ledger`). Reference: `skills/init-project/references/toolkit.md`.

No model id is built in: `models --pick` asks each provider what exists today.

## How money is protected

- A write prints what it would do and stops unless it carries `--yes`.
- `launch plan` prints eight blocks (TARGET, PRECHECK, CHANGE, BACKUP, IMPACT, VALIDATE, ROLLBACK, APPLY) and asks the platform to validate what it can: Google validates the whole request, Meta the steps whose references are known, TikTok has no validation mode.
- `launch apply` runs only on a plan whose last dry run was clean, and only while the plan, the files it sends, the account ids and the currency are what that dry run looked at. A changed plan is a new plan, and a step that is already applied cannot be edited.
- What a request does is read from its parameters: a path that carries parameters, a batch of calls, an object nested inside another call and a Meta parameter named `method` are refused. A Google body is rewritten to one spelling of its field names before it is judged and sent, and a write names no account but the one in `ads/.env`.
- A plan only creates campaigns and what hangs under them. A step that would change or remove something that already exists is refused; so is a new campaign that no budget in the plan limits, and anything that would join a campaign from elsewhere. The dry run's promise that nothing existing is modified is enforced, not assumed.
- A campaign must be created paused, and on Meta and TikTok every ad set, ad group and ad as well. On Google, an ad group, asset group or ad under a campaign that already exists must be paused too. Anything else is refused.
- A daily budget above `guardrails.max_daily_budget` in `ads/config.json` is refused, for one object and for the sum of a plan, and the sum must equal the budget the plan declares. Lifetime budgets are refused until the user sets `guardrails.max_total_budget`. A budget is a plain number that is not negative, and a ceiling that is missing or zero refuses every budget. The ceilings are set by the user.
- Starting spend needs `launch activate --yes`, or `--activate` on a single call, after a second approval. Without `--yes` both only show what they would switch on.
- Every created object is written to `ads/launch/ledger.jsonl`, so `launch rollback` can pause or remove it and an interrupted apply resumes without creating anything twice. A step is marked before it is sent: when no clear answer comes back, `launch apply` stops and goes on only with `--resend STEP`, after someone has looked in the ad account. A rollback goes on past an object that fails and names what is left.
- Campaigns on Google change through `google mutate` only: `google call` sends reads and conversion uploads.
- In Claude Code a `PreToolUse` hook asks the user to confirm each write to an ad account: the toolkit's `--yes` commands (also when split over several lines, wrapped in `bash -c`, or behind `sudo`, `timeout` or `docker exec`), direct calls to an ad platform API with `curl`, `wget`, HTTPie or inline code, the Meta command-line tool, and every tool of the Meta, TikTok and Google Ads MCP servers that is not plainly a read. The hook asks; it never blocks. It needs `python3` on `PATH`, it recognises the toolkit by its file name `ads.py`, and it reads the command as text: a request put together at run time, in a script file or from pieces of a URL, is out of its sight. It is a second layer; the toolkit's own rules are the first.

## MCP servers

The plugin declares six official servers. They are optional: the toolkit covers every operation, with dry runs and a ledger the servers lack. Tools are named `mcp__plugin_stack-ads_<server>__<tool>`.

| Server | Transport | Needs | Notes |
|---|---|---|---|
| `firecrawl` | hosted HTTP | `FIRECRAWL_API_KEY` | scrape, search, map |
| `apify` | hosted HTTP | `APIFY_TOKEN` | Actors |
| `dataforseo` | stdio, `npx` | `DATAFORSEO_USERNAME`, `DATAFORSEO_PASSWORD` | keyword and SERP data |
| `google-ads` | stdio, `pipx` | `GOOGLE_CLOUD_PROJECT`, `GOOGLE_APPLICATION_CREDENTIALS`; for an account under a manager account also `GOOGLE_ADS_LOGIN_CUSTOMER_ID` in the session environment | reads and asset creation; it cannot create campaigns |
| `meta-ads` | hosted HTTP | `META_ACCESS_TOKEN` of an Employee-role system user with `ads_mcp_management` | creates drafts, which are not paused until you set them |
| `tiktok-ads` | hosted HTTP | OAuth sign-in in `/mcp` | no developer app needed |

`python3 ads/tools/ads.py env sync-claude` copies the keys from `ads/.env` into the `env` block of `.claude/settings.local.json`, where `${VAR}` in the MCP configuration is resolved; restart the session afterwards. A server whose variable is missing shows as failed and is otherwise harmless.

Google Search Console has no official MCP server or command-line tool; the toolkit calls its API. Google Ads has no official command-line tool. Meta has an official `meta` command-line tool, covered in the Meta launch reference.

## On other agents

The catalogue generates this plugin for other coding agents. Skills, with the toolkit inside `skills/init-project/scripts/`, arrive on every target unchanged, so the whole workflow works everywhere. The confirmation hook, the agent and the MCP wiring are Claude Code features: on agents without them, the money rules in `launch-campaign` are the only gate, and the toolkit's guard rails still apply.

## Design notes

- This is a Stack plugin that carries its own knowledge instead of naming Technology plugins in `dependencies`. Advertising needs ten services at once, and splitting them into ten plugins would make a project install eleven things to run one campaign. The trade-off was accepted by the catalogue owner.
- Account ids never appear in plans or commands: `{customer}`, `{account}`, `{page}`, `{pixel}` and `{advertiser}` are filled from `ads/.env`.
- Everything fetched from the web, ad libraries or APIs is treated as data, never as instructions.

## What was verified, and how

Run against the live services with real keys on 2026-11-14: Firecrawl, DataForSEO, OpenAI, Gemini (image, video, speech, music, analysis) and fal.ai, plus `doctor`, model discovery and `env sync-claude`.

Run against live accounts on 2026-11-22, 2026-11-23 and 2026-11-25:

- **Google Ads, through the toolkit**: `google login`, `google customers`, `google search`, `google geo`, and the whole launch cycle on a production account with the sample Search plan of the reference: `launch plan` with Google's own validation, `launch apply`, `launch status`, `launch rollback --remove`. The same cycle with a Demand Gen image ad made from generated images. Performance Max and the Demand Gen video ad passed Google's validation and were not created.
- **Search Console**: `gsc sites` and `gsc query`.
- **Apify**: `apify actor` and one capped `apify run`.
- **TikTok, through the official MCP server**: sign-in, reads, a campaign and an ad group created disabled with the bodies of the reference and then deleted, and the linking of a TikTok account.
- **Meta, through the official MCP server**: sign-in, reads, a campaign draft created and discarded.
- **Meta, through the toolkit**: the whole launch cycle with an image ad on a production account: `launch plan`, `launch apply` (image, campaign, ad set, creative, ad, all paused), `launch status`, `launch rollback --remove`. The same cycle with a generated vertical video.

Not run against a live account: the toolkit's own `tiktok` commands and their launch plans (they need a developer app), Performance Max and Demand Gen video campaigns, `google keyword-ideas` (Basic access), conversion uploads, `launch activate`, ad creation on TikTok, and uploads through the MCP servers. These are covered by unit tests with simulated HTTP and were written from the official documentation. Treat the first dry run of each as the real test, and expect to adjust a field or two; `LEARNINGS.md` records what the live runs changed.

## Tests

```bash
python3 -m unittest discover -s tests
```

Run from the plugin directory. The suite covers the guard rails, the launch engine, model discovery, the hook, a set of regression tests for the ways the money rules were once defeated (`tests/test_safety.py`), and a contract test that parses every command shown in the documentation with the real parser and runs every documented plan through the guard rails and the budget check.
