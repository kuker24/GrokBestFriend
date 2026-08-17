# Design Intelligence

Local catalog and Impeccable retrieval engine for GrokBestFriend **1.3.1**.
It is not an independent skill or a second primary router.

```text
active_version          = 1.3.1
feature                 = IMPECCABLE_DESIGN_INTELLIGENCE
routing_integration     = IMPECCABLE_NEW_WORK_ONLY
specialist_activation   = NOT_ACTIVE
```

## Purpose

Index local Open Design packs (systems, templates, plugins, skills) into
a small, deterministic catalog. Impeccable `new-work` may search its
system and structure metadata as bounded challenger evidence. The active
Impeccable stage remains the sole owner.

## Two banks

| Env | Default | Contents |
|---|---|---|
| `GROK_DESIGN_BANK` | `~/Design` | Refero + Motionsites for `/found-this-design` |
| `GROK_DESIGN_INTELLIGENCE_BANK` | `~/DesignIntelligence` | This catalog |

They must not mix. `./install.sh` packages the engine and leaves the
intelligence bank missing unless you pass
`--with-design-intelligence-bank /path/to/packs`. Tests must pass
`--bank` at a temporary path. The installer never scans the home
directory for ZIP files.

## Why the raw ZIPs are not in git

The packs are large, untrusted, and not cleared for redistribution.
GrokBestFriend does not vendor them and does not attach them to a
Release. Bring four legally obtained ZIPs on private media or from the
upstream source you already have rights to use. `*.zip` stays gitignored.

```bash
./install.sh --with-design-intelligence-bank ~/OpenDesignPacks
```

Automatic import is allowed only when the four archives are an exact
known snapshot (`od-packs-2026-07-20` in v1.3.1). A missing bank is
`DEGRADED`, not an engine failure. A successful known-snapshot import
is `SUCCESS_WITH_EXPECTED_LIMITATIONS`: integrity passes, content
stays `DEGRADED` for unknown licenses, stubs, quarantine, and missing
optional connectors. An existing healthy matching bank is reused and
its install manifest fragment is rewritten from the live catalog. An
existing corrupt or different bank is not overwritten. Uninstall keeps
`~/DesignIntelligence` as user data.

The installer bootstrap phases (`stage`, `promote`, `remove-staging`,
`recover-created`) are installer-only. Impeccable may call `plan`,
`shortlist`, `search`, `doctor`, and selection commands; it cannot
invoke bootstrap. Staging lives at `~/DesignIntelligence.stage.<id>`
with a private transaction marker. Recovery of a crash reloads that
state from the installer journal in a new process. Search verification
runs against the staged catalog before the atomic rename. Dry-run
never creates the target parent or a staging directory. The bank
target cannot be `/`, `$HOME`, `~/.grok` or anything inside it, a Git
repository, the archive directory, or a path that reaches those
locations through a symlink.

## Trust, license, evidence

- Unknown license is local reference only. It is not MIT, not
  redistributable, and not authoritative.
- Brand-named systems in the curated fixture are evidence tier **E1**
  and `inspiration-only`. A GitHub origin URL does not make them
  official brand kits.
- `_official` is an Open Design label. It is not GrokBestFriend trust.
- Community plugins are quarantined and never default search hits.

## Kinds

- **system** — portable design-system package. Search sees metadata
  only. After the user locks a direction, selection may open exactly
  `manifest.json`, `DESIGN.md`, and `tokens.css` for that system.
- **structure** — information architecture card stripped of mandatory
  style. Selection loads the normalized card only.
- **recipe** — `open-design.json` workflow data. Never executed.
- **specialist** — ZIP `SKILL.md` as data. 162 folders are not 162
  capabilities. Catalogue stubs stay stubs.

`execution_class` is a static property of the source. Host probes
(`runtime_availability`, `available_via`, derived `execution_status`)
are computed at search/doctor time and are not stored in `catalog.jsonl`.

## Import, search, doctor

```bash
python3 scripts/design-intelligence.py inspect-archive pack.zip
python3 scripts/design-intelligence.py import --bank /tmp/di --archive pack.zip
python3 scripts/design-intelligence.py rebuild --bank /tmp/di
python3 scripts/design-intelligence.py search --bank /tmp/di --kind system --query "editorial dashboard"
python3 scripts/design-intelligence.py plan --intent greenfield --scope world --mode Operate --authority none
python3 scripts/design-intelligence.py shortlist --bank /tmp/di --intent greenfield --mode Operate --query "developer operations dashboard"
python3 scripts/design-intelligence.py pin-selection --bank /tmp/di --project . --intent greenfield --mode Operate --target app/dashboard --query "developer operations dashboard" --primary-system system:example --structure structure:dashboard --user-locked
python3 scripts/design-intelligence.py doctor --bank /tmp/di
```

Bank resolution: `--bank` → `GROK_DESIGN_INTELLIGENCE_BANK` →
`~/DesignIntelligence`.

Search never opens a package (`packages_loaded_during_search = 0`).
Default results hide aliases and duplicates. Systems with unknown
license remain eligible as local reference. ZIP specialists are not
selected unless `--include-unavailable` is set, and even then they are
not executable. A query with no lexical overlap returns no hits.

Doctor returns `PASS`, `DEGRADED`, or `BLOCKED`. A missing bank is
`DEGRADED`. These four current packs should be `DEGRADED`. A known
snapshot matches only when the bank contains exactly that set of
archives and hashes. A partial set or an extra archive is `DEGRADED`.
`--expected-sha` or `--claimed-snapshot` mismatches are `BLOCKED`.

The catalog is generational: `catalog.lock.json` is the commit pointer
and is written last. Both the JSONL and SQLite artifacts must exist
and match the lock. Schema-invalid rows fail the rebuild. A crashed
or invalid rebuild keeps the last healthy lock.

ZIP prose is untrusted. Every persisted string and every dynamic dict
key is sanitized. Structural fields skip prose cleanup only by full
path (`source.url`, `source.path`, identity ids), never by bare key
name. Secret patterns come from policy and redact the assignment and
its value. SPDX `known` requires an exact canonical identifier after
explicit aliases; `MIT` and `MIT-0` are different. Two archives that
collapse to the same logical name (`design-systems.zip` and
`design-systems(1).zip`) fail import and rebuild. Retrieval quotes
stored fields as evidence, not as instructions. An archive
whose top-level family is not systems, templates, plugins, or skills
is quarantined as `UNSUPPORTED_ARCHIVE_FAMILY`.

## Active integration boundaries

- Design Intelligence is internal to Impeccable `new-work`; it never
  becomes a primary route or activates a specialist.
- Narrow changes load nothing. A whole surface in an established world
  may retrieve structure cards only. Greenfield and explicit redesign
  may retrieve systems plus structures.
- Search opens zero packages and returns at most five systems and three
  structures. A selected system opens three allowlisted files after the
  user lock. A structure package is never opened.
- At most one primary system and one secondary influence may survive.
  Product truth, incumbent authority, DESIGN.md, and pinned references
  outrank bank evidence.
- `DEGRADED` may continue with eligible references. `BLOCKED`, missing,
  corrupt, or empty retrieval falls back once to native Impeccable with
  no retry and no substitute specialist.
- `.impeccable/design-intelligence-selection.json` records provenance
  only. It contains no local-only source prose and is not `DESIGN.md` or
  implementation approval. Greenfield and redesign still write
  `DESIGN.md` after build and finish review.

## Remaining limits

- Lexical search only. FTS5 is optional.
- Redistribution of the source packs is not cleared; install packages
  the engine and policy, never the raw bank.
