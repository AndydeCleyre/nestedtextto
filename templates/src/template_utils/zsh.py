"""Utility functions for use in templates."""
from __future__ import annotations

import re
from shlex import quote
from textwrap import indent

__all__ = ['argspecs', 'break_line', 'subcommand_spec']


ACTIONS = {
    'NESTED_TEXT_FILE': '_files -g "*.nt"',
    'YAML_FILE': '_files -g "*.y(a|)ml"',
    'JSON_FILE': '_files -g "*.json"',
    'TOML_FILE': '_files -g "*.toml"',
    'HUML_FILE': '_files -g "*.huml"',
    'MAML_FILE': '_files -g "*.maml"',
    'KSON_FILE': '_files -g "*.kson"',
    'ExistingFile': '_files',
    'SHELL': '(bash zsh fish)',
}
# TODO: helpful message for YAMLPATH, maybe

def guess_action(*keywords: str | None) -> str:
    action = ''

    for clue in keywords:
        if not clue:
            continue

        action = ACTIONS.get(clue, '')

        if not action and clue.lower().endswith('file'):
            action = '_files'

        if action:
            break

    return action


def spec_escape(s: str) -> str:
    return re.sub(r'([:\[\]\{\}])', r'\1', s)


def switch_exclusion_spec(switch: dict) -> str:
    return (switch['multiple'] and '*') or ' '.join(switch['names']).join('()')
    # use info from parent item?


def switch_name_spec(switch: dict) -> str:
    return (
        (len(switch['names']) > 1) and ','.join(switch['names']).join('{}')
    ) or switch['names'][0]


def switch_description_spec(switch: dict) -> str:
    return (switch['description'] and spec_escape(switch['description']).join('[]')) or ''


def switch_argname_spec(switch: dict) -> str:
    spec = ''
    if switch.get('argname'):
        spec = switch['argname'].replace('_', ' ')
        if switch['argtype'] and switch['argtype'][0] in '[':
            spec += f" {switch['argtype']}"
        spec = f":{spec_escape(spec)}:"
    return spec


def switch_action_spec(switch: dict) -> str:
    # (switch['argtype'][0], switch['argtype'][-1]) == ('{', '}')
    if switch.get('argtype') and switch['argtype'].endswith('}') and switch['argtype'].startswith('{'):
        return spec_escape(switch['argtype'].strip('{}').replace(',', '').join('()'))
    return spec_escape(guess_action(switch['argname'], switch['argtype']))


def positional_spec(arg: dict) -> str:
    # multiple?
    # argdefault?
    action = None
    # (switch['argtype'][0], switch['argtype'][-1]) == ('{', '}')
    if arg.get('argtype') and arg['argtype'].endswith('}') and arg['argtype'].startswith('{'):
        action = spec_escape(arg['argtype'].strip('{}').replace(',', '').join('()'))
    return ':'.join((
        (arg['multiple'] and '*') or '',
        spec_escape(arg['argname'].replace('_', ' ')),
        action or spec_escape(guess_action(arg['argname'])),
    ))


def argspecs(command_data: dict, exclude_positionals=False) -> list[str]:
    """Return a list of quoted spec lines for all arguments and switches."""
    specs = [
        '(- *)'  # TODO: this doesn't stop us from completing subcommands
        f"{switch_name_spec(switch)}"
        f"{quote(switch_description_spec(switch) + switch_argname_spec(switch) + switch_action_spec(switch))}"  # noqa: E501
        for switch in command_data['meta_switches']
    ]
    specs += [
        f"{(switch_exclusion_spec(switch) and quote(switch_exclusion_spec(switch)) or '')}"
        f"{switch_name_spec(switch)}"
        f"{quote(switch_description_spec(switch) + switch_argname_spec(switch) + switch_action_spec(switch))}"  # noqa: E501
        for switch in command_data['switches']
    ]
    if not exclude_positionals:
        specs += [
            quote(positional_spec(arg))
            for arg in command_data['arguments']
        ]
    return specs


def subcommand_spec(name: str, data: dict) -> str:
    """Return a quoted spec line for a subcommand."""
    return quote(':'.join((
        spec_escape(name),
        spec_escape(data['description'])
    )))


def break_line(sublines: list[str], leftpad: int = 0) -> str:
    """Return an indented string with trailing-backslash line continuations."""
    return ' \\\n'.join(indent(subline, ' ' * leftpad) for subline in sublines)
