from nestedtext import load as ntload


def casting_args_from_schema_file(schema_file, types=('null', 'number', 'boolean')):
    casting_args = {}
    schema_data = ntload(schema_file)
    attr_names = {
        'null': 'null_paths',
        'boolean': 'bool_paths',
        'number': 'num_paths',
        'date': 'date_paths',
    }
    for cast_type in types:
        casting_args[attr_names[cast_type]] = schema_data.get(cast_type, ())
    return casting_args
