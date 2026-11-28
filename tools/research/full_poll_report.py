"""Offline DuckDB report on immutable TPFan full-poll log snapshots.

No DuckDB or database calls in TPFan. One input file per service run; refuse
ambiguous sequence resets/duplicates instead of joining across processes.
"""
import argparse
import csv
import hashlib
import re
import subprocess
from pathlib import Path

FIELDS = """seq ok dispatch begin_ms end_ms handler now epoch poll_epoch ordered mode level ack ec_max
ta ra tb rb rpm_a lo_a hi_a rpm_b lo_b hi_b cpu_valid cpu_time package hottest command_ok post_level post_pending""".split()

def extract(raw):
    rows = []
    previous = 0
    for offset, line in enumerate(raw.splitlines(keepends=True), 1):
        if b"EcPair full " not in line or not line.endswith(b"\n"):
            continue
        m = re.fullmatch(rb"\[[^\r\n]+\] EcPair full (-?\d+(?:,-?\d+){30})\r?\n", line)
        if not m:
            raise ValueError(f"malformed full poll at line {offset}")
        row = tuple(map(int, m[1].split(b",")))
        if row[0] <= previous:
            raise ValueError("nonmonotonic sequence: separate process runs before analysis")
        previous = row[0]
        rows.append(row)
    return rows

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("log", type=Path)
    p.add_argument("csv", type=Path)
    args = p.parse_args()
    raw = args.log.read_bytes()
    rows = extract(raw)
    if not rows:
        raise SystemExit("no complete full-poll rows")
    with args.csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        w.writerows(rows)
    print("snapshot_sha256", hashlib.sha256(raw).hexdigest(), "bytes", len(raw), "rows", len(rows), flush=True)
    sql = Path(__file__).with_name("full_poll_report.sql").read_text()
    # SQL literal escape; no shell invocation.
    sql = sql.replace("__POLL_CSV__", "'" + str(args.csv.resolve()).replace("'", "''") + "'")
    subprocess.run(["duckdb", "-csv", "-c", sql], check=True)

if __name__ == "__main__":
    main()
