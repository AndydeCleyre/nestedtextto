#!/bin/zsh -e

if [[ "$1" ]] {
  print -rlu2 'Upgrade what we can in our *requirements.txt files' 'Args: None'
  exit 1
}

root="$(git -C $0:P:h rev-parse --show-toplevel)"
cd "$root"

. ./.zpy/zpy.plugin.zsh
if [[ $GITHUB_ACTIONS ]] {
  envin /dev/null
} else {
  activate
}

for reqsfile (
  nt2/requirements.in
  nt2/toml-requirements.in
  test/test-requirements.in
  fmt-requirements.in
  dev-requirements.in
)  pipc -U $reqsfile

pypc
