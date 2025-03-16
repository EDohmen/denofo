import pytest
from unittest.mock import patch
from enum import Enum
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QLineEdit,
)
from PyQt6.QtCore import Qt
from pydantic import BaseModel
from denofo.utils.constants import GoQBack

from denofo.questionnaire.questionnaire_gui import (
    clearLayout,
    MainWindow,
    ErrorDialog,
    ProgressBar,
    Back_button,
    Enum_choice_selection,
    Custom_entry,
    Yes_no,
    get_enum_choice_conversion,
    get_custom_entry,
    get_yes_no,
    valid_input_for_pydmodel,
)


class MockEnum(Enum):
    OPTION1 = "Option 1"
    OPTION2 = "Option 2"
    OPTION3 = "Option 3"


class MockModel(BaseModel):
    text_field: str
    number_field: int
    bool_field: bool


def test_clear_layout(qtbot):
    """Test the clearLayout function."""
    layout = QVBoxLayout()
    widget = QWidget()
    layout.addWidget(widget)

    assert layout.count() == 1
    clearLayout(layout)
    assert layout.count() == 0


def test_main_window(qtbot):
    """Test the MainWindow class."""
    # Test singleton behavior
    window1 = MainWindow()
    window2 = MainWindow()
    qtbot.addWidget(window1)
    assert window1 is window2

    # Test title and style
    assert window1.windowTitle() == "DeNoFo Questionnaire"
    assert "background-color: #454746" in window1.styleSheet()


def test_error_dialog(qtbot):
    """Test the ErrorDialog class."""
    # Test error dialog
    error_dialog = ErrorDialog("Error", "Test error message")
    qtbot.addWidget(error_dialog)
    assert error_dialog.windowTitle() == "Error"
    assert "background-color: #8D3832" in error_dialog.styleSheet()

    # Test warning dialog
    warning_dialog = ErrorDialog("Warning", "Test warning message")
    qtbot.addWidget(warning_dialog)
    assert warning_dialog.windowTitle() == "Warning"
    assert "background-color: #4F6B90" in warning_dialog.styleSheet()


def test_progress_bar(qtbot):
    """Test the ProgressBar class."""
    # Test progress bar at first section
    progress_bar = ProgressBar(0)
    qtbot.addWidget(progress_bar)
    assert progress_bar.section_idx == 0

    # Test progress bar at second section
    progress_bar = ProgressBar(1)
    qtbot.addWidget(progress_bar)
    assert progress_bar.section_idx == 1


def test_back_button(qtbot):
    """Test the Back_button class."""
    back_button = Back_button()
    qtbot.addWidget(back_button)
    assert back_button.text() == "← Go Back"
    assert back_button.choice is None

    # Test click behavior with qtbot's mouseClick
    parent_widget = QWidget()
    parent_layout = QVBoxLayout()
    parent_widget.setLayout(parent_layout)
    parent_layout.addWidget(back_button)
    qtbot.addWidget(parent_widget)

    qtbot.mouseClick(back_button, Qt.MouseButton.LeftButton)
    assert isinstance(back_button.choice, GoQBack)


@pytest.mark.parametrize("multi_choice", [True, False])
def test_enum_choice_selection(qtbot, multi_choice):
    """Test the Enum_choice_selection class."""
    enum_choices = MockEnum
    question = "Test question"

    dialog = Enum_choice_selection(enum_choices, question, multi_choice)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Select an option"

    if multi_choice:
        assert (
            dialog.choices.selectionMode()
            == dialog.choices.SelectionMode.MultiSelection
        )
    else:
        assert len(dialog.choices.buttons()) == len(enum_choices)


@pytest.mark.parametrize("multi_choice", [True, False])
def test_custom_entry(qtbot, multi_choice):
    """Test the Custom_entry class."""

    def patch_entry_text(entry, text):
        """Helper function to patch the text of an entry."""
        return patch.object(entry, "text", return_value=text)

    question = "Test question"

    dialog = Custom_entry(question, multi_choice)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Enter a value"

    if multi_choice:
        assert len(dialog.entries) == 1

        # Test adding an entry
        with patch_entry_text(dialog.entries[0], "test"):
            dialog.add_entry()
            assert len(dialog.entries) == 2

        # Test removing an entry
        dialog.remove_entry()
        assert len(dialog.entries) == 1

        # Test blocking removal of the only entry
        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warning:
            dialog.remove_entry()
            assert len(dialog.entries) == 1
            mock_warning.assert_called_once()

        # Test that adding an entry when the last entry is empty is blocked
        with (
            patch_entry_text(dialog.entries[0], "test"),
            patch("PyQt6.QtWidgets.QMessageBox.warning") as _,
            mock_warning,
        ):
            dialog.add_entry()
            dialog.add_entry()
            assert len(dialog.entries) == 2
            mock_warning.assert_called_once()
            dialog.remove_entry()

        # Test that adding an entry is blocked when a middle entry is cleared
        with (
            patch_entry_text(dialog.entries[0], "test1"),
            patch("PyQt6.QtWidgets.QMessageBox.warning") as _,
            mock_warning,
        ):
            dialog.add_entry()
            dialog.entries[1].setText("test2")
            dialog.add_entry()
            dialog.entries[2].setText("test3")
            dialog.entries[1].setText("")
            dialog.add_entry()
            assert len(dialog.entries) == 3
            mock_warning.assert_called_once()
    else:
        assert isinstance(dialog.entry, QLineEdit)


def test_yes_no(qtbot):
    """Test the Yes_no class."""
    question = "Test question"

    dialog = Yes_no(question)
    qtbot.addWidget(dialog)
    assert dialog.windowTitle() == "Yes or No"

    # Test yes button
    with patch.object(dialog, "close"):
        qtbot.mouseClick(dialog.yes_button, Qt.MouseButton.LeftButton)
        assert dialog.choice is True

    # Test no button
    dialog.choice = None
    with patch.object(dialog, "close"):
        qtbot.mouseClick(dialog.no_button, Qt.MouseButton.LeftButton)
        assert dialog.choice is False


def test_get_custom_entry_with_autospec(qtbot):
    """
    Test get_custom_entry returns the entered value without MagicMock errors
    by patching Back_button to its actual class.
    """
    expected_text = "User input"
    # Patch the exec method of Custom_entry to simulate user input.
    with patch.object(
        Custom_entry, "exec", lambda self: setattr(self, "choice", expected_text)
    ):
        # Patch Back_button to use the real class instead of a MagicMock.
        with patch(
            "denofo.questionnaire.questionnaire_gui.Back_button", new=Back_button
        ):
            result = get_custom_entry("Enter value", multi_choice=False, section_idx=0)
    assert result == expected_text


def test_get_enum_choice_conversion(qtbot):
    """
    Test get_enum_choice_conversion returns the correct enum value.
    Here we simulate the user selecting OPTION2.
    """
    with patch.object(
        Enum_choice_selection, "exec", lambda self: setattr(self, "choice", "Option 2")
    ):
        result = get_enum_choice_conversion(
            MockEnum, "Select an option", multi_choice=False, section_idx=0
        )
    assert result == MockEnum.OPTION2.value


def test_get_yes_no_cancel(qtbot):
    """
    Test get_yes_no returns a valid boolean when the user cancels the dialog.
    Here we simulate no choice being made (i.e. None), then the back button is not triggered.
    """
    with patch.object(Yes_no, "exec", lambda self: setattr(self, "choice", False)):
        result = get_yes_no("Do you agree?", section_idx=0, prev_answer=None)
    assert result is False


def test_enum_choice_selection_no_previous(qtbot):
    """
    Test Enum_choice_selection when no previous answer is provided.
    """
    enum_choices = MockEnum
    question = "Select an option"
    dialog = Enum_choice_selection(enum_choices, question, multi_choice=False)
    qtbot.addWidget(dialog)
    # By default no radio buttons selected, so submit should be disabled.
    for button in dialog.choices.buttons():
        assert not button.isChecked()


def test_custom_entry_multi_incomplete(qtbot):
    """
    Test Custom_entry multi_choice mode does not submit when one or more entries are empty.
    """
    with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warning:
        dialog = Custom_entry("Enter multiple values", multi_choice=True)
        qtbot.addWidget(dialog)
        # Initially only one entry exists.
        assert len(dialog.entries) == 1
        # Leave the entry empty and try to submit.
        dialog.on_submit()
        # The dialog should not close the submission; choice remains None.
        assert dialog.choice is None
        mock_warning.assert_called_once()


def test_valid_input_for_pydmodel():
    """Test the valid_input_for_pydmodel function."""
    model = MockModel(text_field="test", number_field=1, bool_field=True)

    # Test valid input
    assert valid_input_for_pydmodel(model, "text_field", "new text") is True
    assert valid_input_for_pydmodel(model, "number_field", 42) is True
    assert valid_input_for_pydmodel(model, "bool_field", False) is True

    # Test invalid input
    with patch(
        "denofo.questionnaire.questionnaire_gui.show_error_message"
    ) as mock_error:
        assert valid_input_for_pydmodel(model, "number_field", "not a number") is False
        mock_error.assert_called_once()
