import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "full_poll_report", Path(__file__).resolve().parents[1] / "tools/research/full_poll_report.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)

def line(seq):
    return b"[28.11.2026 9:00:00] EcPair full " + b",".join(
        [str(seq).encode()] + [b"0"] * 30) + b"\r\n"

def test_extract_preserves_gaps_and_ignores_incomplete_tail():
    rows = report.extract(b"unrelated\n" + line(1) + line(3) + line(4)[:-2])
    assert [r[0] for r in rows] == [1,3]
    assert all(len(r)==len(report.FIELDS)==31 for r in rows)

def test_duplicate_and_restart_not_silently_merged():
    for raw in [line(1)+line(1),line(8)+line(1)]:
        with pytest.raises(ValueError,match="nonmonotonic"):
            report.extract(raw)

def test_malformed_complete_line_fails_closed():
    with pytest.raises(ValueError,match="malformed"):
        report.extract(b"[T] EcPair full 1,2\n")
