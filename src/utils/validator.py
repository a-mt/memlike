from pydantic_core import (
    core_schema as schema,
    SchemaValidator,
    PydanticCustomError,
)
import web


def is_file(x):
    # used in tests
    if isinstance(x, web.storage):
        return x

    # multipart.MultipartPart
    if hasattr(x, "file"):
        return x

    # cgi.FieldStorage
    if hasattr(x, "value"):
        return x

    # KnownLengthRFile
    if hasattr(x, "read"):
        return x

    raise PydanticCustomError(
        "file",
        "Input should be a valid file",
        {},
    )


def is_file_schema(**kwargs):
    return schema.no_info_plain_validator_function(
        function=is_file,
        **kwargs,
    )


def validate_choices(values):
    def fn(x):
        if x not in values:
            raise PydanticCustomError(
                "enum",
                "Input should be one of ({values}), got '{wrong_value}'",
                {"wrong_value": x, "values": ", ".join([f"'{v}'" for v in values])},
            )
        return x

    return fn


def str_choices_schema(choices, **kwargs):
    return schema.no_info_after_validator_function(
        schema=schema.str_schema(**kwargs),
        function=validate_choices(choices),
    )


class empty:
    pass


def field(schema_instance, *args, **kwargs):
    default = kwargs.pop("default", empty)
    validator = kwargs.pop("validator", empty)

    if validator != empty:
        schema_instance = schema.no_info_after_validator_function(
            schema=schema_instance,
            function=validator,
        )

    if default != empty:
        return schema.typed_dict_field(
            schema.with_default_schema(
                schema_instance,
                default=default,
                **kwargs,
            )
        )

    return schema.typed_dict_field(
        schema_instance,
        **kwargs,
    )


def validate(fields, data):
    return SchemaValidator(schema.typed_dict_schema(fields=fields)).validate_python(data)
