from commands import nt2toml, toml2nt
from plumbum import local
from utils import assert_file_content, casting_args_from_schema_file
from ward import skip, test

try:
    import tomli  # noqa: F401
    import tomli_w  # noqa: F401
except ImportError:
    TOML_DISABLED = True
else:
    TOML_DISABLED = False


SAMPLES = local.path(__file__).up() / 'samples' / 'toml'


for input_toml_name, output_nt_name in {
    'untyped': 'base',
    'typed_all': 'typed_round_trip',
    'typed_dates': 'dates_round_trip',
    'typed_times': 'times',
}.items():

    @skip("TOML support not enabled", when=TOML_DISABLED)
    @test(f"TOML -> NestedText [{input_toml_name}]")
    def _(input_toml_name=input_toml_name, output_nt_name=output_nt_name):
        expected_file = SAMPLES / f"{output_nt_name}.nt"
        output = toml2nt(SAMPLES / f"{input_toml_name}.toml")
        assert_file_content(expected_file, output)


@skip("TOML support not enabled", when=TOML_DISABLED)
@test("NestedText -> TOML [untyped]")
def _():
    expected_file = SAMPLES / 'untyped.toml'
    output = nt2toml(SAMPLES / 'base.nt')
    assert_file_content(expected_file, output)


@skip("TOML support not enabled", when=TOML_DISABLED)
@test("NestedText -> TOML [top level array (kludged)]")
def _():
    expected_file = SAMPLES / 'lines.toml'
    output = nt2toml(SAMPLES / 'lines.nt')
    assert_file_content(expected_file, output)


for schema_file in SAMPLES // 'base.*.types.nt':

    @skip("TOML support not enabled", when=TOML_DISABLED)
    @test(f"NestedText -> TOML [schema file: {schema_file.name}]")
    def _(schema_file=schema_file):
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.toml"
        output = nt2toml(SAMPLES / 'base.nt', schema_files=(schema_file,))
        assert_file_content(expected_file, output)

    @skip("TOML support not enabled", when=TOML_DISABLED)
    @test(f"NestedText -> TOML [casting args from schema: {schema_file.name}]")
    def _(schema_file=schema_file):
        casting_args = casting_args_from_schema_file(schema_file, ('number', 'boolean'))
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.toml"
        output = nt2toml(SAMPLES / 'base.nt', **casting_args)
        assert_file_content(expected_file, output)


@skip("TOML support not enabled", when=TOML_DISABLED)
@test("NestedText -> TOML [blend schema file with casting args]")
def _():
    expected_file = SAMPLES / 'typed_all.toml'
    output = nt2toml(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool.types.nt',),
        **casting_args_from_schema_file(SAMPLES / 'base.num.types.nt', ('number', 'boolean')),
    )
    assert_file_content(expected_file, output)


@skip("TOML support not enabled", when=TOML_DISABLED)
@test("NestedText -> TOML [blend schema files]")
def _():
    expected_file = SAMPLES / 'typed_all.toml'
    output = nt2toml(
        SAMPLES / 'base.nt',
        schema_files=(SAMPLES / 'base.bool.types.nt', SAMPLES / 'base.num.types.nt'),
    )
    assert_file_content(expected_file, output)


for input_file, expected_file, schema_file in (
    (SAMPLES / 'dates.nt', SAMPLES / 'typed_dates.toml', SAMPLES / 'dates.types.nt'),
    (SAMPLES / 'times.nt', SAMPLES / 'typed_times.toml', SAMPLES / 'times.types.nt'),
):

    @skip("TOML support not enabled", when=TOML_DISABLED)
    @test(f"NestedText -> TOML [schema file: {schema_file.name}]")
    def _(input_file=input_file, expected_file=expected_file, schema_file=schema_file):
        output = nt2toml(input_file, schema_files=(schema_file,))
        assert_file_content(expected_file, output)

    casting_args = casting_args_from_schema_file(schema_file, ('date',))

    @skip("TOML support not enabled", when=TOML_DISABLED)
    @test(f"NestedText -> TOML [casting args: {', '.join(casting_args)}]")
    def _(input_file=input_file, expected_file=expected_file, casting_args=casting_args):
        output = nt2toml(input_file, **casting_args)
        assert_file_content(expected_file, output)


for typed_toml in ('all', 'dates', 'times'):

    @skip("TOML support not enabled", when=TOML_DISABLED)
    @test(f"TOML -> schema, NestedText -> TOML [generate schema from typed_{typed_toml}.toml]")
    def _():
        expected_file = SAMPLES / f"typed_{typed_toml}.toml"
        schema_content = toml2nt(expected_file, to_schema=True)
        with local.tempdir() as tmp:
            schema_file = tmp / 'schema.nt'
            schema_file.write(schema_content, 'utf-8')
            output = nt2toml(
                SAMPLES / f"{'base' if typed_toml == 'all' else typed_toml}.nt",
                schema_files=(schema_file,),
            )
        assert_file_content(expected_file, output)
