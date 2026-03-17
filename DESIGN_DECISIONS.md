# Design Decisions

## Problem Framing

The problem is not "how do we automate DMF end to end." The problem is "how do we lower operator risk when translating site variables into an order-sensitive DMF CLI configuration." That framing keeps the project deliberately offline and focused on deterministic artifact generation.

## First-Pass Architecture

The first-pass design separated the system into a strict pipeline:

1. reject unsafe or unsupported workbooks
2. parse workbook rows into permissive raw models
3. lint the raw workbook structure and relationships
4. normalize into canonical fabric models
5. lint version-specific semantics
6. render versioned templates
7. verify the rendered output before writing artifacts

This produced clean boundaries between workbook parsing, canonical data handling, and output rendering.

## Independent Review Round One

The first review challenged several weak spots:

- parser behavior was defined, but its module location was omitted
- version-specific rendering differences were underspecified for `8.6` and `8.7`
- secret handling needed to be explicit for both rendering and redaction
- atomic writes needed to be enforced rather than implied

## Design Revisions

The implementation adopted these revisions:

- parser logic lives in `src/dmf_tool/core/parser.py`, next to the normalizer and generator
- version bundles own features, limits, schema minimums, and template directories
- secrets are rendered only into the sensitive config artifact and redacted by field name for review artifacts
- generator evaluation was split from artifact writing so the CLI can support `validate`, `check`, and `generate` cleanly

## Independent Review Round Two

The second review focused on correctness gaps found during implementation:

- template whitespace collapse caused malformed output and broke secret redaction
- diagnostic writes relied on platform-default text encoding and newline handling
- the final artifact commit path used a copy instead of a move

Those were all corrected in the implementation.

## Final Implementation Boundaries

The V1 boundary is intentionally narrow:

- offline only
- workbook in, artifacts out
- no network activity
- no raw workbook types after normalization
- no hidden templating fallback behavior
- deterministic output with an injectable clock

## Key Tradeoffs

- `openpyxl` was chosen because the scope is `.xlsx` only and the parser must reject macro-enabled and legacy workbooks.
- Pydantic models provide strong parsing and validation ergonomics while keeping the raw-versus-canonical boundary explicit.
- Click plus Rich keeps the CLI simple while still producing readable operator output.
- `8.6` and `8.7` currently reuse the `8.8` template set. This favors conservative progress over inventing unsupported version deltas.

## Deliberate Exclusions

The following were excluded on purpose:

- controller push/apply functionality
- any live DMF interrogation
- database-backed run history
- a web UI
- advanced tunnel and multi-site constructs
- broad speculative support for future DMF versions

## Development Process

The project was designed conversationally, reviewed against explicit operational constraints, revised where the design was too loose, and then implemented in phases. Bugs discovered during testing fed back into both the implementation and the documentation rather than being treated as test-only issues.
