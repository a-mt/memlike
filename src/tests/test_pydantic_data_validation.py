from .testcases import SimpleTestCase

from enum import Enum
from pydantic_core import (
    core_schema,
    SchemaValidator,
    ValidationError,
    PydanticCustomError,
)


class DataValidationTest(SimpleTestCase):
    def test_simple_required_data_validation(self):
        validator = SchemaValidator(
            core_schema.typed_dict_schema(
                fields={
                    "field_a": core_schema.typed_dict_field(
                        core_schema.str_schema(),
                        validation_alias="input_a",
                    ),
                    "field_b": core_schema.typed_dict_field(core_schema.bool_schema()),
                    "field_c": core_schema.typed_dict_field(core_schema.int_schema()),
                },
            )
        )

        with self.assertRaises(ValidationError) as cm:
            validator.validate_python({"a": "hello"})

        exc = cm.exception
        errors = exc.errors()
        self.assertEqual(len(errors), 3)
        self.assertEqual(errors[0]["msg"], "Field required")
        self.assertEqual(errors[0]["loc"], ("input_a",))

        data = validator.validate_python(
            {
                "input_a": "",
                "field_b": 0,
                "field_c": "42",
            }
        )
        self.assertEqual(data.get("field_a", None), "")
        self.assertEqual(data.get("field_b", None), False)
        self.assertEqual(data.get("field_c", None), 42)

    def test_simple_optional_data_validation(self):
        validator = SchemaValidator(
            core_schema.typed_dict_schema(
                fields={
                    "field_a": core_schema.typed_dict_field(
                        core_schema.str_schema(),
                        validation_alias="input_a",
                        required=False,
                    ),
                    "field_b": core_schema.typed_dict_field(
                        core_schema.bool_schema(),
                        required=False,
                    ),
                },
            )
        )
        data = validator.validate_python({"a": "hello"})

        self.assertEqual(len(data.keys()), 0)

    def test_simple_default_optional_data_validation(self):
        validator = SchemaValidator(
            core_schema.typed_dict_schema(
                fields={
                    "field_a": core_schema.typed_dict_field(
                        core_schema.str_schema(),
                        required=False,
                    ),
                    "field_b": core_schema.typed_dict_field(
                        core_schema.with_default_schema(
                            core_schema.int_schema(),
                            default=None,
                        )
                    ),
                    "field_c": core_schema.typed_dict_field(
                        core_schema.with_default_schema(
                            core_schema.int_schema(),
                            default="wrong",
                            validate_default=False,
                        )
                    ),
                },
            )
        )
        data = validator.validate_python({"a": "hello"})

        self.assertEqual(len(data.keys()), 2)
        self.assertIsNone(data.get("field_a", None))
        self.assertIsNone(data.get("field_b", None))
        self.assertEqual(data.get("field_c", None), "wrong")

    def test_simple_lt_data_validation(self):
        validator = SchemaValidator(
            core_schema.typed_dict_schema(
                fields={
                    "field_c": core_schema.typed_dict_field(core_schema.int_schema(lt=10)),
                },
            )
        )

        with self.assertRaises(ValidationError) as cm:
            data = validator.validate_python({"field_c": "42"})

        exc = cm.exception
        errors = exc.errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["msg"], "Input should be less than 10")

        data = validator.validate_python({"field_c": "9"})
        self.assertEqual(data.get("field_c", None), 9)

    def test_custom_error_data_validation(self):
        def fn(x):
            if x == 2:
                raise PydanticCustomError(
                    "not_2",
                    "Expected any value except 2, got '{wrong_value}'",
                    {"wrong_value": x},
                )
            return x + 10

        validator = SchemaValidator(
            core_schema.typed_dict_schema(
                fields={
                    "field_c": core_schema.typed_dict_field(
                        core_schema.no_info_after_validator_function(
                            schema=core_schema.int_schema(lt=10),
                            function=fn,
                        )
                    ),
                },
            )
        )

        # Value greather than 10: doesnt pass the schema validation
        with self.assertRaises(ValidationError) as cm:
            data = validator.validate_python({"field_c": "17"})

        exc = cm.exception
        errors = exc.errors()
        self.assertEqual(len(errors), 1)

        # Value less than 10: goes through our fn and returns the new value
        data = validator.validate_python({"field_c": "7"})
        self.assertEqual(data.get("field_c", None), 17)

        # Value less than 10 but rejected by our fn: returns the error
        with self.assertRaises(ValidationError) as cm:
            data = validator.validate_python({"field_c": "2"})

        exc = cm.exception
        errors = exc.errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["msg"], "Expected any value except 2, got '2'")

    def test_enum_data_validation(self):
        class Values(Enum):
            VALUE_A = "a"
            VALUE_B = "b"

        validator = SchemaValidator(
            core_schema.typed_dict_schema(
                fields={
                    "field_a": core_schema.typed_dict_field(
                        core_schema.enum_schema(Values, list(Values.__members__.values()), sub_type="str"),
                    ),
                },
            )
        )
        with self.assertRaises(ValidationError) as cm:
            data = validator.validate_python({"field_a": "test"})

        exc = cm.exception
        errors = exc.errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["msg"], "Input should be 'a' or 'b'")

        data = validator.validate_python({"field_a": "b"})
        self.assertEqual(data.get("field_a", None).value, "b")

    def test_str_choices_data_validation(self):
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

        validator = SchemaValidator(
            core_schema.typed_dict_schema(
                fields={
                    "field_a": core_schema.typed_dict_field(
                        core_schema.no_info_after_validator_function(
                            schema=core_schema.str_schema(),
                            function=validate_choices(["a", "b"]),
                        )
                    ),
                },
            )
        )
        with self.assertRaises(ValidationError) as cm:
            data = validator.validate_python({"field_a": "test"})

        exc = cm.exception
        errors = exc.errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["msg"], "Input should be one of ('a', 'b'), got 'test'")

        data = validator.validate_python({"field_a": "b"})
        self.assertEqual(data.get("field_a", None), "b")

        # with default value
        validator = SchemaValidator(
            core_schema.typed_dict_schema(
                fields={
                    "field_a": core_schema.typed_dict_field(
                        core_schema.with_default_schema(
                            core_schema.no_info_after_validator_function(
                                schema=core_schema.str_schema(),
                                function=validate_choices(["a", "b"]),
                            ),
                            default="c",
                        )
                    ),
                },
            )
        )
        data = validator.validate_python({})
        self.assertEqual(data.get("field_a", None), "c")

        with self.assertRaises(ValidationError) as cm:
            data = validator.validate_python({"field_a": "c"})

        exc = cm.exception
        errors = exc.errors()
        self.assertEqual(len(errors), 1)

    def test_custom_data_validation(self):
        # is_instance_schema, callable_schema,
        class empty:
            pass

        def is_empty(x):
            if x != empty:
                raise PydanticCustomError(
                    "is_empty",
                    "Input should be empty, got '{wrong_value}'",
                    {"wrong_value": x},
                )
            return x

        validator = SchemaValidator(
            core_schema.typed_dict_schema(
                fields={
                    "field_a": core_schema.typed_dict_field(
                        core_schema.no_info_plain_validator_function(
                            function=is_empty,
                        )
                    ),
                },
            )
        )
        with self.assertRaises(ValidationError) as cm:
            data = validator.validate_python({"field_a": "test"})

        exc = cm.exception
        errors = exc.errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["msg"], "Input should be empty, got 'test'")

        data = validator.validate_python({"field_a": empty})
        self.assertEqual(data.get("field_a", None), empty)

    def test_list_data_validation(self):
        validator = SchemaValidator(
            core_schema.typed_dict_schema(
                fields={
                    "events": core_schema.typed_dict_field(
                        core_schema.list_schema(
                            items_schema=core_schema.typed_dict_schema(
                                fields={
                                    "id": core_schema.typed_dict_field(core_schema.str_schema()),
                                }
                            )
                        ),
                    ),
                },
            )
        )

        with self.assertRaises(ValidationError) as cm:
            validator.validate_python({"events": "hello"})

        exc = cm.exception
        errors = exc.errors()
        self.assertEqual(len(errors), 1)

        data = validator.validate_python({"events": []})
        self.assertEqual(data.get("events", None), [])

        with self.assertRaises(ValidationError) as cm:
            data = validator.validate_python({"events": [{}]})

        exc = cm.exception
        errors = exc.errors()
        self.assertEqual(len(errors), 1)

        data = validator.validate_python({"events": [{"id": "1", "nop": 2}]})
        self.assertEqual(len(data.get("events", None)), 1)
        self.assertIsNotNone(data["events"][0].get("id", None))
        self.assertIsNone(data["events"][0].get("nop", None))
