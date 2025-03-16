import sys
import pytest
from denofo.converter import converter_cli


# Dummy implementations used for testing.
def dummy_check_NCBI_taxDB():
    pass


def dummy_infer_format_from_extension(path):
    mapping = {
        "input.json": "dngf",
        "output.json": "dngf",
        "input.pkl": "pickle",
        "output.pkl": "pickle",
        "input.txt": "shortstr",
        "output.txt": "shortstr",
        "input.fasta": "fasta",
        "output.fasta": "fasta",
        "input.gff": "gff",
        "output.gff": "gff",
    }
    return mapping.get(path.name, "")


def dummy_load_from_json(path):
    return "dummy_model"


def dummy_load_from_pickle(path):
    return "dummy_model"


def dummy_decode_short_str(short_str):
    return "dummy_model"


def dummy_load_from_fasta(path, identifiers):
    return "dummy_model"


def dummy_load_from_gff(path, feature, identifiers):
    return "dummy_model"


def dummy_convert_to_json(model, outfile=None):
    # If outfile is given, simulate writing to file.
    if outfile:
        with open(outfile, "w") as f:
            f.write("json_output")
    else:
        return "json_output"


def dummy_convert_to_pickle(model, outfile=None):
    if outfile:
        with open(outfile, "w") as f:
            f.write("pickle_output")
    else:
        return "pickle_output"


def dummy_encode_short_str(model):
    return "shortstr_output"


def dummy_annotate_fasta(model, add_input, outfile=None, identifiers=None):
    if outfile:
        with open(outfile, "w") as f:
            f.write("annotated_fasta_output")
    else:
        return "annotated_fasta_output"


def dummy_annotate_gff(
    model, add_input, outfile=None, feature="gene", identifiers=None
):
    if outfile:
        with open(outfile, "w") as f:
            f.write("annotated_gff_output")
    else:
        return "annotated_gff_output"


# Pytest fixture to override external functions before each test.
@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    monkeypatch.setattr(converter_cli, "check_NCBI_taxDB", dummy_check_NCBI_taxDB)
    monkeypatch.setattr(
        converter_cli, "infer_format_from_extension", dummy_infer_format_from_extension
    )
    monkeypatch.setattr(converter_cli, "load_from_json", dummy_load_from_json)
    monkeypatch.setattr(converter_cli, "load_from_pickle", dummy_load_from_pickle)
    monkeypatch.setattr(converter_cli, "decode_short_str", dummy_decode_short_str)
    monkeypatch.setattr(converter_cli, "load_from_fasta", dummy_load_from_fasta)
    monkeypatch.setattr(converter_cli, "load_from_gff", dummy_load_from_gff)
    monkeypatch.setattr(converter_cli, "convert_to_json", dummy_convert_to_json)
    monkeypatch.setattr(converter_cli, "convert_to_pickle", dummy_convert_to_pickle)
    monkeypatch.setattr(converter_cli, "encode_short_str", dummy_encode_short_str)
    monkeypatch.setattr(converter_cli, "annotate_fasta", dummy_annotate_fasta)
    monkeypatch.setattr(converter_cli, "annotate_gff", dummy_annotate_gff)


def run_main_with_args(args_list, monkeypatch):
    # Backup original sys.argv and replace
    original_argv = sys.argv
    sys.argv = args_list
    try:
        converter_cli.main()
    finally:
        sys.argv = original_argv


def test_main_dngf_with_output(tmp_path, monkeypatch):
    # Test dngf conversion when output file is provided.
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text('{"dummy": "input"}')

    args = [
        "converter_cli.py",
        "--input",
        str(input_file),
        "--output",
        str(output_file),
    ]
    run_main_with_args(args, monkeypatch)
    # Check that output file has the expected dummy content.
    result = output_file.read_text()
    assert result == "json_output"


def test_main_dngf_stdout(tmp_path, monkeypatch, capsys):
    # Test dngf conversion when no output file is provided.
    input_file = tmp_path / "input.json"
    input_file.write_text('{"dummy": "input"}')
    args = ["converter_cli.py", "--input", str(input_file), "--output_format", "dngf"]
    run_main_with_args(args, monkeypatch)
    captured = capsys.readouterr().out.strip()
    assert captured == "json_output"


def test_main_pickle_with_output(tmp_path, monkeypatch):
    # Test pickle conversion with output file provided.
    input_file = tmp_path / "input.pkl"
    output_file = tmp_path / "output.pkl"
    input_file.write_text("dummy pickle data")
    args = [
        "converter_cli.py",
        "--input",
        str(input_file),
        "--output",
        str(output_file),
    ]
    run_main_with_args(args, monkeypatch)
    result = output_file.read_text()
    assert result == "pickle_output"


def test_main_shortstr_stdout(tmp_path, monkeypatch, capsys):
    # Test shortstr conversion when no output file is provided.
    input_file = tmp_path / "input.txt"
    input_file.write_text("short_string_input\n")
    args = [
        "converter_cli.py",
        "--input",
        str(input_file),
        "--output_format",
        "shortstr",
    ]
    run_main_with_args(args, monkeypatch)
    captured = capsys.readouterr().out.strip()
    assert captured == "shortstr_output"


def test_main_fasta_without_add_input(tmp_path, monkeypatch):
    # Test that conversion to FASTA raises ValueError if add_input is missing.
    input_file = tmp_path / "input.fasta"
    output_file = tmp_path / "output.fasta"
    input_file.write_text(">dummy\nATCG")
    args = [
        "converter_cli.py",
        "--input",
        str(input_file),
        "--output",
        str(output_file),
        "--output_format",
        "fasta",
    ]
    with pytest.raises(ValueError, match="additional input file"):
        run_main_with_args(args, monkeypatch)


def test_main_gff_without_add_input(tmp_path, monkeypatch):
    # Test that conversion to GFF raises ValueError if add_input is missing.
    input_file = tmp_path / "input.gff"
    output_file = tmp_path / "output.gff"
    input_file.write_text("##gff-version 3\n")
    args = [
        "converter_cli.py",
        "--input",
        str(input_file),
        "--output",
        str(output_file),
        "--output_format",
        "gff",
        "--feature",
        "gene",
    ]
    with pytest.raises(ValueError, match="additional input file"):
        run_main_with_args(args, monkeypatch)


def test_main_fasta_with_add_input(tmp_path, monkeypatch):
    # Test FASTA conversion with add_input provided.
    input_file = tmp_path / "input.fasta"
    add_input_file = tmp_path / "add.fasta"
    output_file = tmp_path / "output.fasta"
    input_file.write_text(">dummy\nATCG")
    add_input_file.write_text(">dummy\nATCG")
    args = [
        "converter_cli.py",
        "--input",
        str(input_file),
        "--output",
        str(output_file),
        "--output_format",
        "fasta",
        "--add_input",
        str(add_input_file),
    ]
    run_main_with_args(args, monkeypatch)
    result = output_file.read_text()
    assert result == "annotated_fasta_output"


def test_main_gff_with_add_input(tmp_path, monkeypatch):
    # Test GFF conversion with add_input provided.
    input_file = tmp_path / "input.gff"
    add_input_file = tmp_path / "add.gff"
    output_file = tmp_path / "output.gff"
    input_file.write_text("##gff-version 3\n")
    add_input_file.write_text("dummy feature")
    args = [
        "converter_cli.py",
        "--input",
        str(input_file),
        "--output",
        str(output_file),
        "--output_format",
        "gff",
        "--add_input",
        str(add_input_file),
        "--feature",
        "gene",
    ]
    run_main_with_args(args, monkeypatch)
    result = output_file.read_text()
    assert result == "annotated_gff_output"
