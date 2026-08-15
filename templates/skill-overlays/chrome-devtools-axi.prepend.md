## GrokBuild browser contract

Follow the browser engine rules in `00-routing.md`. Invocation only:

1. Start background Chromium: `grok-chromium-cdp start` (or `$HOME/.grok/bin/grok-chromium-cdp start`).
2. Every command: `CHROME_DEVTOOLS_AXI_BROWSER_URL=http://127.0.0.1:9222 npx -y chrome-devtools-axi <command>`.
3. Never set `CHROME_DEVTOOLS_AXI_HEADED=1` or `CHROME_DEVTOOLS_AXI_AUTO_CONNECT=1` unless the user asks to see a window.
4. If the helper prints `NOT_CONFIGURED`, stop. Do not fall back to Google Chrome.

