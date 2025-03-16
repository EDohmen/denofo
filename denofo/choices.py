from enum import Enum


class AnnotGenomeChoices(str, Enum):
    abInitio = "ab initio approach"
    homology = "homology-based approach"
    unknown = "unknown"


class ORFChoices(str, Enum):
    noORF = "no ORF"
    allORF = "all ORF"
    highestKoz = "highest Kozac"
    longestORF = "longest ORF"
    firstORF = "start first ORF"
    long_5_3_ORF = "long 5` 3` ORF"
    CUSTOM = "custom choice"


class GeneticContextChoices(str, Enum):
    intergenic = "intergenic"
    antisense = "antisense"
    intronic = "intronic"
    overlap_gene = "overlap gene"
    CUSTOM = "custom choice"


class InputDataChoices(str, Enum):
    ANNOT_GENOME = "annotated genome"
    TRANSCRIPTOME = "transcriptome"
    CUSTOM = "custom choice"


class TaxSpecificityChoices(str, Enum):
    conditSpecif = "tissue/condition-specific"
    speciesSpecif = "species-specific"
    lineageSpecif = "lineage-specific"


class HomologyDBChoices(str, Enum):
    NCBINR = "NCBI NR"
    REFSEQ = "RefSeq"
    TrEMBL = "UniProtKB/TrEMBL"
    SWISSPROT = "UniProtKB/Swiss-Prot"
    ENA = "ENA (by EMBL-EBI)"
    ENSEMBL = "Ensembl"
    INTERPRO = "InterPro"
    CUSTOM = "custom choice"


class ThresholdChoices(str, Enum):
    EVALUE = "e-value"
    COVERAGE = "coverage [%]"
    CUSTOM = "custom choice"


class SeqTypeChoices(str, Enum):
    PROT_SEQS = "protein sequences"
    DNA = "DNA"
    FRAME6 = "6-frame translation"
    RNA = "RNA"
    NCRNA = "ncRNAs"
    TE = "transposable elements"
    CUSTOM = "custom choice"


class DirectionChoices(str, Enum):
    FORWARD = "forward"
    ANY = "any direction"


class AnchorChoices(str, Enum):
    GENEANCHOR = "gene anchors"
    GENOMEALIGNMENT = "genome alignment"
    CUSTOM = "custom choice"


class TranslationEvidenceChoices(str, Enum):
    MASS_SPEC = "mass spectrometry"
    RIBO_PROFIL = "ribosome profiling"
    PERIODICITY = "periodicity"
    CUSTOM = "custom choice"
