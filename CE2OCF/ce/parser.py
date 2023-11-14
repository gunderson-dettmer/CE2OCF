from __future__ import annotations

from typing import Any, Callable

from CE2OCF.types.dictionaries import ContractExpressVarObj
from CE2OCF.utils.log_utils import logger

from ..types.exceptions import VariableNotFound
from .mocks import *  # noqa

"""
# Var name roots for variables that can have multiple instances, which, due to weirdness of CE naming conventions,
# will need a regex pattern to filter to the desired instance (e.g. if you have four stockholders, you'll want to find
# a ContractExpressVarObj with the following props:

    {
        "name": "Stockholder_S1",
        "repetition": None
        ...
    },
    {
        "name": "Stockholder",
        "repetition": "[2]"
        ...
    },
    {
        "name": "Stockholder",
        "repetition": "[3]"
        ...
    },{
        "name": "Stockholder",
        "repetition": "[4]"
        ...
    }

FURTHER NOTE: Where you specify to repeat a group of fields - e.g. 5 stockholders - it appears that some repetition
fields are not in the export unless you provide an answer - e.g. if you leave the stockholder name blank for stockholder
5, you won't see this value obj:

    {
        "name": "Stockholder",
        "repetition": "[5]"
        "values":[]
    }

Instead, the obj with "name" of "Stockholder" and "repetition" value of "[5]" just won't be there at all. Fun stuff,
right?

"""


# CE Utility Functions #################################################################################################
#                                                                                                                      #
# These functions help us work with CE's JSON-based values in the datasheetItems field of their Contract objs.         #
# They store data in a sorta weird, flat format, even for nested and related objects, so it takes some processing      #
# to group fields together for related objects (e.g. get all stockholder-related fields for all stockholders...        #
# this requires traversing a list and filtering for "repetition" values)                                               #
#                                                                                                                      #
########################################################################################################################


def is_ce_obj_instance_of_var_with_index(
    ce_obj_var: ContractExpressVarObj,
    name: str = "",
    repetition: int | None = None,
) -> bool:
    """
    Is the ContractExpressVarObj an instance of variable with name of "name"? If optional repetition is passed,
    also check that the ContractExpressVarObj repetition field is a string of form "[{{repetition value}}]"

    :param ce_obj_var: ContractExpressVarObj obj
    :param name: Check that obj has this name field
    :param repetition: If provided, check that obj has name AND has repetition value provided (basically index
                       of 1-indexed list)
    :return: True if obj passes tests or false if it does not.
    """
    matches = ce_obj_var["name"] == name
    if repetition is not None:
        if isinstance(ce_obj_var["repetition"], str):
            matches = matches and int(ce_obj_var["repetition"][1:-1]) == repetition
    return matches


def get_ce_variables(
    name: str,
    ce_jsons: list[ContractExpressVarObj],
    repetition: int | None = None,
) -> list[ContractExpressVarObj]:
    """

    Given a list of ContractExpressVarObjs, filter it to those that have name that matches name exactly and, if optional
    repetition param is set, also have a "repetition" field with a string in form of "[{{repetition}}]"

    :param name: String to match exactly against name fields
    :param ce_jsons: List of ContractExpressVarObjs
    :param repetition: Optional int to match against the repetition field (due to how CE structures data - it sucks :-P)
    :return: List of ContractExpressVarObjs that pass test
    """

    return list(
        filter(
            lambda x: is_ce_obj_instance_of_var_with_index(ce_obj_var=x, name=name, repetition=repetition),
            ce_jsons,
        )
    )


def get_ce_obj_value(ce_obj: ContractExpressVarObj, raw_values_only: bool = False) -> str | list[Any] | None:
    """
    Given a ContractExpressVarObj, get the "value", which SHOULD be the 0th element of an array stored in "values"
    field, though, of course, it's likely some types of questionnaires will have multiple values in the array.

    :param ce_obj: ContractExpressVarObj
    :return: If raw_values_only is True, will return value list. Otherwise, we try to use a convention that generally
             makes sense for CE templates - specifically return value 0 if length is 1, None if length is 0 or
             list if length > 1
    """
    if "values" not in ce_obj or not isinstance(ce_obj["values"], list):
        raise ValueError(f"CE Obj \n{ce_obj}\n is NOT a valid CE object. No values field or values is not a list")

    if raw_values_only:
        return ce_obj["values"]
    else:
        if len(ce_obj["values"]) > 1:
            return ce_obj["values"]
        elif len(ce_obj["values"]) == 1:
            return ce_obj["values"][0]
        else:
            return None


def extract_ce_variable_val(
    ce_var_name: str,
    ce_response_objs: list[ContractExpressVarObj],
    repetition_number: int | None = None,
    static_first_repetition_name_formatter: Callable[[str], str] | None = lambda n: f"{n}_S1",
    fail_on_missing_variable: bool = True,
) -> str | None | list[str]:
    """

    This is our basic building block for fetch variable data from a CE template using their JSON template.
    If you retrieve their questionnaire data via API, the data will be in the form of a list of ContractExpressVarObj
    dictionaries. We have to traverse these jsons to find the value you want. Because of how variable loops are handled
    we need to do a little extra legwork because there can be multiple jsons with same name key. The converse is true...
    sometimes, the template will append a special suffix to a given variable on its first iteration - e.g.
    Address_S1. This appears to happen only sometimes, specifically where you have an option in your template to re-use
    a variable on each repeat. Where you select that option from the start and never fill out values for any loop but
    the first instance, the var name *without* the suffix is used. Where you select a repeat, but you previously
    filled out values for some of the individual repeats, the suffix is appended to the first instance of the var name
    and this json will have a repetition value of null. Subsequent repetitions drop the suffix BUT use a repetition key
    like [2], [3], [4] (yes, a string with brackets like that).

    Args:
        ce_var_name: The string name of the CE template variable you want to get a value for
        ce_response_objs: A list of ContractExpressVarObjs which you can get from their API
        repetition_number: If you're using loops in the template, which loop iteration of this ce_var_name do you want?
        static_first_repetition_name_formatter: As described in the documentation, one way of reducing data entry in a
                                    template is re-using the values from the first repeat of a variable for subsequent
                                    repeats. Our convention is to copy value from repeat 1 into a variable with same
                                    name plus a static suffix '_S1'. Your convention could vary a lot, though, so this
                                    is an optional Callable that takes a string and returns a string. The default
                                    covers our convention where we take the target variable name and add _S1. Provide
                                    a new Callable to do your own mapping or None if you don't want to use this
                                    behavior and want to look up all repetitions with their repetition #.
        fail_on_missing_variable: If set to True, raise a ValueError if length of matching_var_objs is 0 after trying
                                all specified search strategies.

    Returns: The str value retrieved from the ce data or, if the value can't be found, return None if
            fail_on_missing_variable is False or raise ValueError if it's True.

    """

    logger.debug(f"extract_repeated_instance_of_variable() - repetition {repetition_number} for var {ce_var_name}")

    # Depending on the inputs, we'll try different search strategies for the actual variable values:
    search_values: list[tuple[str, int | None]] = []

    if repetition_number is None:
        if static_first_repetition_name_formatter is not None:
            search_values.append((static_first_repetition_name_formatter(ce_var_name), None))
        search_values.append((ce_var_name, None))
    elif isinstance(repetition_number, int):
        if repetition_number <= 0:
            raise ValueError("Repetition number must be None or >= 1")
        elif repetition_number == 1:
            if static_first_repetition_name_formatter is not None:
                search_values.append((static_first_repetition_name_formatter(ce_var_name), None))
            search_values.append((ce_var_name, repetition_number))
        else:
            search_values.append((ce_var_name, repetition_number))
            if static_first_repetition_name_formatter is not None:
                search_values.append((static_first_repetition_name_formatter(ce_var_name), None))

    for name, repetition in search_values:
        matching_var_objs = get_ce_variables(
            ce_jsons=ce_response_objs,
            name=name,
            repetition=repetition,
        )
        if matching_var_objs:
            return get_ce_obj_value(matching_var_objs[0])

    if fail_on_missing_variable:
        raise VariableNotFound(
            f"Could not find variable {ce_var_name} in provided CE data. Check your source data or review the variable "
            f"name."
        )
    return None
