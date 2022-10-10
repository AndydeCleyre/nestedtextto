# NestedTextTo (nt2)

[![tests badge](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/test.yml/badge.svg?branch=develop)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/test.yml)
[![codecov badge](https://codecov.io/github/AndydeCleyre/nestedtextto/branch/develop/graph/badge.svg?token=M30UZQVM4Q)](https://codecov.io/github/AndydeCleyre/nestedtextto)
[![requirements badge](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/reqs.yml/badge.svg)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/reqs.yml)
[![Format and lint](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/fmt.yml/badge.svg)](https://github.com/AndydeCleyre/nestedtextto/actions/workflows/fmt.yml)
[![PyPI version](https://img.shields.io/pypi/v/nt2?color=green&style=plastic)](https://pypi.org/project/nt2/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nt2?color=green&style=plastic)

---

This project was created in appreciation for the design of [NestedText](https://nestedtext.org/),
the readability of [yamlpath](https://github.com/wwkimball/yamlpath) queries,
the utility of [cattrs](https://cattrs.readthedocs.io/),
and the joy of [plumbum](https://plumbum.readthedocs.io/)
and [ward](https://ward.readthedocs.io/) --
none of which are this author's projects.

From the NestedText docs:

> NestedText is a file format for holding structured data to be entered, edited, or viewed by people. It organizes the data into a nested collection of dictionaries, lists, and strings without the need for quoting or escaping. A unique feature of this file format is that it only supports one scalar type: strings.  While the decision to eschew integer, real, date, etc. types may seem counter intuitive, it leads to simpler data files and applications that are more robust.

This project, NestedTextTo ("nt2"), provides six command line tools
for convenient conversion between NestedText and other formats:

- `nt2json`
- `nt2yaml`
- `nt2toml`
- `json2nt`
- `yaml2nt`
- `toml2nt`

When converting from NestedText to the others, which support more value types,
all plain values will be strings by default.
But you can provide options to cast any values as numbers, booleans, nulls, or dates,
if the target language supports it, using the powerful and concise YAML Path query syntax.
These YAML Paths may alternatively be stored in a simple "schema" NestedText file.

![screenshot](https://user-images.githubusercontent.com/1787385/193654318-43c2bd5f-5a88-4751-a759-71ec757d701d.png)

## Installation

If you don't need TOML support, you can omit the `[toml]` bits below.

Here are some ways to install it:

```console
$ pip install 'nt2[toml]'         # Install in current environment
$ pip install --user 'nt2[toml]'  # Install in your user's environment
$ pipx install 'nt2[toml]'        # Install using pipx (Python app manager)
$ pipz install 'nt2[toml]'        # Install using zpy (ZSH Python app and environment manager)
```

## Example

This sample document is taken from the NestedText docs.

`example.nt`:
```yaml
debug: false
secret_key: t=)40**y&883y9gdpuw%aiig+wtc033(ui@^1ur72w#zhw3_ch

allowed_hosts:
  - www.example.com

database:
  engine: django.db.backends.mysql
  host: db.example.com
  port: 3306
  user: www

webmaster_email: admin@example.com
```

To create a corresponding JSON document wherein `debug` and `port` are boolean and int, respectively,
you can run:

```console
$ nt2json example.nt -b /debug -i /database/port
```

```json
{
  "debug": false,  # <-- would be a quoted string if not for '--boolean /debug'
  "secret_key": "t=)40**y&883y9gdpuw%aiig+wtc033(ui@^1ur72w#zhw3_ch",
  "allowed_hosts": [
    "www.example.com"
  ],
  "database": {
    "engine": "django.db.backends.mysql",
    "host": "db.example.com",
    "port": 3306,  # <-- would be a quoted string if not for '--number /database/port'
    "user": "www"
  },
  "webmaster_email": "admin@example.com"
}
```

Those comments are for the sake of this README and don't reflect real output.

You may instead store these type mappings in a NestedText file.

`example.types.nt`:
```yaml
boolean:
  - /debug
number:
  - /database/port
```

The following command will now also yield the above JSON:

```console
$ nt2json example.nt -s example.types.nt
```

## Usage Docs

<details>
  <summary>nt2json</summary>

```
nt2json 0.0.5

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
nt2yaml 0.0.5

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
nt2toml 0.0.5

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
json2nt 0.0.5

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
yaml2nt 0.0.5

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
toml2nt 0.0.5

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

