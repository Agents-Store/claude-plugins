# LEARNINGS — stack-ads

## 2026-11-14 — plugin: a Stack plugin without `dependencies`

**Problem:** The catalogue rule says a Stack plugin describes the architecture only and names its parts in `dependencies`. Advertising needs ten services at once (three ad platforms, Search Console, three research services, three generation providers), and no Technology plugin for most of them exists.
**Fix:** `stack-ads` is self-contained: its skills carry the knowledge and one toolkit carries the calls. The owner accepted the deviation before the build.
**Root cause:** The rule assumes the parts already exist as plugins. Here they do not, and a project would have to install eleven plugins to run one campaign.
**Severity:** Minor

## 2026-11-14 — launch-campaign: ad platform calls were not run against a live account

**Problem:** No Google Ads, Meta or TikTok credentials and no valid Apify token were available during the build. Firecrawl, DataForSEO, OpenAI, Gemini and fal.ai were run live.
**Fix:** The Google Ads, Search Console, Meta, TikTok and Apify paths are covered by unit tests with simulated HTTP and were written from the official documentation read on 2026-11-14. The references mark what is unverified. On first live use check, in this order: `doctor --live` for the platform, a `launch plan` on a minimal plan, `launch apply` of one paused campaign, `launch status`, `launch rollback --remove`.
**Root cause:** Access to a real ad account is the owner's to grant; a test account was not part of the task.
**Severity:** Major

## 2026-11-14 — launch-campaign: TikTok ads stayed disabled after activation

**Problem:** The guard rail accepted ads created with `operation_status` `DISABLE`, but `launch activate` enabled only the campaign and the ad groups, and for Smart+ only the campaign. A plan that followed the reference would have been "activated" and never delivered.
**Fix:** Every level is created disabled and `launch activate` enables campaign, ad groups and ads, in that order, in batches of 20; `launch rollback` reverses it. Smart+ uses its own status endpoints (`campaign_ids`, `adgroup_ids`, `smart_plus_ad_ids`), confirmed on the official pages. A status change TikTok refuses comes back under `code` 0 in `error_list`; the toolkit now treats that as an error.
**Root cause:** The activation code and the launch reference were written separately and disagreed about which levels carry a status.
**Severity:** Critical

## 2026-11-14 — launch-campaign: a GMV Max campaign cannot be created paused

**Problem:** `campaign/gmv_max/create/` has no `operation_status` field, so the rule "everything is created paused" cannot be enforced by sending a status.
**Fix:** The guard rail refuses that call in a launch plan and outside one unless it carries `--activate` as well as `--yes`, and the reference says to pause it afterwards with `campaign/status/update/`.
**Root cause:** The first guard rail assumed every create call takes a status field.
**Severity:** Major

## 2026-11-14 — ad-creatives: an explicit provider replaced the saved default model

**Problem:** `image --provider openai` without `--model` picked a model for that provider and saved it as the project default, silently changing later calls.
**Fix:** The default stays in `models` of `ads/config.json`; a pick made for an explicitly named provider is cached per provider in `model_cache`.
**Root cause:** One function both resolved and saved.
**Severity:** Minor

## 2026-11-14 — ad-creatives: generated files had unpredictable names

**Problem:** File names always carried a timestamp, so a plan file or a later command could not refer to `ads/creatives/hero.png` after `--name hero`.
**Fix:** A given `--name` is kept (`hero.png`, then `hero-2.png`); an existing file is never overwritten. Without a name the timestamp stays.
**Root cause:** Uniqueness was solved by time instead of by checking what exists.
**Severity:** Minor

## 2026-11-14 — references: delegated reference files contradicted the toolkit

**Problem:** Several references, written in parallel with the toolkit, described commands and behaviour it does not have: no upload in `fal run`, no `music` command, wrong default metrics, placeholders "unverified", activation semantics.
**Fix:** Each reference was reconciled with the code, and `tests/test_docs.py` now parses every `python3 ads/tools/ads.py ...` command in any markdown file with the real argument parser and runs every complete plan through the guard rails.
**Root cause:** Documentation written before the tool it documents. Keep the contract test green when a command or a reference changes.
**Severity:** Major

## 2026-11-14 — launch-campaign: an edited plan could be applied without a new dry run

**Problem:** After a failed step the skill said to fix the plan and run `launch apply` again, and `apply` checked only that `--yes` was present. The edited step reached the ad account without the user having seen it, against the skill's own rule that a changed plan is a new plan.
**Fix:** `launch plan` records each dry run in the ledger with a fingerprint of the plan's content; `launch apply` refuses unless the last dry run was clean and the fingerprint still matches. Skill, references and examples say: fix, dry run again, show, ask, apply.
**Root cause:** A rule that lived only in prose. Found by the `plugin-dev:skill-reviewer` review.
**Severity:** Critical

## 2026-11-14 — launch-campaign: the budget ceiling covered one object, not the plan

**Problem:** The ceiling was checked per request, so ten ad sets of 20 each passed a ceiling of 50, lifetime budgets were not checked at all, and the IMPACT block printed the budget the plan declared, not the one its steps carried.
**Fix:** `launch.budget_check` adds up the budgets of all steps (a campaign budget caps the ad sets or ad groups below it), compares the sum with the declared `budget.daily` and with the ceiling, and blocks the plan on a mismatch, in the dry run and again in apply. Lifetime budgets are refused until the owner sets `guardrails.max_total_budget`. `tests/test_docs.py` runs every documented plan through the check.
**Root cause:** The guard rails were written per request, where a plan's total is not visible.
**Severity:** Critical

## 2026-11-14 — hooks: the confirmation hook could be bypassed

**Problem:** The guard matched commands with regular expressions that stopped at a newline, so `launch apply \` continued on the next line passed silently; `curl --request POST`, `-d@file`, `--json`, `wget`, HTTPie and inline Python or Node were not recognised; MCP tools were matched by a list of write verbs and passed when the verb was unknown; the Google Ads server was not covered.
**Fix:** `hooks/guard.py` now joins continued lines, splits the command into simple commands with quotes respected, reads the toolkit's arguments as tokens, knows the common HTTP clients, and asks for every tool of the Meta, TikTok and Google Ads servers that is not plainly a read. Fixtures in `tests/plugins/stack-ads/hooks/` and `tests/test_hook.py` hold the bypass cases.
**Root cause:** A deny-list of shapes instead of parsing the command, and allow-by-default for unknown tools. Found by the `plugin-dev:plugin-validator` review.
**Severity:** Critical

## 2026-11-14 — troubleshoot: the error reference offered spend and appeals as fixes

**Problem:** `errors.md` listed `launch activate --yes` as the fix for a paused parent, an exemption request and a TikTok appeal as commands to run, and "rephrase" as the answer to a safety refusal.
**Fix:** A paused object is not an error; activation, exemptions and appeals are proposed to the account owner and run only on their decision; a refused generation means changing what is asked for.
**Root cause:** A reference written as a list of fixes, without the money rules of the launch skill in view.
**Severity:** Major

## 2026-11-14 — full-campaign: a ticked gate in the checklist read as approval

**Problem:** The checklist survives sessions and said "continue at the first open item", so a new session could take a ticked "user approved activation" as permission to spend.
**Fix:** The skill and the template say that a ticked gate is history, not approval; the apply and activation gates are asked again in the session that acts, and unticked after any plan edit.
**Root cause:** One file served as both memory and permission.
**Severity:** Critical

## 2026-11-14 — all skills: hand-offs and descriptions

**Problem:** Skills ended with "then continue with the next skill", which jumped past the gates of `full-campaign` and past a user who asked for one step; several descriptions overlapped (brief and research on "audience", launch and report on "pause", setup and full path on an empty project).
**Fix:** Each skill offers the next step instead of taking it; every description names its neighbours.
**Root cause:** Skills written one by one, without reading them as a set.
**Severity:** Minor

## 2026-11-14 — tests: the hook fixture runner executes the shell form only

**Problem:** `scripts/plugin_test/checks/hook_fixtures.py` of the public repository runs `bash -c <command>` and ignores `args`. With a hook in exec form (`"command": "python3", "args": [...]`) every "stays silent" fixture passed and every "asks" fixture failed, because the script was never run.
**Fix:** `hooks/hooks.json` uses the shell form, `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/guard.py"`. The runner itself is unchanged; exec-form support there is a repository task.
**Root cause:** The plugin-creator template recommends the exec form, the runner predates it.
**Severity:** Minor

## 2026-11-14 — launch-campaign: a request could hide what it does from the guard rails

**Problem:** The rules read the parameters of a request and the last segment of its path. A Meta path such as `{account}/campaigns?status=ACTIVE&daily_budget=9999999` was not seen as a create at all, so the paused rule, both budget ceilings and the plan sum saw nothing and the call was sent as written. The same held for a TikTok path with a query string, a Meta `batch`, an `adset_spec` nested in an ad, and a copy with `status_option=ACTIVE`.
**Fix:** A path must be plain segments or the call is refused, on Meta, TikTok and Google alike. Calls that carry other calls or a second object are refused. A Meta copy needs `status_option=PAUSED`. A TikTok status counts only where TikTok reads it (top of the body; each entry of `creatives` for a manual ad), and `ENABLE` anywhere needs `--activate`.
**Root cause:** A deny-list keyed on the shape of well-formed requests. Found by an independent code review.
**Severity:** Critical

## 2026-11-14 — launch-campaign: budgets the plan check did not count

**Problem:** With a budget on one campaign, the ad sets of a second campaign in the same plan were ignored, so a plan declared 20 a day and carried 220. Google budget updates were not counted. A budget of `NaN`, a negative number or text switched the comparisons off or crashed the dry run.
**Fix:** Every campaign counts; a campaign budget stands only for the ad sets or ad groups the plan puts under that campaign. Updates count like creates. One function, `guards.amount`, accepts a budget only as a plain number that is not negative. The plan currency and the currency of the ad account must both equal `project.currency`.
**Root cause:** `top or below` instead of adding per campaign, and `float()` without a check of what came out.
**Severity:** Critical

## 2026-11-14 — launch-campaign: an unknown outcome was sent again

**Problem:** After a timeout or a server error the ledger marked the step uncertain, but a second `launch apply` posted it again at once and could create a second campaign. An error the toolkit did not expect (a broken read, an interrupted run, a reply that is not JSON) left no ledger line at all, or was recorded as a definite failure.
**Fix:** A step is marked in the ledger before it is sent. While its last entry is that mark or an uncertain failure, `launch apply` refuses to run until the step is named with `--resend`, after someone has looked in the ad account. Every unexpected error after the send counts as uncertain.
**Root cause:** The rule "look before you repeat" lived in a hint, and the ledger was written only after an answer.
**Severity:** Major

## 2026-11-14 — launch-campaign: the plan file and the account could drift apart

**Problem:** A step that was already applied could be edited in the plan; the dry run passed and apply skipped it, so the plan said 5 a day while the account held 20. The dry-run fingerprint covered the plan text only, not the uploaded files, the account ids in `ads/.env` or the currency. After `rollback --remove` the old dry run still unlocked a new apply. `launch activate` ran on a half-applied plan.
**Fix:** Each applied step is stored with a hash, files included, and a plan in which it differs is refused. The fingerprint covers plan, files, account ids and currency, and a removal invalidates it. Activation needs every step applied, and without `--yes` it prints what it would enable and the budget of the plan.
**Root cause:** Identity was checked by step id and file text, not by content.
**Severity:** Major

## 2026-11-14 — launch-campaign: a rollback stopped at the first failure

**Problem:** Pause and removal raised on the first object that failed. After a partial removal every retry failed on the object that was already deleted, so the ad set and the campaign behind it could no longer be paused or removed with the tool.
**Fix:** Pause and removal go on past a failure and report what is left; each removed object is recorded, so a second run finishes the job; an object the platform reports as gone is skipped. Enabling still stops at the first failure.
**Root cause:** One loop for enabling and for stopping, although the two need opposite behaviour on an error.
**Severity:** Major

## 2026-11-14 — launch-campaign: Google campaigns could be changed around the rules

**Problem:** `google call` blocked only the exact path `googleAds:mutate`, so `campaigns:mutate`, `campaignBudgets:mutate` or a query string behind the path reached the account without the paused rule and the ceilings. Through `google mutate`, an ad group or ad created enabled under a campaign that already ran went live without `--activate`, and `launch activate` and `launch rollback` did not track it.
**Fix:** `google call` sends reads and conversion uploads only and refuses everything else. An ad group, asset group or ad under an existing parent must be created `PAUSED` or needs `--activate`; what a plan creates paused is enabled by `launch activate` and paused by `launch rollback`. `partialFailure` is refused in a plan.
**Root cause:** An escape hatch left open "for other methods", and a paused rule written for the campaign only.
**Severity:** Major

## 2026-11-14 — hooks: more ways past the confirmation hook

**Problem:** The toolkit's parser accepted `--y` for `--yes`, which the hook did not recognise. `curl -sd`, `-sX POST`, a client behind `timeout 30` or `sudo -u`, a URL kept in a shell variable, a script on stdin, backticks, `wget --method POST` and a Google write with `:search` in its query all passed silently. A tool named `search_and_replace_creatives` counted as a read.
**Fix:** The parser rejects abbreviated flags, and the hook reads them anyway for older toolkit copies. The hook parses packed curl options, finds a client behind any wrapper, joins a URL assigned in one command with a write in another, treats a script on stdin as one program, and judges a Google method on the end of the URL path. A tool name that joins two actions is never a read.
**Root cause:** The hook matched the shapes people type first. It stays a second layer: a request assembled at run time is out of its sight, and the README says so.
**Severity:** Major

## 2026-11-14 — launch-campaign: the skill text allowed writes without a yes

**Problem:** On the fallback routes (MCP servers, the `meta` tool) the references asked for approval only before enabling, not before each create and upload. Several single commands were shown with a bare `--yes`. An enabling command could not be previewed, because the guard asked for `--activate` before it looked at `--yes`. The EU political-advertising declaration and the special ad category stood in the samples as if they were defaults.
**Fix:** One yes covers one write, on every route; every single write is run without `--yes` first; a preview needs no `--activate` and says when sending would; the declarations are the user's legal statements, taken from the media plan or asked for.
**Root cause:** The money rules were written for the plan flow, and the side routes were described later without them. Found by the second `plugin-dev:skill-reviewer` pass.
**Severity:** Major

## 2026-11-15 — launch-campaign: the same request in another spelling passed the rules

**Problem:** Google reads `campaign_operation` like `campaignOperation` and a status `2` like `ENABLED`. The rules knew the camelCase names and the word only, so a snake_case budget of any size, a campaign created enabled and a numeric status update all passed. A body could also carry its own `validate_only: false` next to the toolkit's `validateOnly: true`. On Meta, a read with a parameter named `method` is carried out by the Graph API as a write or a delete, with no `--yes` anywhere.
**Fix:** A Google body is rewritten to camelCase field names before it is judged, and the rewritten body is what is sent. A status update counts as switching on unless its value is the word `PAUSED` or `REMOVED`. No Meta call may carry a parameter named `method`, and read paths are checked like write paths.
**Root cause:** The rules matched how the documentation spells a request, not every spelling the platform accepts. Found by the second independent code review.
**Severity:** Critical

## 2026-11-15 — launch-campaign: a plan could create what no budget limits, or aim elsewhere

**Problem:** A TikTok campaign and ad group both without a budget, and a Google campaign attached to a budget that already existed, passed the dry run with "this plan sets no budget": after activation they would have spent without any checked limit. A ceiling of 0 or a missing one was read as "no ceiling". A Meta path with a literal `act_` id, or a TikTok body with its own `advertiser_id`, wrote to another account than the one the dry run showed.
**Fix:** Every campaign a plan creates must be limited by a budget the plan carries, and zero in any spelling is no budget. Nothing in a plan may join a campaign the plan does not create: such an ad set, ad group or ad would have spent from a budget the plan never showed. A ceiling that is missing or zero refuses every budget. A write may name only the account in `ads/.env`.
**Root cause:** The budget check added up what it found and was silent about what was absent.
**Severity:** Major

## 2026-11-15 — launch-campaign: the ledger and the plan could list different steps

**Problem:** Renaming an applied step in the plan file made it a new step: `launch apply` created the object a second time and `launch activate` enabled both, at twice the declared budget. A plan could also contain steps that changed existing objects, while the dry run printed "nothing existing is modified", and `launch rollback --remove` wiped the mark of a step whose outcome was unknown.
**Fix:** A plan whose applied steps are not all still listed under their ids is refused by the dry run, by apply and by activation. A plan only creates: updates, removals and additions to objects it did not create are refused and go through single commands. An unknown outcome stays on record through a removal. Activation checks the budget again.
**Root cause:** Applied steps were matched by id in one direction only, and a sentence of the dry run stated a property nothing enforced. The second point was found by the `plugin-dev:skill-reviewer` re-check.
**Severity:** Major

## 2026-11-15 — hooks: writes without a telling word

**Problem:** The hook looked for a write method or a body option. It missed a Graph API call with `method=delete` in a plain GET, inline code that passes the body as a second positional argument, and the upload host `graph-video.facebook.com`.
**Fix:** A `method=` override is a write for every client and for the toolkit. Code handed to an interpreter that names an ad platform is asked about unless it is plainly a single fetch. The upload host is covered.
**Root cause:** For inline code the hook listed the signs of a write; it now lists the signs of a read and asks for the rest.
**Severity:** Minor

## 2026-11-15 — evals: quality cases the behaviour run could not measure

**Problem:** The first L2 run gave 12 quality cases below the threshold and 3 trigger misses, although the saved answers were right. The prompts said "No tools", and loading a skill is a tool call, so the skill fired in none or one of three runs and the case compared the model with itself. Answers ran to 3,000 characters and more, with the facts behind a preamble about the empty sandbox. Expectations joined several facts in one sentence, which the judge fails as a whole. Three trigger queries were plain questions that the model answers from memory.
**Fix:** Every quality prompt names its skill, asks for a short text answer and ends with a line of the rules relied on, in the style of the calibrated cases of this repository. Each expectation is one literal fact that the skill states. The three trigger queries became tasks that need the skill, and `media-plan` gained the trigger "is this budget enough". No skill text was changed for the run: the last run of every skill shows no warning, with the skill firing in three of three runs.
**Root cause:** Cases written before any run, from the skill author's view of what a good answer contains, not from what the judge can see.
**Severity:** Minor
\n\n## 2026-11-15 — ad-copy, media-plan, performance-report: frontmatter only Claude Code could read

**Problem:** Three descriptions ended with a boundary such as `Text only: for images ...`. A colon followed by a space inside an unquoted YAML value is a syntax error for a strict parser. Claude Code reads it anyway, so the official validator, the contract tests and the behaviour run all passed, and version 1.0.0 shipped with it. Ten of the eleven generated targets receive SKILL.md as written, and an agent with a strict parser would not have loaded these three skills.
**Fix:** The three descriptions say `Text only. For images ...`. `tests/test_docs.py` now refuses a plain frontmatter value that holds `: ` or ` #`, and parses every frontmatter block with a real YAML parser when one is installed. Version 1.0.1.
**Root cause:** The descriptions were checked for length and trigger phrases, never parsed as YAML. Found when the mirrors were compared with the source after the first sync: the OpenCode writer had quoted exactly these three values.
**Severity:** Major

## 2026-11-23 — launch-campaign: first runs against live accounts

**Problem:** Until 2026-11-22 no ad platform call had run against a real account (entry of 2026-11-14). The owner then granted access: Google Ads and Search Console through an OAuth client, TikTok and Meta through their official MCP servers, Apify through a token.
**Fix:** Ran, with the owner's yes before every write: the whole Google launch cycle through the toolkit on a production account (the sample Search plan of the reference validated, applied paused, read back and removed), Search Console reads, one capped Apify run, a TikTok campaign and ad group created disabled and deleted through the MCP server, and a Meta campaign draft created and discarded through the MCP server. The sample bodies of the Google and TikTok references passed unchanged. Still not run live: the toolkit's own `meta` and `tiktok` commands, Performance Max and Demand Gen, `keyword-ideas`, conversion uploads, `launch activate`, ad creation on Meta and TikTok. The README lists both sets.
**Root cause:** Access to real accounts came after the release.
**Severity:** Major

## 2026-11-23 — hooks: plain reads of the live servers asked for confirmation

**Problem:** On the live TikTok server the hook asked before `smart_plus_campaign_get`, `smart_plus_adgroup_get`, `smart_plus_ad_get` and `catalog_set_get`, and before every call of `tool_execute`, through which most TikTok tools run, reads included. On the live Meta server it asked before the read `ads_catalog_get_product_feed_upload_sessions`. A confirmation on every read teaches the user to say yes without reading.
**Fix:** `mcp_reason` reads `smart_plus`, `catalog_set`, `product_set`, `event_set` and `upload_session` as one word, and judges a `tool_execute` call by the tool named in its input: a read runs, a write asks and names the tool, a call without a plain tool name asks. The verdict on all 533 live tool names is stored in `tests/fixtures/mcp-live-names.json` and checked by a test; every name the hook lets through was read against the server's own description. A rule by the last word of a name was rejected: `split_test_end_get` stops a split test and `creative_image_edit_get` stores a new image.
**Root cause:** The word lists were written from documentation, before any server could be listed: "plus" was taken as a joining word and "set" as an action.
**Severity:** Major

## 2026-11-23 — launch-campaign: the MCP routes behaved differently from the references

**Problem:** The TikTok reference listed tools by name without saying that on the layered server only about 45 are called by name and the rest run through `tool_list`, `tool_get` and `tool_execute`. The Meta reference said the server creates paused objects; live, `ads_create_campaign` returned a draft whose stored status was ACTIVE, `DELETED` was refused on it, and a draft is removed with `discard_draft_changes` and a confirmation token. It also said the server has no upload tool, and the live list has several. Neither reference said how a TikTok account is linked to an ad account, without which no ad can be built for TikTok placement.
**Fix:** Section 7 of `tiktok-ads.md` names the dispatcher and marks how each tool is called; section 2 has the two linking steps. Section 6 of `meta-ads.md` describes drafts, what was and was not exercised, and the account fields to read first. `SKILL.md` of `launch-campaign` and `init-project`, the README and the Meta key guide no longer say "paused objects".
**Root cause:** Both servers are new and their behaviour is not documented at this level; the text was written from the vendors' overview pages.
**Severity:** Major

## 2026-11-23 — market-research: an Apify run reported a cost of 0

**Problem:** `apify run` printed `usage_usd: 0` for a run that cost 0.015 USD. Apify fills `usageTotalUsd` a moment after a run ends.
**Fix:** `recon.run_cost` adds up `chargedEventCounts` with the event prices of `pricingInfo` and reports the larger of that sum and `usageTotalUsd`.
**Root cause:** The run object was read once, at the moment it reached SUCCEEDED.
**Severity:** Minor

## 2026-11-23 — init-project: the Google guide lost the owner three times

**Problem:** (1) **Publish app** stayed greyed out with "complete your configuration on the Branding page" although the three required fields were filled: since autumn 2026 Google also wants a home page, a privacy policy link and their authorized domain. (2) The owner twice gave the consent with the login that owns the Cloud project; the ad account belonged to another login, and Google answered `NOT_ADS_USER`. (3) The owner sent the address of Google's warning page instead of the redirect address.
**Fix:** The key guide names the three Branding fields and the Testing fallback, says which login gives the consent and that it need not own the project, and says which address to copy. The consent link carries `prompt=select_account consent`, so Google always shows the account chooser. `NOT_ADS_USER` and the Keyword Planner refusal on Explorer access now print a next step. The errors reference has the new rows.
**Root cause:** The guide was written for a user with one Google login, from Google's pages as they were before the Branding change.
**Severity:** Major

## 2026-11-23 — init-project: sign-in to an MCP server from a remote machine

**Problem:** The TikTok and Meta servers sign in through a browser redirect to `localhost`. On a remote or headless machine that address does not load, and the link expires after 5 minutes: three links expired before the owner got through.
**Fix:** The TikTok and Meta key guides and the errors reference describe `claude mcp login --no-browser <server>` with the pasted redirect address, and say to open the link only when the sign-in can be finished in one go.
**Root cause:** The guides assumed a browser on the machine that runs the session.
**Severity:** Minor

## 2026-11-23 — init-project: Meta refuses a second ad account without a reason

**Problem:** The owner's business portfolio answered "Unable to create" when adding an ad account. Meta's rule, from its Business Help Center: a new portfolio may create one ad account, three once a campaign has delivered and a payment was made, and a closed account keeps counting. The portfolio's only account was disabled, so the limit could not grow.
**Fix:** The Meta key guide and the errors reference explain the limit, where to read it, and the ways on (partner access to an account of another portfolio, support, an appeal), and warn against opening a new portfolio to get around a disabled account.
**Root cause:** The guide assumed a working ad account.
**Severity:** Minor

## 2026-11-23 — launch-campaign: the Meta launch cycle on a live account, through the toolkit

**Problem:** Version 1.0.2 had run Meta only through the MCP server. With a system-user token the toolkit's own cycle ran on a production account for the first time: dry run, apply of an image ad (image, campaign, ad set, creative, ad), status, removal. Four things got in the way. The creative failed with 100/1885183 because the app was still in development mode; the key guide said an app needs no review and did not say it must be published. The token dialog said "No permissions available" until the system user had a role on the app. `{account}/promote_pages` was empty, so the guide's way to find the Page id found nothing. And the project currency was EUR for the Google account while the Meta account bills in USD, so one of the two always failed the dry run.
**Fix:** The key guide has a step that publishes the app and explains both errors; the Page id comes from `me/accounts`, which lists the Pages a system user may advertise for. `project.currencies` names a currency per platform and wins over `project.currency`; `guardrails.max_daily_budget` and `max_total_budget` take one number or one per platform, read in that platform's currency, and a map without the plan's platform refuses every budget there.
**Root cause:** The guide was written from Meta's pages, which treat publishing as part of App Review, and the currency rule assumed one currency per project.
**Severity:** Major

## 2026-11-23 — launch-campaign: a removal left the creative and the image behind

**Problem:** `launch rollback --remove` deleted the ad, the ad set and the campaign, and left the creative and the uploaded image in the account; `meta delete` could not remove an image, because Meta deletes one by its hash, a parameter, and the command took none.
**Fix:** A Meta removal deletes the plan's creatives and then the images it uploaded, once everything that uses them is gone; when an object above them could not be removed, they wait for the next run. An image is deleted only when it entered the library with this upload: Meta keeps one image per hash, so an upload of a file the library already held returns an image other ads may use. Its `created_time` is read right after the upload; an image older than the upload, or one whose age cannot be read, stays, and the output names it with the command that removes it. `meta delete` takes `-p`.
**Root cause:** The rollback knew only what can be paused.
**Severity:** Minor

## 2026-11-25 — launch-campaign: generated creatives in Google and Meta, end to end

**Problem:** Two images and a 5-second video were generated and put through both platforms. Google refused the Performance Max and Demand Gen plans written after the reference: the samples gave image assets no `name` (`NAME_REQUIRED_FOR_ASSET_TYPE`), and one missing name brought up to a dozen follow-up errors about missing headlines, logos and resources. On Meta `meta delete VIDEO_ID` was refused with code 200 and `pages_manage_posts`, so the test video stayed behind. `launch-campaign` still said that Meta creatives and Google budgets stay after a removal, which has been wrong since 1.0.3 for creatives and was never right for a budget that is not shared.
**Fix:** Every image asset in the samples carries a name, a documentation test holds that, and the error tables name the code. Validation showed that text and YouTube assets need no name. The Demand Gen section got the image ad that ran live, the Meta video section the body that ran live (thumbnail by `image_hash`, `message` and `title` accepted). A video leaves the ad account's library through `{account}/advideos` with `video_id`, which needs no extra permission. The text on what stays after a removal is corrected.
**Root cause:** The two Google samples were composed from field definitions and had never met Google's validation. The video edge was looked for on the video object instead of the ad account.
**Severity:** Minor

## 2026-11-25 — launch-campaign: a deleted Meta image came back

**Problem:** The test image deleted on 2026-11-23 (the library showed it gone right after) was listed again two days later: `ACTIVE`, a suffix on its name, `updated_time` seconds after the delete. Before that it had been deleted once and revived by a new upload of the same file.
**Fix:** Deleted again; the library still showed it gone a minute later. The reference says to read the library again some time after a removal.
**Root cause:** Not known. Meta keeps one image per hash and revives a deleted one with its first `created_time` when the same file is uploaded.
**Severity:** Minor
