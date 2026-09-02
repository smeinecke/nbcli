#!/usr/bin/env bash
#
# Portable nbcli skill installer.
# Copies the bundled SKILL.md into an AI agent's global skills directory.
#
# Usage:
#   install-skill.sh <agent>              # dry-run; prints destination
#   install-skill.sh <agent> --apply      # actually copies
#
#   install-skill.sh --export <dir>       # dry-run to arbitrary directory
#   install-skill.sh --export <dir> --apply
#
# Supported agents:
#   claude, claude-code -> ~/.claude/skills/nbcli/SKILL.md
#   codex, openai       -> ~/.agents/skills/nbcli/SKILL.md
#   gemini              -> ~/.gemini/skills/nbcli/SKILL.md
#   copilot, github-copilot -> ~/.copilot/skills/nbcli/SKILL.md
#   devin               -> ~/.config/devin/skills/nbcli/SKILL.md
#   windsurf            -> ~/.codeium/windsurf/skills/nbcli/SKILL.md

set -euo pipefail

SKILL_NAME="nbcli"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="${SCRIPT_DIR}/SKILL.md"
APPLY=0

usage() {
  cat <<EOF
Usage: $(basename "$0") <agent> [--apply]
       $(basename "$0") --export <directory> [--apply]

Install the ${SKILL_NAME} SKILL.md into the global skills directory for the
specified AI agent. Without --apply, the resolved destination is printed but
nothing is written.

Supported agents:
  claude, claude-code     ~/.claude/skills/${SKILL_NAME}/SKILL.md
  codex, openai           ~/.agents/skills/${SKILL_NAME}/SKILL.md
  gemini                  ~/.gemini/skills/${SKILL_NAME}/SKILL.md
  copilot, github-copilot ~/.copilot/skills/${SKILL_NAME}/SKILL.md
  devin                   ~/.config/devin/skills/${SKILL_NAME}/SKILL.md
  windsurf                ~/.codeium/windsurf/skills/${SKILL_NAME}/SKILL.md

Options:
  --export <directory>    Copy to <directory>/${SKILL_NAME}/SKILL.md instead.
  --apply                 Actually perform the copy (default is dry-run).
  -h, --help              Show this help message.
EOF
}

resolve_target() {
  local target="$1"
  case "${target}" in
    claude|claude-code)
      echo "${HOME}/.claude/skills/${SKILL_NAME}"
      ;;
    codex|openai)
      echo "${HOME}/.agents/skills/${SKILL_NAME}"
      ;;
    gemini)
      echo "${HOME}/.gemini/skills/${SKILL_NAME}"
      ;;
    copilot|github-copilot)
      echo "${HOME}/.copilot/skills/${SKILL_NAME}"
      ;;
    devin)
      echo "${HOME}/.config/devin/skills/${SKILL_NAME}"
      ;;
    windsurf)
      echo "${HOME}/.codeium/windsurf/skills/${SKILL_NAME}"
      ;;
    *)
      echo "Unknown agent: ${target}" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main() {
  if [[ $# -eq 0 ]]; then
    usage >&2
    exit 1
  fi

  local target=""
  local export_dir=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
        usage
        exit 0
        ;;
      --apply)
        APPLY=1
        shift
        ;;
      --export)
        if [[ $# -lt 2 ]]; then
          echo "--export requires a directory argument" >&2
          usage >&2
          exit 1
        fi
        export_dir="$2"
        shift 2
        ;;
      -*)
        echo "Unknown option: $1" >&2
        usage >&2
        exit 1
        ;;
      *)
        if [[ -n "${target}" ]]; then
          echo "Only one agent parameter is allowed" >&2
          usage >&2
          exit 1
        fi
        target="$1"
        shift
        ;;
    esac
  done

  if [[ ! -f "${SOURCE}" ]]; then
    echo "Source skill file not found: ${SOURCE}" >&2
    exit 1
  fi

  local dest_dir
  if [[ -n "${export_dir}" ]]; then
    dest_dir="${export_dir}/${SKILL_NAME}"
  elif [[ -n "${target}" ]]; then
    dest_dir="$(resolve_target "${target}")"
  else
    echo "No agent or --export directory specified" >&2
    usage >&2
    exit 1
  fi

  local dest="${dest_dir}/SKILL.md"

  if [[ ${APPLY} -eq 0 ]]; then
    echo "[DRY-RUN] Would install ${SKILL_NAME} skill to:"
    echo "  ${dest}"
  else
    mkdir -p "${dest_dir}"
    cp "${SOURCE}" "${dest}"
    echo "Installed ${SKILL_NAME} skill to:"
    echo "  ${dest}"
  fi
}

main "$@"
