from pathlib import Path
from denofo.comparator.compare import write_comparison
from enum import Enum
from denofo.comparator.compare import _turn_value_to_string

# patch the constants to avoid submodel complications in tests.
# These constants are otherwise imported from denofo.utils.constants.
import denofo.comparator.compare as cmp_mod

cmp_mod.SUBMODELS = {"ModelA", "ModelB", "ModelC", "ModelX"}
cmp_mod.INDENT_LVL_DICT = {
    "ModelA": 1,
    "ModelB": 1,
    "ModelC": 1,
    "ModelX": 1,
    "fieldX": 2,
    "fieldY": 2,
    "fieldZ": 2,
}


def test_write_comparison_similarities():
    # Test a "similarities" comparison.
    # Each tuple is: (comparison_type, model, field, *values)
    comparison = [
        ("same", "ModelA", "fieldX", "identical value"),
        ("same", "ModelB", "fieldY", {"a": 1, "b": 2}),
    ]
    output = write_comparison(
        comparison, mode="similarities", output_path=None, name1="A", name2="B"
    )
    assert "Identical values between A and B" in output
    assert "ModelA:" in output
    assert "fieldX:" in output
    assert "identical value" in output
    # Check that complex value is represented as string
    assert "a:" in output
    assert "1" in output
    assert "b:" in output
    assert "2" in output


def test_write_comparison_differences():
    # Test a "differences" comparison with different comparison types.
    comparison = [
        ("diffval", "ModelA", "fieldX", "val_in_A", "val_in_B"),
        ("1not2", "ModelB", "fieldY", "only in A"),
        ("2not1", "ModelC", "fieldZ", "only in B"),
    ]
    output = write_comparison(
        comparison, mode="differences", output_path=None, name1="A", name2="B"
    )
    assert "Differences between A and B" in output
    # Each model should be printed with its name:
    assert "ModelA:" in output
    assert "ModelB:" in output
    assert "ModelC:" in output
    # Check that the custom prefixes for each difference type exist
    assert "differing values in A and B:" in output
    assert "values in A but not in B:" in output
    assert "values in B but not in A:" in output
    # Check that provided values appear in the output.
    assert "val_in_A" in output
    assert "val_in_B" in output
    assert "only in A" in output
    assert "only in B" in output


def test_write_comparison_file_output(tmp_path: Path):
    # Test that write_comparison correctly writes to a file when output_path is provided.
    comparison = [
        ("diffval", "ModelX", "fieldX", "val1", "val2"),
    ]
    file_path = tmp_path / "output.txt"
    # Call write_comparison with output_path set
    result = write_comparison(
        comparison, mode="differences", output_path=file_path, name1="A", name2="B"
    )
    # When output_path is provided, the function should return None.
    assert result is None
    # Read back the file and verify its content.
    content = file_path.read_text()
    assert "Differences between A and B" in content
    assert "ModelX:" in content
    assert "fieldX:" in content
    assert "val1" in content
    assert "val2" in content


def test_turn_value_to_string_enum_instance():
    class DummyEnum(Enum):
        VALUE = "dummy_value"

    result = _turn_value_to_string(DummyEnum.VALUE, "modelA", "fieldX")
    assert result.strip() == "dummy_value"
