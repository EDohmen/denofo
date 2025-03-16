from pathlib import Path
from enum import Enum
from pydantic import BaseModel
from denofo.utils import helpers
import denofo.utils.constants as const

# Setup dummy constants for testing get_short_repr and get_model_from_short_repr
const.ENCODE_DICT = {"a": "a", "b": "b"}
const.DECODE_DICT = {"a": "a", "b": "b"}
const.REPLACEMENTS = {"[": "[", "]": "]", ",": ","}


# --- Dummy Models and Enums for testing ---


class DummyEnum(Enum):
    A = "A"
    B = "B"
    CUSTOM = "CUSTOM"


class DummyModel(BaseModel):
    a: int = 0
    b: str = ""
    c: list[int] = []
    threshold: list = []
    customThreshold: list = None
    thresholdValue: list = []


class SimpleModel(BaseModel):
    inputData: int = 0


# --- Tests ---


def test_different_answers_with_non_lists():
    # Test for basic types
    assert helpers.different_answers(1, 2) is True
    assert helpers.different_answers("foo", "foo") is False


def test_different_answers_with_lists():
    # Same elements different order should not be considered different.
    list1 = [1, 2, 3]
    list2 = [3, 2, 1]
    assert helpers.different_answers(list1, list2) is False

    # Different counts make lists different.
    list3 = [1, 2, 2, 3]
    list4 = [1, 2, 3]
    assert helpers.different_answers(list3, list4) is True


def test_get_model_from_qstack_dict_returns_none_for_no_matches():
    qstack = {"x": 100, "y": "abc"}
    # no field in DummyModel matches x or y
    result = helpers.get_model_from_qstack_dict(qstack, DummyModel)
    assert result is None


def test_get_model_from_qstack_dict_returns_model_with_matching_fields():
    qstack = {"a": 10, "b": "test", "extra": "ignored"}
    model = helpers.get_model_from_qstack_dict(qstack, DummyModel)
    assert isinstance(model, DummyModel)
    assert model.a == 10
    assert model.b == "test"


def test_add_extension_adds_extension_when_missing():
    p = Path("datafile")
    new_p = helpers.add_extension(p, "dngf")
    assert new_p.suffix == ".dngf"


def test_add_extension_keeps_existing_extension():
    p = Path("datafile.txt")
    new_p = helpers.add_extension(p, "dngf")
    assert new_p.name == "datafile.txt"


def test_infer_format_from_extension_known():
    p = Path("file.dngf")
    f_format = helpers.infer_format_from_extension(p)
    assert f_format == "dngf"

    p = Path("file.faa")
    f_format = helpers.infer_format_from_extension(p)
    assert f_format == "fasta"


def test_infer_format_from_extension_unknown():
    p = Path("file.unknown")
    f_format = helpers.infer_format_from_extension(p)
    assert f_format is None


def test_diff_two_lists_differences():
    lst1 = [1, 2, 3]
    lst2 = [2, 3, 4]
    # Using default mode "differences"
    diff = helpers.diff_two_lists(lst1, lst2, "DummyModel", "test_field")
    # Expecting one element in lst1 not in lst2 and one in lst2 not in lst1
    diffs = [d[0] for d in diff]
    assert "1not2" in diffs
    assert "2not1" in diffs


def test_diff_two_lists_similarities():
    lst1 = [1, 2, 3]
    lst2 = [3, 2, 1]
    diff = helpers.diff_two_lists(
        lst1, lst2, "DummyModel", "test_field", mode="similarities"
    )
    # All elements are similar because sets are identical
    norms = [d[0] for d in diff]
    for item in norms:
        assert item == "same"


def test_compare_two_models_basic():
    model1 = DummyModel(
        a=5,
        b="hello",
        c=[1, 2, 3],
        threshold=["a"],
        customThreshold=["x"],
        thresholdValue=[10],
    )
    model2 = DummyModel(
        a=5,
        b="world",
        c=[1, 2, 4],
        threshold=["a"],
        customThreshold=["x"],
        thresholdValue=[10],
    )
    # b and c should be different
    differences = helpers.compare_two_models(model1, model2, mode="differences")
    # Check that there is a diff for field 'b'
    diff_fields = [d[2] for d in differences if d[0] == "diffval"]
    assert "b" in diff_fields
    # Field c differences should trigger list diff
    list_diffs = [d for d in differences if d[0] in ("1not2", "2not1")]
    assert any("c" in d for d in list_diffs)


def test_get_short_repr_and_get_model_from_short_repr():
    # Testing a simple model with one field.
    instance = SimpleModel(inputData=123)
    short = helpers.get_short_repr(instance)
    # Expecting encoded value to contain our dummy encoding from const.ENCODE_DICT.
    assert "A" in short
    # Recover the model from the short representation.
    new_instance = helpers.get_model_from_short_repr(short, SimpleModel)
    assert new_instance.inputData == instance.inputData
