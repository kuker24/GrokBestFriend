# Design bank

`/found-this-design` reads two catalogs:

- `Refero/bank/catalog.json`
- `motionsites/library/catalog.json`

Root directory:

1. `$GROK_DESIGN_BANK` if set
2. otherwise `~/Design`

`./install.sh` restores the packed bank automatically. It downloads `Design-bank.tgz` from the `v1.0.0` GitHub Release (checksum in `vendor/sources.json`) unless a local archive is already present, then unpacks to `~/Design` and exports `GROK_DESIGN_BANK`.

Skip with `./install.sh --skip-design-bank`.

## Pack again on the source machine

```bash
GROK_DESIGN_BANK="$HOME/Downloads/LAB GITHUB/Design" \
  ./scripts/pack-design-bank.sh "$GROK_DESIGN_BANK" /tmp/gbf-design/Design-bank.tgz
```

Then upload the new archive to the GitHub Release and update the SHA-256 in `vendor/sources.json`.

## Manual restore

```bash
./scripts/restore-design-bank.sh /path/to/Design-bank.tgz
export GROK_DESIGN_BANK="$HOME/Design"
```
