"""Require a clean Codex receipt for this exact PR head (adapted from hermes-otel lab-gate)."""
import json
import os
import re
import subprocess
import time

TRUSTED_USER = 199175422
TRUSTED_LOGIN = "chatgpt-codex-connector[bot]"


def review_state(pages, head):
    for row in reversed([row for page in pages for row in page]):
        user = row.get("user") or {}
        if (user.get("id"), user.get("login"), user.get("type")) != (TRUSTED_USER, TRUSTED_LOGIN, "Bot"):
            continue
        match = re.search(r"codex-review-state:v1 (\{.*?\}) -->", row.get("body", ""))
        if not match:
            continue
        review = json.loads(match.group(1))["code_review"]
        if review.get("commit_sha") != head:
            continue
        if review.get("status") != "completed":
            return "running"
        if review.get("has_unresolved_findings") is False:
            return "clean"
        if review.get("has_unresolved_findings") is True:
            return "findings"
        return "unknown"
    return "missing"


def main():
    repo, pr, head = (os.environ[k] for k in ("REPO", "PR", "EXPECTED_SHA"))
    if subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != head:
        raise RuntimeError("checkout identity mismatch")
    for attempt in range(30):
        data = subprocess.check_output(
            ["gh", "api", f"repos/{repo}/issues/{pr}/comments", "--paginate", "--slurp"],
            text=True, timeout=30,
        )
        state = review_state(json.loads(data), head)
        print(f"exact head {head} attempt {attempt + 1}: {state}", flush=True)
        if state == "clean":
            return
        if state == "findings":
            raise SystemExit("unresolved Codex findings")
        time.sleep(20)
    raise SystemExit("no clean review for exact head")


if __name__ == "__main__":
    main()
