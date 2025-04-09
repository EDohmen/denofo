from pathlib import Path
from enum import Enum
from typing import Any
from denofo.utils.constants import (
    SUBMODELS,
    INDENT_LVL_DICT,
)


def _turn_value_to_string(val: Any, model_name: str, field_name: str) -> str:
    """
    Turn an element into a string.

    :param val: The element to turn into a string.
    :type val: Any
    :param model_name: The name of the model (necessary for correct indentation level).
    :type model_name: str
    :param field_name: The name of the field (necessary for correct indentation level).
    :type field_name: str
    :return: The element as a string.
    :rtype: str
    """
    val_str = ""
    leading_tab_num = max(
        INDENT_LVL_DICT.get(field_name, 0), INDENT_LVL_DICT.get(model_name, 0)
    )

    if isinstance(val, dict):
        val_str = "\n".join(
            [
                (
                    f"{(leading_tab_num + 1) * '\t'}{k}:\n"
                    f"{_turn_value_to_string(v, new_model, new_field)}"
                )
                for k, v in val.items()
                if v is not None
                and (new_model := k if k in SUBMODELS else model_name)
                and (new_field := k if k not in SUBMODELS else field_name)
            ]
        )
    elif isinstance(val, (list, tuple, set)):
        val_str = "\n".join(
            [_turn_value_to_string(e, model_name, field_name) for e in val]
        )
    elif isinstance(val, Enum):
        val_str = f"{(leading_tab_num + 1) * '\t'}{val.value}"
    else:
        val_str = f"{(leading_tab_num + 1) * '\t'}{val}"

    return val_str


def _get_output_string(
    comparison: list[tuple], mode: str, name1: str, name2: str
) -> str:
    """
    Get the comparison result as a string.

    :param comparison: The comparison input as preprocessed by :func:`denofo.utils.helpers.compare_two_models` .
    :type comparison: list[tuple]
    :param mode: The mode of comparison, either "similarities" or "differences".
    :type mode: str
    :param name1: The display name of the first comparison element.
    :type name1: str
    :param name2: The display name of the second comparison element.
    :type name2: str
    :return: The comparison result as a formatted string.
    :rtype: str
    """
    last_model = ""
    last_field = ""
    last_comparison_type = ""
    output_string = ""
    tab = "\t"
    passed_models = set()

    if mode == "similarities":
        output_string += f"Identical values between {name1} and {name2}:\n\n"
        compare_lst = [elem for elem in comparison if elem[0] == "same"]
    elif mode == "differences":
        output_string += f"Differences between {name1} and {name2}:\n\n"
        compare_lst = [elem for elem in comparison if elem[0] != "same"]

    for elem in compare_lst:
        prefix_string = False
        comparison_type = elem[0]
        model = elem[1]
        field = elem[2]
        val_lst = elem[3:]

        if model != last_model:
            if model not in passed_models and model in SUBMODELS:
                output_string += f"{INDENT_LVL_DICT[model] * '\t'}{model}:\n"
                passed_models.add(model)

            last_model = model
            last_field = ""
            last_comparison_type = ""

        if field != last_field:
            output_string += f"{INDENT_LVL_DICT[field] * tab}{field}:\n"
            last_field = field
            last_comparison_type = ""
        if comparison_type != last_comparison_type:
            prefix_string = True
            last_comparison_type = comparison_type

        leading_tabs = (
            max(INDENT_LVL_DICT.get(field, 0), INDENT_LVL_DICT.get(model, 0)) + 1
        ) * tab
        val_str = _turn_value_to_string(val_lst, model, field)

        if mode == "similarities":
            if comparison_type == "same":
                output_string += f"{val_str}\n"
        elif comparison_type == "diffval":
            prefix_string = (
                f"\n{leading_tabs}differing values in {name1} and {name2}:\n"
                if prefix_string
                else ""
            )
            output_string += f"{prefix_string}{val_str}\n\n"
        elif comparison_type == "2not1":
            prefix_string = (
                f"\n{leading_tabs}values in {name2} but not in {name1}:\n"
                if prefix_string
                else ""
            )
            output_string += f"{prefix_string}{val_str}\n\n"
        elif comparison_type == "1not2":
            prefix_string = (
                f"\n{leading_tabs}values in {name1} but not in {name2}:\n"
                if prefix_string
                else ""
            )
            output_string += f"{prefix_string}{val_str}\n\n"

    return output_string.replace("\n\n\n", "\n\n").strip()


def write_comparison(
    comparison: list[tuple],
    mode: str = "differences",
    output_path: Path | None = None,
    name1: str = "dngf_1",
    name2: str = "dngf_2",
) -> str | None:
    """
    Write the comparison result to the output file.

    :param comparison: The comparison input as preprocessed by :func:`denofo.utils.helpers.compare_two_models` .
    :type comparison: list[tuple]
    :param mode: The mode of comparison, either "similarities" or "differences". Defaults to "differences".
    :type mode: str
    :param output_path: The path to the output file. If None, the result is returned as a string.
    :type output_path: Path | None
    :param name1: The display name of the first comparison element. Defaults to "dngf_1".
    :type name1: str
    :param name2: The display name of the second comparison element. Defaults to "dngf_2".
    :type name2: str
    :return: The comparison result as a string if output_path is None, otherwise None.
    :rtype: str | None
    """
    output_str = _get_output_string(comparison, mode, name1, name2)

    if output_path is not None:
        with open(output_path, "w") as output_file:
            output_file.write(output_str)
    else:
        return output_str
