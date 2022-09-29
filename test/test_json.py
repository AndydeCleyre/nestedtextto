from commands import json2nt, nt2json
from plumbum import local
from utils import casting_args_from_schema_file
from ward import test

SAMPLES = local.path(__file__).up() / 'samples' / 'json'


@test("NestedText -> JSON [untyped]")
def _():
    expected_file = SAMPLES / 'untyped.json'
    output = nt2json(SAMPLES / 'base.nt')
    assert output == expected_file.read()


for input_json_name, output_nt_name in {
    'untyped': 'base',
    'typed_all': 'typed_round_trip',
}.items():

    @test(f"JSON -> NestedText [{input_json_name}]")
    def _(input_json_name=input_json_name, output_nt_name=output_nt_name):
        expected_file = SAMPLES / f"{output_nt_name}.nt"
        output = json2nt(SAMPLES / f"{input_json_name}.json")
        assert output == expected_file.read()


for schema_file in SAMPLES // 'base.*.types.nt':

    @test(f"NestedText -> JSON [schema file: {schema_file.name}]")
    def _(schema_file=schema_file):
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.json"
        output = nt2json(SAMPLES / 'base.nt', schema_files=(schema_file,))
        assert output == expected_file.read()

    @test(f"NestedText -> JSON [casting args from schema: {schema_file.name}]")
    def _(schema_file=schema_file):
        casting_args = casting_args_from_schema_file(schema_file)
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.json"
        output = nt2json(SAMPLES / 'base.nt', **casting_args)
        assert output == expected_file.read()


@test("NestedText -> JSON [blend schema file with casting args]")
def _():
    expected_file = SAMPLES / 'typed_all.json'
    output = nt2json(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool_null.types.nt',),
        **casting_args_from_schema_file(SAMPLES / 'base.num.types.nt'),
    )
    assert output == expected_file.read()


@test("NestedText -> JSON [blend schema files]")
def _():
    expected_file = SAMPLES / 'typed_all.json'
    output = nt2json(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool_null.types.nt', SAMPLES / 'base.num.types.nt'),
    )
    assert output == expected_file.read()
