# Design Intelligence

Candidate catalog library for GrokBestFriend **1.2.0**. It is not an
active skill, not a second router, and it does not change Impeccable.

```text
active_version          = 1.2.0
candidate_feature       = DESIGN_INTELLIGENCE_FOUNDATION
routing_integration     = NOT_ACTIVE
specialist_activation   = NOT_ACTIVE
```

## Purpose

Index local Open Design packs (systems, templates, plugins, skills) into
a small, deterministic catalog that later work can search. PR A only
builds that catalog. PR B may teach Impeccable `new-work` to retrieve
from it after a human merges this foundation.

## Two banks

| Env | Default | Contents |
|---|---|---|
| `GROK_DESIGN_BANK` | `~/Design` | Refero + Motionsites for `/found-this-design` |
| `GROK_DESIGN_INTELLIGENCE_BANK` | `~/DesignIntelligence` | This catalog |

They must not mix. Install does not create the intelligence bank. Tests
must pass `--bank` at a temporary path.

## Why the raw ZIPs are not in git

The packs are large, untrusted, and not cleared for redistribution.
GrokBestFriend does not vendor them and does not attach them to a
Release in this change. You keep your own copies. `*.zip` stays gitignored.

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
  only. After a future selection, PR B may open `DESIGN.md` and tokens.
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

ZIP prose is untrusted. Every persisted string is sanitized. Secret
patterns come from policy and redact the assignment and its value.
Future retrieval must quote stored fields as evidence, not as
instructions. An archive whose top-level family is not systems,
templates, plugins, or skills is quarantined as
`UNSUPPORTED_ARCHIVE_FAMILY`.

## Limits

- Not wired into `00-routing.md` or Impeccable.
- `lib/doctor.sh` is unchanged. Use this CLI.
- Lexical search only. FTS5 is optional.
- Redistribution of the source packs is not cleared.

## PR B

Blocked until a human reviews and merges PR A.
`/impeccable` `new-work` may then retrieve a shortlist and write
`.impeccable/design-intelligence-selection.json`. That file is not a
`DESIGN.md`. Greenfield and redesign still write `DESIGN.md` after
build and finish review.
