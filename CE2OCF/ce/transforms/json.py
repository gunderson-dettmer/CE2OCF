from __future__ import annotations

import json
from xml.etree import ElementTree as ET


def convert_ce_answers_xml_to_json_string(xml_data: str | ET.ElementTree) -> str:
    """
    Given CE XML answer export, convert it to JSON format that the API generates.

    :param xml_data: Xml String or ElementTree
    :return: json string
    """

    if isinstance(xml_data, ET.ElementTree):
        root = xml_data
    else:
        element = ET.fromstring(xml_data)
        root = ET.ElementTree(element)

    # Initializing an empty list to hold all variable dictionaries
    json_list = []

    # Iterating over all Variable elements in the XML
    for variable in root.findall("{http://schemas.business-integrity.com/dealbuilder/2006/answers}Variable"):
        # Creating a dictionary for each Variable element

        values = variable.findall("{http://schemas.business-integrity.com/dealbuilder/2006/answers}Value")

        variable_dict = {
            "name": variable.get("Name"),
            "repetition": variable.get("RepeatContext", None),
            "values": [str(value.text) for value in values],
        }

        # Retrieving all Value elements within each Variable element and storing their text in a list

        # Adding the dictionary to the list
        json_list.append(variable_dict)

    # Returning the list as a JSON string
    return json.dumps(json_list, indent=2)
