#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "plumbum",
# ]
# ///
"""Parse plumbum application help output to extract properties, subcommands and switches."""

from __future__ import annotations

import json
import re
import sys
from tomllib import load

from plumbum import local

OVERALL_PATTERN = re.compile(
    r'^(?P<cmd>[^\s].*?) (?P<version>(\d\.?)+)\n\n'
    r'(?P<description>.*)\n\n'
    r'(?P<description_more>(.*\n)*?)'
    r'Usage:\n(?P<usage>(\s{4}.*\n)+)\n'
    r'Meta-switches:\n(?P<meta_switches>(\s{4}.*\n)+)\n'
    r'(Switches:\n(?P<switches>(\s{4}.*\n)+)\n)?'
    r'(Sub-commands:\n(?P<subcommands>(\s{4}.*\n)+))?'
)

USAGE_PATTERN = re.compile(r'\s{4}([^\s].*)')
USAGE_POSITIONAL_ARG_SET_PATTERN = re.compile(r'(?P<argname>[^\s:]+):(?P<argtype>\{([^,\s\}]+(,\s)?)+\})')
USAGE_POSITIONAL_ARG_WITH_DEFAULT_PATTERN = re.compile(r'\[(?P<argname>.+)=(?P<argdefault>.+)\]$')
USAGE_POSITIONAL_ARG_MULTIPLE_PATTERN = re.compile(r'(?P<argname>.*)\.\.\.')


SWITCH_PATTERN = re.compile(
    r'\s{4}(?P<names>-(,\s|[^\s])*)\s*'
    r'((?P<argname>[^:\s]+):(?P<argtype>[^\s].*?)\s{2})?\s*'
    r'(?P<desc>.*(\n\s{5}.*)*)'
)
    # r'((?P<argname>[^:\s]+):(?P<argtype>[^\s]+))?\s*'
SWITCH_DESCRIPTION_MULTIPLE_TAIL = '; may be given multiple times'

# SUBCOMMAND_PATTERN = re.compile(r'\s{4}([^\s]+).*')
SUBCOMMAND_PATTERN = re.compile(r'^\s{4}([^\s]+).*', re.M)
# TODO: use more re.M for better patterns

def process_usage(s: str) -> str:
    """Process usage string to remove indentation and newlines."""
    # TODO: handle multi-line usage strings
    return re.sub(USAGE_PATTERN, r'\1', s).strip()


def process_description_more(s: str) -> str:
    """Process description more string to remove trailing newlines."""
    return s.strip()


def process_switches(s: str) -> list[dict]:
    """Process switches string to extract properties."""
    return [
        {
            'names': match['names'].split(', '),
            'description': re.sub(r'\n\s+', ' ', match['desc']).removesuffix(
                SWITCH_DESCRIPTION_MULTIPLE_TAIL
            ),
            'argname': match['argname'],
            'argtype': match['argtype'],
            'multiple': match['desc'].endswith(SWITCH_DESCRIPTION_MULTIPLE_TAIL),
        }
        for match in re.finditer(SWITCH_PATTERN, s)
    ]


def process_subcommands(s: str) -> dict:
    """Process subcommands string to extract names."""
    return {name: {} for name in re.findall(SUBCOMMAND_PATTERN, s)}


def arguments_from_usage(usage: str) -> list[dict]:
    """Extract arguments from usage string."""
    arguments = []
    # TODO: more work here, to preserve arg order, and fix up those regex patterns
    # maybe keep beheading it and matching till it's all gone
    if usage:
        _usage = usage.split(' [SWITCHES] ', 1)

        if len(_usage) == 2:  # noqa: PLR2004
            if lines := _usage[1].splitlines():
                line = lines[0].strip()

                for match in re.finditer(USAGE_POSITIONAL_ARG_SET_PATTERN, lines[0]):
                    line = re.sub(USAGE_POSITIONAL_ARG_SET_PATTERN, '', line)
                    arg = {'argdefault': None, 'multiple': False}
                    arg.update(match.groupdict())
                    arguments.append(arg)

                argstrs = line.strip().split()

                for argstr in argstrs:
                    if argstr.strip('[]') in ('SUBCOMMAND', 'SWITCHES', 'args...'):
                        continue
                    arg = {'argdefault': None, 'multiple': False}
                    if match := re.match(USAGE_POSITIONAL_ARG_WITH_DEFAULT_PATTERN, argstr):
                        arg.update(match.groupdict())
                    elif match := re.match(USAGE_POSITIONAL_ARG_MULTIPLE_PATTERN, argstr):
                        arg.update(match.groupdict())
                        arg['multiple'] = True
                    else:
                        arg.update({'argname': argstr})
                    arguments.append(arg)
    return arguments
    # TODO: a dataclass or cattrs or attrs thing or typedict or something for arg.


# TODO: a dataclass or cattrs or attrs thing or typedict or something for this output.
def parse_help_output(help_text: str) -> dict:
    """Parse help output to extract properties, subcommands and switches."""
    match = re.match(OVERALL_PATTERN, help_text)
    if not match:
        return {}

    data = match.groupdict()

    usage = (data['usage'] and process_usage(data['usage'])) or ''

    data.update(
        {
            'description_more': (
                data['description_more'] and process_description_more(data['description_more'])
            )
            or '',
            'usage': usage,
            'meta_switches': (data['meta_switches'] and process_switches(data['meta_switches']))
            or [],
            'switches': (data['switches'] and process_switches(data['switches'])) or [],
            'arguments': arguments_from_usage(usage),
            'subcommands': (data['subcommands'] and process_subcommands(data['subcommands']))
            or {},
        }
    )

    return data


def get_app_info(command: str) -> dict:
    """Get application info by parsing help output."""
    main_info = parse_help_output(local[command]('--help'))

    for subcommand_name in main_info['subcommands']:
        main_info['subcommands'][subcommand_name].update(
            parse_help_output(local[command](subcommand_name, '--help'))
        )

    return main_info


def get_shipped_commands() -> list[str]:
    """Get the list of commands that are actually shipped by reading pyproject.toml."""
    data = load((local.path(__file__).up(2) / 'pyproject.toml').open('rb'))
    return list(data['project']['scripts'].keys())


def get_shipped_commands_info() -> dict:
    """Parse all help data and return structured data."""
    data = {'commands': {}}

    for cmd_name in get_shipped_commands():
        data['commands'][cmd_name] = get_app_info(cmd_name)

    return data


if __name__ == '__main__':
    json.dump(get_shipped_commands_info(), sys.stdout, indent=2)
