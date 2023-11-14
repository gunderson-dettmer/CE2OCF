import logging
import re
from typing import Callable

from sympy import Float
from sympy.parsing.sympy_parser import parse_expr

logger = logging.getLogger(__name__)


# If we see a string that starts and ends with pipes (and no pipes in between) - trigger template parser
TEMPLATE_EXPRESSION_REGEX = r"^\|([^|]+)\|$"

# Then within the template, we want to find the double moustache groups, do a lookup, and
# replace the var names with resulting values
MUSTACHE_CAPTURE_REGEX = r"({{[\w\s\d_<>\(\)-\.]+}})"

# As a last step, we call eval() on expressions contained inside brackets [...] after all other
# substititions are completed. This is as safe as sympy's parse_exp function... which should be pretty safe unless
# someone runs some kind of exponential math bomb, but that'll just hang your system
EVALUATION_CAPTURE_REGEX = r"\[([^\[|\]]+)\]"


def str_is_template_expression(input_str: str) -> bool:
    """
    Checks if the given string matches the template indicator pattern of enclosing string in pipes.

    Args:
    - input_str (str): The string to be checked.

    Returns:
    - bool: True if the string matches the regex pattern, False otherwise.
    """
    return bool(re.match(TEMPLATE_EXPRESSION_REGEX, input_str))


def eval_compiled_expression(template_str: str, max_digits: int = 10) -> str:
    """
    Using sympy, find all non-nested text enclosed in brackets [...] and runs it through sympy's parser to let us
     perform math in our templates. This is fairly safe as arbitrary code can't be executed, BUT people could run
     malicious math in a template to overload a system - e.g. a trillion to the power of a billion or something
     like that.

    Args:
        template_str: Template string to parse
    max_digits (int): The maximum number of digits in the output (default 10 to match OCF max).

    Returns: Evaluated mathematical exp value as string

    """

    def replacer(match: re.Match) -> str:
        logger.debug(f"Expression resolver for match: {match}")
        expr = match.group(0)[1:-1]
        logger.debug(f"Resulting expression: {expr}")

        try:
            resolved_val = parse_expr(expr)  # noqa
            if isinstance(resolved_val, Float):
                return f"{resolved_val:.{max_digits}g}"
            else:
                return str(resolved_val)
        except Exception as e:
            logger.error(f"Failed to evaluate expression due to unexpected error: {e}")
            resolved_val = f"ERROR evaluating {expr}: {e}"
        return resolved_val  # Want this to go back to string after calcs

    return re.sub(EVALUATION_CAPTURE_REGEX, replacer, template_str)


def replace_mustache_vars(template_str: str, lookup_func: Callable[[str], str]) -> str:
    """
    Replaces mustache-style variables in a given string using the results of the lookup_func.

    Args:
    - template_str (str): The string containing mustache-style variables.
    - lookup_func (Callable[[str, ...], str]): The function to lookup the value of the variable,
      expecting the var name.

    Returns:
    - str: The string with mustache-style variables replaced.
    """

    logger.debug(f"Replace moustache in {template_str}")

    def replacer(match: re.Match) -> str:
        var_name = match.group(0)[2:-2].strip()  # Extract variable name without {{ and }}
        logger.debug(f"Replacer in operation on {var_name}")
        results = lookup_func(var_name)
        logger.debug(f"Lookup results: {results}")
        return str(results)

    return re.sub(MUSTACHE_CAPTURE_REGEX, replacer, template_str)
