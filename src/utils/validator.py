from pydantic_core import (
    core_schema as schema,
    SchemaValidator,
    PydanticCustomError,
)
import web


def is_file(value):
    # used in tests
    if isinstance(value, web.storage):
        return value

    # multipart.MultipartPart
    if hasattr(value, "file"):
        return value

    # cgi.FieldStorage
    if hasattr(value, "value"):
        return value

    # KnownLengthRFile
    if hasattr(value, "read"):
        return value

    raise PydanticCustomError(
        "file",
        "Input should be a valid file",
        {},
    )


def file_schema(**kwargs):
    return schema.no_info_plain_validator_function(
        function=is_file,
        **kwargs,
    )


def validate_choices(values):
    def is_valid_choice(value):
        if value not in values:
            raise PydanticCustomError(
                "enum",
                "Input should be one of ({values}), got '{wrong_value}'",
                {"wrong_value": value, "values": ", ".join([f"'{v}'" for v in values])},
            )
        return value

    return is_valid_choice


def str_choices_schema(choices, **kwargs):
    return schema.no_info_after_validator_function(
        schema=schema.str_schema(**kwargs),
        function=validate_choices(choices),
    )


class empty:
    pass


def field(schema_instance, *args, **kwargs):
    """
    Helper function to create a typed_dict_field of type schema_instance (ie str_schema)
    with an optional default value and validator function
    """
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
    """
    Create a SchemaValidator instance
    and vallidate the input data
    """
    return SchemaValidator(schema.typed_dict_schema(fields=fields)).validate_python(data)
