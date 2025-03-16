class GoQBack:
    """
    Class to return if the user wants to go back to the previous question.
    """

    pass


SECTIONS = [
    "input data",
    "homology filter",
    "non-coding homologs",
    "evolutionary info",
    "translational evidence",
    "hyperlinks",
]

ENCODE_DICT = {
    "inputData": "A",
    "inputAnnotGenome": "B",
    "inputTranscriptome": "C",
    "customInputData": "D",
    "evolutionaryInformation": "E",
    "homologyFilter": "F",
    "nonCodingHomologs": "G",
    "translationalEvidence": "H",
    "studyURL": "I",
    "AnnotGenome": "J",
    "Transcriptome": "K",
    "EvolutionaryInformation": "L",
    "HomologyFilter": "M",
    "NonCodingHomologs": "N",
    "TranslationalEvidence": "O",
    "translationEvidence": "P",
    "customTranslationEvidence": "Q",
    "selection": "R",
    "enablingMutations": "S",
    "SyntenySearch": "T",
    "anchors": "U",
    "customAnchor": "V",
    "softwareSyntenySearch": "W",
    "phylogeneticTaxa": "X",
    "seqType": "Y",
    "customSeqType": "Z",
    "threshold": "a",
    "customThreshold": "b",
    "thresholdValue": "c",
    "dataBase": "d",
    "customDB": "e",
    "PhylogeneticTaxa": "f",
    "taxSpecificity": "g",
    "taxonID": "h",
    "TaxonID": "i",
    "taxID": "j",
    "expressionLevel": "k",
    "transContextChoice": "l",
    "customGeneticContext": "m",
    "transORFChoice": "n",
    "customORF": "o",
    "transcriptomeInfo": "p",
    "annotGenomeChoice": "q",
    "synteny": "r",
    "structuralSimilarity": "s",
}

DECODE_DICT = {v: k for k, v in ENCODE_DICT.items()}

FUNCS_TO_MODELS_DICT = {
    "q1": "inputData",
    "q1_1": "annotGenomeChoice",
    "q1_2": "inputTranscriptome",
    "q1_2_1": "expressionLevel",
    "q1_2_2": "transContextChoice",
    "q1_2_3": "customGeneticContext",
    "q1_2_4": "transORFChoice",
    "q1_2_5": "customORF",
    "q1_2_6": "answerTranscriptomeInfo",
    "q1_2_7": "transcriptomeInfo",
    "q1_3": "customInputData",
    "q2": "homologyFilter",
    "q2_1": "phylogeneticTaxa",
    "q2_2": "taxSpecificity",
    "q2_2_1": "taxID",
    "q2_3": "seqType",
    "q2_4": "customSeqType",
    "q2_5_1": "QStructuralSimilarity",
    "q2_5_2": "structuralSimilarity",
    "q2_5_3": "threshold",
    "q2_6": "customThreshold",
    "q2_6_1": "thresholdValue",
    "q2_7": "dataBase",
    "q2_8": "customDB",
    "q3": "nonCodingHomologs",
    "q3_1": "enablingMutations",
    "q3_2": "synteny",
    "q3_3": "anchors",
    "q3_3_1": "customAnchor",
    "q3_3_2": "answerSoftwareSyntenySearch",
    "q3_3_3": "softwareSyntenySearch",
    "q4": "evolutionaryInformation",
    "q4_1": "selection",
    "q5": "translationalEvidence",
    "q5_1": "translationEvidence",
    "q5_2": "customTranslationEvidence",
    "q6": "QstudyURL",
    "q6_1": "studyURL",
}

SUBMODELS = {
    "AnnotGenome",
    "Transcriptome",
    "TaxonID",
    "PhylogeneticTaxa",
    "HomologyFilter",
    "SyntenySearch",
    "NonCodingHomologs",
    "EvolutionaryInformation",
    "TranslationalEvidence",
}

SUBMODEL_FIELDS = {
    "AnnotGenome": "inputAnnotGenome",
    "Transcriptome": "inputTranscriptome",
    "TaxonID": "taxonID",
    "PhylogeneticTaxa": "phylogeneticTaxa",
    "HomologyFilter": "homologyFilter",
    "SyntenySearch": "synteny",
    "NonCodingHomologs": "nonCodingHomologs",
    "EvolutionaryInformation": "evolutionaryInformation",
    "TranslationalEvidence": "translationalEvidence",
}

FIELDS_OF_LVL1_SUBMODELS = {
    "inputAnnotGenome",
    "inputTranscriptome",
    "phylogeneticTaxa",
    "homologyFilter",
    "nonCodingHomologs",
    "evolutionaryInformation",
    "translationalEvidence",
}  # without taxonID and synteny, because these are second level submodels

REPLACEMENTS = {
    "[": '["',
    "]": '"]',
    ",": '","',
}
