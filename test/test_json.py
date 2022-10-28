from commands import json2nt, nt2json
from plumbum import local
from utils import assert_file_content, casting_args_from_schema_file
from ward import test

SAMPLES = local.path(__file__).up() / 'samples' / 'json'


@test("JSON Lines -> NestedText")
def _():
    expected_file = SAMPLES / 'lines.nt'
    output = json2nt(SAMPLES / 'lines.jsonl')
    assert_file_content(expected_file, output)


for input_json_name, output_nt_name in {
    'untyped': 'base',
    'typed_all': 'typed_round_trip',
}.items():

    @test(f"JSON -> NestedText [{input_json_name}]")
    def _(input_json_name=input_json_name, output_nt_name=output_nt_name):
        expected_file = SAMPLES / f"{output_nt_name}.nt"
        output = json2nt(SAMPLES / f"{input_json_name}.json")
        assert_file_content(expected_file, output)


@test("NestedText -> JSON [untyped]")
def _():
    expected_file = SAMPLES / 'untyped.json'
    output = nt2json(SAMPLES / 'base.nt')
    assert_file_content(expected_file, output)


@test("NestedText -> JSON [top level array]")
def _():
    expected_file = SAMPLES / 'lines.json'
    output = nt2json(SAMPLES / 'lines.nt')
    assert_file_content(expected_file, output)


for schema_file in SAMPLES // 'base.*.types.nt':

    @test(f"NestedText -> JSON [schema file: {schema_file.name}]")
    def _(schema_file=schema_file):
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.json"
        output = nt2json(SAMPLES / 'base.nt', schema_files=(schema_file,))
        assert_file_content(expected_file, output)

    @test(f"NestedText -> JSON [casting args from schema: {schema_file.name}]")
    def _(schema_file=schema_file):
        casting_args = casting_args_from_schema_file(schema_file)
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.json"
        output = nt2json(SAMPLES / 'base.nt', **casting_args)
        assert_file_content(expected_file, output)


@test("NestedText -> JSON [blend schema file with casting args]")
def _():
    expected_file = SAMPLES / 'typed_all.json'
    output = nt2json(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool_null.types.nt',),
        **casting_args_from_schema_file(SAMPLES / 'base.num.types.nt'),
    )
    assert_file_content(expected_file, output)


@test("NestedText -> JSON [blend schema files]")
def _():
    expected_file = SAMPLES / 'typed_all.json'
    output = nt2json(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool_null.types.nt', SAMPLES / 'base.num.types.nt'),
    )
    assert_file_content(expected_file, output)


@test("JSON -> schema, NestedText -> JSON [generate schema from typed_all.json]")
def _():
    expected_file = SAMPLES / 'typed_all.json'
    schema_content = json2nt(expected_file, to_schema=True)
    with local.tempdir() as tmp:
        schema_file = tmp / 'schema.nt'
        schema_file.write(schema_content, 'utf-8')
        output = nt2json(SAMPLES / 'base.nt', schema_files=(schema_file,))
    assert_file_content(expected_file, output)
