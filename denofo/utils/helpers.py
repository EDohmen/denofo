import re
from pydantic import BaseModel
from enum import Enum
from types import UnionType, GenericAlias
from collections import Counter
from pathlib import Path
from ast import literal_eval
from denofo.choices import ThresholdChoices
from denofo.utils.constants import ENCODE_DICT, DECODE_DICT, REPLACEMENTS


def different_answers(answer: any, prev_answer: any) -> bool:
    """
    Check if new answer differs from previously given answer.

    :param answer: The answer.
    :type answer: any
    :param prev_answer: The previous answer.
    :type prev_answer: any
    :return: True if the answers are different, False otherwise.
    :rtype: bool
    """
    if isinstance(answer, list) and isinstance(prev_answer, list):
        return Counter(answer) != Counter(prev_answer)

    return answer != prev_answer


def get_model_from_qstack_dict(
    qstack_dict: dict,
    model: BaseModel,
) -> BaseModel:
    """
    Get a BaseModel object from a qstack dictionary (which can contain field
    names and values from other models as well).

    :param qstack_dict: The qstack dictionary. keys = model field names, values = model field values.
    :type qstack_dict: dict
    :param model: The BaseModel object.
    :type model: BaseModel
    :return: The BaseModel object with respective field values.
    :rtype: BaseModel
    """
    model_fields = model.model_fields.keys()
    matching_fields = {k: v for k, v in qstack_dict.items() if k in model_fields and v}
    if len(matching_fields) == 0:
        return None

    return model(**matching_fields)


def add_extension(file_path: Path, extension: str = "dngf") -> Path:
    """
    Add an extension to a file path if it does not already have one.

    :param file_path: The file path.
    :type file_path: Path
    :param extension: The extension to add.
    :type extension: str
    :return: The file path with the extension added.
    :rtype: Path
    """
    if not file_path.suffix:
        file_path = file_path.with_suffix(f".{extension}")

    return file_path


def infer_format_from_extension(file_path: Path) -> str:
    """
    Infer the format of a file based on its extension.

    :param file_path: The file path.
    :type file_path: Path
    :return: The inferred format.
    :rtype: str
    """
    ext_to_format = {
        ".dngf": "dngf",
        ".json": "dngf",
        ".pickle": "pickle",
        ".fasta": "fasta",
        ".fa": "fasta",
        ".fna": "fasta",
        ".faa": "fasta",
        ".txt": "shortstr",
        ".gff": "gff",
        ".gtf": "gff",
    }

    extension = file_path.suffix

    return ext_to_format.get(extension, None)


def diff_two_lists(
    list1: list,
    list2: list,
    model_name: str,
    field_name: str,
    mode: str = "differences",
) -> list:
    """
    Compare two lists.

    :param list1: The first list.
    :type list1: list
    :param list2: The second list.
    :type list2: list
    :return: The comparison result.
    :rtype: list
    """
    diff = []

    set1 = set(list1)
    set2 = set(list2)

    if mode == "similarities":
        diff.extend(
            [("same", model_name, field_name, overlap) for overlap in set1 & set2]
        )
    if mode == "differences":
        diff.extend([("1not2", model_name, field_name, only1) for only1 in set1 - set2])
        diff.extend([("2not1", model_name, field_name, only2) for only2 in set2 - set1])

    return diff


def _merge_thresholds_with_vals(thres_lst: list, thresval_lst: list) -> list:
    """
    Merge threshold types with their respective values.

    :param thres_lst: The list of threshold types.
    :type thres_lst: list
    :param thresval_lst: The list of threshold values.
    :type thresval_lst: list
    :return: The merged list of threshold types and values.
    :rtype: list
    """
    clist = thres_lst.copy()

    if ThresholdChoices.CUSTOM in clist:
        clist.remove(ThresholdChoices.CUSTOM)
    clist = [(threstype, thresval) for threstype, thresval in zip(clist, thresval_lst)]

    return clist


def compare_two_models(
    dngf1: BaseModel,
    dngf2: BaseModel,
    mode: str = "differences",
) -> list[tuple]:
    """
    Compare two BaseModel objects.

    :param dngf1: The first BaseModel object.
    :type dngf1: BaseModel
    :param dngf2: The second BaseModel object.
    :type dngf2: BaseModel
    :param mode: The mode of comparison. Options: 'differences' (default) or 'similarities'.
    :type mode: str
    :param name1: The name of the first BaseModel object in output.
    :type name1: str
    :param name2: The name of the second BaseModel object in output.
    :type name2: str
    :return: The comparison result.
    :rtype: list[tuple[str]]
    """
    comparison = []

    for it1, it2 in zip(dngf1.model_dump().items(), dngf2.model_dump().items()):
        field1, value1 = it1
        field2, value2 = it2
        if isinstance(value1, dict) and isinstance(value2, dict):  # nested models
            model1 = dngf1.__annotations__[field1]
            model2 = dngf2.__annotations__[field2]
            if isinstance(model1, UnionType):
                model1 = model1.__args__[0]
                model2 = model2.__args__[0]

            model1 = model1.model_validate(value1)
            model2 = model2.model_validate(value2)
            comparison.extend(compare_two_models(model1, model2, mode=mode))
        elif (
            field1 == "threshold"
        ):  # special case for mapping threshold metrics to threshold values
            full_list1 = value1 + (
                dngf1.customThreshold if dngf1.customThreshold is not None else []
            )
            full_list2 = value2 + (
                dngf2.customThreshold if dngf2.customThreshold is not None else []
            )
            full_list1 = _merge_thresholds_with_vals(full_list1, dngf1.thresholdValue)
            full_list2 = _merge_thresholds_with_vals(full_list2, dngf2.thresholdValue)

            comp_new = diff_two_lists(
                full_list1, full_list2, dngf1.__class__.__name__, field1, mode=mode
            )

            if mode == "differences":
                to_skip = set()
                for elem in comp_new:
                    threstype, thresval = elem[3]

                    if threstype in to_skip:
                        continue
                    threstypes = [
                        elem[3] for elem in comp_new if elem[3][0] == threstype
                    ]
                    if len(threstypes) > 1:
                        to_skip.add(threstype)
                        thresvals = ", ".join([str(elem[1]) for elem in threstypes])
                        comparison.append(
                            (
                                "diffval",
                                dngf1.__class__.__name__,
                                field1,
                                threstype,
                                thresvals,
                            )
                        )
                    else:
                        comparison.append(elem)

        elif field1 in ("customThreshold", "thresholdValue"):  # see special case above
            continue
        elif value1 == value2 and mode == "similarities" and value1 is not None:
            comparison.append(("same", dngf1.__class__.__name__, field1, value1))
        elif value1 != value2:
            if value1 and not value2:
                comparison.append(("1not2", dngf1.__class__.__name__, field1, value1))
            elif not value1 and value2:
                comparison.append(("2not1", dngf2.__class__.__name__, field2, value2))
            elif isinstance(value1, list) and isinstance(value2, list):
                comparison.extend(
                    diff_two_lists(
                        value1, value2, dngf1.__class__.__name__, field1, mode=mode
                    )
                )
            else:
                comparison.append(
                    ("diffval", dngf1.__class__.__name__, field1, value1, value2)
                )

    return comparison


def _get_index_from_enum_choice(enum_choice: Enum) -> int:
    """
    Get the index of an Enum choice.

    :param enum_choice: The Enum choice.
    :type enum_choice: Enum
    :return: The index of the Enum choice.
    :rtype: int
    """
    enum_order = list(enum_choice.__class__)
    if (
        hasattr(enum_choice.__class__, "CUSTOM")
        and enum_choice == enum_choice.__class__.CUSTOM
    ):
        value_idx = 0
    else:
        value_idx = enum_order.index(enum_choice) + 1

    return value_idx


def get_short_repr(orig_model: BaseModel) -> str:
    """
    Get a short representation string of a BaseModel object.

    :param orig_model: The BaseModel object.
    :type orig_model: BaseModel
    :return: The short representation of the BaseModel object.
    :rtype: str
    """
    model_dict = orig_model.model_dump()
    short_repr = ""
    for field, value in model_dict.items():
        if not value:
            continue
        if field in ENCODE_DICT:
            value_short_repr = ""

            if isinstance(value, dict):  # nested model
                submodel = orig_model.__annotations__[field]
                if isinstance(submodel, UnionType):
                    submodel = submodel.__args__[0]
                value_short_repr += get_short_repr(submodel.validate(value))
            elif isinstance(value, Enum):
                value_idx = _get_index_from_enum_choice(value)
                value_short_repr += str(value_idx)
            elif isinstance(value, list):
                if isinstance(value[0], Enum):
                    for val in value:
                        val_idx = _get_index_from_enum_choice(val)
                        value_short_repr += str(val_idx)
                elif isinstance(value[0], str) or isinstance(value[0], float):
                    vals = ",".join(map(str, value))
                    value_short_repr += f"'[{vals}]'"
            elif (
                isinstance(value, str)
                or isinstance(value, int)
                or isinstance(value, float)
            ):
                value_short_repr += f"'{value}'"
            elif isinstance(value, bool):
                value_short_repr += str(int(value))

            if value_short_repr:
                short_repr += ENCODE_DICT[field]
                short_repr += value_short_repr

    return short_repr


def _process_short_matches(short_matches: list) -> list:
    """
    Process the short matches to translate back to original values.

    :param short_matches: The short matches.
    :type short_matches: list
    :return: The processed short matches.
    :rtype: list
    """
    shrt_mtchs_trns = []
    for match in short_matches:
        if match[0]:  # list values
            pattern = re.compile(r"\[|\]|,")
            ematch = pattern.sub(lambda m: REPLACEMENTS[m.group()], match[0])
            mlst = literal_eval(ematch)
            if isinstance(mlst, list):
                shrt_mtchs_trns.append(mlst)
            else:
                raise ValueError(f"Could not convert to list: {match[0]}")
        elif match[1]:  # single str/int/float values
            if match[1].isdigit():
                shrt_mtchs_trns.append(int(match[1]))
            try:
                shrt_mtchs_trns.append(float(match[1]))
            except ValueError:
                shrt_mtchs_trns.append(match[1])
        elif match[2]:  # enum choices encoded
            field_name = DECODE_DICT[match[2][0]]
            enum_nums = list(map(int, list(match[2][1:])))
            shrt_mtchs_trns.append((field_name, enum_nums))
        elif match[3]:  # single field names encoded
            shrt_mtchs_trns.append(DECODE_DICT[match[3]])

    return shrt_mtchs_trns


def _get_enum_choices_from_num(enum_nums: list, enum_class: Enum) -> Enum:
    """
    Get the Enum choices from their respective numbers.

    :param enum_nums: The list of Enum numbers.
    :type enum_nums: list
    :param enum_class: The Enum class.
    :type enum_class: Enum
    :return: The Enum choices.
    :rtype: Enum
    """
    enum_choices = []
    enum_order = list(enum_class)

    for enum_num in enum_nums:
        if enum_num == 0:
            enum_choices.append(enum_class.CUSTOM)
        else:
            enum_choices.append(enum_order[enum_num - 1])

    return enum_choices


def _fill_model_dict(
    shrt_mtchs_trns: list, model_dict: dict, model: BaseModel
) -> tuple[dict, list]:
    """
    Fill the model dictionary with values from the short representation.

    :param shrt_mtchs_trns: The short matches.
    :type shrt_mtchs_trns: list
    :param model_dict: The model dictionary.
    :type model_dict: dict
    :param model: The BaseModel object.
    :type model: BaseModel
    :return: The model dictionary and the remaining short matches.
    :rtype: tuple[dict, list]
    """
    while shrt_mtchs_trns:
        elem = shrt_mtchs_trns.pop(0)

        if isinstance(elem, tuple):
            enum_choices = None
            field_name = elem[0]

            if field_name not in model.__annotations__:
                return model_dict, [elem] + shrt_mtchs_trns
            enum_class = model.__annotations__[field_name]

            if not isinstance(enum_class, UnionType) and issubclass(enum_class, bool):
                enum_choices = elem[1][0]
            elif not isinstance(enum_class, UnionType) and issubclass(enum_class, Enum):
                enum_choices = _get_enum_choices_from_num(elem[1], enum_class)
                enum_choices = enum_choices[0]
            elif isinstance(enum_class, GenericAlias) or isinstance(
                enum_class, UnionType
            ):
                enum_class = enum_class.__args__[0]
                if isinstance(enum_class, GenericAlias):
                    enum_class = enum_class.__args__[0]
            if not enum_choices:
                enum_choices = _get_enum_choices_from_num(elem[1], enum_class)

            model_dict[field_name] = enum_choices

        elif isinstance(elem, str):
            if elem in model.__annotations__:
                val_type = model.__annotations__[elem]
                if isinstance(val_type, UnionType):
                    val_type = val_type.__args__[0]

                if not isinstance(val_type, GenericAlias) and issubclass(
                    val_type, BaseModel
                ):  # val is BaseModel
                    vdict, shrt_mtchs_trns = _fill_model_dict(
                        shrt_mtchs_trns, {}, val_type
                    )
                    model_dict[elem] = vdict
                else:  # val is not a BaseModel
                    model_dict[elem] = shrt_mtchs_trns.pop(0)
            else:  # field name not in model
                return model_dict, [elem] + shrt_mtchs_trns

    return model_dict, shrt_mtchs_trns


def get_model_from_short_repr(short_repr: str, model: BaseModel) -> BaseModel:
    """
    Get a BaseModel object from a short representation string.

    :param short_repr: The short representation string.
    :type short_repr: str
    :param model: The BaseModel object.
    :type model: BaseModel
    :return: The BaseModel object.
    :rtype: BaseModel
    """
    model_dict = {}

    short_matches = re.findall(
        r"'(\[.*?\])'|'(.*?)'|([A-Za-z$]\d+)|([A-Za-z$])", short_repr
    )
    shrt_mtchs_trns = _process_short_matches(short_matches)

    model_dict, _ = _fill_model_dict(shrt_mtchs_trns, model_dict, model())

    out_model = model(**model_dict)

    return out_model
