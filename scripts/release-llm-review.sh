#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

output=""
skip_preflight=0
card_only=0
while [ $# -gt 0 ]; do
  case "$1" in
    --output)
      if [ $# -lt 2 ]; then
        echo "--output requires a path" >&2
        exit 2
      fi
      output="$2"
      shift 2
      ;;
    --skip-preflight)
      skip_preflight=1
      shift
      ;;
    --card-only)
      card_only=1
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./scripts/release-llm-review.sh [--output PATH] [--skip-preflight] [--card-only]
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ "$skip_preflight" -eq 0 ]; then
  ./scripts/release-preflight.sh
fi

if [ -z "$output" ]; then
  output=$(mktemp /private/tmp/maxcpa-release-review.XXXXXX)
fi

mkdir -p "$(dirname "$output")"

.venv/bin/python - "$output" "$card_only" <<'PY'
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

from frontend_project_analysis.core import (
    build_release_review_packet_manifest,
    build_release_review_reviewer_card,
    build_release_review_system_prompt,
    build_release_review_user_prompt,
)

output = Path(sys.argv[1])
card_only = int(sys.argv[2])


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def git(*args: str, check: bool = True) -> str:
    return run(["git", *args], check=check).stdout


def section(title: str) -> str:
    return f"## {title}\n\n"


def code_block(text: str, lang: str = "") -> str:
    fence = f"```{lang}\n{text.rstrip()}\n```\n\n"
    return fence


status_lines = [line for line in git("status", "--porcelain=v1").splitlines() if line.strip()]
diff_stat = git("diff", "--stat", "HEAD", "--")
branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
head = git("rev-parse", "HEAD").strip()

tracked_paths = [line for line in git("diff", "--name-only", "HEAD", "--").splitlines() if line.strip()]
untracked_paths = [line for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line.strip()]

parts: list[str] = []
repository_context = {
    "branch": branch,
    "head": head,
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
}
audit_focus = [
    "Confirm every changed public behavior in code has matching description updates.",
    "Confirm every changed public claim in description files has matching code, tests, or workflow rules.",
    "Confirm `references/glossary.md` still owns the vocabulary used by release-facing files.",
    "Confirm English-only terms remain unchanged.",
    "Confirm the reviewer context is fresh and packet-only.",
]
prompt_rules = [
    "Read only this packet.",
    "Do not inspect drafting chat, hidden scratch work, or other repository context.",
    "Return JSON only.",
    "List counterexamples first, then findings with evidence.",
]

packet_manifest = build_release_review_packet_manifest(
    {
        "repository_context": repository_context,
        "changed_surface": status_lines,
        "audit_focus": audit_focus,
        "prompt_rules": prompt_rules,
    }
)

if card_only:
    parts.append(build_release_review_reviewer_card(packet_manifest))
else:
    parts.append("# Release LLM Review Packet\n\n")
    parts.append(
        "This packet must be reviewed in a fresh Codex or Claude Code session that "
        "does not reuse the drafting conversation.\n\n"
    )
    parts.append(section("Review Rule"))
    parts.append(
        "- Read only this packet.\n"
        "- Do not inspect the drafting chat, hidden scratch work, or other repository context.\n"
        "- Return JSON only.\n"
        "- List counterexamples first, then findings with evidence.\n"
        "- Focus on code/document parity, terminology alignment, and release readiness.\n\n"
    )
    parts.append(section("Preflight Status"))
    parts.append(
        "The deterministic release preflight has already passed in the drafting session.\n\n"
    )
    parts.append(section("Repository Context"))
    parts.append(code_block(json.dumps(repository_context, indent=2, ensure_ascii=True), "json"))
    parts.append("\n")
    parts.append(section("Changed Surface"))
    parts.append("```text\n")
    parts.append("\n".join(status_lines) + ("\n" if status_lines else ""))
    parts.append("```\n\n")
    parts.append(section("Diff Stat"))
    parts.append(code_block(diff_stat or "(no tracked diff)"))
    parts.append(section("Audit Focus"))
    parts.append(
        "".join(f"- {item}\n" for item in audit_focus) + "\n"
    )

    parts.append(section("Packet Manifest"))
    parts.append(code_block(json.dumps(packet_manifest, indent=2, ensure_ascii=True), "json"))
    parts.append(section("Reviewer Card"))
    parts.append(code_block(build_release_review_reviewer_card(packet_manifest), "text"))
    parts.append(section("System Prompt"))
    parts.append(code_block(build_release_review_system_prompt(), "text"))
    parts.append(section("User Prompt"))
    parts.append(
        code_block(
            build_release_review_user_prompt(
                {
                    "repository_context": repository_context,
                    "changed_surface": status_lines,
                    "audit_focus": audit_focus,
                    "prompt_rules": prompt_rules,
                }
            ),
            "text",
        )
    )

if not card_only and tracked_paths:
    parts.append(section("Tracked Changes"))
    for path in tracked_paths:
        diff = run(["git", "diff", "HEAD", "--", path], check=False).stdout.rstrip()
        parts.append(f"### {path}\n\n")
        parts.append(code_block(diff or "(no diff output)", "diff"))

if not card_only and untracked_paths:
    parts.append(section("Untracked Files"))
    for path in untracked_paths:
        diff = run(["git", "diff", "--no-index", "--", "/dev/null", path], check=False).stdout.rstrip()
        parts.append(f"### {path}\n\n")
        parts.append(code_block(diff or "(no diff output)", "diff"))

output.write_text("".join(parts), encoding="utf-8")
PY

if [ "$card_only" -eq 1 ]; then
  echo "Wrote release reviewer card to $output"
  echo "Open a fresh Codex or Claude Code session now."
  echo "Load only this card:"
else
  echo "Wrote release LLM review packet to $output"
  echo "Open a fresh Codex or Claude Code session now."
  echo "Load only this packet:"
fi
echo "$output"
echo "Return JSON only, then use the result to decide whether to revise and rerun the script."
