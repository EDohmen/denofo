import argparse
import warnings
from pathlib import Path
from denofo.utils.ncbiTaxDBcheck import check_NCBI_taxDB
from denofo.utils.helpers import infer_format_from_extension
from denofo.converter.convert import (
    convert_to_pickle,
    load_from_pickle,
    convert_to_json,
    load_from_json,
    load_from_fasta,
    annotate_fasta,
    load_from_gff,
    annotate_gff,
    decode_short_str,
    encode_short_str,
)


def main():
    """
    The main function of the program including argument parsing.
    """
    parser = argparse.ArgumentParser(
        description=("Convert a de DeNoFo annotation to a different file format.")
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help=(
            "The path and name of the input file. "
            "This file has to contain the DeNoFo annotation to be converted "
            "to another file format. "
            "If you want to annotate sequences in a FASTA/GFF file, please "
            "provide the FASTA/GFF file to annotate as --add_input parameter."
        ),
        metavar="\b",
    )
    parser.add_argument(
        "-if",
        "--input_format",
        type=str,
        choices=["dngf", "pickle", "fasta", "shortstr", "gff"],
        default="",  # infer from file extension
        help=(
            "The format of the input file. If not provided, the format is "
            "inferred based on the file extension."
        ),
        metavar="\b",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="",  # stdout
        help=(
            "Select the destination for the converted file "
            "(optional). If no output file is specified, the output will be "
            "printed to the console. "
            "If you want to annotate sequences in a FASTA/GFF file, please "
            "select the FASTA/GFF file to annotate as --add_input parameter "
            "and either another file location as --output to keep "
            "the original FASTA/GFF file unchanged (recommended) or select "
            "the same file as --output, which overwrites the original "
            "FASTA/GFF file."
        ),
        metavar="\b",
    )
    parser.add_argument(
        "-of",
        "--output_format",
        type=str,
        choices=["dngf", "pickle", "fasta", "shortstr", "gff"],
        help=(
            "The format of the output file. If not provided, the format is "
            "inferred based on the file extension. output_format is required if "
            "--output is empty (i.e. output is printed to console) or output "
            "file has no known file extension."
        ),
        metavar="\b",
    )
    parser.add_argument(
        "-a",
        "--add_input",
        type=str,
        help=(
            "Select an additional input file if required by the output "
            "format (only for FASTA or GFF). "
            "If the --output file is the same as the --add_input file, "
            "the original FASTA/GFF file will be overwritten with the "
            "annotated version of the file. It is recommended to select a "
            "different --output file to keep the original FASTA/GFF file unchanged."
        ),
        metavar="\b",
    )
    parser.add_argument(
        "-ids",
        "--identifiers",
        type=str,
        help=(
            "Optional file containing sequence identifiers for annotation/"
            "extraction in/from a FASTA/GFF file. "
            "If not provided, all FASTA/GFF entries will be considered. "
            "The file should contain one identifier per line. "
            "In FASTA format, the identifiers are matched with sequence IDs at "
            "the beginning of the fasta headers. In GFF format, existence of "
            "given identifiers is checked in the 9th attributes column."
        ),
        metavar="\b",
    )
    parser.add_argument(
        "-f",
        "--feature",
        type=str,
        default="gene",
        help=(
            "Specify the feature type for GFF annotation/extraction. "
            "Only sequences with this feature type are considered "
            "(default: gene)."
        ),
        metavar="\b",
    )

    # argument parsing and pre-processing
    args = parser.parse_args()

    # Check the NCBI Taxonomy Database
    check_NCBI_taxDB()

    warnings.filterwarnings("ignore")

    if not args.input_format:
        args.input_format = infer_format_from_extension(Path(args.input))
        if not args.input_format:
            raise ValueError(
                "Format couldn't be inferred from the input file extension. "
                "Please provide the input format."
            )
        args.input = Path(args.input)

    if not args.output:
        if not args.output_format:
            raise ValueError(
                "Output format is required if the output is printed to the "
                "console (empty output parameter)."
            )
    else:
        if not args.output_format:
            args.output_format = infer_format_from_extension(Path(args.output))
            if not args.output_format:
                raise ValueError(
                    "Format couldn't be inferred from the output file extension. "
                    "Please provide the output format."
                )
            args.output = Path(args.output)

    if (
        args.output_format == "fasta" or args.output_format == "gff"
    ) and not args.add_input:
        raise ValueError(
            f"Please provide an additional input file (add_inp parameter) for "
            f"conversion to {args.output_format} format."
        )

    # process identifiers
    identifiers = None
    if args.identifiers:
        if Path(args.identifiers).is_file():
            with open(args.identifiers, "r") as infile:
                identifiers = set([line.strip() for line in infile])
        else:
            raise ValueError(f"Identifiers file not found at {args.identifiers}.")

    # load the model
    if args.input_format == "dngf":
        dnga_model = load_from_json(Path(args.input))
    elif args.input_format == "pickle":
        dnga_model = load_from_pickle(Path(args.input))
    elif args.input_format == "shortstr":
        short_str = ""
        with open(Path(args.input), "r") as infile:
            short_str = infile.readline().strip()
        dnga_model = decode_short_str(short_str)
    elif args.input_format == "fasta":
        dnga_model = load_from_fasta(Path(args.input), identifiers)
    elif args.input_format == "gff":
        dnga_model = load_from_gff(Path(args.input), args.feature, identifiers)

    # convert the model to output format
    if args.output_format == "dngf":
        if args.output:
            convert_to_json(dnga_model, Path(args.output))
        else:
            print(convert_to_json(dnga_model))
    elif args.output_format == "pickle":
        if args.output:
            convert_to_pickle(dnga_model, Path(args.output))
        else:
            print(convert_to_pickle(dnga_model))
    elif args.output_format == "fasta":
        if args.output:
            annotate_fasta(
                dnga_model, Path(args.add_input), Path(args.output), identifiers
            )
        else:
            print(annotate_fasta(dnga_model, Path(args.add_input), identifiers))
    elif args.output_format == "gff":
        if args.output:
            annotate_gff(
                dnga_model,
                Path(args.add_input),
                Path(args.output),
                args.feature,
                identifiers,
            )
        else:
            print(
                annotate_gff(
                    dnga_model, Path(args.add_input), None, args.feature, identifiers
                )
            )
    elif args.output_format == "shortstr":
        if args.output:
            with open(args.output, "w") as outfile:
                outfile.write(encode_short_str(dnga_model))
        else:
            print(encode_short_str(dnga_model))


if __name__ == "__main__":
    main()
