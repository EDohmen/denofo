import curses
import pytest
from enum import Enum
from pydantic import BaseModel, model_validator
from denofo.models import ModelValidError
from denofo.utils.constants import GoQBack
from denofo.questionnaire.questionnaire_cli import (
    valid_input_for_pydmodel,
    get_yes_no,
    get_enum_choice_conversion,
    get_custom_entry,
)


# DummyWindow simulates a curses window for our tests.
class DummyWindow:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0

    def getch(self):
        if self.index < len(self.keys):
            key = self.keys[self.index]
            self.index += 1
            return key
        return ord("n")  # Default key

    def clear(self):
        pass

    def addstr(self, *args, **kwargs):
        pass

    def refresh(self):
        pass

    def attron(self, attr):
        pass

    def attroff(self, attr):
        pass


def patch_curses(monkeypatch):
    monkeypatch.setattr(curses, "setupterm", lambda *args, **kwargs: None)
    monkeypatch.setattr(curses, "initscr", lambda: DummyWindow([ord("a")]))
    monkeypatch.setattr(curses, "nocbreak", lambda: None)
    monkeypatch.setattr(curses, "endwin", lambda: None)
    monkeypatch.setattr(curses, "cbreak", lambda: None)
    monkeypatch.setattr(curses, "echo", lambda: None)
    monkeypatch.setattr(curses, "noecho", lambda: None)
    monkeypatch.setattr(curses, "curs_set", lambda x: None)
    monkeypatch.setattr(curses, "start_color", lambda: None)
    monkeypatch.setattr(
        curses, "newwin", lambda *args, **kwargs: DummyWindow([ord("a")])
    )
    monkeypatch.setattr(curses, "has_colors", lambda: False)
    monkeypatch.setattr(curses, "init_pair", lambda *args, **kwargs: None)
    monkeypatch.setattr(curses, "color_pair", lambda n: n)
    monkeypatch.setattr(curses, "delay_output", lambda n: None)


# Dummy wrappers to simulate curses.wrapper behavior.
def dummy_wrapper_yes(func):
    # Simulate pressing 'y' in a yes/no prompt.
    dummy = DummyWindow([ord("y")])
    return func(dummy)


def dummy_wrapper_no(func):
    dummy = DummyWindow([ord("n")])
    return func(dummy)


def dummy_enum_wrapper(func):
    # Simulate selecting an enum option:
    # Press Enter to select the current option and then 'a' to accept.
    dummy = DummyWindow([ord("\n"), ord("a")])
    return func(dummy)


def dummy_wrapper_custom_single(func):
    # Simulate entering a custom entry.
    dummy = DummyWindow(
        [ord("c"), ord("u"), ord("s"), ord("t"), ord("o"), ord("m"), ord("\n")]
    )
    return func(dummy)


def dummy_wrapper_custom_multi(func):
    # Simulate entering a custom entry.
    dummy = DummyWindow(
        [
            ord("c"),
            ord("u"),
            ord("s"),
            ord("t"),
            ord("o"),
            ord("m"),
            ord("\n"),  # Enter the first custom entry
            ord("y"),  # Select "Yes" to add another custom entry
            ord("a"),
            ord("b"),
            ord("c"),
            ord("\n"),  # Enter the second custom entry
            ord("n"),  # Select "No" to finish
        ]
    )
    return func(dummy)


def dummy_wrapper_custom_multi_delete(func):
    # Simulate entering a custom entry.
    dummy = DummyWindow(
        [
            ord("a"),
            ord("b"),
            ord("c"),
            ord("\n"),  # Enter the first custom entry
            ord("y"),  # Select "Yes" to add another custom entry
            ord("a"),
            ord("s"),
            ord("d"),
            ord("\n"),  # Enter the second custom entry
            ord("d"),  # Select "d" to delete the second custom entry
            ord("n"),  # Select "No" to finish
        ]
    )
    return func(dummy)


def dummy_wrapper_custom_prev_answer(func):
    # Simulate entering a custom entry and then going back.
    dummy = DummyWindow([ord("a"), ord("b"), ord("c"), ord("\n")])
    return func(dummy)


def dummy_wrapper_custom_backspace(func):
    # Simulate entering a custom entry and then going back.
    dummy = DummyWindow([ord("a"), ord("b"), ord("c"), curses.KEY_BACKSPACE, ord("\n")])
    return func(dummy)


def dummy_wrapper_custom_del_and_try_empty_entry(func):
    # Simulate deleting prev_answer and then try accepting an empty entry (and accept "a" afterwards).
    dummy = DummyWindow([27, ord("\n"), ord("a"), ord("\n")])
    return func(dummy)


def dummy_wrapper_custom_multi_go_back(func):
    # Simulate going back a question in multi-choice mode after entering multiple custom entries.
    dummy = DummyWindow(
        [ord("a"), ord("\n"), ord("y"), ord("b"), ord("\n"), curses.KEY_LEFT]
    )
    return func(dummy)


def dummy_wrapper_go_back(func):
    # Simulate pressing left arrow key to go back.
    dummy = DummyWindow([curses.KEY_LEFT])
    return func(dummy)


def dummy_wrapper_forward(func):
    # Simulate pressing right arrow key to go forward.
    dummy = DummyWindow([curses.KEY_RIGHT])
    return func(dummy)


def dummy_wrapper_up_down_over_boarders_select_first(func):
    # Simulate pressing up and down arrow keys to go over boarders.
    dummy = DummyWindow(
        [
            curses.KEY_UP,
            curses.KEY_DOWN,
            curses.KEY_DOWN,
            curses.KEY_UP,
            ord(" "),  # Select the first option
            ord("a"),  # Accept the selection
        ]
    )
    return func(dummy)


def dummy_wrapper_unselect_accept(func):
    # Simulate pressing space to unselect prev_answer and then 'a' to accept.
    dummy = DummyWindow([ord(" "), ord("a"), ord(" "), ord("a")])
    return func(dummy)


def dummy_wrapper_select_multi_in_single_mode(func):
    # Simulate selecting multiple options in single choice mode.
    dummy = DummyWindow(
        [ord("\n"), curses.KEY_DOWN, ord("\n"), ord("a"), ord("\n"), ord("a")]
    )
    return func(dummy)


def dummy_wrapper_generic(func):
    # Generic dummy wrapper using a DummyWindow with a default key.
    dummy = DummyWindow([ord("a")])
    return func(dummy)


# -------------------------------------------------------------------
# Dummy model and validator for testing valid_input_for_pydmodel


class DummyModel(BaseModel):
    test_field: str = ""

    @model_validator(mode="after")
    def validate_field(self):
        if self.test_field == "valid":
            return True
        elif self.test_field == "warn":
            raise UserWarning("dummy warning")
        elif self.test_field == "ModelValidError":
            raise ModelValidError("dummy error")
        else:
            raise ValueError("dummy error")


# -------------------------------------------------------------------
# Tests for get_yes_no


def test_get_yes_no_true(monkeypatch):
    # Simulate user pressing 'y'
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_yes)
    result = get_yes_no("Do you agree?", section_idx=0, prev_answer=None)
    assert result is True


def test_get_yes_no_false(monkeypatch):
    # Simulate user pressing 'n'
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_no)
    result = get_yes_no("Do you agree?", section_idx=0, prev_answer=None)
    assert result is False


def test_get_yes_no_go_back(monkeypatch):
    # Simulate user pressing left arrow key
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_go_back)
    result = get_yes_no("Do you agree?", section_idx=0, prev_answer=None)
    assert isinstance(result, GoQBack)


def test_get_yes_no_prev_answer_yes(monkeypatch):
    # Simulate accepting the previous answer
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_forward)
    result = get_yes_no("Do you agree?", section_idx=0, prev_answer=True)
    assert result is True


def test_get_yes_no_prev_answer_no(monkeypatch):
    # Simulate accepting the previous answer
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_forward)
    result = get_yes_no("Do you agree?", section_idx=0, prev_answer=False)
    assert result is False


def test_get_yes_no_prev_answer_yes_forward(monkeypatch):
    # Simulate accepting the previous answer and then going forward
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_forward)
    result = get_yes_no("Do you agree?", section_idx=0, prev_answer=True)
    assert result is True


def test_get_yes_no_prev_answer_no_forward(monkeypatch):
    # Simulate accepting the previous answer and then going forward
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_forward)
    result = get_yes_no("Do you agree?", section_idx=0, prev_answer=False)
    assert result is False


# -------------------------------------------------------------------
# Tests for get_enum_choice_conversion


class DummyEnum(Enum):
    OPTION_A = "Option A"
    OPTION_B = "Option B"


@pytest.mark.parametrize("multi_choice", [True, False])
def test_get_enum_choice_conversion(multi_choice, monkeypatch):
    # Simulate selecting the only available option.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_enum_wrapper)
    result = get_enum_choice_conversion(
        DummyEnum,
        question="Select an option:",
        multi_choice=multi_choice,
        section_idx=0,
        prev_answer=None,
    )

    if multi_choice:
        assert result == ["Option A"]
    else:
        assert result == "Option A"


def test_get_enum_choice_conversion_back(monkeypatch):
    # Simulate going back a question.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_go_back)
    result = get_enum_choice_conversion(
        DummyEnum,
        question="Select an option:",
        multi_choice=False,
        section_idx=0,
        prev_answer=None,
    )
    assert isinstance(result, GoQBack)


def test_get_enum_choice_prev_answer(monkeypatch):
    # Simulate accepting the previous answer.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_forward)
    result = get_enum_choice_conversion(
        DummyEnum,
        question="Select an option:",
        multi_choice=False,
        section_idx=0,
        prev_answer="Option B",
    )
    assert result == "Option B"


def test_get_enum_choice_up_down_over_boarders(monkeypatch):
    # Simulate going over boarders with up and down arrow keys.
    patch_curses(monkeypatch)
    monkeypatch.setattr(
        curses, "wrapper", dummy_wrapper_up_down_over_boarders_select_first
    )
    result = get_enum_choice_conversion(
        DummyEnum,
        question="Select an option:",
        multi_choice=False,
        section_idx=0,
        prev_answer=None,
    )
    assert result == "Option A"


def test_get_enum_choice_unselect_accept(monkeypatch):
    # Simulate unselecting the previous answer and then accepting the new one.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_unselect_accept)
    result = get_enum_choice_conversion(
        DummyEnum,
        question="Select an option:",
        multi_choice=False,
        section_idx=0,
        prev_answer="Option A",
    )
    assert result == "Option A"


def test_get_enum_choice_select_multi_in_single_mode(monkeypatch):
    # Simulate selecting multiple options in single choice mode.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_select_multi_in_single_mode)
    result = get_enum_choice_conversion(
        DummyEnum,
        question="Select an option:",
        multi_choice=False,
        section_idx=0,
        prev_answer=None,
    )
    assert result == "Option A"


# -------------------------------------------------------------------
# Tests for valid_input_for_pydmodel


def test_valid_input_valid(monkeypatch):
    # Simulate valid input: "valid" should return True without errors.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_generic)

    result = valid_input_for_pydmodel(DummyModel, "test_field", "valid")
    assert result is True


def test_valid_input_warning(monkeypatch):
    # Simulate a warning input: "warn" should raise UserWarning and return True.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_generic)

    result = valid_input_for_pydmodel(DummyModel, "test_field", "warn")
    assert result is True


def test_valid_input_model_valid_error(monkeypatch):
    # Simulate a ModelValidError input: "ModelValidError" should raise ModelValidError.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_generic)

    result = valid_input_for_pydmodel(DummyModel, "test_field", "ModelValidError")
    assert result is True


def test_valid_input_invalid(monkeypatch):
    # Simulate invalid input: any input other than "valid" or "warn" or "ModelValidError" should return False.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_generic)

    result = valid_input_for_pydmodel(DummyModel, "test_field", "invalid")
    assert result is False


# -------------------------------------------------------------------
# Tests for get_custom_entry


def test_get_custom_entry_single(monkeypatch):
    # Simulate entering a single custom entry.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_custom_single)

    result = get_custom_entry("Enter a custom entry:", section_idx=0, prev_answer=None)
    assert result == "custom"


def test_get_custom_entry_multi(monkeypatch):
    # Simulate entering multiple custom entries.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_custom_multi)

    result = get_custom_entry(
        "Enter a custom entry:", section_idx=0, prev_answer=None, multi_choice=True
    )
    assert result == ["custom", "abc"]


def test_get_custom_entry_multi_delete(monkeypatch):
    # Simulate entering multiple custom entries and deleting one.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_custom_multi_delete)

    result = get_custom_entry(
        "Enter a custom entry:", section_idx=0, prev_answer=None, multi_choice=True
    )
    assert result == ["abc"]


def test_get_custom_entry_go_back(monkeypatch):
    # Simulate entering a custom entry and then going back.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_go_back)

    result = get_custom_entry("Enter a custom entry:", section_idx=0, prev_answer=None)
    assert isinstance(result, GoQBack)


def test_get_custom_entry_prev_answer(monkeypatch):
    # Simulate accepting the previous answer.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_custom_prev_answer)

    result = get_custom_entry("Enter a custom entry:", section_idx=0, prev_answer="abc")
    assert result == "abcabc"


def test_get_custom_entry_backspace(monkeypatch):
    # Simulate entering a custom entry and then going back.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_custom_backspace)

    result = get_custom_entry("Enter a custom entry:", section_idx=0, prev_answer=None)
    assert result == "ab"


def test_get_custom_entry_del_and_try_empty_entry(monkeypatch):
    # Simulate deleting prev_answer and then try accepting an empty entry (and accept "a" afterwards).
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_custom_del_and_try_empty_entry)

    result = get_custom_entry("Enter a custom entry:", section_idx=0, prev_answer="abc")
    assert result == "a"


def test_custom_entry_multi_choice_go_back(monkeypatch):
    # Simulate going back a question.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_custom_multi_go_back)
    result = get_custom_entry(
        "Enter a custom entry:",
        section_idx=0,
        multi_choice=True,
        prev_answer=None,
    )
    assert isinstance(result, GoQBack)


"""
def test_get_custom_entry_no_entry(monkeypatch):
    # Simulate not entering any custom entries.
    patch_curses(monkeypatch)
    monkeypatch.setattr(curses, "wrapper", dummy_wrapper_generic)

    result = get_custom_entry("Enter a custom entry:", section_idx=0, prev_answer=None)
    assert result is None
"""
