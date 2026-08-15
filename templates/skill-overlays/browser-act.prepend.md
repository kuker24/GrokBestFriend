## GrokBuild browser contract

Follow the browser engine rules in `00-routing.md`. Invocation only:

- After this skill loads, run `browser-act` via `run_terminal_command`.
- `browser open` without `--headed`. Add `--headed` only if the user asks to see a window.
- Create browsers only with `--type chrome`. Never `--type chrome-direct`.
- Do not reuse a `chrome-direct` browser (including `pulse-test`).
- `stealth-extract` is allowed for sessionless fetch.

