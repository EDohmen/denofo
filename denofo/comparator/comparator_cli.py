import argparse
import warnings
from pathlib import Path
from denofo.converter.convert import load_from_json
from denofo.utils.ncbiTaxDBcheck import check_NCBI_taxDB
from denofo.utils.helpers import compare_two_models, add_extension
from denofo.comparator.compare import write_comparison


def main():
    """
    The main function of the program including argument parsing.
    """
    parser = argparse.ArgumentParser(
        description=("Compare two de novo gene annotation files.")
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        default="differences",
        choices=[
            "differences",
            "d",
            "dif",
            "diff",
            "differ",
            "similarities",
            "s",
            "sim",
            "simi",
            "same",
            "similar",
        ],
        help=(
            "The mode of comparison. "
            "Options: '(d)ifferences' (default) or '(s)imilarities'."
        ),
        metavar="\b",  # don't show capitalised param name and choices in help
    )
    parser.add_argument(
        "-i1",
        "--input1",
        type=Path,
        required=True,
        help="Path to the first dngf file.",
        metavar="\b",
    )
    parser.add_argument(
        "-i2",
        "--input2",
        type=Path,
        required=True,
        help="Path to the second dngf file.",
        metavar="\b",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="",  # stdout
        help=(
            "Path to the output file to store the comparison result. "
            "If not provided, the result will be printed to stdout."
        ),
        metavar="\b",
    )
    parser.add_argument(
        "-n1",
        "--name1",
        type=str,
        default="dngf_1",
        help=(
            "The name of the first dngf file in output. "
            "This can be used to give the compared studies/datasets a name for the output."
            " If the name should contain spaces, please use quotes around the name."
        ),
        metavar="\b",
    )
    parser.add_argument(
        "-n2",
        "--name2",
        type=str,
        default="dngf_2",
        help=(
            "The name of the second dngf file in output. "
            "This can be used to give the compared studies/datasets a name for the output."
            " If the name should contain spaces, please use quotes around the name."
        ),
        metavar="\b",
    )

    args = parser.parse_args()

    # Check the NCBI Taxonomy Database
    check_NCBI_taxDB()

    warnings.filterwarnings("ignore")

    if args.mode in {"d", "dif", "diff", "differ"}:
        args.mode = "differences"
    elif args.mode in {"s", "sim", "simi", "same", "similar"}:
        args.mode = "similarities"

    if args.output:
        output = add_extension(Path(args.output))
    else:
        output = None

    # load the dngf files
    dngf1 = load_from_json(Path(args.input1))
    dngf2 = load_from_json(Path(args.input2))

    # compare the dngf files and write the output
    comparison = compare_two_models(dngf1, dngf2, args.mode)
    outstr = write_comparison(comparison, args.mode, output, args.name1, args.name2)

    # print the output to stdout if no output file is provided
    if not output:
        print(outstr)


if __name__ == "__main__":
    main()
