import warnings
from typing import Self
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    model_validator,
    field_validator,
    ValidationInfo,
)
from denofo.utils.ncbiTaxDBcheck import check_NCBI_taxDB
from denofo.choices import (
    AnnotGenomeChoices,
    ORFChoices,
    GeneticContextChoices,
    InputDataChoices,
    TaxSpecificityChoices,
    HomologyDBChoices,
    ThresholdChoices,
    SeqTypeChoices,
    AnchorChoices,
    TranslationEvidenceChoices,
)


class TaxIDTranslation(UserWarning):
    """
    Warning raised when a taxon ID is translated to a taxon name or vice versa.
    """

    pass


class ModelValidError(ValueError):
    """
    Error raised when a model validation fails.
    Necessary to ignore field validators when checking only field validators.
    """

    pass


class AnnotGenome(BaseModel):
    annotGenomeChoice: list[AnnotGenomeChoices] = Field(default_factory=list)

    @field_validator("annotGenomeChoice")
    @classmethod
    def annotGenomeChoice_unknown(
        cls, annotGenomeChoice: list[AnnotGenomeChoices], info: ValidationInfo
    ) -> list[AnnotGenomeChoices]:
        if (
            AnnotGenomeChoices.unknown in annotGenomeChoice
            and len(annotGenomeChoice) > 1
        ):
            raise ValueError(
                "Unknown is not allowed in combination with other choices."
            )
        return annotGenomeChoice


class Transcriptome(BaseModel):
    expressionLevel: float | None = Field(default=None)
    transContextChoice: list[GeneticContextChoices] = Field(default_factory=list)
    customGeneticContext: list[str] | None = Field(default=None)
    transORFChoice: list[ORFChoices] = Field(default_factory=list)
    customORF: list[str] | None = Field(default=None)
    transcriptomeInfo: str | None = Field(default=None)

    @field_validator("transORFChoice")
    @classmethod
    def transORFChoice_exclude(
        cls, transORFChoice: list[ORFChoices], info: ValidationInfo
    ) -> list[ORFChoices]:
        excluding_ORFs = [
            ORFChoices.highestKoz,
            ORFChoices.longestORF,
            ORFChoices.firstORF,
        ]
        if len(set(excluding_ORFs) & set(transORFChoice)) > 1:
            raise ValueError(
                "The options 'highest Kozac', 'longest ORF' and 'start first ORF'"
                " exclude each other."
            )

        if ORFChoices.noORF in transORFChoice and len(transORFChoice) > 1:
            raise ValueError("noORF is not allowed in combination with other choices.")

        if ORFChoices.allORF in transORFChoice and len(transORFChoice) > 1:
            raise ValueError("allORF is not allowed in combination with other choices.")

        return transORFChoice

    @model_validator(mode="after")
    def customGeneticContext_required(self) -> Self:
        if (
            self.transContextChoice
            and GeneticContextChoices.CUSTOM in self.transContextChoice
            and self.customGeneticContext is None
        ):
            raise ModelValidError(
                "customGeneticContext is required when transContextChoice is custom."
            )
        return self

    @model_validator(mode="after")
    def customORFChoice_required(self) -> Self:
        if (
            self.transORFChoice
            and ORFChoices.CUSTOM in self.transORFChoice
            and self.customORF is None
        ):
            raise ModelValidError("customORF is required when ORFChoices is CUSTOM")
        return self


class TaxonID(BaseModel):
    taxID: str | int = Field(default="")

    @field_validator("taxID")
    @classmethod
    def taxID_valid(cls, taxID: str | int, info: ValidationInfo) -> str | int:
        entry = taxID
        ncbi = check_NCBI_taxDB()
        if isinstance(taxID, str) and taxID.isdigit():
            taxID = int(taxID)

        if isinstance(taxID, str):
            try:
                name2taxid = ncbi.get_name_translator([taxID])
                taxID = name2taxid[taxID][0]
                warnings.warn(
                    f"{entry} was translated to taxon ID {taxID}.",
                    TaxIDTranslation,
                )
            except KeyError:
                warnings.warn(
                    f"{taxID} not found in NCBI Taxonomy Database! Using as is.",
                    TaxIDTranslation,
                )

        elif isinstance(taxID, int):
            try:
                taxnames = ncbi.get_taxid_translator([taxID])
                taxname = taxnames[taxID]
                warnings.warn(
                    f"{taxID} translates to {taxname}. Using as is.",
                    TaxIDTranslation,
                )
            except KeyError:
                raise ValueError("TaxonID not found in NCBI Taxonomy Database!")

        return taxID


class PhylogeneticTaxa(BaseModel):
    taxSpecificity: TaxSpecificityChoices = Field(
        default=TaxSpecificityChoices.lineageSpecif
    )
    taxonID: TaxonID = Field(default=TaxonID())


class HomologyFilter(BaseModel):
    phylogeneticTaxa: PhylogeneticTaxa | None = Field(default=None)
    seqType: list[SeqTypeChoices] = Field(default_factory=list)
    customSeqType: list[str] | None = Field(default=None)
    structuralSimilarity: str | None = Field(default=None)
    threshold: list[ThresholdChoices] = Field(default_factory=list)
    customThreshold: list[str] | None = Field(default=None)
    thresholdValue: list[float] = Field(default_factory=list)
    dataBase: list[HomologyDBChoices] = Field(default_factory=list)
    customDB: list[str] | None = Field(default=None)

    @model_validator(mode="after")
    def customs_required(self) -> Self:
        num_threshold_choices = (
            len(self.threshold)
            if not self.customThreshold
            else len(self.threshold) - 1 + len(self.customThreshold)
        )

        if (
            self.seqType
            and SeqTypeChoices.CUSTOM in self.seqType
            and self.customSeqType is None
        ):
            raise ModelValidError(
                "customSeqType is required when SeqTypeChoices is CUSTOM"
            )
        if (
            self.threshold
            and ThresholdChoices.CUSTOM in self.threshold
            and self.customThreshold is None
        ):
            raise ModelValidError(
                "customThreshold is required when ThresholdChoices is CUSTOM"
            )
        if len(self.thresholdValue) != num_threshold_choices:
            raise ModelValidError(
                f"Number of threshold values must match number of threshold choices. You got {len(self.thresholdValue)} threshold values for {num_threshold_choices} threshold choices."
            )
        if (
            self.dataBase
            and HomologyDBChoices.CUSTOM in self.dataBase
            and self.customDB is None
        ):
            raise ModelValidError(
                "customDB is required when HomologyDBChoices is CUSTOM"
            )
        return self


class SyntenySearch(BaseModel):
    anchors: list[AnchorChoices] = Field(default_factory=list)
    customAnchor: list[str] | None = Field(default=None)
    softwareSyntenySearch: list[str] | None = Field(default=None)

    @model_validator(mode="after")
    def customAnchor_required(self) -> Self:
        if (
            self.anchors
            and AnchorChoices.CUSTOM in self.anchors
            and self.customAnchor is None
        ):
            raise ModelValidError(
                "customAnchor is required when AnchorChoices is CUSTOM"
            )
        return self


class NonCodingHomologs(BaseModel):
    enablingMutations: bool = Field(default=False)
    synteny: SyntenySearch | None = Field(default=None)


class EvolutionaryInformation(BaseModel):
    selection: str | None = Field(default=None)


class TranslationalEvidence(BaseModel):
    translationEvidence: list[TranslationEvidenceChoices] | None = Field(default=None)
    customTranslationEvidence: list[str] | None = Field(default=None)

    @model_validator(mode="after")
    def customTranslationEvidence_required(self) -> Self:
        if (
            self.translationEvidence
            and TranslationEvidenceChoices.CUSTOM in self.translationEvidence
            and self.customTranslationEvidence is None
        ):
            raise ModelValidError(
                "customTranslationEvidence is required when TranslationEvidenceChoices is CUSTOM"
            )
        return self


class DeNovoGeneAnnotation(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        exclude_none=True,
        title="De Novo Gene Annotation",
    )

    inputData: list[InputDataChoices] = Field(default_factory=list)
    inputAnnotGenome: AnnotGenome | None = Field(default=None)
    inputTranscriptome: Transcriptome | None = Field(default=None)
    customInputData: str | None = Field(default=None)
    evolutionaryInformation: EvolutionaryInformation | None = Field(default=None)
    homologyFilter: HomologyFilter | None = Field(default=None)
    nonCodingHomologs: NonCodingHomologs | None = Field(default=None)
    translationalEvidence: TranslationalEvidence | None = Field(default=None)
    studyURL: list[str] | None = Field(default=None)

    @model_validator(mode="after")
    def inputDataType_required(self) -> Self:
        if (
            InputDataChoices.ANNOT_GENOME in self.inputData
            and self.inputAnnotGenome is None
        ):
            raise ModelValidError(
                "AnnotGenome is required when inputData contains ANNOT_GENOME"
            )
        if (
            InputDataChoices.TRANSCRIPTOME in self.inputData
            and self.inputTranscriptome is None
        ):
            raise ModelValidError(
                "Transcriptome is required when inputData contains TRANSCRIPTOME"
            )
        if InputDataChoices.CUSTOM in self.inputData and (self.customInputData is None):
            raise ModelValidError(
                "customInputData is required if inputData contains CUSTOM"
            )
        return self
