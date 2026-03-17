"""Output encoding tests."""

from dmf_tool.core.linters.output.encoding import EncodingLinter


def test_encoding_linter_passes_ascii_output() -> None:
    assert EncodingLinter().run("switch leaf-1\nexit\n") == []


def test_encoding_linter_flags_non_ascii_characters() -> None:
    findings = EncodingLinter().run("switch leaf-1\nnaive cafe\xe9\n")
    assert len(findings) == 1
    assert findings[0].code == "OUT002"
    assert findings[0].location == "rendered output, line 2"
