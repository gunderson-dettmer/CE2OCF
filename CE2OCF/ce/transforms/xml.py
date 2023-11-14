"""
These are utility to generate a mock CE XML export (which you get from the web application typically when you
export a questionnaire). Currently not covered by tests.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from enum import Enum

from CE2OCF.types.enums import (
    RepeatableFields,
    map_repeat_variable_names_to_template_choices,
)
from CE2OCF.types.models import Director, Stockholder


def add_param_elem_to_tree(root: ET.Element):
    """
    CE has a bunch of <Parameter> tags that I thought were variables. They seem static (possibly excepting
    db_contract_id)

    :param root:
    :return:
    """
    # Define the elements to be added
    elements = [
        {"Name": "db_contract_id", "Value": "1771616"},
        {"Name": "db_document_restrict_guests", "Value": "none"},
        {"Name": "db_document_restrict_post_approval", "Value": "none"},
        {"Name": "db_implied_alttext", "Value": "_________"},
        {"Name": "db_output_field_brackets", "Value": "[]"},
        {"Name": "db_output_update_fields", "Value": "true"},
        {"Name": "db_profile", "Value": "GD Default"},
        {"Name": "db_questionnaire_complete", "Value": "False"},
        {"Name": "db_questionnaire_complete_compulsory", "Value": "True"},
        {"Name": "db_questionnaire_complete_key", "Value": "True"},
        {"Name": "db_show_all_repeat_buttons", "Value": "first"},
        {
            "Name": "db_template_reference",
            "Value": "Formation Questionnaire (Corporate)",
        },
        {"Name": "db_template_version", "Value": "2021-09-03.1549"},
    ]

    # Add the elements to the root
    for element_data in elements:
        element = ET.SubElement(root, "Parameter", Name=element_data["Name"])
        value_element = ET.SubElement(element, "Value")
        value_element.text = element_data["Value"]

    return root


def create_variable_element(
    name: str,
    value: int | str | Enum | bool | float,
    counter: None | int = None,
    repeat_fields: list[str] = [],
    override_repeat_context: str | None = None,
):
    """

    Annoyingly, not ALL variables follow the _S1 for the first object's var name followed by using name without _S1 PLUS
    a RepeatContext value. DirectorName, for example, JUST uses a RepeatContext, so we need a way to just inject a
    specific RepeatContext

    :param name:
    :param value:
    :param counter:
    :param repeat_fields:
    :param override_repeat_context:
    :return:
    """

    if override_repeat_context is None:
        repeat_names = [
            *(e for e in repeat_fields),
            *list(Stockholder.__fields__.keys()),
            *list(Director.__fields__.keys()),
        ]
        if name in repeat_names:
            # IF this is one of the repeated variables, append '_S1' for first elem and add 'RepeatContext' for
            # subsequent stakeholders
            attrs = {"Name": f"{name}_S1" if counter == 0 else name}
            if counter is not None and counter >= 1:
                attrs["RepeatContext"] = f"[{counter+1}]"
        else:
            attrs = {"Name": name}
    else:
        attrs = {"Name": name, "RepeatContext": override_repeat_context}

    variable_elem = ET.Element("Variable", attrs)
    if isinstance(value, list):
        for v in value:
            value_elem = ET.SubElement(variable_elem, "Value")
            if isinstance(v, RepeatableFields):
                answer_xml_value = map_repeat_variable_names_to_template_choices[v.value]
                value_elem.text = answer_xml_value
            elif isinstance(v, Enum):
                value_elem.text = str(v.value)
            elif isinstance(v, bool):
                value_elem.text = str(v).lower()
            else:
                value_elem.text = str(v)
    else:
        value_elem = ET.SubElement(variable_elem, "Value")
        # Thanks to the odd choices of variable names need to handle this separately

        if isinstance(value, RepeatableFields):
            answer_xml_value = map_repeat_variable_names_to_template_choices[value.value]
            value_elem.text = answer_xml_value
        elif isinstance(value, Enum):
            value_elem.text = str(value.value)
        elif isinstance(value, bool):
            value_elem.text = str(value).lower()
        else:
            value_elem.text = str(value)
    return variable_elem


def convert_pydantic_to_xml_elem(
    elem,
    counter: None | int = None,
    repeat_fields: list[str] = [],
    override_repeat_context: str | None = None,
) -> list[ET.Element]:
    # logger.debug(f"convert_pydantic_to_xml_elem() for type {type(elem)}: {elem}")
    var_elems = []
    for field_name in elem.__fields__:
        field_value = getattr(elem, field_name)
        var_elems.append(
            create_variable_element(field_name, field_value, counter, repeat_fields, override_repeat_context)
        )
    return var_elems


def xml_elements_to_ce_xml_tree(xml_elems: list[ET.Element]):

    assert isinstance(xml_elems, list)
    root = ET.Element("Session")
    root.attrib["xmlns"] = "http://schemas.business-integrity.com/dealbuilder/2006/answers"
    for var_elem in xml_elems:
        assert isinstance(var_elem, ET.Element)
        root.append(var_elem)

    # Add parameter tags
    updated_tree = add_param_elem_to_tree(root)

    return ET.tostring(updated_tree, encoding="unicode")
