"""Output markers tests."""

from dmf_tool.core.linters.output.markers import MarkerLinter


def test_marker_linter_passes_clean_output() -> None:
    assert MarkerLinter().run("switch leaf-1\nexit\n") == []


def test_marker_linter_flags_all_jinja_marker_variants() -> None:
    findings = MarkerLinter().run("{{ foo }}\n{% if bar %}\n%}\n")
    assert [finding.code for finding in findings] == ["OUT001", "OUT001", "OUT001"]
    assert all(finding.suggestion for finding in findings)
