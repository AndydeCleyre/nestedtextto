from commands import nt2toml, toml2nt
from plumbum import local
from utils import casting_args_from_schema_file
from ward import test

SAMPLES = local.path(__file__).up() / 'samples' / 'toml'


@test("NestedText -> TOML [untyped]")
def _():
    expected_file = SAMPLES / 'untyped.toml'
    output = nt2toml(SAMPLES / 'base.nt')
    # print(repr(output))
    assert output == expected_file.read()


for input_toml_name, output_nt_name in {
    'untyped': 'base',
    'typed_all': 'typed_round_trip',
    'typed_dates': 'dates_round_trip',
}.items():

    @test(f"TOML -> NestedText [{input_toml_name}]")
    def _(input_toml_name=input_toml_name, output_nt_name=output_nt_name):
        expected_file = SAMPLES / f"{output_nt_name}.nt"
        output = toml2nt(SAMPLES / f"{input_toml_name}.toml")
        assert output == expected_file.read()


for schema_file in SAMPLES // 'base.*.types.nt':

    @test(f"NestedText -> TOML [schema file: {schema_file.name}]")
    def _(schema_file=schema_file):
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.toml"
        output = nt2toml(SAMPLES / 'base.nt', schema_files=(schema_file,))
        assert output == expected_file.read()

    casting_args = casting_args_from_schema_file(schema_file, ('number', 'boolean'))

    @test(f"NestedText -> TOML [casting args: {', '.join(casting_args)}]")
    def _(schema_file=schema_file, casting_args=casting_args):
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.toml"
        output = nt2toml(SAMPLES / 'base.nt', **casting_args)
        assert output == expected_file.read()


@test("NestedText -> TOML [schema file: dates.types.nt]")
def _():
    expected_file = SAMPLES / 'typed_dates.toml'
    output = nt2toml(SAMPLES / 'dates.nt', schema_files=(SAMPLES / 'dates.types.nt',))
    assert output == expected_file.read()


casting_args = casting_args_from_schema_file(SAMPLES / 'dates.types.nt', ('date',))


@test(f"NestedText -> TOML [casting args: {', '.join(casting_args)}]")
def _(casting_args=casting_args):
    expected_file = SAMPLES / 'typed_dates.toml'
    output = nt2toml(SAMPLES / 'dates.nt', **casting_args)
    assert output == expected_file.read()


@test("NestedText -> TOML [blend schema file with casting args]")
def _():
    expected_file = SAMPLES / 'typed_all.toml'
    output = nt2toml(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool.types.nt',),
        **casting_args_from_schema_file(SAMPLES / 'base.num.types.nt', ('number', 'boolean')),
    )
    assert output == expected_file.read()


@test("NestedText -> TOML [blend schema files]")
def _():
    expected_file = SAMPLES / 'typed_all.toml'
    output = nt2toml(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool.types.nt', SAMPLES / 'base.num.types.nt'),
    )
    assert output == expected_file.read()
