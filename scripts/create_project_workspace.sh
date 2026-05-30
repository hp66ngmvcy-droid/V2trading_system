#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/create_project_workspace.sh <project-slug>" >&2
  exit 1
fi

slug="$1"

if [[ ! "$slug" =~ ^[a-z0-9][a-z0-9-]*[a-z0-9]$ ]]; then
  echo "Project slug must use lowercase letters, numbers, and hyphens." >&2
  echo "Example: strategy-health-dashboard" >&2
  exit 1
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
template_dir="$repo_root/docs/projects/_template"
target_dir="$repo_root/docs/projects/$slug"

if [[ ! -d "$template_dir" ]]; then
  echo "Missing template folder: $template_dir" >&2
  exit 1
fi

if [[ -e "$target_dir" ]]; then
  echo "Project already exists: $target_dir" >&2
  exit 1
fi

cp -RX "$template_dir" "$target_dir"

today="$(date +%Y-%m-%d)"
title="$(printf '%s' "$slug" | tr '-' ' ')"

tmp_file="$target_dir/README.md.tmp"
sed \
  -e "s/^# Project Title/# $title/" \
  -e "s/^Created: YYYY-MM-DD/Created: $today/" \
  "$target_dir/README.md" > "$tmp_file"
mv "$tmp_file" "$target_dir/README.md"

tmp_file="$target_dir/PROJECT_INDEX.yaml.tmp"
sed \
  -e "s/^project: project-title/project: $slug/" \
  -e "s/^created: YYYY-MM-DD/created: $today/" \
  "$target_dir/PROJECT_INDEX.yaml" > "$tmp_file"
mv "$tmp_file" "$target_dir/PROJECT_INDEX.yaml"

echo "Created project workspace: docs/projects/$slug"
