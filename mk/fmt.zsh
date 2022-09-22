#!/bin/zsh -e

if [[ "$1" ]] {
  print -rlu2 'Format and lint project' 'Args: None'
  exit 1
}

root="$(git -C $0:P:h rev-parse --show-toplevel)"
cd "$root"

. ./.zpy/zpy.plugin.zsh
envin dev-requirements.txt

ssort .
black .
isort .
ruff .
