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


def test_duckdb_episode_report(tmp_path):
    import csv
    import shutil
    import subprocess

    if not shutil.which("duckdb"):
        pytest.skip("DuckDB CLI integration test; run in analytics runtime")
    p = tmp_path / "poll.csv"
    def sample(seq, now, ready=1):
        return [seq,1,now-800,now-700,now-100,now-50,now,2,2,1,3,1,1,70,
                70,1,71,1,2510,1,1,2511,1,ready,1,now-80,72,74,1,1,0]
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(report.FIELDS)
        w.writerows([sample(1,1000),sample(2,2000,0),sample(3,3000,0),
                     sample(4,4000),sample(5,5000,0),sample(7,7000),
                     sample(8,8000,0)])
    sql = Path(report.__file__).with_name("full_poll_report.sql").read_text()
    result = subprocess.run(["duckdb","-csv","-c",sql.replace("__POLL_CSV__","'"+str(p)+"'")],
                            capture_output=True,text=True,check=True)
    block = result.stdout.split("episode,first_seq,last_seq,samples,observed_span_ms,first_bad_to_recovery_ms,thermal_bad,tach_bad,both_bad\n")[1]
    rows = block.split("thermal_permit,tach_quality,polls")[0].strip().splitlines()
    assert [r.split(",")[1:] for r in rows] == [
        ["2","3","2","1000","2000","0","2","0"],
        ["5","5","1","0","NULL","0","1","0"],
        ["8","8","1","0","NULL","0","1","0"]]
