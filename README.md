# DENOFO Toolkit

[![Denofo Logo](https://raw.githubusercontent.com/EDohmen/denofo/main/denofo/static/denofo-logo.jpg)](https://github.com/EDohmen/denofo)

Denofo is a toolkit developed for the de novo gene research community. It provides tools for working with a standardized de novo gene annotation format, facilitating the annotation, conversion, and comparison of de novo gene annotations.

## Table of Contents

- [De Novo Gene Annotation Format (DNGF)](#de-novo-gene-annotation-format-dngf)
- [Documentation and User Manual](#documentation)
- [Tools](#tools)
- [Installation](#installation)
  - [Installation with pip](#installation-with-pip)
  - [Installation with uv](#installation-with-uv)
- [Usage](#usage)
- [The NCBI Taxonomy Database](#the-ncbi-taxonomy-database)
- [Contributing, feature requests and bug reports](#contributing-feature-requests-and-bug-reports)
- [Publications and Citation](#publications-and-citation)
- [License](#license)

## De Novo Gene Annotation Format (DNGF)

The Denofo toolkit introduces a standardized annotation format for de novo genes. This format aims to streamline the annotation process and ensure consistency across different studies and methodologies used to detect de novo genes. The *.dngf file extension is used for these annotation files.

## Documentation
For Documentation and Manuals, please visit [https://denofo.readthedocs.io/en/latest/](https://denofo.readthedocs.io/en/latest/).

## Tools

The Denofo toolkit comprises three main tools, each available in both a command-line interface (CLI) and a graphical user interface (GUI):

1.  **denofo-questionnaire:** Interactively guides the user through a series of questions, saving the resulting annotation in a *.dngf file.
2.  **denofo-converter:** Converts annotations between different file types. For example, it can annotate sequences in a *.fasta or *.gff file with an existing *.dngf annotation file using a short string encoding.
3.  **denofo-comparator:** Compares two annotation files, highlighting similarities and differences in methodology.

Both CLI and GUI versions are provided to cater to different user needs and environments. The CLI tools are suitable for remote servers, HPC environments without display, and automated pipelines. The GUI tools offer an intuitive interface for users without extensive command-line experience.

## Installation

> [!CAUTION]
This tool is not yet published on PyPI, but it will be available soon. In the meantime, please use the installation from the local Git repository.

### Prerequisites

*   pip or uv

### Installation with pip

**1. Install from PyPI:**

```bash
pip install denofo
```

**2. Install from the local Git repository:**

```bash
git clone https://github.com/EDohmen/denofo.git
cd denofo
pip install -e .
```

### Installation with uv

**1. Install from PyPI:**
```bash
uv pip install denofo
```

**2. Install from the local Git repository:**

```bash
git clone https://github.com/EDohmen/denofo.git
cd denofo
uv pip install -e .
```

## Usage

After installation, you can access the tools via the command line:


**Graphical User Interfaces (GUI):**

```bash
denofo-questionnaire
denofo-converter
denofo-comparator
```

**Command Line Interfaces (CLI):**

```bash
denofo-questionnaire-cli --help
denofo-converter-cli --help
denofo-comparator-cli --help
```

**If you use uv, you can run any of the above commands with `uv run`:**
```bash
uv run denofo-questionnaire
```

## The NCBI Taxonomy Database

For some parts of the annotation format DENOFO needs access to the NCBI Taxonomy Database
through the ete3 library. When you first run a tool that needs the NCBI Taxonomy Database
(e.g. denofo-questionnaire) and the database could not be found, it will download
and process it, which can take some minutes. This local database version will be used from
now on without additional waiting times.

In case you want to update your local version of the NCBI Taxonomy Database, please run:

```bash
update-ncbi-taxdb
# or for uv
uv run update-ncbi-taxdb
```

## Contributing, feature requests and bug reports

Contributions and feedback are very welcome! We tried our best to make the DENOFO
annotation format and toolkit as open and easily accessible as possible and tested
the toolkit extensively. However, there will always be some bugs on specific platforms
or with specific combinations of hardware/software. Also, some bugs will sneak into the 
codebase over time with changes in our dependencies or features we add.
If you find any bug or have trouble with our toolkit, please reach out to us either
here on GitHub or via email. The more information you can provide about the error or bug,
the faster we will be able to help you or fix it, but it does not matter if you know
exactly what the issue is. We would still like to hear about all problems with DENOFO.

We are fully aware that de novo gene research is a very young and fast-moving field,
where a large variety of methods and terms is used and this makes it difficult to
standardise everything to the satisfaction of everyone. We want to encourage the 
scientific community to discuss here also about all changes or novel developments
of the field and how we can put these in better ways into the annotation format
or the toolkit. If you are missing any features in the DENOFO toolkit that would
make your work easier or would be a great addition in your opinion, please let us 
know and we will try to implement them over time!


## Publications and Citation

**Publications:**
We have two publications linked to our de novo gene annotation format and the DENOFO 
toolkit:

- [DeNoFo: a file format and toolkit for standardised, comparable de novo gene annotation (2025) E. Dohmen, M. Aubel, L. A. Eicholt, P. Roginski, V. Luria, A. Karger, A. Grandchamp; bioRxiv](https://doi.org/10.1101/2025.03.31.644673) An Application Note introducing the 
denofo toolkit
- [De Novo Gene Emergence: Summary, Classification, and Challenges of Current Methods (2025) A. Grandchamp, M. Aubel, L. A. Eicholt, P. Roginski, V. Luria, A. Karger, E. Dohmen; EcoEvoRxiv](https://doi.org/10.32942/X2DP88) A review introducing the concepts and decisions
for the standardised de novo annotation format

**Citation:**
If you used denofo for your work, please cite the [Application Note](https://doi.org/10.1101/2025.03.31.644673) linked above.

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE.
