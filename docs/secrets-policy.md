# Secrets policy

This repository is public. The installer is written so a new laptop can match the *system*, not the *credentials*.

## Never commit

- Grok login files (`~/.grok/auth.json`)
- API keys and bearer tokens
- Gateway URLs and custom model-mapping tables
- `trusted_folders.toml`
- Session transcripts and MCP logs
- Design-bank archives (`.tgz`)

## What the installer may write

- Public MCP URLs already used on the source machine (`mcp.context7.com`, `mcp.exa.ai`)
- Official model ids (`grok-4.6`, `grok-4.5`)
- Checksums and GitHub release URLs in `vendor/sources.json`

## Checks

```bash
./tests/test-no-secrets.sh
gitleaks detect --source . --no-git
```

If either fails, do not push.
