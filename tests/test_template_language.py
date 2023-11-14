import unittest

from CE2OCF.utils.string_templating_utils import (
    eval_compiled_expression,
    replace_mustache_vars,
    str_is_template_expression,
)


class TestCE2OCFFunctions(unittest.TestCase):
    def math_var_lookup_function(self, key: str) -> str:
        """Sample lookup function for testing."""
        data = {"VAR1": "5", "VAR2": "3", "VAR3": "2"}
        return data.get(key, "")

    def test_str_is_blueshift_expression(self):
        self.assertTrue(str_is_template_expression("|Hello|"))
        self.assertFalse(str_is_template_expression("Hello|"))
        self.assertFalse(str_is_template_expression("|Hello"))
        self.assertFalse(str_is_template_expression("Hello"))
        self.assertFalse(str_is_template_expression("||Hello||"))
        self.assertFalse(str_is_template_expression("|Hello|World|"))

    def test_replace_mustache_vars(self):
        lookup = {"name": "John", "age": "25"}
        lookup_func = lambda var_name: lookup.get(var_name, "")  # noqa

        self.assertEqual(replace_mustache_vars("Hello, {{name}}!", lookup_func), "Hello, John!")
        self.assertEqual(replace_mustache_vars("{{name}} is {{age}} years old.", lookup_func), "John is 25 years old.")
        self.assertEqual(replace_mustache_vars("Hello, World!", lookup_func), "Hello, World!")
        self.assertEqual(replace_mustache_vars("{{unknown_var}}", lookup_func), "")

    def test_eval_compiled_expression(self):
        result = eval_compiled_expression("[5*3]")
        self.assertEqual(result, "15")

    def test_combined_mustache_and_eval(self):
        # Replacing mustache vars
        result = replace_mustache_vars("|Hello {{VAR1}}*{{VAR2}} World|"[1:-1], self.math_var_lookup_function)
        self.assertEqual(result, "Hello 5*3 World")

        # Combining both conventions
        combined = replace_mustache_vars("|[{{VAR1}}*{{VAR2}}]|"[1:-1], self.math_var_lookup_function)
        self.assertEqual(combined, "[5*3]")

        # Evaluating the expression
        result = eval_compiled_expression(combined)
        self.assertEqual(result, "15")

    def test_float_evaluation(self):
        combined = replace_mustache_vars("|[{{VAR1}}*{{VAR3}}]|"[1:-1], self.math_var_lookup_function)
        self.assertEqual(combined, "[5*2]")
        self.assertEqual(eval_compiled_expression(combined), "10")

    def test_mixed_evaluation(self):
        combined = replace_mustache_vars("|{{VAR1}} + [{{VAR2}}*{{VAR3}}]|"[1:-1], self.math_var_lookup_function)
        self.assertEqual(combined, "5 + [3*2]")
        self.assertEqual(eval_compiled_expression(combined), "5 + 6")

    def test_no_evaluation_without_brackets(self):
        # Without brackets
        result = eval_compiled_expression("Hello 5*3 World")
        self.assertEqual(result, "Hello 5*3 World")

        # With just one bracket (should remain unchanged)
        result = eval_compiled_expression("Hello [5*3 World")
        self.assertEqual(result, "Hello [5*3 World")

        # With mismatched brackets
        result = eval_compiled_expression("Hello [5*3] World]")
        self.assertEqual(result, "Hello 15 World]")

        # With empty brackets
        result = eval_compiled_expression("Hello [] World")
        self.assertEqual(result, "Hello [] World")


if __name__ == "__main__":
    unittest.main()
