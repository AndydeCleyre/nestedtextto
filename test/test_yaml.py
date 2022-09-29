from commands import nt2yaml, yaml2nt
from plumbum import local
from utils import casting_args_from_schema_file
from ward import test

SAMPLES = local.path(__file__).up() / 'samples' / 'yaml'


@test("NestedText -> YAML [untyped]")
def _():
    expected_file = SAMPLES / 'untyped.yml'
    output = nt2yaml(SAMPLES / 'base.nt')
    assert output == expected_file.read()


for input_yaml_name, output_nt_name in {
    'untyped': 'base',
    'typed_all': 'typed_round_trip',
    'typed_all_verbose_null': 'typed_round_trip',
    'typed_dates': 'dates',
}.items():

    @test(f"YAML -> NestedText [{input_yaml_name}]")
    def _(input_yaml_name=input_yaml_name, output_nt_name=output_nt_name):
        expected_file = SAMPLES / f"{output_nt_name}.nt"
        output = yaml2nt(SAMPLES / f"{input_yaml_name}.yml")
        assert output == expected_file.read()


for schema_file in SAMPLES // 'base.*.types.nt':

    @test(f"NestedText -> YAML [schema file: {schema_file.name}]")
    def _(schema_file=schema_file):
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.yml"
        output = nt2yaml(SAMPLES / 'base.nt', schema_files=(schema_file,))
        assert output == expected_file.read()

    @test(f"NestedText -> YAML [casting args from schema: {schema_file.name}]")
    def _(schema_file=schema_file):
        casting_args = casting_args_from_schema_file(schema_file)
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.yml"
        output = nt2yaml(SAMPLES / 'base.nt', **casting_args)
        assert output == expected_file.read()


@test("NestedText -> YAML [schema file: dates.types.nt]")
def _():
    expected_file = SAMPLES / 'typed_dates_round_trip.yml'
    output = nt2yaml(SAMPLES / 'dates.nt', schema_files=(SAMPLES / 'dates.types.nt',))
    assert output == expected_file.read()


@test("NestedText -> YAML [casting args from schema: dates.types.nt]")
def _():
    casting_args = casting_args_from_schema_file(SAMPLES / 'dates.types.nt', ('date',))
    expected_file = SAMPLES / 'typed_dates_round_trip.yml'
    output = nt2yaml(SAMPLES / 'dates.nt', **casting_args)
    assert output == expected_file.read()


@test("NestedText -> YAML [blend schema file with casting args]")
def _():
    expected_file = SAMPLES / 'typed_all.yml'
    output = nt2yaml(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool_null.types.nt',),
        **casting_args_from_schema_file(SAMPLES / 'base.num.types.nt'),
    )
    assert output == expected_file.read()


@test("NestedText -> YAML [blend schema files]")
def _():
    expected_file = SAMPLES / 'typed_all.yml'
    output = nt2yaml(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool_null.types.nt', SAMPLES / 'base.num.types.nt'),
    )
    assert output == expected_file.read()
