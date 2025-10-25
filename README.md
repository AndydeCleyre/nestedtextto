# NestedTextTo
## CLI to convert between NestedText and JSON, YAML, HUML, or TOML, with explicit type casting

![Python versions](https://img.shields.io/pypi/pyversions/nt2?logo=python)
[![PyPI version](https://img.shields.io/pypi/v/nt2?logo=pypi&label=PyPI&color=yellowgreen)](https://pypi.org/project/nt2/)
[![Publish to PyPI](https://img.shields.io/github/actions/workflow/status/andydecleyre/nestedtextto/pypi.yml?label=Publish%20to%20PyPI&logo=github)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/pypi.yml)

![Runs on Linux](https://img.shields.io/badge/Runs%20on-Linux-yellowgreen?logo=linux)
![Runs on macOS](https://img.shields.io/badge/Runs%20on-macOS-red?logo=macos)
![Runs on Windows](https://img.shields.io/badge/Runs%20on-Windows-blue?logo=windows)

[![Tests badge](https://img.shields.io/github/actions/workflow/status/andydecleyre/nestedtextto/test.yml?branch=develop&label=Tests&logo=github)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/test.yml)
[![codecov badge](https://codecov.io/github/AndydeCleyre/nestedtextto/branch/develop/graph/badge.svg?token=M30UZQVM4Q)](https://codecov.io/github/AndydeCleyre/nestedtextto)


[![Format and lint](https://img.shields.io/github/actions/workflow/status/andydecleyre/nestedtextto/fmt.yml?branch=develop&label=Format%20%26%20Lint&logo=github)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/fmt.yml)
[![Generate docs from templates](https://img.shields.io/github/actions/workflow/status/andydecleyre/nestedtextto/doc.yml?branch=develop&label=Make%20Docs&logo=github)](https://andydecleyre.github.io/nestedtextto/moduleIndex.html)
[![Requirements badge](https://img.shields.io/github/actions/workflow/status/andydecleyre/nestedtextto/reqs.yml?branch=develop&label=Bump%20Reqs&logo=github)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/reqs.yml)

<img src="https://github.com/AndydeCleyre/nestedtextto/blob/assets/logo.png?raw=true" alt="logo" width="160" height="160" />

This project was created in appreciation for the design of [NestedText](https://nestedtext.org/),
the readability of [yamlpath](https://github.com/wwkimball/yamlpath) queries,
the utility of [cattrs](https://cattrs.readthedocs.io/),
and the joy of [plumbum](https://plumbum.readthedocs.io/)
and [ward](https://ward.readthedocs.io/) --
none of which are this author's projects.

This project, NestedTextTo, provides command line tools
for convenient conversion between NestedText and other formats:



- `nt2` with subcommands: `json`, `yaml`, `toml`, `huml`

  - `nt2 {json,toml,yaml}` can also be invoked as a single command: `nt2json`, `nt2toml`, `nt2yaml`

- `2nt` with subcommands: `json`, `yaml`, `toml`, `huml`

  - `2nt {json,toml,yaml}` can also be invoked as a single command: `json2nt`, `toml2nt`, `yaml2nt`

---

<!--TOC-->

- [What's NestedText?](#whats-nestedtext)
- [How does this translate to formats with more value types?](#how-does-this-translate-to-formats-with-more-value-types)
- [Installation](#installation)
  - [Shell Completion](#shell-completion)
- [Usage Docs](#usage-docs)
  - [Limitations](#limitations)
- [More Examples](#more-examples)
  - [View JSON Lines logs in a more readable format](#view-json-lines-logs-in-a-more-readable-format)
  - [View TOML as NestedText](#view-toml-as-nestedtext)
  - [Convert NestedText to TOML, with and without casting](#convert-nestedtext-to-toml-with-and-without-casting)
  - [Convert NestedText to TOML with casting via auto-schema](#convert-nestedtext-to-toml-with-casting-via-auto-schema)
  - [Query TOML with JSON tools, with and without casting](#query-toml-with-json-tools-with-and-without-casting)
- [Development Docs](#development-docs)

<!--TOC-->

---

### What's NestedText?

From the NestedText docs, with emphasis added:

> NestedText is a file format for holding structured data to be entered, edited, or viewed by people. It organizes the data into a nested collection of *dictionaries*, *lists*, and *strings* **without the need for quoting or escaping**. A unique feature of this file format is that it only supports *one scalar type:* **strings**.  While the decision to eschew integer, real, date, etc. types may seem counter intuitive, it leads to simpler data files and applications that are more robust.

### How does this translate to formats with more value types?

When converting from NestedText to formats supporting more value types,
all plain values will be strings by default.
But you can provide options to cast any values as numbers, booleans, nulls, or dates/times,
if the target format supports it, using the powerful and concise YAML Path query syntax.

```console
$ cat config.nt
```
```yaml
logging:
  level: info
  file: /var/log/app.log
  rotate: yes
  max_size: 100
```
```console
$ nt2json config.nt --number logging.max_size --boolean logging.rotate
```
```json
{
  "logging": {
    "level": "info",
    "file": "/var/log/app.log",
    "rotate": true,
    "max_size": 100
  }
}
```

You may instead store these type mappings in a NestedText "schema" file.

```console
$ cat config.types.nt
```
```yaml
boolean:
  - logging.rotate
number:
  - logging.max_size
```

The following command will then also yield the above JSON:

```console
$ nt2json config.nt --schema config.types.nt
```

Such a schema may be automatically generated from any of the typed formats:

```console
$ json2nt --to-schema config.json
```

Options may be provided before or after the document,
and content may be piped directly to the command instead of specifying a file.

For more YAML Path syntax information see
[the YAML Path wiki](https://github.com/wwkimball/yamlpath/wiki/Search-Expressions).

For example, you could match all items which are *probably* intended as booleans,
at any depth, with `--boolean '**[. =~ /(?i)^(yes|no|true|false)$/]'`.

### Installation

Support for JSON and YAML are always included.
If you don't need support for more than those, you can omit the `[all]` bits below.
Or you can use a comma-separated list of extra formats, like `[toml,huml]`.

Here are some ways to install it:

```console
$ uv tool install 'nt2[all]'     # Install using uv (Python all-around manager)
$ pipx install 'nt2[all]'        # Install using pipx (Python app manager)
$ pipz install 'nt2[all]'        # Install using zpy (Python app and environment manager for Zsh)
$ pip install --user 'nt2[all]'  # Install in your user's environment
$ pip install 'nt2[all]'         # Install in current environment
```

I recommend using [uv](https://github.com/astral-sh/uv),
[pipx](https://github.com/pypa/pipx),
or `pipz` from [zpy](https://github.com/AndydeCleyre/zpy).

#### Shell Completion

For Zsh completion, add this line to your `.zshrc`, any time after `compinit`:

```zsh
compdef _gnu_generic nt2{json,{to,ya}ml} {json,{to,ya}ml}2nt
```


### Usage Docs

<details>
  <summary>nt2</summary>

```
nt2 0.3.0

Convert NestedText to another format.

Examples:
    - nt2 json config.nt
    - nt2 json config.nt --number font.size --boolean font.bold
    - nt2 json config.nt --schema config.types.nt
    - cat config.nt | nt2 json

Usage:
    nt2 [SWITCHES] [SUBCOMMAND [SWITCHES]] args...

Meta-switches:
    -h, --help         Prints this help message and quits
    --help-all         Prints help messages of all sub-commands and quits
    -v, --version      Prints the program's version and quits

Sub-commands:
    completion         Print completion code for the given shell.
    hjson              Read NestedText and output its content as Hjson.
    huml               Read NestedText and output its content as HUML.
    json               Read NestedText and output its content as JSON.
    maml               Read NestedText and output its content as MAML.
    toml               Read NestedText and output its content as TOML.
    xml                Read NestedText and output its content as XML.
    yaml               Read NestedText and output its content as YAML.

```

</details>

<details>
  <summary>2nt</summary>

```
2nt 0.3.0

Convert another format to NestedText.

Examples:
    - 2nt config.json
    - 2nt config.json --to-schema >config.types.nt
    - cat config.json | 2nt json
    - cat config.json | 2nt --from json

Usage:
    2nt [SWITCHES] [SUBCOMMAND [SWITCHES]] DATA_FILE...

Meta-switches:
    -h, --help                      Prints this help message and quits
    --help-all                      Prints help messages of all sub-commands and
                                    quits
    -v, --version                   Prints the program's version and quits

Switches:
    --from, -f FROM_FORMAT:{maml, hjson, huml, toml, yml, yaml, json, jsonl, xml}
                                    Format to convert from
    --inline-width, -i WIDTH:[0..120] Maximum line width for inline dictionaries
                                    and lists
    --to-schema, -s                 Rather than convert the inputs, generate a
                                    schema

Sub-commands:
    completion                      Print completion code for the given shell.
    hjson                           Read Hjson and output its content as
                                    NestedText.
    huml                            Read HUML and output its content as
                                    NestedText.
    json                            Read JSON and output its content as
                                    NestedText.
    maml                            Read MAML and output its content as
                                    NestedText.
    toml                            Read TOML and output its content as
                                    NestedText.
    xml                             Read XML and output its content as
                                    NestedText.
    yaml                            Read YAML and output its content as
                                    NestedText.

```

</details>

<details>
  <summary>nt2 json</summary>

```
nt2 json 0.3.0

Read NestedText and output its content as JSON.

By default, generated JSON values will only contain strings, arrays, and maps,
but you can cast nodes matching YAML Paths to boolean, number or null.

Switches may be before or after file arguments.

Examples:
    - nt2 json config.nt
    - nt2 json config.nt --number font.size --boolean font.bold
    - nt2 json config.nt --schema config.types.nt
    - cat config.nt | nt2 json

It can be invoked as either the subcommand `nt2 json` or the single command
`nt2json`.

Usage:
    nt2 json [SWITCHES] NESTED_TEXT_FILE...

Meta-switches:
    -h, --help                      Prints this help message and quits
    -v, --version                   Prints the program's version and quits

Switches:
    --boolean, -b YAMLPATH:str      Cast each node matching the given YAML Path
                                    query as boolean; may be given multiple
                                    times
    --null, -n YAMLPATH:str         Cast each node matching the given YAML Path
                                    query as null, if it is an empty string; may
                                    be given multiple times
    --number, --int, --float, -i, -f YAMLPATH:str
                                    Cast each node matching the given YAML Path
                                    query as a number; may be given multiple
                                    times
    --schema, -s NESTED_TEXT_FILE:ExistingFile
                                    Cast nodes matching YAML Path queries
                                    specified in a NestedText document. It must
                                    be a map whose keys are names of supported
                                    types (a subset of 'null', 'boolean',
                                    'number', and 'date'). Each key's value is a
                                    list of YAML Paths; may be given multiple
                                    times


```

</details>

<details>
  <summary>nt2 yaml</summary>

```
nt2 yaml 0.3.0

Read NestedText and output its content as YAML.

By default, generated YAML values will only contain strings, arrays, and maps,
but you can cast nodes matching YAML Paths to boolean, number, null or date.

Switches may be before or after file arguments.

Examples:
    - nt2 yaml config.nt
    - nt2 yaml config.nt --number font.size --boolean font.bold
    - nt2 yaml config.nt --schema config.types.nt
    - cat config.nt | nt2 yaml

It can be invoked as either the subcommand `nt2 yaml` or the single command
`nt2yaml`.

Usage:
    nt2 yaml [SWITCHES] NESTED_TEXT_FILE...

Meta-switches:
    -h, --help                      Prints this help message and quits
    -v, --version                   Prints the program's version and quits

Switches:
    --boolean, -b YAMLPATH:str      Cast each node matching the given YAML Path
                                    query as boolean; may be given multiple
                                    times
    --date, -d YAMLPATH:str         Cast each node matching the given YAML Path
                                    query as a date, assuming it's ISO 8601; may
                                    be given multiple times
    --null, -n YAMLPATH:str         Cast each node matching the given YAML Path
                                    query as null, if it is an empty string; may
                                    be given multiple times
    --number, --int, --float, -i, -f YAMLPATH:str
                                    Cast each node matching the given YAML Path
                                    query as a number; may be given multiple
                                    times
    --schema, -s NESTED_TEXT_FILE:ExistingFile
                                    Cast nodes matching YAML Path queries
                                    specified in a NestedText document. It must
                                    be a map whose keys are names of supported
                                    types (a subset of 'null', 'boolean',
                                    'number', and 'date'). Each key's value is a
                                    list of YAML Paths; may be given multiple
                                    times


```

</details>

<details>
  <summary>nt2 toml</summary>

```
nt2 toml 0.3.0

Read NestedText and output its content as TOML.

By default, generated TOML values will only contain strings, arrays, and maps,
but you can cast nodes matching YAML Paths to boolean, number or date.

Switches may be before or after file arguments.

Examples:
    - nt2 toml config.nt
    - nt2 toml config.nt --number font.size --boolean font.bold
    - nt2 toml config.nt --schema config.types.nt
    - cat config.nt | nt2 toml

It can be invoked as either the subcommand `nt2 toml` or the single command
`nt2toml`.

Usage:
    nt2 toml [SWITCHES] NESTED_TEXT_FILE...

Meta-switches:
    -h, --help                      Prints this help message and quits
    -v, --version                   Prints the program's version and quits

Switches:
    --boolean, -b YAMLPATH:str      Cast each node matching the given YAML Path
                                    query as boolean; may be given multiple
                                    times
    --date, -d YAMLPATH:str         Cast each node matching the given YAML Path
                                    query as a date, assuming it's ISO 8601; may
                                    be given multiple times
    --number, --int, --float, -i, -f YAMLPATH:str
                                    Cast each node matching the given YAML Path
                                    query as a number; may be given multiple
                                    times
    --schema, -s NESTED_TEXT_FILE:ExistingFile
                                    Cast nodes matching YAML Path queries
                                    specified in a NestedText document. It must
                                    be a map whose keys are names of supported
                                    types (a subset of 'null', 'boolean',
                                    'number', and 'date'). Each key's value is a
                                    list of YAML Paths; may be given multiple
                                    times


```

</details>

<details>
  <summary>nt2 huml</summary>

```
nt2 huml 0.3.0

Read NestedText and output its content as HUML.

By default, generated HUML values will only contain strings, arrays, and maps,
but you can cast nodes matching YAML Paths to boolean, number or null.

Switches may be before or after file arguments.

Examples:
    - nt2 huml config.nt
    - nt2 huml config.nt --number font.size --boolean font.bold
    - nt2 huml config.nt --schema config.types.nt
    - cat config.nt | nt2 huml

Usage:
    nt2 huml [SWITCHES] NESTED_TEXT_FILE...

Meta-switches:
    -h, --help                      Prints this help message and quits
    -v, --version                   Prints the program's version and quits

Switches:
    --boolean, -b YAMLPATH:str      Cast each node matching the given YAML Path
                                    query as boolean; may be given multiple
                                    times
    --null, -n YAMLPATH:str         Cast each node matching the given YAML Path
                                    query as null, if it is an empty string; may
                                    be given multiple times
    --number, --int, --float, -i, -f YAMLPATH:str
                                    Cast each node matching the given YAML Path
                                    query as a number; may be given multiple
                                    times
    --schema, -s NESTED_TEXT_FILE:ExistingFile
                                    Cast nodes matching YAML Path queries
                                    specified in a NestedText document. It must
                                    be a map whose keys are names of supported
                                    types (a subset of 'null', 'boolean',
                                    'number', and 'date'). Each key's value is a
                                    list of YAML Paths; may be given multiple
                                    times


```

</details>

<details>
  <summary>2nt json</summary>

```
2nt json 0.3.0

Read JSON and output its content as NestedText.

Examples:
    - 2nt json config.json
    - 2nt json config.json --to-schema >config.types.nt
    - cat config.json | 2nt json

It can be invoked as either the subcommand `2nt json` or the single command
`json2nt`.

Usage:
    2nt json [SWITCHES] JSON_FILE...

Meta-switches:
    -h, --help                      Prints this help message and quits
    -v, --version                   Prints the program's version and quits

Switches:
    --inline-width, -i WIDTH:[0..120] Maximum line width for inline dictionaries
                                    and lists
    --to-schema, -s                 Rather than convert the inputs, generate a
                                    schema


```

</details>

<details>
  <summary>2nt yaml</summary>

```
2nt yaml 0.3.0

Read YAML and output its content as NestedText.

Examples:
    - 2nt yaml config.yml
    - 2nt yaml config.yml --to-schema >config.types.nt
    - cat config.yml | 2nt yaml

It can be invoked as either the subcommand `2nt yaml` or the single command
`yaml2nt`.

Usage:
    2nt yaml [SWITCHES] YAML_FILE...

Meta-switches:
    -h, --help                      Prints this help message and quits
    -v, --version                   Prints the program's version and quits

Switches:
    --inline-width, -i WIDTH:[0..120] Maximum line width for inline dictionaries
                                    and lists
    --to-schema, -s                 Rather than convert the inputs, generate a
                                    schema


```

</details>

<details>
  <summary>2nt toml</summary>

```
2nt toml 0.3.0

Read TOML and output its content as NestedText.

Examples:
    - 2nt toml config.toml
    - 2nt toml config.toml --to-schema >config.types.nt
    - cat config.toml | 2nt toml

It can be invoked as either the subcommand `2nt toml` or the single command
`toml2nt`.

Usage:
    2nt toml [SWITCHES] TOML_FILE...

Meta-switches:
    -h, --help                      Prints this help message and quits
    -v, --version                   Prints the program's version and quits

Switches:
    --inline-width, -i WIDTH:[0..120] Maximum line width for inline dictionaries
                                    and lists
    --to-schema, -s                 Rather than convert the inputs, generate a
                                    schema


```

</details>

<details>
  <summary>2nt huml</summary>

```
2nt huml 0.3.0

Read HUML and output its content as NestedText.

Examples:
    - 2nt huml config.huml
    - 2nt huml config.huml --to-schema >config.types.nt
    - cat config.huml | 2nt huml

Usage:
    2nt huml [SWITCHES] HUML_FILE...

Meta-switches:
    -h, --help                      Prints this help message and quits
    -v, --version                   Prints the program's version and quits

Switches:
    --inline-width, -i WIDTH:[0..120] Maximum line width for inline dictionaries
                                    and lists
    --to-schema, -s                 Rather than convert the inputs, generate a
                                    schema


```

</details>

#### Limitations

##### Non-string Keys

YAML officially supports non-string key types,
like maps, lists, and numbers.
Support for non-string keys varies from one YAML parser to the next,
and is currently not handled by NestedTextTo.

If anyone is interested in using NestedTextTo with non-string key types,
please open an issue and I'll see what I can do!

##### Duplicate Keys

Most of the formats don't support duplicate keys,
and they are not currently handled by NestedTextTo.

Please open an issue if this matters to you.

### More Examples

#### View JSON Lines logs in a more readable format

```console
$ cat log.jsonl
```
<details>
  <summary>Output</summary>

```json
{"chat_id": 651321, "event": "receiving code", "user_first_name": "Andy", "user_id": 651321}
{"event": "guessed syntax", "ext": null, "probability": 0.05201493203639984, "probability_min": 0.12, "syntax": "Matlab"}
{"chat_id": 651321, "event": "colorizing code", "syntax": "py3", "user_first_name": "Andy", "user_id": 651321}
{"event": "Got deletion request", "reply_to_msg_user_id": 651321, "user_id": 651321}
{"chat_id": 651321, "event": "failed to delete message (it's probably gone already)", "exception": "Traceback (most recent call last):\n  File \"/home/andy/Code/colorcodebot/app/colorcodebot.py\", line 278, in delete_after_delay\n    bot.delete_message(message.chat.id, message.message_id)\n  File \"/home/andy/.local/share/venvs/84f7fb558856f9ccc2c54e3d122862b6/venv/lib/python3.10/site-packages/telebot/__init__.py\", line 1081, in delete_message\n    return apihelper.delete_message(self.token, chat_id, message_id, timeout)\n  File \"/home/andy/.local/share/venvs/84f7fb558856f9ccc2c54e3d122862b6/venv/lib/python3.10/site-packages/telebot/apihelper.py\", line 1299, in delete_message\n    return _make_request(token, method_url, params=payload, method='post')\n  File \"/home/andy/.local/share/venvs/84f7fb558856f9ccc2c54e3d122862b6/venv/lib/python3.10/site-packages/telebot/apihelper.py\", line 152, in _make_request\n    json_result = _check_result(method_name, result)\n  File \"/home/andy/.local/share/venvs/84f7fb558856f9ccc2c54e3d122862b6/venv/lib/python3.10/site-packages/telebot/apihelper.py\", line 179, in _check_result\n    raise ApiTelegramException(method_name, result, result_json)\ntelebot.apihelper.ApiTelegramException: A request to the Telegram API was unsuccessful. Error code: 400. Description: Bad Request: message to delete not found"}
```

</details>

```console
$ json2nt log.jsonl
```

<details>
  <summary>Output</summary>

```yaml
-
  chat_id: 651321
  event: receiving code
  user_first_name: Andy
  user_id: 651321
-
  event: guessed syntax
  ext:
  probability: 0.05201493203639984
  probability_min: 0.12
  syntax: Matlab
-
  chat_id: 651321
  event: colorizing code
  syntax: py3
  user_first_name: Andy
  user_id: 651321
-
  event: Got deletion request
  reply_to_msg_user_id: 651321
  user_id: 651321
-
  chat_id: 651321
  event: failed to delete message (it's probably gone already)
  exception:
    > Traceback (most recent call last):
    >   File "/home/andy/Code/colorcodebot/app/colorcodebot.py", line 278, in delete_after_delay
    >     bot.delete_message(message.chat.id, message.message_id)
    >   File "/home/andy/.local/share/venvs/84f7fb558856f9ccc2c54e3d122862b6/venv/lib/python3.10/site-packages/telebot/__init__.py", line 1081, in delete_message
    >     return apihelper.delete_message(self.token, chat_id, message_id, timeout)
    >   File "/home/andy/.local/share/venvs/84f7fb558856f9ccc2c54e3d122862b6/venv/lib/python3.10/site-packages/telebot/apihelper.py", line 1299, in delete_message
    >     return _make_request(token, method_url, params=payload, method='post')
    >   File "/home/andy/.local/share/venvs/84f7fb558856f9ccc2c54e3d122862b6/venv/lib/python3.10/site-packages/telebot/apihelper.py", line 152, in _make_request
    >     json_result = _check_result(method_name, result)
    >   File "/home/andy/.local/share/venvs/84f7fb558856f9ccc2c54e3d122862b6/venv/lib/python3.10/site-packages/telebot/apihelper.py", line 179, in _check_result
    >     raise ApiTelegramException(method_name, result, result_json)
    > telebot.apihelper.ApiTelegramException: A request to the Telegram API was unsuccessful. Error code: 400. Description: Bad Request: message to delete not found
```

</details>

#### View TOML as NestedText

![View TOML as NestedText](https://user-images.githubusercontent.com/1787385/199562999-d702bfb5-859c-417d-b8a4-ffb0d36e7537.png)

#### Convert NestedText to TOML, with and without casting

![Convert NestedText to TOML, with and without casting](https://user-images.githubusercontent.com/1787385/199562703-db0fec70-bb18-431a-aa01-c4858b449c56.png)

#### Convert NestedText to TOML with casting via auto-schema

![Convert NestedText to TOML with casting via auto-schema](https://user-images.githubusercontent.com/1787385/199562909-a1060b9b-0446-4aba-81b1-5ff288c839ed.png)

#### Query TOML with JSON tools, with and without casting

![Query TOML with JSON tools, with and without casting](https://user-images.githubusercontent.com/1787385/199562454-b6267df2-aaa9-421b-a47d-93cb49641a30.png)

### Development Docs

For local development, it's recommended to install and activate mise, then

```console
$ mise run install
```

From there, you may want to look at common task definitions:

```console
$ mise tasks
```

And you may wish to browse the structure and in-code documentation as rendered HTML,
at [the GitHub Pages site](https://andydecleyre.github.io/nestedtextto/moduleIndex.html).
