"""
What you're probably looking for here is `traverse_datamap()` which takes s pydantic BaseModel, dict
or subclass and then uses it plus our parsing conventions to traverse a CE JSON list and produce
an object that has the same keys as the datamap and the values that result from traversing the datamap.
There are a number of helper functions in here that are used by the capstone function but are not meant
to be called separately (though they could be, I suppose, if that were useful to you).
"""
from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel

from CE2OCF.ce import extract_ce_variable_val
from CE2OCF.datamap import (
    FieldPostProcessorModel,
    OverridableBoolField,
    OverridableFloatField,
    OverridableIntField,
    OverridableStringField,
    RepeatableDataMap,
)
from CE2OCF.types.dictionaries import ContractExpressVarObj
from CE2OCF.types.exceptions import VariableNotFoundError
from CE2OCF.utils.log_utils import logger
from CE2OCF.utils.string_templating_utils import (
    eval_compiled_expression,
    replace_mustache_vars,
    str_is_template_expression,
)


def traverse_field_post_processor_model(
    datamap: FieldPostProcessorModel,
    ce_objs: list[ContractExpressVarObj],
    iteration: int | None = None,
    value_overrides: dict | None = None,
    fail_on_missing_variable: bool = False,
) -> dict[str, Any] | str | list | None:
    result = {}

    logger.debug(f"datamap is FieldPostProcessorModel: {datamap}")
    for field_name, _ in datamap.__fields__.items():
        try:
            value = getattr(datamap, field_name)

            if field_name in datamap.__class__.get_postprocessors():
                logger.debug(f"Field {field_name} exists in field_postprocessors()...")
                resolved_val = traverse_datamap(
                    value,
                    field_name,
                    ce_objs,
                    post_processor=datamap.__class__.get_postprocessors()[field_name],
                    iteration=iteration,
                    value_overrides=value_overrides,
                    fail_on_missing_variable=fail_on_missing_variable,
                )
            else:
                logger.debug(f"No field name {field_name} found in field_postprocessors()...")
                resolved_val = traverse_datamap(
                    value,
                    field_name,
                    ce_objs,
                    iteration=iteration,
                    value_overrides=value_overrides,
                    fail_on_missing_variable=fail_on_missing_variable,
                )

            result[field_name] = resolved_val

        except VariableNotFoundError as e:
            msg = f"traverse_field_post_processor_model() - Variable {field_name} not found: {e}"
            if fail_on_missing_variable:
                raise VariableNotFoundError(msg) from e
            else:
                logger.warning(
                    msg + f" but fail_on_missing_variable is set to False, so return result without {field_name}"
                )

    return result


def lookup_straight_var(
    var_name: str,
    field_name: str | None,
    ce_objs: list[ContractExpressVarObj],
    post_processor: Callable | None = None,
    iteration: int | None = None,
    value_overrides: dict[str, Any] | None = None,
    fail_on_missing_variable: bool = False,
) -> str:
    """
    For typing purposes, created this wrapper around traverse_datamap that should be used where we're doing a lookup
    and are expecting a return type of string.

    Args:
        fail_on_missing_variable:
        var_name:
        field_name:
        ce_objs:
        post_processor:
        iteration:
        value_overrides:

    Returns: String or assertion error thrown

    """

    val = traverse_datamap(
        var_name,
        field_name,
        ce_objs,
        post_processor=post_processor,
        iteration=iteration,
        value_overrides=value_overrides,
        fail_on_missing_variable=fail_on_missing_variable,
    )

    if val is None:
        return ""
    else:
        assert isinstance(val, (str, int))
        return str(val)


def handle_string_datamap(
    datamap: str,
    field_name: str | None,
    ce_objs: list[ContractExpressVarObj],
    post_processor: Callable | None = None,
    iteration: int | None = None,
    value_overrides: dict[str, Any] | None = None,
    fail_on_missing_variable: bool = False,
) -> str:
    # Handle the case where datamap value is a string
    logger.debug(f"Detected terminal datamap leaf with value of {datamap}")
    # First check if we have an override value
    if isinstance(value_overrides, dict) and datamap in value_overrides:
        logger.debug(f"Variable name {datamap} for repetition {iteration} in value override dict")
        result = value_overrides[datamap]
    # If not... we're going to look up value from ce_json list
    else:
        # If we're iterating
        if iteration is not None:
            logger.debug(f"It's an iteration - loop index #{iteration}")
            if str_is_template_expression(datamap):
                logger.debug(f"Detected blueshift expression: {datamap}")
                # If it's a blueshift expression (enclosed by pipes)
                result = eval_compiled_expression(
                    replace_mustache_vars(
                        datamap[1:-1],
                        lambda var_name: lookup_straight_var(
                            var_name,
                            field_name,
                            ce_objs,
                            post_processor=post_processor,
                            iteration=iteration,
                            value_overrides=value_overrides,
                            fail_on_missing_variable=fail_on_missing_variable,
                        ),
                    )
                )
                logger.debug(f"Compiled value: {result}")
            else:
                logger.debug(f"Detected variable name: {datamap}")
                # If we're using reserved word <<LOOP_INDEX>>... drop in iteration index value.
                if datamap == "<<LOOP_INDEX>>":
                    result = iteration
                else:
                    result = extract_ce_variable_val(
                        datamap,
                        ce_objs,
                        repetition_number=iteration,
                        fail_on_missing_variable=fail_on_missing_variable,
                    )
        # Otherwise use standard CE function
        else:
            if datamap == "<<LOOP_INDEX>>":
                msg = "You used reserved variable name <<LOOP_INDEX>> in a non-repeating pattern... can't do that"
                raise ValueError(msg)

            logger.debug("Not an iteration lookup...")
            if str_is_template_expression(datamap):
                logger.debug(f"Detected blueshift expression: {datamap}")
                result = replace_mustache_vars(
                    datamap[1:-1],
                    lambda var_name: lookup_straight_var(
                        var_name,
                        field_name,
                        ce_objs,
                        post_processor=post_processor,
                        iteration=iteration,
                        value_overrides=value_overrides,
                        fail_on_missing_variable=fail_on_missing_variable,
                    ),
                )
            else:
                logger.debug(f"Detected variable name: {datamap}")
                result = extract_ce_variable_val(datamap, ce_objs, fail_on_missing_variable=fail_on_missing_variable)

    logger.debug(f"\tResulting lookup: {result}")
    return result


def handle_list_datamap(
    datamap: list,
    field_name: str | None,
    ce_objs: list[ContractExpressVarObj],
    iteration: int | None = None,
    value_overrides: dict[str, Any] | None = None,
) -> list:
    # Handle the case where datamap is a list

    # If key maps to a list, iterate over the list and resolve contents
    result = []
    for item in datamap:
        resolved_val = traverse_datamap(
            item,
            field_name,
            ce_objs,
            iteration=iteration,
            value_overrides=value_overrides,
        )

        # We don't have OCF lists with nulls or empty objects.
        if resolved_val != {} and resolved_val is not None:
            result.append(resolved_val)

    return result


def handle_dict_datamap(
    datamap: dict[str, Any],
    ce_objs: list[ContractExpressVarObj],
    iteration: int | None = None,
    value_overrides: dict[str, Any] | None = None,
    fail_on_missing_variable: bool = False,
) -> str | float | bool | int | dict[str, Any]:
    # Handle the case where datamap is a dictionary
    if len(datamap.items()) == 1 and "static" in datamap:
        result = datamap["static"]
    else:
        result = {}
        for key, value in datamap.items():
            if isinstance(value, dict) and "val" in value:
                result[key] = value["val"]
            else:
                try:
                    resolved_val = traverse_datamap(
                        value,
                        key,
                        ce_objs,
                        iteration=iteration,
                        value_overrides=value_overrides,
                    )
                    result[key] = resolved_val
                except VariableNotFoundError as e:
                    if fail_on_missing_variable:
                        raise VariableNotFoundError from e
    return result


def handle_overridable_datamap(
    datamap: (OverridableStringField | OverridableFloatField | OverridableBoolField | OverridableIntField),
) -> str | float | bool | int:
    # Handle the case where datamap is an instance of OverridableStringField,
    # OverridableFloatField, OverridableBoolField, OverridableIntField
    logger.debug(
        f"Datamap is RepeatableDataMap, OverridableStringField, "
        f"OverridableFloatField, OverridableBoolField: {datamap}"
    )
    return datamap.static


def handle_repeatable_model_datamap(
    datamap: RepeatableDataMap,
    field_name: str | None,
    ce_objs: list[ContractExpressVarObj],
    value_overrides: dict[str, Any] | None = None,
    fail_on_missing_variable: bool = False,
    drop_null_leaves: bool = True,
) -> list[dict[str, Any] | str | float | int | bool | list | None]:
    if value_overrides is None:
        value_overrides = {}

    logger.debug(f"{datamap} is subclass of RepeatableDataMap")
    result = []
    repeat_count = int(
        lookup_straight_var(
            datamap.repeat_count,
            "repeat_count",
            ce_objs,
            value_overrides=value_overrides,
            fail_on_missing_variable=fail_on_missing_variable,
        )
    )
    logger.debug(f"Detected a repeat variable block with repetition count {repeat_count}")

    repeated_variables = traverse_datamap(
        datamap.repeated_variables,
        "repeated_variables",
        ce_objs,
        value_overrides=value_overrides,
        drop_null_leaves=drop_null_leaves,
    )
    logger.debug(f"Repeated variables: {repeated_variables}")
    if isinstance(repeated_variables, str):
        repeated_variables = [repeated_variables]

    if "repeated_variables" in datamap.__class__.get_postprocessors():
        logger.debug("Post processor defined for repeated_variables")
        repeated_variables = datamap.__class__.get_postprocessors()["repeated_variables"](repeated_variables, ce_objs)

    logger.debug(f"Repeat variables with name after processing: {repeated_variables}")

    repeat_var_lookup = {}
    if isinstance(repeated_variables, list) and len(repeated_variables) > 0:
        repeat_var_lookup = {
            var_name: traverse_datamap(
                var_name,
                "repeated_variables",
                ce_objs,
                value_overrides=value_overrides,
                drop_null_leaves=drop_null_leaves,
            )
            for var_name in repeated_variables
        }
        logger.debug(f"Resulting repeat variable lookup: {repeat_var_lookup}")
    else:
        logger.debug("No repeat variable lookup")

    for i in range(1, repeat_count + 1):
        logger.debug(f"Process obj repetition #{i}")
        result.append(
            traverse_datamap(
                datamap.repeated_pattern,
                field_name,
                ce_objs,
                iteration=i,
                value_overrides={**value_overrides, **repeat_var_lookup},
                drop_null_leaves=drop_null_leaves,
            )
        )
    return result


def handle_base_model_datamap(
    datamap: BaseModel,
    field_name: str | None,
    ce_objs: list[ContractExpressVarObj],
    iteration: int | None = None,
    value_overrides: dict[str, Any] | None = None,
    fail_on_missing_variable: bool = False,
    drop_null_leaves: bool = True,
) -> dict[str, Any]:
    # Handle the case where datamap is an instance of BaseModel
    logger.debug("Datamap is subclass of BaseModel")
    result = {}
    for field_name, _ in datamap.__fields__.items():
        if field_name is not None:
            try:
                logger.debug(f"\tHandle model attr {field_name}")
                value = getattr(datamap, field_name)
                logger.debug(f"\tHandle value: {value}")
                resolved_val = traverse_datamap(
                    value,
                    field_name,
                    ce_objs,
                    iteration=iteration,
                    value_overrides=value_overrides,
                    drop_null_leaves=drop_null_leaves,
                )
                logger.debug(f"\tResolved value: {resolved_val}")

                result[field_name] = resolved_val

            except VariableNotFoundError as e:
                if fail_on_missing_variable:
                    raise VariableNotFoundError from e

    logger.debug(f"\tResulting result: {result}")
    return result


def traverse_datamap(
    datamap: dict[str, Any] | BaseModel | str | list | FieldPostProcessorModel,
    field_name: str | None,
    ce_objs: list[ContractExpressVarObj],
    post_processor: Callable | None = None,
    iteration: int | None = None,
    value_overrides: dict[str, Any] | None = None,
    fail_on_missing_variable: bool = False,
    drop_null_leaves: bool = True,
) -> dict[str, Any] | str | bool | float | int | list | None:
    """
    Recursively traverse the CE-2-OCF datamap and generate the desired object.

    Args:
        drop_null_leaves: If True, don't retain leaf keys where value is null / None
        fail_on_missing_variable: If set to true, if any CE variable is NOT found, the function will
                                raise a ValueError. If set to False, you'll get a None. Helpful for debugging or
                                mission-critical applications where you don't want silent failures where you get a
                                resulting dictionary from the datamap, but it's missing values.
        value_overrides: If this is populated, check to see if leaf value variable name is in this dict, and if so, use
                        value provided in dict. Useful in iterative loops where we want to lock value of subsequent
                        iterations to first loop. Once this has been provided at a level within the datamap, all
                        children of that specific field (if it's a nested dict) will receive the same overrides unless
                        overriden by a child tree.
        iteration: Where we want to parse CE objs for multiple repetitions of the same values, set iteration to indicate
                   which iteration to look at. Warning - once specified, all recursive calls from the first call to have
                   iteration defined will receive the same iteration value.
        datamap (Union[Dict[str, Any], BaseModel]): The current level of the datamap.
        field_name: Field name we're looking for.
        post_processor: A function to process the extracted value for field_name. Expects two args, raw value and the
                        ce_json list
        ce_objs (List[Any]): The list of objects to extract values from.

    Returns:
        Dict[str, Any]: The resulting object.
    """

    logger.debug(f"\n\n* --- Traversing field {field_name} iteration {iteration}")
    logger.debug(f"\tOverrides: {value_overrides}")
    if post_processor is not None:
        logger.debug(f"\tPost processor registered for field {field_name}: {post_processor}")
    else:
        logger.debug(f"\tNo post processor registered for field {field_name}")

    if value_overrides is None:
        value_overrides = {}

    result: str | bool | int | float | dict | list | None = None

    if isinstance(datamap, str):
        logger.debug(f"traverse_datamap() - datamap is instance of str - type {type(datamap)}")
        result = handle_string_datamap(
            datamap,
            field_name,
            ce_objs,
            post_processor=post_processor,
            iteration=iteration,
            value_overrides=value_overrides,
            fail_on_missing_variable=fail_on_missing_variable,
        )
        logger.debug(f"traverse_datamap - result {result}")

    elif isinstance(datamap, (int, float, bool)):
        logger.debug(f"traverse_datamap() - datamap is instance of int, float or bool - type {type(datamap)}")
        result = datamap
    elif isinstance(datamap, list):
        logger.debug(f"traverse_datamap() - datamap is instance of list - type {type(datamap)}")
        result = handle_list_datamap(datamap, field_name, ce_objs, iteration=iteration, value_overrides=value_overrides)
    elif isinstance(datamap, dict):
        logger.debug(f"traverse_datamap() - datamap is instance of dict - type {type(datamap)}")
        result = handle_dict_datamap(
            datamap,
            ce_objs,
            iteration=iteration,
            value_overrides=value_overrides,
            fail_on_missing_variable=fail_on_missing_variable,
        )
    elif isinstance(
        datamap,
        (
            OverridableStringField,
            OverridableFloatField,
            OverridableBoolField,
            OverridableIntField,
        ),
    ):
        logger.debug(f"traverse_datamap() - datamap is instance of override type - type {type(datamap)}")
        result = handle_overridable_datamap(datamap)
        if not isinstance(result, bool):
            result = str(result)

    elif issubclass(datamap.__class__, FieldPostProcessorModel):
        logger.debug(f"traverse_datamap() - datamap is subclass of FieldPostProcessorModel - type {type(datamap)}")

        # RepeatableDataMap is a sublass of FieldPostProcessorModel, so test for that here...
        if issubclass(datamap.__class__, RepeatableDataMap):
            logger.debug(f"{datamap} is subclass of RepeatableDataMap")
            result = handle_repeatable_model_datamap(
                datamap,  # typing has trouble interpreting the implications of issubclass... ignore warning
                field_name,
                ce_objs,
                value_overrides=value_overrides,
                fail_on_missing_variable=fail_on_missing_variable,
                drop_null_leaves=drop_null_leaves,
            )

        # And, if we're not looking at a RepeatableDataMap, use FieldPostProcessorModel regular logic
        else:
            logger.debug("Datamap is not a subclass of RepeatableDataMap")
            result = traverse_field_post_processor_model(
                datamap,
                ce_objs,
                iteration=iteration,
                value_overrides=value_overrides,
                fail_on_missing_variable=fail_on_missing_variable,
            )

    elif issubclass(datamap.__class__, BaseModel):
        logger.debug(f"traverse_datamap() - datamap is subclass of BaseModel - type {type(datamap)}")
        result = handle_base_model_datamap(
            datamap,
            field_name,
            ce_objs,
            iteration=iteration,
            value_overrides=value_overrides,
            fail_on_missing_variable=fail_on_missing_variable,
            drop_null_leaves=drop_null_leaves,
        )
    elif datamap is None:
        logger.warning("Datamap was None")

    else:
        logger.error(f"Unexpected value for datamap: {datamap} {type(datamap)}")

    if post_processor is not None:
        logger.debug(
            f"\tXXX - Datamap with name {field_name} has a postprocessor for this field... with initial value: {result}"
        )
        result = post_processor(result, ce_objs)
        logger.debug(f"Post-processed value: {result}")

    if result == {}:
        return None

    return result
