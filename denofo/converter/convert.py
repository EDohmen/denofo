import pickle
import re
import warnings
from pathlib import Path
from Bio import SeqIO
from denofo.models import DeNovoGeneAnnotation
from denofo.utils.helpers import get_short_repr, get_model_from_short_repr


def convert_to_pickle(
    dnga_model: DeNovoGeneAnnotation, outf: Path | None = None
) -> bytes:
    """
    Convert a DeNovoGeneAnnotation model to a pickle file.

    :param dnga_model: DeNovoGeneAnnotation model to convert
    :type dnga_model: DeNovoGeneAnnotation
    :param outf: output file path, defaults to None
    :type outf: Path, optional
    :return: pickled model
    :rtype: bytes
    """
    if outf:
        with open(outf, "wb") as outfile:
            pickle.dump(dnga_model, outfile)
    return pickle.dumps(dnga_model)


def load_from_pickle(pkl_file: Path) -> DeNovoGeneAnnotation:
    """
    Load a DeNovoGeneAnnotation model from a pickle file.

    :param pkl_file: pickle file path
    :type pkl_file: Path
    :return: DeNovoGeneAnnotation model
    :rtype: DeNovoGeneAnnotation
    """
    with open(pkl_file, "rb") as infile:
        return pickle.load(infile)


def convert_to_json(dnga_model: DeNovoGeneAnnotation, outf: Path | None = None) -> str:
    """
    Convert a DeNovoGeneAnnotation model to a JSON file.

    :param dnga_model: DeNovoGeneAnnotation model to convert
    :type dnga_model: DeNovoGeneAnnotation
    :param outf: output file path, defaults to None
    :type outf: Path, optional
    :return: JSON string
    :rtype: str
    """
    json_str = dnga_model.model_dump_json(exclude_none=True, by_alias=True, indent=2)
    if outf:
        with open(outf, "w") as outfile:
            outfile.write(json_str)
    return json_str


def load_from_json(json_file: Path) -> DeNovoGeneAnnotation:
    """
    Load a DeNovoGeneAnnotation model from a JSON file.

    :param json_file: JSON file path
    :type json_file: Path
    :return: DeNovoGeneAnnotation model
    :rtype: DeNovoGeneAnnotation
    """
    with open(json_file, "r") as infile:
        return DeNovoGeneAnnotation.model_validate_json(infile.read())


def load_from_fasta(
    fasta_file: Path, identifiers: set[str] | None = None
) -> DeNovoGeneAnnotation:
    """
    Load a DeNovoGeneAnnotation model from a FASTA file.

    :param fasta_file: FASTA file path
    :type fasta_file: Path
    :param identifiers: identifiers to filter, defaults to None
    :type identifiers: set[str], optional
    :return: DeNovoGeneAnnotation model
    :rtype: DeNovoGeneAnnotation
    """
    short_strs = set()

    with open(fasta_file, "r") as infile:
        for record in SeqIO.parse(infile, "fasta"):
            if identifiers and record.id not in identifiers:
                continue
            short_str = re.search(
                r'denofo:["\'](.+?)(?=["\'](?: |$))', record.description
            )  # regex to match until first space outside of quotes or end of string
            if short_str:
                short_strs.add(short_str.group(1))

    if len(short_strs) == 0:
        raise ValueError(
            f"No denofo annotation found in the FASTA file"
            f"{' with given identifiers' if identifiers else ''}."
        )
    elif len(short_strs) > 1:
        raise ValueError(
            f"Multiple different denofo annotations found in the FASTA file"
            f"{' with given identifiers' if identifiers else ''}.\n"
            f"The following annotations were found: {short_strs}\n"
        )

    return decode_short_str(short_strs.pop())


def encode_short_str(dnga_model: DeNovoGeneAnnotation) -> str:
    """
    Encode a DeNovoGeneAnnotation model as a short representation string.

    :param dnga_model: DeNovoGeneAnnotation model to encode
    :type dnga_model: DeNovoGeneAnnotation
    :return: short representation string
    :rtype: str
    """
    short_str = get_short_repr(dnga_model)
    return short_str


def decode_short_str(short_str: str) -> DeNovoGeneAnnotation:
    """
    Decode a short representation string into a DeNovoGeneAnnotation model.

    :param short_str: short representation string
    :type short_str: str
    :return: DeNovoGeneAnnotation model
    :rtype: DeNovoGeneAnnotation
    """
    return get_model_from_short_repr(short_str, DeNovoGeneAnnotation)


def annotate_fasta(
    dnga_model: DeNovoGeneAnnotation,
    fasta_file: Path,
    outf: Path | None = None,
    identifiers: set[str] | None = None,
) -> str:
    """
    Annotate a FASTA file with the model short string representation.

    :param dnga_model: DeNovoGeneAnnotation model to annotate with
    :type dnga_model: DeNovoGeneAnnotation
    :param fasta_file: additional input file path
    :type fasta_file: Path
    :param outf: output file path, defaults to None
    :type outf: Path, optional
    :param identifiers: identifiers to filter, defaults to None
    :type identifiers: set[str], optional
    :return: annotated FASTA string, if outf is None
    :rtype: str
    """
    short_str = encode_short_str(dnga_model)
    seqs = []

    with open(fasta_file, "r") as infile:
        for record in SeqIO.parse(infile, "fasta"):
            if identifiers and record.id not in identifiers:
                seqs.append(record)
                continue
            record.description += f' denofo:"{short_str}"'  # attributeName:value according to ncbi or ensemble standards
            seqs.append(record)

    if outf:
        with open(outf, "w") as outfile:
            SeqIO.write(seqs, outfile, "fasta")

    return "\n".join(f">{record.description}\n{record.seq}\n" for record in seqs)


def annotate_gff(
    dnga_model: DeNovoGeneAnnotation,
    gff_file: Path,
    outf: Path | None = None,
    feature: str = "gene",
    identifiers: set[str] | None = None,
) -> str:
    """
    Annotate a GFF file with the model short string representation.

    :param dnga_model: DeNovoGeneAnnotation model to annotate with
    :type dnga_model: DeNovoGeneAnnotation
    :param gff_file: GFF file path
    :type gff_file: Path
    :param outf: output file path, defaults to None
    :type outf: Path, optional
    :param feature: feature to annotate, defaults to "gene"
    :type feature: str, optional
    :param identifiers: identifiers to filter, defaults to None
    :type identifiers: set[str], optional
    :return: annotated GFF string, if outf is None
    :rtype: str
    """
    short_str = encode_short_str(dnga_model)
    outstr = ""

    with open(gff_file, "r") as infile:
        for line in infile:
            if line.startswith("#"):
                outstr += f"{line}\n"
                continue
            fields = line.strip().split("\t")
            if len(fields) < 8 or len(fields) > 9:
                raise ValueError(
                    f"GFF file has {len(fields)} columns. "
                    "Only 8 or 9 columns are allowed."
                )
            if len(fields) == 8:
                warnings.warn(
                    "The line has only 8 columns, if identifiers were "
                    "given, this line will be ignored. Otherwise, the line will be "
                    "annotated if feature matches.\n"
                    f"line: {line}"
                )
                if identifiers:
                    outstr += f"{line}\n"
                    continue
            if fields[2] != feature:
                outstr += f"{line}\n"
                continue
            if identifiers and not any(ident in fields[8] for ident in identifiers):
                outstr += f"{line}\n"
                continue

            prefix = " " if fields[8] else ""
            fields[8] += f'{prefix}denofo "{short_str}";'
            # "; " and 'attrName "attrValue";' according to gff3/gtf standards (see e.g. ensembl)
            cstr = "\t".join(fields)
            outstr += f"{cstr}\n"

    if outf:
        with open(outf, "w") as outfile:
            outfile.write(outstr)

    return outstr


def load_from_gff(
    gff_file: Path, feature: str = "gene", identifiers: set[str] | None = None
) -> DeNovoGeneAnnotation:
    """
    Load a DeNovoGeneAnnotation model from a GFF file.

    :param gff_file: GFF file path
    :type gff_file: Path
    :param feature: feature to load, defaults to "gene"
    :type feature: str, optional
    :param identifiers: identifiers to filter, defaults to None
    :type identifiers: set[str], optional
    :return: DeNovoGeneAnnotation model
    :rtype: DeNovoGeneAnnotation
    """
    short_strs = set()

    with open(gff_file, "r") as infile:
        for line in infile:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            if len(fields) < 9:
                continue
            if fields[2] != feature:
                continue
            if identifiers and not any(ident in fields[8] for ident in identifiers):
                continue
            short_str = re.search(
                r'denofo ["\'](.+?)(?=["\'];)',  # regex to match until first semicolon outside of quotes
                fields[8],
            )
            if short_str:
                short_strs.add(short_str.group(1))

    if len(short_strs) == 0:
        raise ValueError("No denofo annotation found in the GFF file.")
    elif len(short_strs) > 1:
        raise ValueError(
            "Multiple different denofo annotations found in the GFF file.\n"
            f"The following annotations were found: {short_strs}\n"
        )

    return decode_short_str(short_strs.pop())
