*[!] This project has not been tested in a production environment. You are responsible for validating, understanding, and testing it in your own environment before any real-world use. [!]*

# DMF Config Tool

DMF Config Tool is an offline workbook-to-CLI generator for Arista DANZ
Monitoring Fabric deployments. It validates a site-specific Excel workbook,
normalizes the workbook into canonical fabric models, and renders DMF CLI
artifacts for manual review and manual application.

See [DISCLAIMER.md](./DISCLAIMER.md) for the full repository disclaimer.

## Overview

DMF configuration is order-dependent and operationally sensitive. Controllers,
switches, interfaces, groups, and policies all reference one another, so a
typo or wrong command order can produce invalid or unsafe configuration. This
tool reduces that risk by turning a checked workbook into deterministic CLI
output and by writing review artifacts alongside the rendered configuration.

The tool is intentionally offline. It does not connect to a controller, does
not call cloud APIs, and does not fetch remote templates or rules.

## Non-Goals

This tool does not:

- push configuration to DMF
- provide a web UI
- store run history in a database
- diff existing controller state against a workbook
- implement V2 workflow features such as tunnels

## Requirements

- Python `3.12`
- `uv`
- a workbook saved as plain `.xlsx`
- a local environment where generated artifacts can be reviewed safely

## Assumptions

- Operators review generated CLI before using it.
- Operators apply configuration manually through their existing DMF workflow.
- Input workbooks follow the expected tab structure and version metadata rules.
- Sensitive values may appear in the workbook and in `cli-config.txt`.

## Supported DMF Versions

| DMF Version | Workbook Schema | Template Set | Notes |
| --- | --- | --- | --- |
| `8.6` | `>=1.0` | Reuses `8.8` templates conservatively | Feature and limit checks come from the `8.6` bundle |
| `8.7` | `>=1.0` | Reuses `8.8` templates conservatively | Feature and limit checks come from the `8.7` bundle |
| `8.8` | `>=1.0` | Native `8.8` templates | Full current bundle |

## Setup

1. Install Python `3.12`.
2. Install `uv` if it is not already available.
3. Sync the project dependencies:

```bash
uv sync --all-extras --dev
```

4. Optionally install the repo hook path so pre-commit runs the local gate:

```bash
git config core.hooksPath .githooks
```

## Usage

1. Prepare an input workbook that follows the expected tab layout.
2. Run validation first.
3. Run `check` if you want the full render pipeline without file writes.
4. Run generation only after errors are cleared.
5. Review the generated artifacts before using the sensitive output.

List supported versions:

```bash
uv run dmf-tool versions
```

Validate workbook input only:

```bash
uv run dmf-tool validate --input ./samples/sample-workbook.xlsx --dmf-version 8.8
```

Run the full pipeline without writing files:

```bash
uv run dmf-tool check --input ./samples/sample-workbook.xlsx --dmf-version 8.8
```

Generate artifacts:

```bash
uv run dmf-tool generate \
  --input ./samples/sample-workbook.xlsx \
  --dmf-version 8.8 \
  --output ./output
```

## Input Workbook Expectations

The workbook must be a plain `.xlsx` file with a `metadata` tab and the
following data tabs:

| Tab | Purpose |
| --- | --- |
| `metadata` | Contains `dmf_version` and `workbook_schema_version` |
| `controllers` | Controller names, management IPs, roles, HA peers, and sites |
| `switches` | Switch identity, management IP, role, model, and site |
| `interfaces` | Filter or delivery interfaces and their operational settings |
| `groups` | Interface group definitions |
| `group_members` | Members that belong to each group |
| `policies` | Policy metadata and delivery/filter references |
| `match_rules` | Per-policy match criteria |
| `service_nodes` | Service node attachments |
| `analytics_nodes` | Analytics node attachments |
| `recorder_nodes` | Recorder node attachments |
| `fabric_settings` | Fabric-wide settings, including sensitive values |
| `sites` | Site names and location metadata |

Rejected workbook characteristics include:

- `.xls` and `.xlsm`
- hidden sheets
- formulas
- external links
- oversized workbooks
- corrupt zip structure

## Expected Output

Exit codes:

- `0`: success with no blocking errors
- `1`: findings with `ERROR` severity present
- `2`: bad CLI arguments or unexpected tool failure

Generated artifacts:

| Artifact | When Written | Sensitivity | Purpose |
| --- | --- | --- | --- |
| `findings.json` | Always | Non-sensitive | Machine-readable findings |
| `findings.txt` | Always | Non-sensitive | Human-readable findings |
| `cli-config.txt` | Success only | Sensitive | Real rendered CLI with secrets present |
| `cli-config-redacted.txt` | Success only, when secrets exist | Non-sensitive | Safe review copy with secrets replaced |
| `summary.md` | Success only | Non-sensitive | Structured operator summary |

## Quality Gate

Run the local repo gate before committing:

```bash
./check.sh
```

The gate runs:

- staged-diff Git hygiene checks
- `ruff format --check`
- `ruff check`
- `pyright`
- `pytest`
- `pip-audit`
- optional `gitleaks` and `git-secrets` scans when those tools are installed
- Markdown relative-link validation
- `pyproject.toml` syntax validation

CI uses the same `./check.sh` entry point.

## Troubleshooting

`uv: command not found`
: install `uv`, then rerun `uv sync --all-extras --dev`.

`Tool error` from the CLI
: verify the workbook is a plain `.xlsx` file and that the requested
  `--dmf-version` appears in `uv run dmf-tool versions`.

Validation fails with structural errors
: compare the workbook tabs and metadata against the required sheet list above.

Generated output contains only findings artifacts
: the run hit at least one `ERROR` severity finding, so no CLI artifact was
  written.

`pip-audit` or secret scanners are unavailable locally
: the repo gate reports that those checks were skipped; install the missing
  tools before treating the run as a stronger release signal.

## Recovery And Rollback

- `generate` writes into a timestamped run directory, so a failed run does not
  overwrite a prior successful run.
- If a generated artifact set is not acceptable, discard that output directory
  and rerun with a corrected workbook.
- The tool does not mutate DMF directly, so rollback of controller state
  remains an operator responsibility outside this repository.

## Compatibility Notes

- Changes to workbook tab names, metadata keys, or DMF-version handling are
  compatibility-sensitive for existing operators and sample workbooks.
- The current command surface is `validate`, `check`, `generate`, and
  `versions`.

## Known Limitations

- The project is validated locally and in CI, not in a production DMF
  environment.
- The tool does not verify generated commands against live controller state.
- The workflow is file-based and manual by design.

## Samples And Additional Docs

- [`samples/`](./samples/) contains a fictional workbook and representative
  generated artifacts.
- [ARCHITECTURE.md](./ARCHITECTURE.md) describes the pipeline shape.
- [DESIGN_DECISIONS.md](./DESIGN_DECISIONS.md) captures key implementation
  choices.
- [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md) lists bundled third-party
  attributions.
