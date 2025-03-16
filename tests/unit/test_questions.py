import pytest
from denofo.questionnaire.questions import DeNovoQuestionnaire
from denofo.utils.constants import GoQBack
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

# Patch the DeNovoQuestionnaire class to bypass start_questionnaire.
DeNovoQuestionnaire.start_questionnaire = lambda self: None


# Dummy functions to record call order and parameters.
class CallRecorder:
    def __init__(self):
        self.called = False
        self.args = None

    def __call__(self, answer):
        self.called = True
        self.args = answer


# Create a fixture that returns a dummy interface functions dict.
@pytest.fixture
def dummy_interface_funcs():
    calls = {}

    def get_yes_no(prompt, **kwargs):
        calls["get_yes_no"] = prompt
        # Default: return True; tests can override by setting a key
        return False

    def get_custom_entry(prompt, **kwargs):
        calls["get_custom_entry"] = prompt
        return "dummy_custom"

    def get_enum_choice_conversion(choices, prompt, **kwargs):
        calls["get_enum_choice_conversion"] = prompt
        return []

    def valid_input_for_pydmodel(model, field, value):
        calls["valid_input_for_pydmodel"] = (model, field, value)
        return True

    funcs = {
        "get_yes_no": get_yes_no,
        "get_custom_entry": get_custom_entry,
        "get_enum_choice_conversion": get_enum_choice_conversion,
        "valid_input_for_pydmodel": valid_input_for_pydmodel,
    }
    return funcs


@pytest.fixture
def dummy_call_next_question_fixture():
    call_args = {}

    def dummy_call_next_question(current_answer, this_q, next_q, answer):
        call_args["current_answer"] = current_answer
        call_args["this_q"] = this_q.__name__
        call_args["next_q"] = next_q.__name__
        call_args["prev_answer"] = answer

    return call_args, dummy_call_next_question


@pytest.fixture
def dummy_call_last_question_fixture():
    call_args = {}

    def dummy_call_last_question():
        call_args["call_last_question"] = True

    return call_args, dummy_call_last_question


def test_call_next_question_new_answer(dummy_interface_funcs):
    """
    Test that call_next_question appends a new entry to the question stack
    when the current answer is different from the previous answer.
    """
    # In this test, different_answers returns True so we expect a new entry to be appended.
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = []
    dq.current_idx = 0

    # current_answer is different from prev_answer ("new" vs "old")
    current_answer = "new"
    prev_answer = "old"

    # Define dummy functions for this_q and next_q.
    def dummy_this(answer):
        pass

    # Use a recorder for next_q.
    next_recorder = CallRecorder()

    dq.call_next_question(current_answer, dummy_this, next_recorder, prev_answer)
    # We expect that the question stack was truncated and then appended a new entry.
    assert len(dq.question_stack) == 1
    assert dq.question_stack[0] == (dummy_this, current_answer)
    # And current_idx has been incremented.
    assert dq.current_idx == 1
    # And next_q was called with next_answer as None.
    assert next_recorder.called
    assert next_recorder.args is None


def test_call_next_question_reuse_next_answer(dummy_interface_funcs):
    # In this test, current_answer equals prev_answer so question stack uses the existing next question.
    dq = DeNovoQuestionnaire(dummy_interface_funcs)

    next_recorder = CallRecorder()

    # Prepopulate question_stack with two entries.
    def dummy_first(answer):
        pass

    def dummy_second(answer):
        next_recorder(answer)

    # Define a dummy next_q that will be overwritten by call_next_question.
    def dummy_next_q():
        pass

    dq.question_stack = [(dummy_first, "same"), (dummy_second, "existing_next")]
    dq.current_idx = 0

    # current_answer equals prev_answer => different_answers returns False.
    dq.call_next_question("same", dummy_first, dummy_next_q, "same")
    # Expect that the next question is taken from question_stack at index current_idx+1.
    # current_idx should have been incremented to 1 and dummy_second called with "existing_next".
    assert dq.current_idx == 1
    assert next_recorder.called
    assert next_recorder.args == "existing_next"


def test_call_last_question(dummy_interface_funcs):
    # Set up a question stack with two items; current_idx > 0 so that we can go back.
    call_history = []

    def dummy_q1(answer):
        call_history.append(("q1", answer))

    def dummy_q2(answer):
        call_history.append(("q2", answer))

    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [(dummy_q1, "answer1"), (dummy_q2, "answer2")]
    dq.current_idx = 1  # currently at second question
    dq.call_last_question()
    # current_idx should be decreased to 0 and dummy_q1 should have been called with its answer.
    assert dq.current_idx == 0
    assert call_history == [("q1", "answer1")]


def test_call_last_question_no_previous(dummy_interface_funcs):
    # Test call_last_question when there is no previous question.
    call_history = []

    def dummy_q1(answer):
        call_history.append(("q1", answer))

    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [(dummy_q1, "answer1")]
    dq.current_idx = 0  # currently at first question
    dq.call_last_question()
    # current_idx should remain at 0 and call_history should be empty.
    assert dq.current_idx == 0
    assert call_history == [("q1", "answer1")]


def test_call_last_question_no_stack(dummy_interface_funcs, monkeypatch):
    # Test call_last_question when there is no question stack.
    monkeypatch.setattr(DeNovoQuestionnaire, "q1", lambda self, answer: None)
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = []
    dq.current_idx = 0
    dq.call_last_question()
    # current_idx should remain at 0 and there should be no errors.
    assert dq.current_idx == 0
    assert dq.question_stack == []


def test_q_end(dummy_interface_funcs):
    # Test q_end function.
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.q_end()
    # q_end should set next_question_callable to None.


def test_q6_yes_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q6 when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q6("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q6"
    assert call_args.get("next_q") == "q6_1"
    assert call_args.get("prev_answer") == "prev"


def test_q6_no_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q6 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q6("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q6"
    assert call_args.get("next_q") == "q_end"
    assert call_args.get("prev_answer") == "prev"


def test_q1_annotGenome_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1 flow when user answers annotated Genome
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: InputDataChoices.ANNOT_GENOME
    )
    dq.q1("prev")

    assert call_args.get("current_answer") == InputDataChoices.ANNOT_GENOME
    assert call_args.get("this_q") == "q1"
    assert call_args.get("next_q") == "q1_1"
    assert call_args.get("prev_answer") == "prev"


def test_q1_transcriptome_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1 flow when user answers transcriptome
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: InputDataChoices.TRANSCRIPTOME
    )
    dq.q1("prev")

    assert call_args.get("current_answer") == InputDataChoices.TRANSCRIPTOME
    assert call_args.get("this_q") == "q1"
    assert call_args.get("next_q") == "q1_2"
    assert call_args.get("prev_answer") == "prev"


def test_q1_custom_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1 flow when user answers custom
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: InputDataChoices.CUSTOM
    )
    dq.q1("prev")

    assert call_args.get("current_answer") == InputDataChoices.CUSTOM
    assert call_args.get("this_q") == "q1"
    assert call_args.get("next_q") == "q1_3"
    assert call_args.get("prev_answer") == "prev"


def test_q1_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q1 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.interface_funcs_dict["get_enum_choice_conversion"] = lambda c, p, **kw: GoQBack()
    dq.call_last_question = dummy_call_last_question
    dq.q1("prev")

    assert call_args.get("call_last_question") is True


def test_q1_ValueError_flow(dummy_interface_funcs):
    # Test q1 flow when user answers an unexpected value
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.interface_funcs_dict["get_enum_choice_conversion"] = (
        lambda c, p, **kw: "unexpected"
    )
    with pytest.raises(ValueError):
        dq.q1("prev")


def test_q1_1_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_1 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [("q1", "annotated_genome")]
    dq.call_next_question = dummy_call_next_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = (
        lambda c, p, **kw: AnnotGenomeChoices.abInitio
    )
    dq.q1_1("prev")

    assert call_args.get("current_answer") == AnnotGenomeChoices.abInitio
    assert call_args.get("this_q") == "q1_1"
    assert call_args.get("next_q") == "q2"
    assert call_args.get("prev_answer") == "prev"


def test_q1_1_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q1_1 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [("q1", "annotated_genome")]
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = lambda c, p, **kw: GoQBack()
    dq.q1_1("prev")

    assert call_args.get("call_last_question") is True


def test_q1_2_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [("q1", "transcriptome")]
    dq.call_next_question = dummy_call_next_question
    dq.interface_funcs_dict["get_yes_no"] = lambda prompt, **kw: True
    dq.q1_2("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q1_2"
    assert call_args.get("next_q") == "q1_2_1"
    assert call_args.get("prev_answer") == "prev"


def test_q1_2_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q1_2 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [("q1", "transcriptome")]
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_yes_no"] = lambda prompt, **kw: GoQBack()
    dq.q1_2("prev")

    assert call_args.get("call_last_question") is True


def test_q1_2_1_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2_1 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dq.interface_funcs_dict["get_custom_entry"] = lambda prompt, **kw: 0.5
    dq.q1_2_1(0.3)

    assert call_args.get("current_answer") == 0.5
    assert call_args.get("this_q") == "q1_2_1"
    assert call_args.get("next_q") == "q1_2_2"
    assert call_args.get("prev_answer") == 0.3


def test_1_2_1_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q1_2_1 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [("q1", "transcriptome")]
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = lambda c, p, **kw: GoQBack()
    dq.q1_2_1("prev")

    assert call_args.get("call_last_question") is True


def test_1_2_2_nocustom_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2_2 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = (
        lambda c, p, **kw: GeneticContextChoices.antisense
    )
    dq.q1_2_2("prev")

    assert call_args.get("current_answer") == GeneticContextChoices.antisense
    assert call_args.get("this_q") == "q1_2_2"
    assert call_args.get("next_q") == "q1_2_4"
    assert call_args.get("prev_answer") == "prev"


def test_1_2_2_custom_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2_2 flow when user answers custom.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = (
        lambda c, p, **kw: GeneticContextChoices.CUSTOM
    )
    dq.q1_2_2("prev")

    assert call_args.get("current_answer") == GeneticContextChoices.CUSTOM
    assert call_args.get("this_q") == "q1_2_2"
    assert call_args.get("next_q") == "q1_2_3"
    assert call_args.get("prev_answer") == "prev"


def test_1_2_2_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q1_2_2 flow when user answers GoQBack.
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = lambda c, p, **kw: GoQBack()
    dq.q1_2_2("prev")

    assert call_args.get("call_last_question", False) is True


def test_q3_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3 flow when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q3("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q3"
    assert call_args.get("next_q") == "q3_1"
    assert call_args.get("prev_answer") == "prev"


def test_q3_no_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q3("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q3"
    assert call_args.get("next_q") == "q4"
    assert call_args.get("prev_answer") == "prev"


def test_1_2_3_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2_3 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = (
        lambda prompt, **kw: "custom genetic context"
    )
    dq.q1_2_3("prev")

    assert call_args.get("current_answer") == "custom genetic context"
    assert call_args.get("this_q") == "q1_2_3"
    assert call_args.get("next_q") == "q1_2_4"
    assert call_args.get("prev_answer") == "prev"


def test_1_2_3_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q1_2_3 flow when user answers GoQBack.
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_custom_entry"] = lambda p, **kw: GoQBack()
    dq.q1_2_3("prev")

    assert call_args.get("call_last_question", False) is True


def test_q1_2_4_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2_4 flow when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: ORFChoices.long_5_3_ORF
    )
    dq.q1_2_4("prev")

    assert call_args.get("current_answer") == ORFChoices.long_5_3_ORF
    assert call_args.get("this_q") == "q1_2_4"
    assert call_args.get("next_q") == "q1_2_6"
    assert call_args.get("prev_answer") == "prev"


def test_q_1_2_4_custom_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2_4 flow when user answers custom.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = (
        lambda c, p, **kw: ORFChoices.CUSTOM
    )
    dq.q1_2_4("prev")

    assert call_args.get("current_answer") == ORFChoices.CUSTOM
    assert call_args.get("this_q") == "q1_2_4"
    assert call_args.get("next_q") == "q1_2_5"
    assert call_args.get("prev_answer") == "prev"


def test_q1_2_4_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q1_2_4 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.interface_funcs_dict["get_yes_no"] = lambda p, **kw: GoQBack()
    dq.call_last_question = dummy_call_last_question
    dq.q1_2_4("prev")

    assert call_args.get("call_last_question") is True


def test_q3_1_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3_1 flow when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q3_1("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q3_1"
    assert call_args.get("next_q") == "q3_2"
    assert call_args.get("prev_answer") == "prev"


def test_q3_1_no_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3_1 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q3_1("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q3_1"
    assert call_args.get("next_q") == "q3_2"
    assert call_args.get("prev_answer") == "prev"


def test_q1_2_5_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2_5 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: "custom orf type"
    dq.q1_2_5("prev")

    assert call_args.get("current_answer") == "custom orf type"
    assert call_args.get("this_q") == "q1_2_5"
    assert call_args.get("next_q") == "q1_2_6"
    assert call_args.get("prev_answer") == "prev"


def test_q1_2_5_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q1_2_5 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.interface_funcs_dict["get_custom_entry"] = lambda p, **kw: GoQBack()
    dq.call_last_question = dummy_call_last_question
    dq.q1_2_5("prev")

    assert call_args.get("call_last_question") is True


def test_q1_2_6_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2_6 flow when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [("q1", [InputDataChoices.CUSTOM])]
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q1_2_6("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q1_2_6"
    assert call_args.get("next_q") == "q1_2_7"
    assert call_args.get("prev_answer") == "prev"


def test_q1_2_6_no_custom_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2_6 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [("q1", [InputDataChoices.CUSTOM])]
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q1_2_6("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q1_2_6"
    assert call_args.get("next_q") == "q1_3"
    assert call_args.get("prev_answer") == "prev"


def test_q1_2_6_no_nocustom_flow(
    dummy_interface_funcs, dummy_call_next_question_fixture
):
    # Test q1_2_6 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [("q1", [InputDataChoices.TRANSCRIPTOME])]
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q1_2_6("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q1_2_6"
    assert call_args.get("next_q") == "q2"
    assert call_args.get("prev_answer") == "prev"


def test_q1_2_6_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q1_2_6 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [("q1", [InputDataChoices.CUSTOM])]
    dq.interface_funcs_dict["get_yes_no"] = lambda p, **kw: GoQBack()
    dq.call_last_question = dummy_call_last_question
    dq.q1_2_6("prev")

    assert call_args.get("call_last_question") is True


def test_q1_2_7_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2_7 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dq.question_stack = [("q1", [InputDataChoices.TRANSCRIPTOME])]
    dummy_interface_funcs["get_custom_entry"] = (
        lambda p, **kw: "dummy custom additional info"
    )
    dq.q1_2_7("prev")

    assert call_args.get("current_answer") == "dummy custom additional info"
    assert call_args.get("this_q") == "q1_2_7"
    assert call_args.get("next_q") == "q2"
    assert call_args.get("prev_answer") == "prev"


def test_q1_2_7_custom_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q1_2_7 flow when user answers custom.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [("q1", [InputDataChoices.CUSTOM])]
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = (
        lambda p, **kw: "dummy custom additional info"
    )
    dq.q1_2_7("prev")

    assert call_args.get("current_answer") == "dummy custom additional info"
    assert call_args.get("this_q") == "q1_2_7"
    assert call_args.get("next_q") == "q1_3"
    assert call_args.get("prev_answer") == "prev"


def test_q1_2_7_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q1_2_7 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = [("q1", [InputDataChoices.CUSTOM])]
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_custom_entry"] = lambda p, **kw: GoQBack()
    dq.q1_2_7("prev")

    assert call_args.get("call_last_question") is True


def test_q3_2_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3_2 flow when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q3_2("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q3_2"
    assert call_args.get("next_q") == "q3_3"
    assert call_args.get("prev_answer") == "prev"


def test_q3_2_no_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3_2 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q3_2("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q3_2"
    assert call_args.get("next_q") == "q4"
    assert call_args.get("prev_answer") == "prev"


def test_q3_3_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3_3 flow when user answers custom.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: AnchorChoices.CUSTOM
    )
    dq.q3_3("prev")

    assert call_args.get("current_answer") == AnchorChoices.CUSTOM
    assert call_args.get("this_q") == "q3_3"
    assert call_args.get("next_q") == "q3_3_1"
    assert call_args.get("prev_answer") == "prev"


def test_q3_3_nocustom_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3_3 flow when user answers not custom.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: AnchorChoices.GENEANCHOR
    )
    dq.q3_3("prev")

    assert call_args.get("current_answer") == AnchorChoices.GENEANCHOR
    assert call_args.get("this_q") == "q3_3"
    assert call_args.get("next_q") == "q3_3_2"
    assert call_args.get("prev_answer") == "prev"


def test_q3_3_1_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3_3_1 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: "custom anchor"
    dq.q3_3_1("prev")

    assert call_args.get("current_answer") == "custom anchor"
    assert call_args.get("this_q") == "q3_3_1"
    assert call_args.get("next_q") == "q3_3_2"
    assert call_args.get("prev_answer") == "prev"


def test_q3_3_2_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3_3_2 flow when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q3_3_2("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q3_3_2"
    assert call_args.get("next_q") == "q3_3_3"
    assert call_args.get("prev_answer") == "prev"


def test_q3_3_2_no_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3_3_2 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q3_3_2("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q3_3_2"
    assert call_args.get("next_q") == "q4"
    assert call_args.get("prev_answer") == "prev"


def test_q3_3_3_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q3_3_3 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: "custom software"
    dq.q3_3_3("prev")

    assert call_args.get("current_answer") == "custom software"
    assert call_args.get("this_q") == "q3_3_3"
    assert call_args.get("next_q") == "q4"
    assert call_args.get("prev_answer") == "prev"


def test_q4_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q4 flow when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q4("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q4"
    assert call_args.get("next_q") == "q4_1"
    assert call_args.get("prev_answer") == "prev"


def test_q4_no_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q4 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q4("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q4"
    assert call_args.get("next_q") == "q5"
    assert call_args.get("prev_answer") == "prev"


def test_q4_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q4 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.interface_funcs_dict["get_yes_no"] = lambda p, **kw: GoQBack()
    dq.call_last_question = dummy_call_last_question
    dq.q4("prev")

    assert call_args.get("call_last_question") is True


def test_q4_1_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q4_1 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: "custom selection"
    dq.q4_1("prev")

    assert call_args.get("current_answer") == "custom selection"
    assert call_args.get("this_q") == "q4_1"
    assert call_args.get("next_q") == "q5"
    assert call_args.get("prev_answer") == "prev"


def test_q4_1_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q4_1 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_custom_entry"] = lambda p, **kw: GoQBack()
    dq.q4_1("prev")

    assert call_args.get("call_last_question") is True


def test_q5_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q5 flow when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q5("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q5"
    assert call_args.get("next_q") == "q5_1"
    assert call_args.get("prev_answer") == "prev"


def test_q5_no_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q5 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q5("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q5"
    assert call_args.get("next_q") == "q6"
    assert call_args.get("prev_answer") == "prev"


def test_q5_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q5 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.interface_funcs_dict["get_yes_no"] = lambda p, **kw: GoQBack()
    dq.call_last_question = dummy_call_last_question
    dq.q5("prev")

    assert call_args.get("call_last_question") is True


def test_q5_1_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q5_1 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: TranslationEvidenceChoices.RIBO_PROFIL
    )
    dq.q5_1("prev")

    assert call_args.get("current_answer") == TranslationEvidenceChoices.RIBO_PROFIL
    assert call_args.get("this_q") == "q5_1"
    assert call_args.get("next_q") == "q6"
    assert call_args.get("prev_answer") == "prev"


def test_q5_1_custom_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q5_1 flow when user answers custom.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: TranslationEvidenceChoices.CUSTOM
    )
    dq.q5_1("prev")

    assert call_args.get("current_answer") == TranslationEvidenceChoices.CUSTOM
    assert call_args.get("this_q") == "q5_1"
    assert call_args.get("next_q") == "q5_2"
    assert call_args.get("prev_answer") == "prev"


def test_q5_1_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q5_1 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = lambda c, p, **kw: GoQBack()
    dq.q5_1("prev")

    assert call_args.get("call_last_question") is True


def test_q5_2_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q5_2 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: "custom method"
    dq.q5_2("prev")

    assert call_args.get("current_answer") == "custom method"
    assert call_args.get("this_q") == "q5_2"
    assert call_args.get("next_q") == "q6"
    assert call_args.get("prev_answer") == "prev"


def test_q5_2_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q5_2 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_custom_entry"] = lambda p, **kw: GoQBack()
    dq.q5_2("prev")

    assert call_args.get("call_last_question") is True


def test_q6_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q6 when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q6("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q6"
    assert call_args.get("next_q") == "q6_1"
    assert call_args.get("prev_answer") == "prev"


def test_q6_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q6 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.interface_funcs_dict["get_yes_no"] = lambda p, **kw: GoQBack()
    dq.call_last_question = dummy_call_last_question
    dq.q6("prev")

    assert call_args.get("call_last_question") is True


def test_q6_1_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q6_1 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: "custom URL"
    dq.q6_1("prev")

    assert call_args.get("current_answer") == "custom URL"
    assert call_args.get("this_q") == "q6_1"
    assert call_args.get("next_q") == "q_end"
    assert call_args.get("prev_answer") == "prev"


def test_q6_1_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q6_1 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_custom_entry"] = lambda p, **kw: GoQBack()
    dq.q6_1("prev")

    assert call_args.get("call_last_question") is True


def test_q2_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2 flow when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q2("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q2"
    assert call_args.get("next_q") == "q2_1"
    assert call_args.get("prev_answer") == "prev"


def test_q2_no_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q2("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q2"
    assert call_args.get("next_q") == "q3"
    assert call_args.get("prev_answer") == "prev"


def test_q2_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.interface_funcs_dict["get_yes_no"] = lambda p, **kw: GoQBack()
    dq.call_last_question = dummy_call_last_question
    dq.q2("prev")

    assert call_args.get("call_last_question") is True


def test_q2_1_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_1 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q2_1("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q2_1"
    assert call_args.get("next_q") == "q2_2"
    assert call_args.get("prev_answer") == "prev"


def test_q2_1_no_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_1 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q2_1("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q2_1"
    assert call_args.get("next_q") == "q2_3"
    assert call_args.get("prev_answer") == "prev"


def test_q2_1_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2_1 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.interface_funcs_dict["get_yes_no"] = lambda p, **kw: GoQBack()
    dq.call_last_question = dummy_call_last_question
    dq.q2_1("prev")

    assert call_args.get("call_last_question") is True


def test_q2_2_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_2 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: TaxSpecificityChoices.speciesSpecif
    )
    dq.q2_2("prev")

    assert call_args.get("current_answer") == TaxSpecificityChoices.speciesSpecif
    assert call_args.get("this_q") == "q2_2"
    assert call_args.get("next_q") == "q2_2_1"
    assert call_args.get("prev_answer") == "prev"


def test_q2_2_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2_2 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = lambda c, p, **kw: GoQBack()
    dq.q2_2("prev")

    assert call_args.get("call_last_question") is True


def test_q2_2_1_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_2_1 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: "custom taxID"
    dq.q2_2_1("prev")

    assert call_args.get("current_answer") == "custom taxID"
    assert call_args.get("this_q") == "q2_2_1"
    assert call_args.get("next_q") == "q2_3"
    assert call_args.get("prev_answer") == "prev"


def test_q2_2_1_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2_2_1 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_custom_entry"] = lambda p, **kw: GoQBack()
    dq.q2_2_1("prev")

    assert call_args.get("call_last_question") is True


def test_q2_3_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_3 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: SeqTypeChoices.PROT_SEQS
    )
    dq.q2_3("prev")

    assert call_args.get("current_answer") == SeqTypeChoices.PROT_SEQS
    assert call_args.get("this_q") == "q2_3"
    assert call_args.get("next_q") == "q2_5_1"
    assert call_args.get("prev_answer") == "prev"


def test_q2_3_custom_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_3 flow when user answers custom.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: SeqTypeChoices.CUSTOM
    )
    dq.q2_3("prev")

    assert call_args.get("current_answer") == SeqTypeChoices.CUSTOM
    assert call_args.get("this_q") == "q2_3"
    assert call_args.get("next_q") == "q2_4"
    assert call_args.get("prev_answer") == "prev"


def test_q2_3_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2_3 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = lambda c, p, **kw: GoQBack()
    dq.q2_3("prev")

    assert call_args.get("call_last_question") is True


def test_q2_4_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_4 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: "custom seq type"
    dq.q2_4("prev")

    assert call_args.get("current_answer") == "custom seq type"
    assert call_args.get("this_q") == "q2_4"
    assert call_args.get("next_q") == "q2_5_1"
    assert call_args.get("prev_answer") == "prev"


def test_q2_4_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2_4 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_custom_entry"] = lambda p, **kw: GoQBack()
    dq.q2_4("prev")

    assert call_args.get("call_last_question") is True


def test_q2_5_1_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_5_1 flow when user answers yes.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: True
    dq.q2_5_1("prev")

    assert call_args.get("current_answer") is True
    assert call_args.get("this_q") == "q2_5_1"
    assert call_args.get("next_q") == "q2_5_2"
    assert call_args.get("prev_answer") == "prev"


def test_q2_5_1_no_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_5_1 when user answers no.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_yes_no"] = lambda prompt, **kw: False
    dq.q2_5_1("prev")

    assert call_args.get("current_answer") is False
    assert call_args.get("this_q") == "q2_5_1"
    assert call_args.get("next_q") == "q2_5_3"
    assert call_args.get("prev_answer") == "prev"


def test_q2_5_1_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2_5_1 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.interface_funcs_dict["get_yes_no"] = lambda p, **kw: GoQBack()
    dq.call_last_question = dummy_call_last_question
    dq.q2_5_1("prev")

    assert call_args.get("call_last_question") is True


def test_q2_5_2_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_5_2 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: "custom struct sim"
    dq.q2_5_2("prev")

    assert call_args.get("current_answer") == "custom struct sim"
    assert call_args.get("this_q") == "q2_5_2"
    assert call_args.get("next_q") == "q2_5_3"
    assert call_args.get("prev_answer") == "prev"


def test_q2_5_2_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2_5_2 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_custom_entry"] = lambda p, **kw: GoQBack()
    dq.q2_5_2("prev")

    assert call_args.get("call_last_question") is True


def test_q2_5_3_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_5_3 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: ThresholdChoices.EVALUE
    )
    dq.q2_5_3("prev")

    assert call_args.get("current_answer") == ThresholdChoices.EVALUE
    assert call_args.get("this_q") == "q2_5_3"
    assert call_args.get("next_q") == "q2_6_1"
    assert call_args.get("prev_answer") == "prev"


def test_q2_5_3_custom_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_5_3 flow when user answers custom.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: ThresholdChoices.CUSTOM
    )
    dq.q2_5_3("prev")

    assert call_args.get("current_answer") == ThresholdChoices.CUSTOM
    assert call_args.get("this_q") == "q2_5_3"
    assert call_args.get("next_q") == "q2_6"
    assert call_args.get("prev_answer") == "prev"


def test_q2_5_3_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2_5_3 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = lambda c, p, **kw: GoQBack()
    dq.q2_5_3("prev")

    assert call_args.get("call_last_question") is True


def test_q2_6_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_6 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: "custom metric"
    dq.q2_6("prev")

    assert call_args.get("current_answer") == "custom metric"
    assert call_args.get("this_q") == "q2_6"
    assert call_args.get("next_q") == "q2_6_1"
    assert call_args.get("prev_answer") == "prev"


def test_q2_6_1_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_6_1 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = {
        dq.q2_5_3: [ThresholdChoices.EVALUE],
        dq.q2_6: [],
    }
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: 0.05
    dq.q2_6_1("prev")

    assert call_args.get("current_answer") == [0.05]
    assert call_args.get("this_q") == "q2_6_1"
    assert call_args.get("next_q") == "q2_7"
    assert call_args.get("prev_answer") == "prev"


def test_q2_6_1_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2_6_1 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.question_stack = {
        dq.q2_5_3: [ThresholdChoices.EVALUE],
        dq.q2_6: [],
    }
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_custom_entry"] = lambda p, **kw: GoQBack()
    dq.q2_6_1("prev")

    assert call_args.get("call_last_question") is True


def test_q2_7_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_7 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: HomologyDBChoices.ENSEMBL
    )
    dq.q2_7("prev")

    assert call_args.get("current_answer") == HomologyDBChoices.ENSEMBL
    assert call_args.get("this_q") == "q2_7"
    assert call_args.get("next_q") == "q3"
    assert call_args.get("prev_answer") == "prev"


def test_q2_7_custom_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_7 flow when user answers custom.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_enum_choice_conversion"] = (
        lambda c, p, **kw: HomologyDBChoices.CUSTOM
    )
    dq.q2_7("prev")

    assert call_args.get("current_answer") == HomologyDBChoices.CUSTOM
    assert call_args.get("this_q") == "q2_7"
    assert call_args.get("next_q") == "q2_8"
    assert call_args.get("prev_answer") == "prev"


def test_q2_7_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2_7 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_enum_choice_conversion"] = lambda c, p, **kw: GoQBack()
    dq.q2_7("prev")

    assert call_args.get("call_last_question") is True


def test_q2_8_flow(dummy_interface_funcs, dummy_call_next_question_fixture):
    # Test q2_8 flow.
    call_args, dummy_call_next_question = dummy_call_next_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_next_question = dummy_call_next_question
    dummy_interface_funcs["get_custom_entry"] = lambda prompt, **kw: "custom database"
    dq.q2_8("prev")

    assert call_args.get("current_answer") == "custom database"
    assert call_args.get("this_q") == "q2_8"
    assert call_args.get("next_q") == "q3"
    assert call_args.get("prev_answer") == "prev"


def test_q2_8_GoQBack_flow(dummy_interface_funcs, dummy_call_last_question_fixture):
    # Test q2_8 flow when user answers GoQBack
    call_args, dummy_call_last_question = dummy_call_last_question_fixture
    dq = DeNovoQuestionnaire(dummy_interface_funcs)
    dq.call_last_question = dummy_call_last_question
    dq.interface_funcs_dict["get_custom_entry"] = lambda p, **kw: GoQBack()
    dq.q2_8("prev")

    assert call_args.get("call_last_question", False) is True
