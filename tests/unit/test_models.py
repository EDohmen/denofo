import pytest
from pydantic_core import ValidationError  # Added import

from denofo import models

from denofo.models import (
    AnnotGenome,
    Transcriptome,
    TaxonID,
    PhylogeneticTaxa,
    HomologyFilter,
    SyntenySearch,
    NonCodingHomologs,
    EvolutionaryInformation,
    TranslationalEvidence,
    DeNovoGeneAnnotation,
    TaxIDTranslation,
)
from denofo.choices import (
    AnnotGenomeChoices,
    ORFChoices,
    GeneticContextChoices,
    InputDataChoices,
    TaxSpecificityChoices,
    HomologyDBChoices,
    SeqTypeChoices,
    AnchorChoices,
    TranslationEvidenceChoices,
    ThresholdChoices,
)


# Dummy NCBI taxonomy DB for testing purposes
class DummyNCBITaxDB:
    def get_name_translator(self, names):
        # Only "human" translates to taxID 9606.
        mapping = {"human": [9606]}
        if names[0] in mapping:
            return mapping
        raise KeyError

    def get_taxid_translator(self, ids):
        mapping = {9606: "human"}
        if ids[0] in mapping:
            return mapping
        raise KeyError


# Override check_NCBI_taxDB in TaxonID validator using monkeypatch fixture in tests.
@pytest.fixture(autouse=True)
def patch_ncbi(monkeypatch):
    monkeypatch.setattr(models, "check_NCBI_taxDB", lambda: DummyNCBITaxDB())


# Tests for AnnotGenome
def test_annot_genome_valid():
    # valid: list without unknown combined with others
    instance = AnnotGenome(annotGenomeChoice=[AnnotGenomeChoices.unknown])
    # Should work when only unknown is provided.
    assert instance.annotGenomeChoice == [AnnotGenomeChoices.unknown]

    # Valid: list without unknown at all
    instance = AnnotGenome(annotGenomeChoice=[])
    assert instance.annotGenomeChoice == []


def test_annot_genome_invalid_unknown_combined():
    # invalid: unknown combined with another choice
    with pytest.raises(ValueError) as excinfo:
        AnnotGenome(
            annotGenomeChoice=[AnnotGenomeChoices.unknown, AnnotGenomeChoices.unknown]
        )
    # Although the error message is generic, we check that ValueError was raised.
    assert "Unknown is not allowed" in str(excinfo.value)


# Tests for Transcriptome
def test_transcriptome_valid():
    # Valid transcriptome: if CUSTOM genetic context or ORF, provide corresponding custom fields.
    instance = Transcriptome(
        transContextChoice=[GeneticContextChoices.CUSTOM],
        customGeneticContext=["custom_context"],
        transORFChoice=[ORFChoices.CUSTOM],
        customORF=["custom_orf"],
    )
    assert instance.customGeneticContext == ["custom_context"]
    assert instance.customORF == ["custom_orf"]


def test_transcriptome_missing_customGeneticContext():
    # Missing customGeneticContext when CUSTOM is specified should raise error.
    with pytest.raises(ValidationError) as excinfo:
        Transcriptome(
            transContextChoice=[GeneticContextChoices.CUSTOM],
            transORFChoice=[ORFChoices.CUSTOM],
            customORF=["custom_orf"],
        )
    assert "customGeneticContext is required" in str(excinfo.value)


def test_transcriptome_missing_customORF():
    # Missing customORF when CUSTOM is specified in ORF
    with pytest.raises(ValidationError) as excinfo:
        Transcriptome(
            transContextChoice=[GeneticContextChoices.someCustomChoice]
            if hasattr(GeneticContextChoices, "someCustomChoice")
            else [GeneticContextChoices.CUSTOM],
            customGeneticContext=["custom_context"],
            transORFChoice=[ORFChoices.CUSTOM],
        )
    assert "customORF is required" in str(excinfo.value)


def test_transcriptome_orf_exclusions():
    # Test that mutually exclusive ORF choices raise error.
    # Using two mutually exclusive choices (assuming they are defined).
    with pytest.raises(ValueError) as excinfo:
        Transcriptome(
            transORFChoice=[ORFChoices.highestKoz, ORFChoices.longestORF],
            customORF=["dummy"],
        )
    assert "exclude each other" in str(excinfo.value)

    # Test error when noORF is combined with others.
    with pytest.raises(ValueError) as excinfo:
        Transcriptome(
            transORFChoice=[ORFChoices.noORF, ORFChoices.CUSTOM], customORF=["dummy"]
        )
    assert "noORF is not allowed" in str(excinfo.value)


# Tests for TaxonID
def test_taxon_id_from_name():
    # When taxID is provided as string name.
    # In DummyNCBITaxDB, "human" returns 9606.
    with pytest.warns(TaxIDTranslation) as record:
        instance = TaxonID(taxID="human")
    assert instance.taxID == 9606
    assert any("translated to taxon ID 9606" in str(w.message) for w in record)


def test_taxon_id_from_int():
    # When taxID is provided as integer and exists.
    with pytest.warns(TaxIDTranslation) as record:
        instance = TaxonID(taxID=9606)
    assert instance.taxID == 9606
    assert any("translates to human" in str(w.message) for w in record)


def test_taxon_id_invalid_int():
    # When integer taxID is not present in dummy DB.
    with pytest.raises(ValueError) as excinfo:
        TaxonID(taxID=9999)
    assert "TaxonID not found" in str(excinfo.value)


# Tests for HomologyFilter
def test_homology_filter_valid():
    # Provide valid custom fields.
    instance = HomologyFilter(
        seqType=[SeqTypeChoices.CUSTOM],
        customSeqType=["custom_seq"],
        threshold=[ThresholdChoices.CUSTOM],
        customThreshold=["custom_thresh"],
        thresholdValue=[0.5],
        dataBase=[HomologyDBChoices.CUSTOM],
        customDB=["custom_db"],
    )
    assert instance.customSeqType == ["custom_seq"]


def test_homology_filter_missing_custom_fields():
    # Missing customSeqType
    with pytest.raises(ValidationError) as excinfo:
        HomologyFilter(
            seqType=[SeqTypeChoices.CUSTOM],
            threshold=[ThresholdChoices.CUSTOM],
            customThreshold=["custom_thresh"],
            thresholdValue=[0.5],
            dataBase=[HomologyDBChoices.CUSTOM],
            customDB=["custom_db"],
        )
    assert "customSeqType is required" in str(excinfo.value)

    # Missing customThreshold
    with pytest.raises(ValidationError) as excinfo:
        HomologyFilter(
            seqType=[],
            threshold=[ThresholdChoices.CUSTOM],
            thresholdValue=[0.5],
            dataBase=[],
        )
    assert "customThreshold is required" in str(excinfo.value)

    # Incorrect thresholdValue length
    with pytest.raises(ValidationError) as excinfo:
        HomologyFilter(
            seqType=[],
            threshold=[ThresholdChoices.COVERAGE],
            thresholdValue=[],
            dataBase=[],
        )
    # Incorrect thresholdValue length
    with pytest.raises(ValidationError) as excinfo:
        HomologyFilter(
            seqType=[],
            threshold=[ThresholdChoices.COVERAGE],
            thresholdValue=[0.4, 0.2],
            dataBase=[],
        )
    # This test may not trigger if no custom threshold is provided.
    # So we test with a mismatch scenario:
    with pytest.raises(ValidationError) as excinfo:
        HomologyFilter(
            seqType=[],
            threshold=[ThresholdChoices.CUSTOM, ThresholdChoices.COVERAGE],
            customThreshold=["custom1"],
            thresholdValue=[0.5],
            dataBase=[HomologyDBChoices.CUSTOM],
            customDB=["custom_db"],
        )
    assert "Number of threshold values must match number of threshold choices" in str(
        excinfo.value
    )

    # Missing customDB
    with pytest.raises(ValidationError) as excinfo:
        HomologyFilter(
            seqType=[],
            threshold=[],
            thresholdValue=[],
            dataBase=[HomologyDBChoices.CUSTOM],
        )
    assert "customDB is required" in str(excinfo.value)


# Tests for SyntenySearch
def test_synteny_search_valid():
    instance = SyntenySearch(
        anchors=[AnchorChoices.CUSTOM],
        customAnchor=["custom_anchor"],
        softwareSyntenySearch=["search_tool"],
    )
    assert instance.customAnchor == ["custom_anchor"]


def test_synteny_search_missing_customAnchor():
    with pytest.raises(ValidationError) as excinfo:
        SyntenySearch(
            anchors=[AnchorChoices.CUSTOM], softwareSyntenySearch=["search_tool"]
        )
    assert "customAnchor is required" in str(excinfo.value)


# Tests for TranslationalEvidence
def test_translational_evidence_valid():
    instance = TranslationalEvidence(
        translationEvidence=[TranslationEvidenceChoices.CUSTOM],
        customTranslationEvidence=["custom_translation"],
    )
    assert instance.customTranslationEvidence == ["custom_translation"]


def test_translational_evidence_missing_custom():
    with pytest.raises(ValidationError) as excinfo:
        TranslationalEvidence(translationEvidence=[TranslationEvidenceChoices.CUSTOM])
    assert "customTranslationEvidence is required" in str(excinfo.value)


# Tests for DeNovoGeneAnnotation
def test_denovo_gene_annotation_valid():
    # Provide all required nested models when using inputData choices.
    annot_genome = AnnotGenome(annotGenomeChoice=[])
    transcriptome = Transcriptome(
        transContextChoice=[],
        transORFChoice=[],
    )
    instance = DeNovoGeneAnnotation(
        inputData=[InputDataChoices.ANNOT_GENOME, InputDataChoices.TRANSCRIPTOME],
        inputAnnotGenome=annot_genome,
        inputTranscriptome=transcriptome,
    )
    assert instance.inputAnnotGenome is not None
    assert instance.inputTranscriptome is not None


def test_denovo_gene_annotation_missing_annotGenome():
    # Missing inputAnnotGenome when required.
    with pytest.raises(ValidationError) as excinfo:
        DeNovoGeneAnnotation(
            inputData=[InputDataChoices.ANNOT_GENOME],
            inputTranscriptome=Transcriptome(transContextChoice=[], transORFChoice=[]),
        )
    assert "AnnotGenome is required" in str(excinfo.value)


def test_denovo_gene_annotation_missing_transcriptome():
    # Missing inputTranscriptome when required.
    with pytest.raises(ValidationError) as excinfo:
        DeNovoGeneAnnotation(
            inputData=[InputDataChoices.TRANSCRIPTOME],
            inputAnnotGenome=AnnotGenome(annotGenomeChoice=[]),
        )
    assert "Transcriptome is required" in str(excinfo.value)


def test_denovo_gene_annotation_missing_customInputData():
    # When CUSTOM inputData is provided, customInputData should be specified.
    with pytest.raises(ValidationError) as excinfo:
        DeNovoGeneAnnotation(
            inputData=[InputDataChoices.CUSTOM],
        )
    assert "customInputData is required" in str(excinfo.value)
