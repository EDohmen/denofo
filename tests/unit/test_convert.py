import json
import pickle
from pathlib import Path
import pytest
from Bio import SeqIO
from denofo.converter import convert


# Dummy DeNovoGeneAnnotation for testing
class DummyDeNovoGeneAnnotation:
    def __init__(self, value):
        self.value = value

    def model_dump_json(self, exclude_none=True, by_alias=True, indent=2):
        return json.dumps({"value": self.value}, indent=indent)

    @classmethod
    def model_validate_json(cls, json_str):
        data = json.loads(json_str)
        return cls(data["value"])

    def __eq__(self, other):
        return (
            isinstance(other, DummyDeNovoGeneAnnotation) and self.value == other.value
        )


# Dummy helper functions
def dummy_get_short_repr(dnga_model):
    return f"short_{dnga_model.value}"


def dummy_get_model_from_short_repr(short_str, model_cls):
    # Assume the string is of the form "short_<value>"
    value = short_str.replace("short_", "")
    return model_cls(value)


# Fixture to monkeypatch helper functions in the convert module
@pytest.fixture(autouse=True)
def patch_helpers(monkeypatch):
    monkeypatch.setattr(convert, "get_short_repr", dummy_get_short_repr)
    monkeypatch.setattr(
        convert, "get_model_from_short_repr", dummy_get_model_from_short_repr
    )
    # Also override DeNovoGeneAnnotation with our dummy for testing
    monkeypatch.setattr(convert, "DeNovoGeneAnnotation", DummyDeNovoGeneAnnotation)


@pytest.fixture
def dummy_model():
    return DummyDeNovoGeneAnnotation("dummy")


def test_convert_to_pickle(tmp_path, dummy_model):
    pkl_file = tmp_path / "test.pkl"
    # Write pickle to file and get bytes
    pickled_bytes = convert.convert_to_pickle(dummy_model, outf=pkl_file)
    # Load from file and compare
    loaded_model = convert.load_from_pickle(pkl_file)
    assert loaded_model == dummy_model
    # Also check that pickle.dumps produces the same result
    expected_bytes = pickle.dumps(dummy_model)
    assert pickled_bytes == expected_bytes


def test_convert_to_json(tmp_path, dummy_model):
    json_file = tmp_path / "test.json"
    json_str = convert.convert_to_json(dummy_model, outf=json_file)
    # Load from file and compare
    loaded_model = convert.load_from_json(json_file)
    assert loaded_model == dummy_model
    # Check that JSON string is as expected
    expected_json = dummy_model.model_dump_json(
        exclude_none=True, by_alias=True, indent=2
    )
    assert json.loads(json_str) == json.loads(expected_json)


def test_encode_and_decode_short_str(dummy_model):
    short_str = convert.encode_short_str(dummy_model)
    assert short_str == f"short_{dummy_model.value}"
    decoded_model = convert.decode_short_str(short_str)
    assert decoded_model == dummy_model


def write_fasta_file(path: Path, records: list[str]):
    path.write_text("\n".join(records))


def test_load_from_fasta(tmp_path, dummy_model):
    # Create a FASTA file with a header that contains the denofo tag.
    short_repr = dummy_get_short_repr(dummy_model)
    fasta_content = [
        f'>seq1 denofo:"{short_repr}" some extra info',
        "ATGCGTACGTAGCTAGCTACG",
    ]
    fasta_file = tmp_path / "test.fasta"
    write_fasta_file(fasta_file, fasta_content)

    # Load the model from fasta
    loaded_model = convert.load_from_fasta(fasta_file, identifiers={"seq1"})
    assert loaded_model == dummy_model


def test_load_from_fasta_no_annotation(tmp_path):
    # FASTA file with no denofo annotation
    fasta_content = [
        ">seq1 some header without annotation",
        "ATGCGTACGTAGCTAGCTACG",
    ]
    fasta_file = tmp_path / "no_annotation.fasta"
    write_fasta_file(fasta_file, fasta_content)
    with pytest.raises(ValueError, match="No denofo annotation found"):
        convert.load_from_fasta(fasta_file)


def test_load_from_fasta_multiple_annotations(tmp_path):
    # FASTA file with two different annotations
    fasta_content = [
        '>seq1 denofo:"short_1"',
        "ATGCGTACGTAGCTAGCTACG",
        '>seq2 denofo:"short_2"',
        "CGTACGTAGCTAGCTACGATC",
    ]
    fasta_file = tmp_path / "multiple_annotations.fasta"
    write_fasta_file(fasta_file, fasta_content)
    with pytest.raises(ValueError, match="Multiple different denofo annotations found"):
        convert.load_from_fasta(fasta_file)


def test_annotate_fasta(tmp_path, dummy_model):
    # Create a FASTA file without annotation and then annotate it.
    fasta_content = [
        ">seq1 description",
        "ATGCGTACGTAGCTAGCTACG",
        ">seq2 description",
        "CGTACGTAGCTAGCTACGATC",
    ]
    fasta_file = tmp_path / "input.fasta"
    write_fasta_file(fasta_file, fasta_content)
    out_file = tmp_path / "annotated.fasta"
    annotated_str = convert.annotate_fasta(
        dummy_model, fasta_file, outf=out_file, identifiers=None
    )
    # Parse the annotated fasta using SeqIO to check de novo annotation
    records = []
    with SeqIO.parse(str(out_file), "fasta") as handle:
        records = list(handle)
    for record in records:
        assert f'denofo:"short_{dummy_model.value}"' in record.description
    # Also check the returned string contains the annotation
    assert f'denofo:"short_{dummy_model.value}"' in annotated_str


def test_annotate_gff(tmp_path, dummy_model):
    # Create a minimal GFF file with one gene feature
    gff_lines = [
        "chr1\tsource\tgene\t100\t200\t.\t+\t.\tID=gene1;",
        "chr1\tsource\texon\t150\t180\t.\t+\t.\tParent=gene1;",
    ]
    gff_file = tmp_path / "input.gff"
    gff_file.write_text("\n".join(gff_lines))
    out_file = tmp_path / "annotated.gff"
    annotated_gff = convert.annotate_gff(
        dummy_model, gff_file, outf=out_file, feature="gene", identifiers=None
    )
    # The gene feature line should now contain the appended denofo annotation
    for line in annotated_gff.splitlines():
        if "\tgene\t" in line:
            assert f'denofo "short_{dummy_model.value}"' in line


def test_load_from_gff(tmp_path, dummy_model):
    # Create a GFF file with a gene feature that contains the denofo annotation
    # The annotating format is: denofo "short_str";
    short_repr = dummy_get_short_repr(dummy_model)
    gff_lines = [
        'chr1\tsource\tgene\t100\t200\t.\t+\t.\tID=gene1; note=example; denofo "{}";'.format(
            short_repr
        ),
        "chr1\tsource\texon\t150\t180\t.\t+\t.\tParent=gene1;",
    ]
    gff_file = tmp_path / "input.gff"
    gff_file.write_text("\n".join(gff_lines))
    loaded_model = convert.load_from_gff(gff_file, feature="gene", identifiers=None)
    assert loaded_model == dummy_model
