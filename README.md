# NestedTextTo
## CLI to convert between NestedText and JSON, YAML or TOML, with explicit type casting

[![PyPI version](https://img.shields.io/pypi/v/nt2?color=blue)](https://pypi.org/project/nt2/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nt2)
[![tests badge](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/test.yml/badge.svg?branch=develop)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/test.yml)
[![codecov badge](https://codecov.io/github/AndydeCleyre/nestedtextto/branch/develop/graph/badge.svg?token=M30UZQVM4Q)](https://codecov.io/github/AndydeCleyre/nestedtextto)
[![Format and lint](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/fmt.yml/badge.svg)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/fmt.yml)
[![requirements badge](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/reqs.yml/badge.svg)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/reqs.yml)
[![Generate docs from templates](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/doc.yml/badge.svg)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/doc.yml)
[![Publish to PyPI](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/pypi.yml/badge.svg)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/pypi.yml)

---

This project was created in appreciation for the design of [NestedText](https://nestedtext.org/),
the readability of [yamlpath](https://github.com/wwkimball/yamlpath) queries,
the utility of [cattrs](https://cattrs.readthedocs.io/),
and the joy of [plumbum](https://plumbum.readthedocs.io/)
and [ward](https://ward.readthedocs.io/) --
none of which are this author's projects.

This project, NestedTextTo, provides six command line tools
for convenient conversion between NestedText and other formats:
- `nt2json`, `nt2toml`, `nt2yaml`
- `json2nt`, `toml2nt`, `yaml2nt`

### What's NestedText?

From the NestedText docs, with emphasis added:

> NestedText is a file format for holding structured data to be entered, edited, or viewed by people. It organizes the data into a nested collection of *dictionaries*, *lists*, and *strings* **without the need for quoting or escaping**. A unique feature of this file format is that it only supports *one scalar type:* **strings**.  While the decision to eschew integer, real, date, etc. types may seem counter intuitive, it leads to simpler data files and applications that are more robust.

### How does this translate to formats with more value types?

When converting from NestedText to formats supporting more value types,
all plain values will be strings by default.
But you can provide options to cast any values as numbers, booleans, nulls, or dates/times,
if the target format supports it, using the powerful and concise YAML Path query syntax.

```console
$ cat example.nt
```
```yaml
people:
  -
    name: Bill Sky
    problems: 99
    happy: False
  -
    name: Vorbis Florbis
    problems: 6
    happy: yes
```
```console
$ nt2json example.nt --number /people/problems --boolean /people/happy
```
```json
{
  "people": [
    {
      "name": "Bill Sky",
      "problems": 99,
      "happy": false
    },
    {
      "name": "Vorbis Florbis",
      "problems": 6,
      "happy": true
    }
  ]
}
```

You may instead store these type mappings in a NestedText "schema" file.

```console
$ cat example.types.nt
```
```yaml
boolean:
  - /people/happy
number:
  - /people/problems
```

The following command will then also yield the above JSON:

```console
$ nt2json example.nt --schema example.types.nt
```

Options may be provided before or after the document,
and content may be piped directly to the command instead of specifying a file.

For more YAML Path syntax information see
[the YAML Path wiki](https://github.com/wwkimball/yamlpath/wiki/Search-Expressions).

For example, you could match all items which are *probably* intended as booleans,
at any depth, with `--boolean '/**[.=~/^(?i)(yes|no|true|false)$/]'`.

### Installation

If you don't need TOML support, you can omit the `[toml]` bits below.

Here are some ways to install it:

```console
$ pipx install 'nt2[toml]'        # Install using pipx (Python app manager)
$ pipz install 'nt2[toml]'        # Install using zpy (Python app and environment manager for Zsh)
$ pip install --user 'nt2[toml]'  # Install in your user's environment
$ pip install 'nt2[toml]'         # Install in current environment
```

I recommend using [pipx](https://github.com/pypa/pipx)
or `pipz` from [zpy](https://github.com/AndydeCleyre/zpy).

### Usage Docs

<details>
  <summary>nt2json</summary>

```
nt2json 0.1.5

Read NestedText and output its content as JSON.

By default, generated JSON values will only contain strings, arrays, and maps,
but you can cast nodes matching YAML Paths to boolean, null, or number.

Casting switches may be before or after file arguments.

Examples:
    nt2json example.nt
    nt2json <example.nt
    cat example.nt | nt2json
    nt2json -b '/People/"is a wizard"' -b '/People/"is awake"' example.nt

Usage:
    nt2json [SWITCHES] input_files...

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
    --schema, -s NESTEDTEXTFILE:ExistingFile
                                    Cast nodes matching YAML Path queries
                                    specified in a NestedText document. It must
                                    be a map with one or more of the keys:
                                    'null', 'boolean', 'number'Each key's value
                                    is a list of YAML Paths.; may be given
                                    multiple times


```

</details>


<details>
  <summary>nt2yaml</summary>

```
nt2yaml 0.1.5

Read NestedText and output its content as YAML.

By default, generated YAML values will only contain strings, arrays, and maps,
but you can cast nodes matching YAML Paths to boolean, null, number, or date.

Casting switches may be before or after file arguments.

Examples:
    nt2yaml example.nt
    nt2yaml <example.nt
    cat example.nt | nt2yaml
    nt2yaml -b '/People/"is a wizard"' -b '/People/"is awake"' example.nt

Usage:
    nt2yaml [SWITCHES] input_files...

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
    --schema, -s NESTEDTEXTFILE:ExistingFile
                                    Cast nodes matching YAML Path queries
                                    specified in a NestedText document. It must
                                    be a map with one or more of the keys:
                                    'null', 'boolean', 'number'Each key's value
                                    is a list of YAML Paths.; may be given
                                    multiple times


```

</details>


<details>
  <summary>nt2toml</summary>

```
nt2toml 0.1.5

Read NestedText and output its content as TOML.

By default, generated TOML values will only contain strings, arrays, and maps,
but you can cast nodes matching YAML Paths to boolean, number, or date.

Casting switches may be before or after file arguments.

Examples:
    nt2toml example.nt
    nt2toml <example.nt
    cat example.nt | nt2toml
    nt2toml -b '/People/"is a wizard"' -b '/People/"is awake"' example.nt

Usage:
    nt2toml [SWITCHES] input_files...

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
    --schema, -s NESTEDTEXTFILE:ExistingFile
                                    Cast nodes matching YAML Path queries
                                    specified in a NestedText document. It must
                                    be a map with one or more of the keys:
                                    'null', 'boolean', 'number'Each key's value
                                    is a list of YAML Paths.; may be given
                                    multiple times


```

</details>


<details>
  <summary>json2nt</summary>

```
json2nt 0.1.5

Read JSON and output its content as NestedText.

Examples:
    json2nt example.json
    json2nt <example.json
    cat example.json | json2nt

Usage:
    json2nt [SWITCHES] input_files...

Meta-switches:
    -h, --help         Prints this help message and quits
    -v, --version      Prints the program's version and quits


```

</details>


<details>
  <summary>yaml2nt</summary>

```
yaml2nt 0.1.5

Read YAML and output its content as NestedText.

Examples:
    yaml2nt example.yml
    yaml2nt <example.yml
    cat example.yml | yaml2nt

Usage:
    yaml2nt [SWITCHES] input_files...

Meta-switches:
    -h, --help         Prints this help message and quits
    -v, --version      Prints the program's version and quits


```

</details>


<details>
  <summary>toml2nt</summary>

```
toml2nt 0.1.5

Read TOML and output its content as NestedText.

Examples:
    toml2nt example.yml
    toml2nt <example.yml
    cat example.yml | toml2nt

Usage:
    toml2nt [SWITCHES] input_files...

Meta-switches:
    -h, --help         Prints this help message and quits
    -v, --version      Prints the program's version and quits


```

</details>



### More Examples

`json2nt` can be useful for viewing JSON Lines logs in a more readable format:

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


### Development Docs

For local development, it's recommended to activate a venv, then

```console
$ pip install -r local-requirements.txt
```

From there, you may want to look at common task definitions:

```console
$ task -l
$ nox -l
```

And you may wish to browse the structure and in-code documentation as rendered HTML,
at [the GitHub Pages site](https://andydecleyre.github.io/nestedtextto/moduleIndex.html).
