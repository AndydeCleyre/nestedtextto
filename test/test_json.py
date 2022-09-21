from nestedtext import load as ntload
from plumbum import local
from plumbum.cmd import json2nt, nt2json
from ward import test

SAMPLES = local.path(__file__).up() / 'samples' / 'json'


# TODO: use programmatic invocations rather than plumbum.cmd,
# so that coverage can be tracked.


@test("convert NestedText to untyped JSON")
def _():
    expected_file = SAMPLES / 'untyped.json'
    output = nt2json(SAMPLES / 'base.nt')
    assert output == expected_file.read()


for input_json_name, output_nt_name in {
    'untyped': 'base',
    'typed_all': 'typed_round_trip',
}.items():

    @test(f"convert {input_json_name} JSON to NestedText")
    def _(input_json_name=input_json_name, output_nt_name=output_nt_name):
        expected_file = SAMPLES / f"{output_nt_name}.nt"
        output = json2nt(SAMPLES / f"{input_json_name}.json")
        assert output == expected_file.read()


def casting_args_from_schema_file(schema_file):
    casting_args = []
    schema_data = ntload(schema_file)
    for cast_type in ('null', 'number', 'boolean'):
        if yamlpaths := schema_data.get(cast_type):
            for yp in yamlpaths:
                casting_args.extend((f"--{cast_type}", yp))
    return casting_args


for schema_file in SAMPLES // 'base.*.types.nt':

    @test(f"convert NestedText to typed JSON, using schema file [{schema_file.name}]")
    def _(schema_file=schema_file):
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.json"
        output = nt2json(SAMPLES / 'base.nt', '--schema', schema_file)
        assert output == expected_file.read()

    casting_args = casting_args_from_schema_file(schema_file)

    @test(
        "convert NestedText to typed JSON, using casting args ["
        + ', '.join(set(arg.lstrip('-') for arg in casting_args[::2]))
        + "]"
    )
    def _(schema_file=schema_file, casting_args=casting_args):
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.json"
        output = nt2json(SAMPLES / 'base.nt', *casting_args)
        assert output == expected_file.read()


@test("convert NestedText to typed JSON, combining schema file and casting args")
def _():
    expected_file = SAMPLES / 'typed_all.json'
    output = nt2json(
        SAMPLES / 'base.nt',
        '--schema',
        SAMPLES / 'base.bool_null.types.nt',
        *casting_args_from_schema_file(SAMPLES / 'base.num.types.nt'),
    )
    assert output == expected_file.read()


@test("convert NestedText to typed JSON, combining multiple schema files")
def _():
    expected_file = SAMPLES / 'typed_all.json'
    output = nt2json(
        SAMPLES / 'base.nt',
        '--schema',
        SAMPLES / 'base.bool_null.types.nt',
        '--schema',
        SAMPLES / 'base.num.types.nt',
    )
    assert output == expected_file.read()
