# Design bank

`/found-this-design` reads two catalogs:

- `Refero/bank/catalog.json`
- `motionsites/library/catalog.json`

Root directory:

1. `$GROK_DESIGN_BANK` if set
2. otherwise `~/Design`

The source machine keeps the bank outside this repo (~462MB). Do not commit it.

## Pack on the old laptop

```bash
GROK_DESIGN_BANK="$HOME/Downloads/LAB GITHUB/Design" \
  ./scripts/pack-design-bank.sh "$GROK_DESIGN_BANK" ./Design-bank.tgz
```

Copy `Design-bank.tgz` with USB or another private channel.

## Restore on the new laptop

```bash
./scripts/restore-design-bank.sh ./Design-bank.tgz
export GROK_DESIGN_BANK="$HOME/Design"
```

Add the export to your shell rc if you want it permanent.

Without the bank, every other GrokBestFriend surface still works. Only `/found-this-design` exits until the catalogs exist.
