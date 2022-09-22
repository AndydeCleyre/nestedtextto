from nestedtext import load as ntload
from plumbum import local
from plumbum.cmd import nt2toml, toml2nt
from ward import test

SAMPLES = local.path(__file__).up() / 'samples' / 'toml'


# TODO: use programmatic invocations rather than plumbum.cmd,
# so that coverage can be tracked.

# TODO: add dates to tests


@test("NestedText -> TOML [untyped]")
def _():
    expected_file = SAMPLES / 'untyped.toml'
    output = nt2toml(SAMPLES / 'base.nt')
    assert output == expected_file.read()


for input_toml_name, output_nt_name in {
    'untyped': 'base',
    'typed_all': 'typed_round_trip',
}.items():

    @test(f"TOML -> NestedText [{input_toml_name}]")
    def _(input_toml_name=input_toml_name, output_nt_name=output_nt_name):
        expected_file = SAMPLES / f"{output_nt_name}.nt"
        output = toml2nt(SAMPLES / f"{input_toml_name}.toml")
        assert output == expected_file.read()


def casting_args_from_schema_file(schema_file):
    casting_args = []
    schema_data = ntload(schema_file)
    for cast_type in ('number', 'boolean'):
        if yamlpaths := schema_data.get(cast_type):
            for yp in yamlpaths:
                casting_args.extend((f"--{cast_type}", yp))
    return casting_args


for schema_file in SAMPLES // 'base.*.types.nt':

    @test(f"NestedText -> TOML [schema file: {schema_file.name}]")
    def _(schema_file=schema_file):
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.toml"
        output = nt2toml(SAMPLES / 'base.nt', '--schema', schema_file)
        assert output == expected_file.read()

    casting_args = casting_args_from_schema_file(schema_file)

    @test(
        "NestedText -> TOML [casting args: "
        + ', '.join(set(arg.lstrip('-') for arg in casting_args[::2]))
        + "]"
    )
    def _(schema_file=schema_file, casting_args=casting_args):
        expected_file = SAMPLES / f"typed_{schema_file.name.split('.')[1]}.toml"
        output = nt2toml(SAMPLES / 'base.nt', *casting_args)
        assert output == expected_file.read()


@test("NestedText -> TOML [blend schema file with casting args]")
def _():
    expected_file = SAMPLES / 'typed_all.toml'
    output = nt2toml(
        SAMPLES / 'base.nt',
        '--schema',
        SAMPLES / 'base.bool.types.nt',
        *casting_args_from_schema_file(SAMPLES / 'base.num.types.nt'),
    )
    assert output == expected_file.read()


@test("NestedText -> TOML [blend schema files]")
def _():
    expected_file = SAMPLES / 'typed_all.toml'
    output = nt2toml(
        SAMPLES / 'base.nt',
        '--schema',
        SAMPLES / 'base.bool.types.nt',
        '--schema',
        SAMPLES / 'base.num.types.nt',
    )
    assert output == expected_file.read()
