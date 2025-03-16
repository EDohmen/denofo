from pathlib import Path
from enum import Enum
from typing import Any
from denofo.utils.constants import SUBMODELS, SUBMODEL_FIELDS, FIELDS_OF_LVL1_SUBMODELS


def _turn_value_to_string(val: Any, sep_num: int = 2) -> str:
    """
    Turn an element into a string.

    :param val: The element to turn into a string.
    :type val: Any
    :param sep_num: The number of separators.
    :type sep_num: int
    :return: The element as a string.
    :rtype: str
    """
    val_str = ""
    tab = "\t"
    separator = "\n" + sep_num * tab

    if isinstance(val, dict):
        val_str += separator.join(
            [
                f"{k}: {separator + tab if isinstance(v, dict) else ''}"
                f"{separator + tab if isinstance(v, list) and len(v) > 1 else ''}"
                f"{_turn_value_to_string(v, sep_num=sep_num + 1)}"
                for k, v in val.items()
                if v is not None
            ]
        )
    elif isinstance(val, (list, tuple, set)):
        val_str += separator.join(
            [_turn_value_to_string(e, sep_num=sep_num + 1) for e in val]
        )
    elif isinstance(val, Enum):
        val_str += f"{val.value}"
    else:
        val_str += f"{val}"

    return val_str


def _get_output_string(
    comparison: list[tuple], mode: str, name1: str, name2: str
) -> str:
    """
    Get the comparison result as a string.

    :param comparison: The comparison result.
    :type comparison: list[tuple]
    :return: The comparison result as a string.
    :rtype: str
    """
    last_model = ""
    last_field = ""
    last_comparison_type = ""
    output_string = ""
    tab = "\t"
    sep_num = 1
    passed_models = set()

    if mode == "similarities":
        output_string += f"Identical values between {name1} and {name2}:\n"
        compare_lst = [elem for elem in comparison if elem[0] == "same"]
    elif mode == "differences":
        output_string += f"Differences between {name1} and {name2}:\n"
        compare_lst = [elem for elem in comparison if elem[0] != "same"]

    for elem in compare_lst:
        prefix_string = False
        comparison_type = elem[0]
        model = elem[1]
        field = elem[2]
        val_lst = elem[3:]

        if model != last_model:
            if model not in passed_models:
                if model in SUBMODELS:
                    if SUBMODEL_FIELDS[model] in FIELDS_OF_LVL1_SUBMODELS:
                        sep_num = 1
                    output_string += f"\n{sep_num * tab}{SUBMODEL_FIELDS[model]}:\n"
                    sep_num += 1
                else:
                    output_string += f"\n{model}:\n"
                    sep_num = 1

            last_model = model
            last_field = ""
            last_comparison_type = ""

        if field != last_field:
            if field in FIELDS_OF_LVL1_SUBMODELS:
                sep_num = 1
            output_string += f"\n{sep_num * tab}{field}:\n"
            last_field = field
            last_comparison_type = ""
        if comparison_type != last_comparison_type:
            prefix_string = True
            last_comparison_type = comparison_type

        vals = _turn_value_to_string(val_lst, sep_num=sep_num)
        sep_num += 1

        if mode == "similarities":
            if comparison_type == "same":
                output_string += f"{sep_num * tab}{vals}\n"
        elif comparison_type == "diffval":
            prefix_string = (
                f"\n{sep_num * tab}differing values in {name1} and {name2}:\n"
                if prefix_string
                else ""
            )
            output_string += f"{prefix_string}{sep_num * tab}{vals}\n"
        elif comparison_type == "2not1":
            prefix_string = (
                f"\n{sep_num * tab}values in {name2} but not in {name1}:\n"
                if prefix_string
                else ""
            )
            output_string += f"{prefix_string}{sep_num * tab}{vals}\n"
        elif comparison_type == "1not2":
            prefix_string = (
                f"\n{sep_num * tab}values in {name1} but not in {name2}:\n"
                if prefix_string
                else ""
            )
            output_string += f"{prefix_string}{sep_num * tab}{vals}\n"

        passed_models.add(model)
        sep_num -= 1

    return output_string


def write_comparison(
    comparison: list[tuple],
    mode: str = "differences",
    output_path: Path | None = None,
    name1: str = "dngf_1",
    name2: str = "dngf_2",
) -> str | None:
    """
    Write the comparison result to the output file.

    :param comparison: The comparison result.
    :type comparison: list[tuple]
    :param output_path: The path to the output file. If None, the result is returned as a string.
    :type output_path: Path | None
    :return: The comparison result as a string if output_path is None, otherwise None.
    :rtype: str | None
    """
    output_str = _get_output_string(comparison, mode, name1, name2)

    if output_path is not None:
        with open(output_path, "w") as output_file:
            output_file.write(output_str)
    else:
        return output_str
