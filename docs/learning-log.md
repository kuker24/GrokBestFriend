# Learning log

GrokBestFriend records **local evidence**, not self-mutating rules.

File: `~/.grok/runtime/learning/events.jsonl` (mode 600, created on install).

Each line is one JSON event matching `vendor/learning-event.schema.json`.

## What to store

- Hashes of the user prompt, not the prompt itself
- Chosen primary skill and optional verification specialist
- Tool names (not arguments that may contain secrets)
- Failure stage, retry count, verification profile, pass/fail
- Whether the user corrected the route

## What never happens

- The model must not rewrite `00-routing.md` or a skill from this log
- Promotion path is: change the policy → routing eval + tests + doctor
- Do not commit `events.jsonl`

## Report

```bash
python3 scripts/learning-report.py
python3 scripts/learning-report.py --file ~/.grok/runtime/learning/events.jsonl
```
