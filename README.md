# DMF Config Tool

DMF Config Tool is an offline workbook-to-CLI generator for Arista DANZ Monitoring Fabric deployments. An operator fills out a site-specific Excel workbook, the tool validates that input against structural, semantic, and version-specific rules, and it renders an ordered DMF CLI artifact for manual review and manual application.

## Why This Exists

DMF configuration is order-dependent and operationally sensitive. Controllers, switches, interfaces, groups, and policies all reference one another, so a typo or wrong command order can produce invalid or unsafe configuration. This tool reduces that risk by turning a checked workbook into deterministic CLI output.

## Offline Trust Boundary

This project is intentionally offline. It does not talk to a controller, it does not call cloud APIs, and it does not fetch remote templates or rules. The workbook enters the tool locally, the generated artifacts leave the tool locally, and the operator remains responsible for reviewing and applying the resulting configuration manually.

## Scope

What the tool does:

- Accepts `.xlsx` workbooks that follow the expected tab layout
- Rejects unsupported workbook constructs such as macros, hidden sheets, and formulas
- Parses workbook rows into raw models and normalizes them into canonical fabric models
- Runs structural, schema, relational, semantic, best-practice, and output-verification checks
- Renders DMF CLI configuration for supported DMF versions
- Writes findings and operator-facing artifacts to disk

What the tool does not do:

- It does not send configuration to DMF
- It does not use any network connectivity
- It does not store run history in a database
- It does not implement V2 features such as tunnels, diffing, or a web UI

## Supported DMF Versions

| DMF Version | Workbook Schema | Template Set | Notes |
| --- | --- | --- | --- |
| `8.6` | `>=1.0` | Reuses `8.8` templates conservatively | Feature and limit checks come from the `8.6` bundle |
| `8.7` | `>=1.0` | Reuses `8.8` templates conservatively | Feature and limit checks come from the `8.7` bundle |
| `8.8` | `>=1.0` | Native `8.8` templates | Full current bundle |

## Installation

Python `3.12.3` is the pinned development/runtime target in this repository.

```bash
uv sync --all-extras --dev
```

The CLI entry point is:

```bash
uv run dmf-tool --help
```

## Quickstart

1. Prepare an input workbook that follows the expected tab structure.
2. Run validation first.
3. Run generation only after errors are cleared.
4. Review `findings.txt`, `summary.md`, and `cli-config-redacted.txt` before using the sensitive config artifact.

Example:

```bash
uv run dmf-tool validate --input ./samples/sample-workbook.xlsx --dmf-version 8.8
uv run dmf-tool generate --input ./samples/sample-workbook.xlsx --dmf-version 8.8 --output ./output
```

## CLI Reference

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
uv run dmf-tool generate --input ./samples/sample-workbook.xlsx --dmf-version 8.8 --output ./output
```

Exit codes:

- `0` success with no errors
- `1` findings with `ERROR` severity present
- `2` bad CLI arguments or unexpected tool failure

## Input Workbook Guide

The workbook must be a plain `.xlsx` file with a `metadata` tab and the following data tabs:

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

## Output Artifacts

| Artifact | Always Written | Sensitivity | Purpose |
| --- | --- | --- | --- |
| `findings.json` | Yes | Non-sensitive | Machine-readable findings |
| `findings.txt` | Yes | Non-sensitive | Human-readable findings |
| `cli-config.txt` | Success only | Sensitive | Real rendered CLI with secrets present |
| `cli-config-redacted.txt` | Success only, when secrets exist | Non-sensitive | Safe review copy with secrets replaced |
| `summary.md` | Success only | Non-sensitive | Structured operator summary |

## Samples

The [`samples/`](./samples/) directory contains a fictional deployment workbook, matching generated artifacts, and an illustrative findings report that shows the CLI/report format for warning and info-level findings.

## Further Reading

- [Architecture](./ARCHITECTURE.md)
- [Design Decisions](./DESIGN_DECISIONS.md)
