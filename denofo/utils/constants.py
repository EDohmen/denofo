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
    "DeNovoGeneAnnotation",
    "AnnotGenome",
    "Transcriptome",
    "PhylogeneticTaxa",
    "HomologyFilter",
    "SyntenySearch",
    "NonCodingHomologs",
    "EvolutionaryInformation",
    "TranslationalEvidence",
}

REPLACEMENTS = {
    "[": '["',
    "]": '"]',
    ",": '","',
}

INDENT_LVL_DICT = {
    "DeNovoGeneAnnotation": 0,
    "inputData": 1,
    "inputAnnotGenome": 2,
    "AnnotGenome": 3,
    "annotGenomeChoice": 3,
    "inputTranscriptome": 2,
    "Transcriptome": 2,
    "expressionLevel": 3,
    "transContextChoice": 3,
    "customGeneticContext": 3,
    "transORFChoice": 3,
    "customORF": 3,
    "transcriptomeInfo": 3,
    "customInputData": 2,
    "nonCodingHomologs": 1,
    "translationalEvidence": 1,
    "taxonID": 2,
    "TaxonID": 2,
    "HomologyFilter": 1,
    "homologyFilter": 1,
    "PhylogeneticTaxa": 2,
    "phylogeneticTaxa": 2,
    "taxSpecificity": 3,
    "taxID": 3,
    "seqType": 2,
    "customSeqType": 2,
    "structuralSimilarity": 2,
    "threshold": 2,
    "customThreshold": 2,
    "thresholdValue": 2,
    "dataBase": 2,
    "customDB": 2,
    "NonCodingHomologs": 1,
    "enablingMutations": 2,
    "synteny": 2,
    "SyntenySearch": 2,
    "anchors": 3,
    "customAnchor": 3,
    "softwareSyntenySearch": 3,
    "EvolutionaryInformation": 1,
    "evolutionaryInformation": 1,
    "selection": 2,
    "TranslationalEvidence": 1,
    "translationEvidence": 2,
    "customTranslationEvidence": 2,
    "studyURL": 1,
}
