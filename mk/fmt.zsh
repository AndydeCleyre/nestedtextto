#!/bin/zsh -e

if [[ "$1" ]] {
  print -rlu2 'Upgrade what we can in our *requirements.txt files' 'Args: None'
  exit 1
}

root="$(git -C $0:P:h rev-parse --show-toplevel)"
cd "$root"

. ./.zpy/zpy.plugin.zsh
activate
pip install -qr dev-requirements.txt

ssort .
black .
isort .
ruff .
