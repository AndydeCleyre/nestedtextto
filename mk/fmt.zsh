#!/bin/zsh -e

if [[ "$1" ]] {
  print -rlu2 'Format and lint project' 'Args: None'
  exit 1
}

root="$(git -C $0:P:h rev-parse --show-toplevel)"
cd "$root"

. ./.zpy/zpy.plugin.zsh
if [[ $GITHUB_ACTIONS ]] {
  envin dev-requirements.txt
} else {
  activate
  pipi -qr dev-requirements.txt
}

set -x

ssort .
black .
isort .
ruff .
