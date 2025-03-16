import warnings
from typing import Any
from denofo.utils.constants import FUNCS_TO_MODELS_DICT, GoQBack
from denofo.utils.helpers import different_answers, get_model_from_qstack_dict
from denofo.models import (
    AnnotGenome,
    DeNovoGeneAnnotation,
    EvolutionaryInformation,
    HomologyFilter,
    TranslationalEvidence,
    NonCodingHomologs,
    PhylogeneticTaxa,
    SyntenySearch,
    TaxonID,
    Transcriptome,
)
from denofo.choices import (
    AnchorChoices,
    AnnotGenomeChoices,
    GeneticContextChoices,
    HomologyDBChoices,
    InputDataChoices,
    ORFChoices,
    SeqTypeChoices,
    TaxSpecificityChoices,
    ThresholdChoices,
    TranslationEvidenceChoices,
)


class DeNovoQuestionnaire:
    """
    A class to handle the questionnaire for the de novo gene annotation.
    Order of questions is defined here as well as the logic to call the next question
    or go back to the previous question.

    :param user_interface_funcs_dict: The user interface functions dictionary.
    :type user_interface_funcs_dict: dict

    :cvar question_stack: The question stack.
    :vartype question_stack: list[tuple[callable, Any]]
    :cvar current_idx: The current index in the question stack.
    :vartype current_idx: int
    :cvar interface_funcs_dict: The user interface functions dictionary.
    :vartype interface_funcs_dict: dict

    :func call_last_question: Call the previous question in the question stack.
    :func call_next_question: Call the next question in the question stack.
    :func q_end: End of the questionnaire.
    :func start_questionnaire: Start the questionnaire.
    """

    def __init__(self, user_interface_funcs_dict: dict):
        self.question_stack: list[tuple[callable, Any]] = []
        self.current_idx: int = 0
        self.interface_funcs_dict = user_interface_funcs_dict

        self.deNovoGeneAnnotation = self.start_questionnaire()

    def call_last_question(self):
        """
        Call the previous question in the question stack.
        """
        answer = None

        if self.current_idx > 0:
            self.current_idx -= 1
            prev_answer = self.question_stack[self.current_idx][1]
            self.question_stack[self.current_idx][0](prev_answer)
            return

        if self.question_stack:
            answer = self.question_stack[self.current_idx][1]
            self.question_stack[self.current_idx][0](answer)
            return

        self.q1(answer)
        return

    def call_next_question(
        self,
        current_answer: Any,
        this_q: callable,
        next_q: callable,
        prev_answer: list = None,
    ):
        """
        Call the next question in the question stack.

        :param current_answer: The current answer.
        :type current_answer: Any
        :param this_q: The current question.
        :type this_q: callable
        :param next_q: The next question.
        :type next_q: callable
        :param prev_answer: The previous answer.
        :type prev_answer: list, optional
        """
        next_answer = None

        if different_answers(current_answer, prev_answer):
            self.question_stack = self.question_stack[: self.current_idx]
            self.question_stack.append((this_q, current_answer))
        else:
            if len(self.question_stack) > self.current_idx + 1:
                next_answer = self.question_stack[self.current_idx + 1][1]
                next_q = self.question_stack[self.current_idx + 1][0]

        self.current_idx += 1
        next_q(next_answer)

    def q_end(self, answer: Any = None):
        """
        End of the questionnaire.
        Calling this last function (without an actual question) is necessary to trigger
        saving the last answer in the question stack through the call_next_question function.
        """
        return  # end of questionnaire

    def q6_1(self, answer: Any = None):
        """
        Get the URL/doi to the study/detailed methods.
        """
        studyURL = self.interface_funcs_dict["get_custom_entry"](
            "Please provide the URL/doi to your study/detailed methods:",
            multi_choice=True,
            section_idx=5,
            prev_answer=answer,
        )

        if isinstance(studyURL, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(studyURL, self.q6_1, self.q_end, answer)

    def q6(self, answer: Any = None):
        """
        Check if URL/doi to the study/detailed methods should be provided.
        """
        answerStudyURL = self.interface_funcs_dict["get_yes_no"](
            "Do you want to provide a URL/doi to your study/detailed methods? (yes/no)",
            section_idx=5,
            prev_answer=answer,
        )

        if isinstance(answerStudyURL, GoQBack):
            self.call_last_question()
            return
        elif answerStudyURL:
            next_question_callable = self.q6_1
        else:
            next_question_callable = self.q_end

        self.call_next_question(answerStudyURL, self.q6, next_question_callable, answer)

    def q5_2(self, answer: Any = None):
        """
        Get the custom method used as evidence for translation.
        """
        cstmTranslatEvidnc = self.interface_funcs_dict["get_custom_entry"](
            "Please provide your custom method used as evidence for translation:",
            multi_choice=True,
            section_idx=4,
            prev_answer=answer,
        )

        if isinstance(cstmTranslatEvidnc, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(cstmTranslatEvidnc, self.q5_2, self.q6, answer)

    def q5_1(self, answer: Any = None):
        """
        Get the custom method used as evidence for translation.
        """
        translatEvidence = self.interface_funcs_dict["get_enum_choice_conversion"](
            TranslationEvidenceChoices,
            "Please choose the method used as evidence for translation:",
            multi_choice=True,
            section_idx=4,
            prev_answer=answer,
        )

        if isinstance(translatEvidence, GoQBack):
            self.call_last_question()
            return
        elif translatEvidence and TranslationEvidenceChoices.CUSTOM in translatEvidence:
            next_question_callable = self.q5_2
        else:
            next_question_callable = self.q6

        self.call_next_question(
            translatEvidence, self.q5_1, next_question_callable, answer
        )

    def q5(self, answer: Any = None):
        """
        Check if translation of the de novo genes was verified.
        """
        translationEvidence = self.interface_funcs_dict["get_yes_no"](
            "Did you verify the translation of the de novo genes? (yes/no)",
            section_idx=4,
            prev_answer=answer,
        )

        if isinstance(translationEvidence, GoQBack):
            self.call_last_question()
            return
        elif translationEvidence:
            next_question_callable = self.q5_1
        else:
            next_question_callable = self.q6

        self.call_next_question(
            translationEvidence, self.q5, next_question_callable, answer
        )

    def q4_1(self, answer: Any = None):
        """
        Get the custom metric or method used to identify selection pressure.
        """
        selection = self.interface_funcs_dict["get_custom_entry"](
            "Please provide the metric or method used to identify selection pressure:",
            section_idx=3,
            prev_answer=answer,
        )

        if isinstance(selection, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(selection, self.q4_1, self.q5, answer)

    def q4(self, answer: Any = None):
        """
        Check if selection pressure was studied for the de novo genes.
        """
        selectionPressure = self.interface_funcs_dict["get_yes_no"](
            "Did you study selection pressure of the de novo genes? (yes/no)",
            section_idx=3,
            prev_answer=answer,
        )

        if isinstance(selectionPressure, GoQBack):
            self.call_last_question()
            return
        elif selectionPressure:
            next_question_callable = self.q4_1
        else:
            next_question_callable = self.q5

        self.call_next_question(
            selectionPressure, self.q4, next_question_callable, answer
        )

    def q3_3_3(self, answer: Any = None):
        """
        Get the custom software used for the synteny search.
        """
        softwareSyntenySearch = self.interface_funcs_dict["get_custom_entry"](
            "Please choose the software used for the synteny search:",
            multi_choice=True,
            section_idx=2,
            prev_answer=answer,
        )

        if isinstance(softwareSyntenySearch, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(softwareSyntenySearch, self.q3_3_3, self.q4, answer)

    def q3_3_2(self, answer: Any = None):
        """
        Check if specific software was used for the synteny search.
        """
        sftwrSyntSearch = self.interface_funcs_dict["get_yes_no"](
            "Did you use a specific software for the synteny search? (yes/no)",
            section_idx=2,
            prev_answer=answer,
        )

        if isinstance(sftwrSyntSearch, GoQBack):
            self.call_last_question()
            return
        elif sftwrSyntSearch:
            next_question_callable = self.q3_3_3
        else:
            next_question_callable = self.q4

        self.call_next_question(
            sftwrSyntSearch, self.q3_3_2, next_question_callable, answer
        )

    def q3_3_1(self, answer: Any = None):
        """
        Get the custom anchor for synteny search.
        """
        customAnchor = self.interface_funcs_dict["get_custom_entry"](
            "Please provide your custom anchor for synteny search:",
            multi_choice=True,
            section_idx=2,
            prev_answer=answer,
        )

        if isinstance(customAnchor, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(customAnchor, self.q3_3_1, self.q3_3_2, answer)

    def q3_3(self, answer: Any = None):
        """
        Get the synteny search information from the user.
        """
        geneAnchor = self.interface_funcs_dict["get_enum_choice_conversion"](
            AnchorChoices,
            "What was used to identify the syntenic region?:",
            multi_choice=True,
            section_idx=2,
            prev_answer=answer,
        )

        if isinstance(geneAnchor, GoQBack):
            self.call_last_question()
            return
        elif geneAnchor and AnchorChoices.CUSTOM in geneAnchor:
            next_question_callable = self.q3_3_1
        else:
            next_question_callable = self.q3_3_2

        self.call_next_question(geneAnchor, self.q3_3, next_question_callable, answer)

    def q3_2(self, answer: Any = None):
        """
        Check if synteny was studied between de novo genes and homologous sequences.
        """
        answerSynteny = self.interface_funcs_dict[
            "get_yes_no"
        ](
            "Did you check for synteny between de novo genes and their homologous sequences? (yes/no)",  # TODO: +non-genic?
            section_idx=2,
            prev_answer=answer,
        )

        if isinstance(answerSynteny, GoQBack):
            self.call_last_question()
            return
        elif answerSynteny:
            next_question_callable = self.q3_3
        else:
            next_question_callable = self.q4

        self.call_next_question(
            answerSynteny, self.q3_2, next_question_callable, answer
        )

    def q3_1(self, answer: Any = None):
        """
        Check if conservation/mutations between de novo genes and homologous sequences were studied.
        """
        enablingMutations = self.interface_funcs_dict[
            "get_yes_no"
        ](
            "Did you study conservation/mutations between de novo genes and homologous sequences?",  # TODO: +non-genic?
            section_idx=2,
            prev_answer=answer,
        )

        if isinstance(enablingMutations, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(enablingMutations, self.q3_1, self.q3_2, answer)

    def q3(self, answer: Any = None):
        """
        Check if non-genic homologous sequences were detected.
        """
        nonCodeHomolog = self.interface_funcs_dict["get_yes_no"](
            "Did you detect non-genic homologous sequences in genomes from other taxonomic groups? (yes/no)",
            section_idx=2,
            prev_answer=answer,
        )

        if isinstance(nonCodeHomolog, GoQBack):
            self.call_last_question()
            return
        elif nonCodeHomolog:
            next_question_callable = self.q3_1
        else:
            next_question_callable = self.q4

        self.call_next_question(nonCodeHomolog, self.q3, next_question_callable, answer)

    def q2_8(self, answer: Any = None):
        """
        Get the custom database(s) used for homology filtering.
        """
        customDB = self.interface_funcs_dict["get_custom_entry"](
            "Please provide your custom database used for homology filtering:",
            multi_choice=True,
            section_idx=1,
            prev_answer=answer,
        )

        if isinstance(customDB, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(customDB, self.q2_8, self.q3, answer)

    def q2_7(self, answer: Any = None):
        """
        Get the custom database(s) used for homology filtering.
        """
        homologyDBChoice = self.interface_funcs_dict["get_enum_choice_conversion"](
            HomologyDBChoices,
            "Please choose the database(s) used for homology filtering:",
            multi_choice=True,
            section_idx=1,
            prev_answer=answer,
        )

        if isinstance(homologyDBChoice, GoQBack):
            self.call_last_question()
            return
        elif homologyDBChoice and HomologyDBChoices.CUSTOM in homologyDBChoice:
            next_question_callable = self.q2_8
        else:
            next_question_callable = self.q3

        self.call_next_question(
            homologyDBChoice, self.q2_7, next_question_callable, answer
        )

    def q2_6_1(self, answer: Any = None):
        """
        Get the threshold value(s) for homology filtering based on selected metric(s).
        """
        thresholdValid = False
        thresholdValue = []
        thresholdChoice = dict(self.question_stack)[self.q2_5_3]
        customThreshold = dict(self.question_stack).get(self.q2_6, [])

        for idx, thChoice in enumerate(
            [it for it in thresholdChoice if it != ThresholdChoices.CUSTOM]
            + customThreshold
        ):
            while not thresholdValid:
                if answer:
                    prev_answer = answer[idx] if len(answer) > idx else None
                else:
                    prev_answer = None
                answrThreshVal = self.interface_funcs_dict["get_custom_entry"](
                    f"Please provide the threshold value for your homology "
                    f"filtering based on {thChoice}:",
                    section_idx=1,
                    prev_answer=prev_answer,
                )

                if isinstance(answrThreshVal, GoQBack):
                    self.call_last_question()
                    return

                if prev_answer and not different_answers(answrThreshVal, prev_answer):
                    thresholdValid = True
                else:
                    thresholdValid = self.interface_funcs_dict[
                        "valid_input_for_pydmodel"
                    ](HomologyFilter, "thresholdValue", [answrThreshVal])

                if thresholdValid:
                    thresholdValue.append(answrThreshVal)

            thresholdValid = False

        self.call_next_question(thresholdValue, self.q2_6_1, self.q2_7, answer)

    def q2_6(self, answer: Any = None):
        """
        Get the custom metric for homology filtering.
        """
        customThreshold = self.interface_funcs_dict["get_custom_entry"](
            "Please provide your custom metric for homology filtering:",
            multi_choice=True,
            section_idx=1,
            prev_answer=answer,
        )

        if isinstance(customThreshold, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(customThreshold, self.q2_6, self.q2_6_1, answer)

    def q2_5_3(self, answer: Any = None):
        """
        Get the metric used for homology filtering.
        """
        thresholdChoice = self.interface_funcs_dict["get_enum_choice_conversion"](
            ThresholdChoices,
            "Please choose the metric used for homology filtering:",
            multi_choice=True,
            section_idx=1,
            prev_answer=answer,
        )

        if isinstance(thresholdChoice, GoQBack):
            self.call_last_question()
            return
        elif thresholdChoice and ThresholdChoices.CUSTOM in thresholdChoice:
            next_question_callable = self.q2_6
        else:
            next_question_callable = self.q2_6_1

        self.call_next_question(
            thresholdChoice, self.q2_5_3, next_question_callable, answer
        )

    def q2_5_2(self, answer: Any = None):
        """
        Get the custom structural similarity search software/method used for homology filtering
        """
        structSim = self.interface_funcs_dict["get_custom_entry"](
            "Please provide the structural similarity search software/method used for homology filtering:",
            multi_choice=False,
            section_idx=1,
            prev_answer=answer,
        )

        if isinstance(structSim, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(structSim, self.q2_5_2, self.q2_5_3, answer)

    def q2_5_1(self, answer: Any = None):
        """
        Check if structural similarity was used for homology filtering.
        """
        structSim = self.interface_funcs_dict["get_yes_no"](
            "Did you use structural similarity for homology filtering? (yes/no)",
            section_idx=1,
            prev_answer=answer,
        )

        if isinstance(structSim, GoQBack):
            self.call_last_question()
            return

        if structSim:
            next_question_callable = self.q2_5_2
        else:
            next_question_callable = self.q2_5_3

        self.call_next_question(structSim, self.q2_5_1, next_question_callable, answer)

    def q2_4(self, answer: Any = None):
        """
        Get the custom sequence type(s) used for homology filtering.
        """
        customSeqType = self.interface_funcs_dict["get_custom_entry"](
            "Please provide your custom sequence type(s) used for homology filtering:",
            multi_choice=True,
            section_idx=1,
            prev_answer=answer,
        )

        if isinstance(customSeqType, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(customSeqType, self.q2_4, self.q2_5_1, answer)

    def q2_3(self, answer: Any = None):
        """
        Get the sequence type(s) used for homology filtering.
        """
        seqTypeChoice = self.interface_funcs_dict["get_enum_choice_conversion"](
            SeqTypeChoices,
            "Please choose your sequence type(s) used for homology filtering:",
            multi_choice=True,
            section_idx=1,
            prev_answer=answer,
        )

        if isinstance(seqTypeChoice, GoQBack):
            self.call_last_question()
            return
        elif seqTypeChoice and SeqTypeChoices.CUSTOM in seqTypeChoice:
            next_question_callable = self.q2_4
        else:
            next_question_callable = self.q2_5_1

        self.call_next_question(
            seqTypeChoice, self.q2_3, next_question_callable, answer
        )

    def q2_2_1(self, answer: Any = None):
        """
        Get the taxonomic ID where the de novo genes emerged.
        """
        taxIDvalid = False

        while not taxIDvalid:
            warnings.filterwarnings("error")

            answerTaxonID = self.interface_funcs_dict["get_custom_entry"](
                "Please provide the taxonomic ID (name or number from NCBI Taxonomy DB) where they emerged:",
                section_idx=1,
                prev_answer=answer,
            )

            if isinstance(answerTaxonID, GoQBack):
                self.call_last_question()
                return

            if answer and not different_answers(answerTaxonID, answer):
                taxIDvalid = True
            else:
                taxIDvalid = self.interface_funcs_dict["valid_input_for_pydmodel"](
                    TaxonID, "taxID", answerTaxonID
                )

            warnings.filterwarnings("ignore")

        self.call_next_question(answerTaxonID, self.q2_2_1, self.q2_3, answer)

    def q2_2(self, answer: Any = None):
        """
        Get the taxonomic group where the de novo genes emerged.
        """
        taxSpecificity = self.interface_funcs_dict["get_enum_choice_conversion"](
            TaxSpecificityChoices,
            "Please choose the specificity for the taxonomic group where they emerged:",
            section_idx=1,
            prev_answer=answer,
        )

        if isinstance(taxSpecificity, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(taxSpecificity, self.q2_2, self.q2_2_1, answer)

    def q2_1(self, answer: Any = None):
        """
        Check if phylogenetic taxa information is known.
        """
        phylogeneticTaxa = self.interface_funcs_dict["get_yes_no"](
            "Do you know in which taxonomic group your de novo gene candidates emerged? (yes/no)",
            section_idx=1,
            prev_answer=answer,
        )

        if isinstance(phylogeneticTaxa, GoQBack):
            self.call_last_question()
            return
        elif phylogeneticTaxa:
            next_question_callable = self.q2_2  # get_PhylogeneticTaxa
        else:
            next_question_callable = self.q2_3

        self.call_next_question(
            phylogeneticTaxa, self.q2_1, next_question_callable, answer
        )

    def q2(self, answer: Any = None):
        """
        Check if a homology filter was applied.
        """
        homologyFilter = self.interface_funcs_dict["get_yes_no"](
            "Did you validate absence of homology of your de novo genes? (yes/no)",
            section_idx=1,
            prev_answer=answer,
        )

        if isinstance(homologyFilter, GoQBack):
            self.call_last_question()
            return
        elif homologyFilter:
            next_question_callable = self.q2_1
        else:
            next_question_callable = self.q3

        self.call_next_question(homologyFilter, self.q2, next_question_callable, answer)

    def q1_3(self, answer: Any = None):
        """
        Get the custom input data (not annotated genome or transcriptome).
        """
        customInputData = self.interface_funcs_dict["get_custom_entry"](
            "Please provide your custom input data for de novo gene detection:",
            section_idx=0,
            prev_answer=answer,
        )

        if isinstance(customInputData, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(customInputData, self.q1_3, self.q2, answer)

    def q1_2_7(self, answer: Any = None):
        """
        Get the additional, custom transcriptome information from the user.
        """
        inputDataChoice = self.question_stack[0][1]

        transcriptomeInfo = self.interface_funcs_dict["get_custom_entry"](
            "Please provide the information about the transcriptome (e.g. tissue, cell type, ...):",
            section_idx=0,
            prev_answer=answer,
        )

        if isinstance(transcriptomeInfo, GoQBack):
            self.call_last_question()
            return
        elif inputDataChoice and InputDataChoices.CUSTOM in inputDataChoice:
            next_question_callable = self.q1_3
        else:
            next_question_callable = self.q2

        self.call_next_question(
            transcriptomeInfo, self.q1_2_7, next_question_callable, answer
        )

    def q1_2_6(self, answer: Any = None):
        """
        Check if additional info about the transcriptome should be added.
        """
        inputDataChoice = self.question_stack[0][1]

        transcriptomeInfo = self.interface_funcs_dict["get_yes_no"](
            "Do you want to add additional information about the transcriptome (e.g. tissue, cell type, ...)? (yes/no)",
            section_idx=0,
            prev_answer=answer,
        )

        if isinstance(transcriptomeInfo, GoQBack):
            self.call_last_question()
            return
        elif transcriptomeInfo:
            next_question_callable = self.q1_2_7
        elif inputDataChoice and InputDataChoices.CUSTOM in inputDataChoice:
            next_question_callable = self.q1_3
        else:
            next_question_callable = self.q2

        self.call_next_question(
            transcriptomeInfo, self.q1_2_6, next_question_callable, answer
        )

    def q1_2_5(self, answer: Any = None):
        """
        Get the custom ORF selection for the transcriptome data.
        """
        customORF = self.interface_funcs_dict["get_custom_entry"](
            "Please provide your custom ORF selection for your transcriptome data:",
            multi_choice=True,
            section_idx=0,
            prev_answer=answer,
        )

        if isinstance(customORF, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(customORF, self.q1_2_5, self.q1_2_6, answer)

    def q1_2_4(self, answer: Any = None):
        """
        Get which ORFs in transcripts were selected.
        """
        ORFChoiceValid = False

        while not ORFChoiceValid:
            transORFChoice = self.interface_funcs_dict["get_enum_choice_conversion"](
                ORFChoices,
                "Please choose which ORFs in the transcripts were selected:",
                multi_choice=True,
                section_idx=0,
                prev_answer=answer,
            )

            if isinstance(transORFChoice, GoQBack):
                self.call_last_question()
                return

            if answer and not different_answers(transORFChoice, answer):
                ORFChoiceValid = True
            else:
                ORFChoiceValid = self.interface_funcs_dict["valid_input_for_pydmodel"](
                    Transcriptome, "transORFChoice", transORFChoice
                )

        if transORFChoice and ORFChoices.CUSTOM in transORFChoice:
            next_question_callable = self.q1_2_5
        else:
            next_question_callable = self.q1_2_6

        self.call_next_question(
            transORFChoice, self.q1_2_4, next_question_callable, answer
        )

    def q1_2_3(self, answer: Any = None):
        """
        Get the custom genetic context information from the user.
        """
        customGeneticContext = self.interface_funcs_dict["get_custom_entry"](
            "Please provide your custom genetic context for your transcriptome data:",
            multi_choice=True,
            section_idx=0,
            prev_answer=answer,
        )

        if isinstance(customGeneticContext, GoQBack):
            self.call_last_question()
            return

        self.call_next_question(customGeneticContext, self.q1_2_3, self.q1_2_4, answer)

    def q1_2_2(self, answer: Any = None):
        """
        Get the genetic context information from the user.
        """
        transContextChoice = self.interface_funcs_dict[
            "get_enum_choice_conversion"
        ](
            GeneticContextChoices,
            "Please indicate which transcripts were kept based on their overlap with the following genetic contexts:",  # add a None / not filtererd any genetic context option?
            multi_choice=True,
            section_idx=0,
            prev_answer=answer,
        )

        if isinstance(transContextChoice, GoQBack):
            self.call_last_question()
            return
        elif transContextChoice and GeneticContextChoices.CUSTOM in transContextChoice:
            next_question_callable = self.q1_2_3
        else:
            next_question_callable = self.q1_2_4

        self.call_next_question(
            transContextChoice, self.q1_2_2, next_question_callable, answer
        )

    def q1_2_1(self, answer: Any = None):
        """
        Get the TPM threshold used as a minimum level of transcript expression.
        """
        validExpressionLevel = False

        while not validExpressionLevel:
            expressionLevel = self.interface_funcs_dict["get_custom_entry"](
                "Please provide the TPM threshold used as a minimum level of transcript expression:",
                section_idx=0,
                prev_answer=answer,
            )
            if isinstance(expressionLevel, GoQBack):
                self.call_last_question()
                return

            if answer and not different_answers(expressionLevel, answer):
                validExpressionLevel = True
            else:
                validExpressionLevel = self.interface_funcs_dict[
                    "valid_input_for_pydmodel"
                ](Transcriptome, "expressionLevel", expressionLevel)

        self.call_next_question(expressionLevel, self.q1_2_1, self.q1_2_2, answer)

    def q1_2(self, answer: Any = None):
        """
        Get the transcriptome information from the user.
        """
        inputDataChoice = self.question_stack[0][1]

        answerExpressionLevel = self.interface_funcs_dict[
            "get_yes_no"
        ](
            "Did you apply a TPM threshold used as a minimum level of transcript expression? (yes/no)",  # None means unknown/no threshold?
            section_idx=0,
            prev_answer=answer,
        )

        if isinstance(answerExpressionLevel, GoQBack):
            self.call_last_question()
            return
        elif answerExpressionLevel:
            next_question_callable = self.q1_2_1
        elif inputDataChoice and InputDataChoices.CUSTOM in inputDataChoice:
            next_question_callable = self.q1_3
        else:
            next_question_callable = self.q1_2_2

        self.call_next_question(
            answerExpressionLevel, self.q1_2, next_question_callable, answer
        )

    def q1_1(self, answer: Any = None):
        """
        Get the genome annotation method from the user.
        """
        inputDataChoice = self.question_stack[0][1]
        genomeChoicevalid = False

        while not genomeChoicevalid:
            annoGenom = self.interface_funcs_dict["get_enum_choice_conversion"](
                AnnotGenomeChoices,
                "Please choose the genome annotation method:",
                multi_choice=True,
                section_idx=0,
                prev_answer=answer,
            )

            if isinstance(annoGenom, GoQBack):
                self.call_last_question()
                return

            if answer and not different_answers(annoGenom, answer):
                genomeChoicevalid = True
            else:
                genomeChoicevalid = self.interface_funcs_dict[
                    "valid_input_for_pydmodel"
                ](AnnotGenome, "annotGenomeChoice", annoGenom)

        if inputDataChoice and InputDataChoices.TRANSCRIPTOME in inputDataChoice:
            next_question_callable = self.q1_2
        elif inputDataChoice and InputDataChoices.CUSTOM in inputDataChoice:
            next_question_callable = self.q1_3
        else:
            next_question_callable = self.q2

        self.call_next_question(annoGenom, self.q1_1, next_question_callable, answer)

    def q1(self, answer: Any = None):
        """
        Get the input data choice from the user.
        """
        inputDataChoice = self.interface_funcs_dict["get_enum_choice_conversion"](
            InputDataChoices,
            "Did you detect your candidate de novo genes from a:",
            multi_choice=True,
            section_idx=0,
            prev_answer=answer,
        )

        if isinstance(inputDataChoice, GoQBack):
            self.call_last_question()
            return
        elif inputDataChoice and InputDataChoices.ANNOT_GENOME in inputDataChoice:
            next_question_callable = self.q1_1
        elif inputDataChoice and InputDataChoices.TRANSCRIPTOME in inputDataChoice:
            next_question_callable = self.q1_2
        elif inputDataChoice and InputDataChoices.CUSTOM in inputDataChoice:
            next_question_callable = self.q1_3
        else:
            raise ValueError(
                "Invalid input data choice. Please select from the following options: "
                "ANNOT_GENOME, TRANSCRIPTOME, CUSTOM."
            )

        self.call_next_question(
            inputDataChoice, self.q1, next_question_callable, answer
        )

    def get_DeNovoGeneAnnotation_from_qstack(
        self,
        match_dict: dict[str, Any] = FUNCS_TO_MODELS_DICT,
    ) -> DeNovoGeneAnnotation:
        """
        Create a DeNovoGeneAnnotation object from the given question stack.

        :param question_stack: The question stack.
        :type question_stack: list[tuple[callable, Any]]
        :param match_dict: The dictionary to match function callables to field names.
        :type match_dict: dict[str, Any]
        :return: The DeNovoGeneAnnotation object.
        :rtype: DeNovoGeneAnnotation
        """
        # match function callables to field names
        qstack_dict = dict(
            map(
                lambda kv: (match_dict[kv[0].__func__.__name__], kv[1]),
                self.question_stack,
            )
        )

        # create all sub-models
        annotGenome = get_model_from_qstack_dict(qstack_dict, AnnotGenome)
        transcriptome = get_model_from_qstack_dict(qstack_dict, Transcriptome)
        evolInfo = get_model_from_qstack_dict(qstack_dict, EvolutionaryInformation)
        if qstack_dict.get("taxID", False) and qstack_dict.get(
            "phylogeneticTaxa", False
        ):
            taxonID = get_model_from_qstack_dict(qstack_dict, TaxonID)
            qstack_dict["taxonID"] = taxonID
            phylogeneticTaxa = get_model_from_qstack_dict(qstack_dict, PhylogeneticTaxa)
            qstack_dict["phylogeneticTaxa"] = phylogeneticTaxa
        homologyFilter = get_model_from_qstack_dict(qstack_dict, HomologyFilter)
        if qstack_dict.get("synteny", False):
            syntenySearch = get_model_from_qstack_dict(qstack_dict, SyntenySearch)
            qstack_dict["synteny"] = syntenySearch
        nonCodingHomologs = get_model_from_qstack_dict(qstack_dict, NonCodingHomologs)
        translatEvidnce = get_model_from_qstack_dict(qstack_dict, TranslationalEvidence)

        # create the DeNovoGeneAnnotation object
        return DeNovoGeneAnnotation(
            inputData=qstack_dict["inputData"],
            inputAnnotGenome=annotGenome,
            inputTranscriptome=transcriptome,
            customInputData=qstack_dict.get("customInputData", None),
            evolutionaryInformation=evolInfo,
            homologyFilter=homologyFilter,
            nonCodingHomologs=nonCodingHomologs,
            translationalEvidence=translatEvidnce,
            studyURL=qstack_dict.get("studyURL", None),
        )

    def start_questionnaire(self) -> DeNovoGeneAnnotation:
        """
        Start the questionnaire to get the user input.

        :return: The DeNovoGeneAnnotation object.
        :rtype: DeNovoGeneAnnotation
        """

        self.q1()

        if not self.question_stack:
            raise ValueError(
                "Question stack is empty. Ensure that questions are answered before proceeding."
            )

        return self.get_DeNovoGeneAnnotation_from_qstack()
