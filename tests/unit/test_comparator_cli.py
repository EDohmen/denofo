import sys
import pytest
from denofo.comparator import comparator_cli


# Dummy implementations to override imported functions in comparator_cli.py
def dummy_check_NCBI_taxDB():
    pass


def dummy_load_from_json(path):
    # Return a simple dummy model
    return {"dummy": f"loaded from {path}"}


def dummy_compare_two_models(model1, model2, mode):
    # Return a string that embeds the mode for testing purposes
    return f"compared in {mode}"


def dummy_add_extension(path):
    # Simply return the given path without modification
    return path


def dummy_write_comparison(comparison, mode, output, name1, name2):
    # Return a string that shows how the comparison was "written"
    return f"{name1} vs {name2}: {comparison} (mode: {mode}, output: {output})"


@pytest.fixture(autouse=True)
def patch_helpers(monkeypatch):
    # Patch all dependencies used by main() in comparator_cli.py
    monkeypatch.setattr(comparator_cli, "check_NCBI_taxDB", dummy_check_NCBI_taxDB)
    monkeypatch.setattr(comparator_cli, "load_from_json", dummy_load_from_json)
    monkeypatch.setattr(comparator_cli, "compare_two_models", dummy_compare_two_models)
    monkeypatch.setattr(comparator_cli, "add_extension", dummy_add_extension)
    monkeypatch.setattr(comparator_cli, "write_comparison", dummy_write_comparison)


def run_cli_with_args(args_list):
    # Backup original sys.argv
    orig_argv = sys.argv
    sys.argv = args_list
    try:
        # Call main() function of the cli module
        comparator_cli.main()
    finally:
        sys.argv = orig_argv


def test_prints_to_stdout_when_no_output(monkeypatch, capsys):
    # Test when no -o/--output is provided so the result is printed to stdout.
    test_args = [
        "comparator_cli.py",
        "-i1",
        "dummy1.json",
        "-i2",
        "dummy2.json",
        # use explicit mode differences using an alias; should be normalized to "differences"
        "-m",
        "d",
    ]
    run_cli_with_args(test_args)

    captured = capsys.readouterr().out.strip()
    expected = (
        "dngf_1 vs dngf_2: compared in differences (mode: differences, output: None)"
    )
    assert captured == expected


def test_no_stdout_when_output_provided(monkeypatch, capsys, tmp_path):
    # When -o/--output is provided, nothing is printed to stdout.
    # Create a temporary output file name
    output_file = tmp_path / "out.txt"
    test_args = [
        "comparator_cli.py",
        "-i1",
        "dummy1.json",
        "-i2",
        "dummy2.json",
        "-o",
        str(output_file),
        "-n1",
        "Study_One",
        "-n2",
        "Study_Two",
        "-m",
        "s",  # alias for similarities
    ]
    run_cli_with_args(test_args)

    captured = capsys.readouterr().out.strip()
    # Since output file is provided, main() should not print anything.
    assert captured == ""


def test_mode_aliases(monkeypatch, capsys):
    # Test that different aliases for modes are correctly mapped.
    # Here we test the alias for "similarities", e.g., "sim".
    test_args = [
        "comparator_cli.py",
        "-i1",
        "dummy1.json",
        "-i2",
        "dummy2.json",
        "-m",
        "sim",  # alias for similarities; should be normalized to "similarities"
        "-n1",
        "First",
        "-n2",
        "Second",
    ]
    run_cli_with_args(test_args)

    captured = capsys.readouterr().out.strip()
    expected = (
        "First vs Second: compared in similarities (mode: similarities, output: None)"
    )
    assert captured == expected
