from commands import nt2yaml, yaml2nt
from plumbum import local
from utils import assert_file_content, casting_args_from_schema_file
from ward import test

SAMPLES = local.path(__file__).up() / 'samples' / 'yaml'


for input_yaml_name, output_nt_name in {
    'untyped': 'base',
    'typed_all': 'typed_round_trip',
    'typed_all_verbose_null': 'typed_round_trip',
    'typed_dates': 'dates',
    'typed_floats': 'floats',
}.items():

    @test(f"YAML -> NestedText [{input_yaml_name}]")
    def _(input_yaml_name=input_yaml_name, output_nt_name=output_nt_name):
        expected_file = SAMPLES / f"{output_nt_name}.nt"
        output = yaml2nt(SAMPLES / f"{input_yaml_name}.yml")
        assert_file_content(expected_file, output)


@test("NestedText -> YAML [untyped]")
def _():
    expected_file = SAMPLES / 'untyped.yml'
    output = nt2yaml(SAMPLES / 'base.nt')
    assert_file_content(expected_file, output)


@test("NestedText -> YAML [top level array]")
def _():
    expected_file = SAMPLES / 'lines.yml'
    output = nt2yaml(SAMPLES / 'lines.nt')
    assert_file_content(expected_file, output)


for schema_file in SAMPLES // 'base.*.types.nt':

    @test(f"NestedText -> YAML [schema file: {schema_file.name}]")
    def _(schema_file=schema_file):
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.yml"
        output = nt2yaml(SAMPLES / 'base.nt', schema_files=(schema_file,))
        assert_file_content(expected_file, output)

    @test(f"NestedText -> YAML [casting args from schema: {schema_file.name}]")
    def _(schema_file=schema_file):
        casting_args = casting_args_from_schema_file(schema_file)
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.yml"
        output = nt2yaml(SAMPLES / 'base.nt', **casting_args)
        assert_file_content(expected_file, output)


for num_type in ('floats', 'ints'):

    @test(f"NestedText -> YAML [schema file: {num_type}.types.nt]")
    def _(num_type=num_type):
        expected_file = SAMPLES / f"typed_{num_type}.yml"
        output = nt2yaml(
            SAMPLES / f"{num_type}.nt", schema_files=(SAMPLES / f"{num_type}.types.nt",)
        )
        assert_file_content(expected_file, output)


@test("NestedText -> YAML [schema file: dates.types.nt]")
def _():
    expected_file = SAMPLES / 'typed_dates_round_trip.yml'
    output = nt2yaml(SAMPLES / 'dates.nt', schema_files=(SAMPLES / 'dates.types.nt',))
    assert_file_content(expected_file, output)


@test("NestedText -> YAML [casting args from schema: dates.types.nt]")
def _():
    casting_args = casting_args_from_schema_file(SAMPLES / 'dates.types.nt', ('date',))
    expected_file = SAMPLES / 'typed_dates_round_trip.yml'
    output = nt2yaml(SAMPLES / 'dates.nt', **casting_args)
    assert_file_content(expected_file, output)


@test("NestedText -> YAML [blend schema file with casting args]")
def _():
    expected_file = SAMPLES / 'typed_all.yml'
    output = nt2yaml(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool_null.types.nt',),
        **casting_args_from_schema_file(SAMPLES / 'base.num.types.nt'),
    )
    assert_file_content(expected_file, output)


@test("NestedText -> YAML [blend schema files]")
def _():
    expected_file = SAMPLES / 'typed_all.yml'
    output = nt2yaml(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool_null.types.nt', SAMPLES / 'base.num.types.nt'),
    )
    assert_file_content(expected_file, output)


for typed_yml in ('all', 'floats', 'dates'):

    @test(f"YAML -> schema, NestedText -> YAML [generate schema from typed_{typed_yml}.yml]")
    def _():
        expected_file = SAMPLES / f"typed_{typed_yml}.yml"
        schema_content = yaml2nt(expected_file, to_schema=True)
        with local.tempdir() as tmp:
            schema_file = tmp / 'schema.nt'
            schema_file.write(schema_content, 'utf-8')
            output = nt2yaml(
                SAMPLES / f"{'base' if typed_yml == 'all' else typed_yml}.nt",
                schema_files=(schema_file,),
            )
        if typed_yml == 'dates':
            expected_file = SAMPLES / 'typed_dates_round_trip.yml'
        assert_file_content(expected_file, output)
