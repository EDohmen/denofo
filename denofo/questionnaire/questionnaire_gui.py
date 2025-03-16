import sys
from typing import Any
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, ValidationError
from denofo.utils.constants import SECTIONS, GoQBack
from denofo.converter.convert import convert_to_json
from denofo.models import ModelValidError
from denofo.utils.ncbiTaxDBcheck import check_NCBI_taxDB
from denofo.questionnaire.questions import DeNovoQuestionnaire
from PyQt6.QtCore import Qt, QObject
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QLineEdit,
    QMessageBox,
    QListWidgetItem,
    QRadioButton,
    QButtonGroup,
    QDialog,
    QFileDialog,
)


def clearLayout(layout):
    """
    Function to clear the layout of a QWidget.
    """
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


class QSingleton(type(QObject)):
    """Metaclass for Qt classes that are singletons."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = super().__call__(*args, **kwargs)
        return self.instance


class MainWindow(QMainWindow, metaclass=QSingleton):
    """
    Main window class for the GUI application.
    """

    _geometry = None
    _centered = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("DeNoFo Questionnaire")
        self.setStyleSheet("background-color: #454746; color: white;")
        self.resize(500, 250)  # Set default size

        if MainWindow._geometry is not None:
            self.setGeometry(*MainWindow._geometry)
        else:
            self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen is not None:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())
            MainWindow._geometry = self.geometry().getRect()
            MainWindow._centered = True
        else:
            # Fallback position if screen cannot be detected
            MainWindow._geometry = (100, 100, 500, 250)
            self.setGeometry(*MainWindow._geometry)
            MainWindow._centered = True

    def closeEvent(self, event):
        MainWindow._geometry = self.geometry().getRect()
        if event.spontaneous():
            if (
                QMessageBox.question(
                    self,
                    "Quit",
                    "Are you sure you want to quit?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                == QMessageBox.StandardButton.Yes
            ):
                event.accept()
                QApplication.closeAllWindows()
                sys.exit(0)
            else:
                event.ignore()
        else:
            event.accept()


class ErrorDialog(QDialog):
    """
    Error dialog class for the GUI application.
    """

    def __init__(self, err_warn_type: str = "Error", error_message: str = ""):
        super().__init__()

        self.err_warn_type = err_warn_type
        self.error_message = error_message

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.err_warn_type)

        layout = QVBoxLayout()
        error_label = QLabel(self.error_message)
        error_label.setStyleSheet("font-weight: bold; color: white;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_label)
        ok_button = QPushButton("Ok")
        layout.addWidget(ok_button)

        if self.err_warn_type == "Error":
            self.setStyleSheet("background-color: #8D3832;")
        else:
            self.setStyleSheet("background-color: #4F6B90;")

        self.setLayout(layout)
        ok_button.clicked.connect(self.close)


def show_error_message(warn_type: str = "Error", message: str = ""):
    """
    Function to show an error message to the user.
    """
    # Create main window
    main_window = MainWindow()
    main_layout = QVBoxLayout()

    # Create a central widget
    central_widget = QWidget(parent=main_window)

    # Add ErrorDialog widget
    error_dialog = ErrorDialog(warn_type, message)
    main_layout.addWidget(error_dialog, stretch=1)

    # Set the layout
    central_widget.setLayout(main_layout)
    main_window.setCentralWidget(central_widget)

    error_dialog.exec()

    return


class ProgressBar(QWidget):
    """
    Progress bar class for the GUI application.
    """

    def __init__(self, section_idx):
        super().__init__()
        self.section_idx = section_idx
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        for idx, section in enumerate(SECTIONS):
            section_button = QPushButton(section)
            section_button.setStyleSheet(
                "background-color: #545A61; font-weight: bold;"  # lowlight
            )
            if idx == self.section_idx:
                section_button.setStyleSheet(
                    "background-color: #4F6B90; font-weight: bold;"  # highlight
                )
            layout.addWidget(section_button)
            if idx < len(SECTIONS) - 1:
                dot_label = QLabel(" • ")
            layout.addWidget(dot_label)
        self.setLayout(layout)


class Back_button(QPushButton):
    """
    Back button class for the GUI application.
    """

    def __init__(self):
        super().__init__()
        self.choice = None
        self.initUI()

    def initUI(self):
        self.setText("← Go Back")
        self.setStyleSheet("background-color: #8D3832; padding: 5px;")
        self.clicked.connect(self.on_click)

    def on_click(self):
        self.choice = GoQBack()
        # clearLayout removes all widgets from the layout of the center_widget (such as ProgressBar, Enum_choice_selection and other open Dialogs)
        # without this the Back_button just disappears, but the center_widget stays open
        clearLayout(self.parent().layout())


class Enum_choice_selection(QDialog):
    """
    Enum choice selection class for the GUI application.
    """

    def __init__(self, enum_choices, question, multi_choice=False, prev_answer=None):
        super().__init__()

        self.enum_choices = enum_choices
        self.question = question
        self.multi_choice = multi_choice
        self.prev_answer = prev_answer

        self.choice = None

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Select an option")

        layout = QVBoxLayout()
        if self.question:
            question_label = QLabel(self.question)
            layout.addWidget(question_label)

        if self.multi_choice:
            self.choices = QListWidget()
            self.choices.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            self.choices.setStyleSheet(
                "QListWidget::item:selected { background-color: #7E8A97; }"
            )
            for choice in self.enum_choices:
                item = QListWidgetItem(choice.value)
                self.choices.addItem(item)
                if self.prev_answer and choice.value in self.prev_answer:
                    self.choices.setCurrentItem(item)
            layout.addWidget(self.choices)
            self.choices.itemSelectionChanged.connect(self.update_submit_button)
        else:
            self.choices = QButtonGroup()
            for idx, choice in enumerate(self.enum_choices):
                radio_button = QRadioButton(choice.value)
                if self.prev_answer and choice.value == self.prev_answer.value:
                    radio_button.setChecked(True)
                self.choices.addButton(radio_button, idx)
                layout.addWidget(radio_button)
                radio_button.toggled.connect(self.update_submit_button)

        submit_button = QPushButton("Continue →")
        submit_button.setStyleSheet(
            """
            QPushButton {
                background-color: #454746;
                color: grey;
                padding: 5px;
            }
            QPushButton:enabled {
                background-color: #545A61;
                color: white;
            }
            QPushButton:disabled {
                background-color: #454746;
                color: gray;
            }
            """
        )
        submit_button.setEnabled(bool(self.prev_answer))
        layout.addWidget(submit_button)
        self.setLayout(layout)

        submit_button.clicked.connect(self.on_submit)
        self.submit_button = submit_button

    def update_submit_button(self):
        if self.multi_choice:
            has_selection = len(self.choices.selectedItems()) > 0
        else:
            has_selection = self.choices.checkedId() != -1
        self.submit_button.setEnabled(has_selection)

    def on_submit(self):
        if self.multi_choice:
            self.choice = [item.text() for item in self.choices.selectedItems()]
        else:
            self.choice = list(self.enum_choices)[self.choices.checkedId()]
        self.close()


class Custom_entry(QDialog):
    """
    Custom entry class for the GUI application.
    """

    def __init__(
        self, question, multi_choice: bool, prev_answer: str | list[str] | None = None
    ):
        super().__init__()

        self.question = question
        self.multi_choice = multi_choice
        self.prev_answer = prev_answer

        self.choice = None

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Enter a value")

        layout = QVBoxLayout()
        if self.question:
            question_label = QLabel(self.question)
            layout.addWidget(question_label)

        if self.multi_choice:
            self.entries = []
            self.add_entry_button = QPushButton("+")
            self.remove_entry_button = QPushButton("-")
            self.entry_layout = QVBoxLayout()
            entry = QLineEdit()
            self.entries.append(entry)
            self.entry_layout.addWidget(entry)
            layout.addLayout(self.entry_layout)
            button_layout = QHBoxLayout()
            button_layout.addWidget(self.add_entry_button)
            button_layout.addWidget(self.remove_entry_button)
            layout.addLayout(button_layout)
            self.add_entry_button.clicked.connect(self.add_entry)
            self.remove_entry_button.clicked.connect(self.remove_entry)
            if self.prev_answer:
                self.remove_entry(ignore_warning=True)
                for entry_text in self.prev_answer:
                    self.add_entry(ignore_warning=True)
                    self.entries[-1].setText(entry_text)
        else:
            self.entry = QLineEdit()
            if self.prev_answer:
                self.entry.setText(self.prev_answer)
            layout.addWidget(self.entry)

        submit_button = QPushButton("Continue →")
        submit_button.setStyleSheet(
            """
            QPushButton {
                background-color: #454746;
                color: grey;
                padding: 5px;
            }
            QPushButton:enabled {
                background-color: #545A61;
                color: white;
            }
            QPushButton:disabled {
                background-color: #454746;
                color: gray;
            }
            """
        )
        layout.addWidget(submit_button)
        self.setLayout(layout)
        submit_button.clicked.connect(self.on_submit)
        self.submit_button = submit_button
        self.update_submit_button()
        self.connect_signals()

    def connect_signals(self):
        if self.multi_choice:
            for entry in self.entries:
                entry.textChanged.connect(self.update_submit_button)
            self.add_entry_button.clicked.connect(self.update_submit_button)
            self.remove_entry_button.clicked.connect(self.update_submit_button)
        else:
            self.entry.textChanged.connect(self.update_submit_button)

    def update_submit_button(self):
        if self.multi_choice:
            has_text = all(entry.text().strip() for entry in self.entries)
        else:
            has_text = bool(self.entry.text().strip())
        self.submit_button.setEnabled(has_text)

    def on_submit(self):
        if self.multi_choice:
            if any(not entry.text().strip() for entry in self.entries):
                QMessageBox.warning(
                    self,
                    "Incomplete Entries",
                    "Please fill in all entries before submitting.",
                )
                return
            self.choice = [entry.text() for entry in self.entries]
        else:
            if not self.entry.text().strip():
                QMessageBox.warning(
                    self,
                    "Empty Field",
                    "Please fill in the text field before submitting.",
                )
                return
            self.choice = self.entry.text()
        self.close()

    def add_entry(self, ignore_warning: bool = False):
        if all(entry.text().strip() for entry in self.entries) or ignore_warning:
            entry = QLineEdit()
            self.entries.append(entry)
            self.entry_layout.addWidget(entry)
            if not ignore_warning:
                entry.textChanged.connect(self.update_submit_button)
        else:
            QMessageBox.warning(
                self,
                "Incomplete Entries",
                "Please fill in all existing entries before adding a new one.",
            )

    def remove_entry(self, ignore_warning: bool = False):
        if (self.multi_choice and len(self.entries) > 1) or ignore_warning:
            entry = self.entries.pop()
            self.entry_layout.removeWidget(entry)
            entry.deleteLater()
            if not ignore_warning:
                self.update_submit_button()
        else:
            QMessageBox.warning(
                self,
                "Cannot Remove",
                "At least one entry is required.",
            )


class Yes_no(QDialog):
    """
    Yes or No class for the GUI application.
    """

    def __init__(self, question, prev_answer=None):
        super().__init__()

        self.question = question
        self.prev_answer = prev_answer

        self.choice = None

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Yes or No")

        layout = QVBoxLayout()
        if self.question:
            question_label = QLabel(self.question)
            layout.addWidget(question_label)
        self.yes_button = QPushButton("Yes")
        self.no_button = QPushButton("No")
        if self.prev_answer is not None:
            if self.prev_answer is True:
                self.yes_button.setStyleSheet("background-color: #2E5539")
            elif self.prev_answer is False:
                self.no_button.setStyleSheet("background-color: #73403F")
        layout.addWidget(self.yes_button)
        layout.addWidget(self.no_button)
        self.setLayout(layout)

        self.yes_button.clicked.connect(self.on_yes)
        self.no_button.clicked.connect(self.on_no)

    def on_yes(self):
        self.choice = True
        self.close()

    def on_no(self):
        self.choice = False
        self.close()


def get_enum_choice_conversion(
    my_enum: Enum,
    question: str = "",
    multi_choice: bool = False,
    section_idx: int = 0,
    prev_answer: Any = None,
) -> Any:
    """
    Function to get the user's choice for an Enum.

    :param my_enum: Enum class to get the choices from
    :type my_enum: Enum
    :param question: Question to ask the user
    :type question: str
    :param multi_choice: Whether the user can select multiple choices
    :type multi_choice: bool
    :param section_idx: Index of the section in the progress bar
    :type section_idx: int
    :param prev_answer: Previous answer given by the user
    :type prev_answer: Any
    :return: User's choice
    :rtype: Any
    """
    choice = None

    # Create main window
    main_window = MainWindow()
    main_layout = QVBoxLayout()

    # Create a central widget and set the layout
    central_widget = QWidget(parent=main_window)

    # Add progress bar
    progress_bar = ProgressBar(section_idx)
    main_layout.addWidget(progress_bar, stretch=2)

    # Add Enum_choice_selection widget
    enum_selection_widget = Enum_choice_selection(
        my_enum, question, multi_choice, prev_answer
    )
    main_layout.addWidget(enum_selection_widget, stretch=7)

    # Add Back_button widget
    back_button = Back_button()
    main_layout.addWidget(back_button, stretch=1)

    # Set the layout
    central_widget.setLayout(main_layout)
    main_window.setCentralWidget(central_widget)

    # Execute the Yes_no dialog
    enum_selection_widget.exec()

    if isinstance(back_button.choice, GoQBack):
        choice = GoQBack()
    else:
        choice = enum_selection_widget.choice

    return choice


def get_custom_entry(
    question: str = "",
    multi_choice: bool = False,
    section_idx: int = 0,
    prev_answer: any = None,
) -> Any:
    """
    Function to get the user's custom entry.

    :param question: Question to ask the user
    :type question: str
    :param multi_choice: Whether the user can enter multiple values
    :type multi_choice: bool
    :param section_idx: Index of the section in the progress bar
    :type section_idx: int
    :param prev_answer: Previous answer given by the user
    :type prev_answer: any
    :return: User's choice
    :rtype: Any
    """
    choice = None

    # Create main window
    main_window = MainWindow()
    main_layout = QVBoxLayout()

    # Create a central widget
    central_widget = QWidget(parent=main_window)

    # Add progress bar
    progress_bar = ProgressBar(section_idx)
    main_layout.addWidget(progress_bar, stretch=2)

    # Add Custom_entry widget
    custom_entry_widget = Custom_entry(question, multi_choice, prev_answer)
    main_layout.addWidget(custom_entry_widget, stretch=7)

    # Add Back_button widget
    back_button = Back_button()
    main_layout.addWidget(back_button, stretch=1)

    # Set the layout
    central_widget.setLayout(main_layout)
    main_window.setCentralWidget(central_widget)

    # Execute the Yes_no dialog
    custom_entry_widget.exec()

    if isinstance(back_button.choice, GoQBack):
        choice = GoQBack()
    else:
        choice = custom_entry_widget.choice

    return choice


def get_yes_no(
    question: str = "", section_idx: int = 0, prev_answer: any = None
) -> bool:
    """
    Function to get the user's choice for Yes or No.

    :param question: Question to ask the user
    :type question: str
    :param section_idx: Index of the section in the progress bar
    :type section_idx: int
    :param prev_answer: Previous answer given by the user
    :type prev_answer: any
    :return: User's choice
    :rtype: bool
    """
    choice = None

    # Create main window
    main_window = MainWindow()
    main_layout = QVBoxLayout()

    # Create a central widget
    central_widget = QWidget(parent=main_window)

    # Add progress bar
    progress_bar = ProgressBar(section_idx)
    main_layout.addWidget(progress_bar, stretch=2)

    # Add Yes_no widget
    yes_no_widget = Yes_no(question, prev_answer)
    main_layout.addWidget(yes_no_widget, stretch=7)

    # Add Back_button widget
    back_button = Back_button()
    main_layout.addWidget(back_button, stretch=1)

    # Set the layout
    central_widget.setLayout(main_layout)
    main_window.setCentralWidget(central_widget)

    # Execute the Yes_no dialog
    yes_no_widget.exec()

    if isinstance(back_button.choice, GoQBack):
        choice = GoQBack()
    else:
        choice = yes_no_widget.choice

    return choice


def valid_input_for_pydmodel(
    pydmodel: BaseModel, field_name: str, inp_val: Any
) -> bool:
    """
    Validate the input value with a certain pydantic model and model field
    to ask the user for input again if the input is invalid.

    :param pydmodel: Pydantic model to validate the input with
    :type pydmodel: BaseModel
    :param field_name: Field name of the model to validate the input with
    :type field_name: str
    :param inp_val: Input value to validate
    :type inp_val: Any
    :return: Whether the input is valid
    :rtype: bool
    """
    try:
        # pydmodel.validate({field_name: inp_val})
        pydmodel.__pydantic_validator__.validate_assignment(
            pydmodel.model_construct(), field_name, inp_val
        )
        return True
    except UserWarning as w:
        warning = str(w)
        show_error_message("Warning", warning)
        return True
    except ValidationError as e:
        errors = e.errors()
        modelValErr = errors[0].get("ctx", dict()).get("error", None)
        if isinstance(modelValErr, ModelValidError):
            return True
        else:
            val_err = e
            err_msg = ", ".join(val_err.errors()[0]["msg"].split(",")[1:])
            show_error_message("Error", err_msg)
            return False


def save_annotation(gene_annotation: BaseModel):
    """
    Function to save the gene annotation in the dngf format into a file.

    :param gene_annotation: Gene annotation to save
    :type gene_annotation: BaseModel
    """
    fileName = None
    main_window = MainWindow()

    while not fileName:
        fileName, _ = QFileDialog.getSaveFileName(
            main_window, "Save File", "my_model.dngf", "dngf (*.dngf)"
        )
        if not fileName:
            reply = QMessageBox.question(
                main_window,
                "Quit without Saving?",
                "Do you want to close the application without saving the annotation file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                # quit without saving file
                return None

    convert_to_json(gene_annotation, Path(fileName))


def main_app():
    """
    The main function for the GUI application. Calls questionnaire functions
    and saves the gene annotation, while showing Widgets in the privously initiated
    MainWindow.
    """
    GUI_INTERFACE_FUNCTS = {
        "get_enum_choice_conversion": get_enum_choice_conversion,
        "get_custom_entry": get_custom_entry,
        "get_yes_no": get_yes_no,
        "valid_input_for_pydmodel": valid_input_for_pydmodel,
    }

    try:
        # Start of the questionnaire
        de_novo_questionnaire = DeNovoQuestionnaire(GUI_INTERFACE_FUNCTS)
        gene_annotation = de_novo_questionnaire.deNovoGeneAnnotation

        # save model in the dngf (de novo gene format) format (JSON)
        save_annotation(gene_annotation)

        # close all windows and quit the application
        QApplication.closeAllWindows()
        sys.exit(0)

    except Exception as e:
        raise NotImplementedError(f"Error: {e}")


def main():
    """
    The main function of the program. Entry point for the GUI executable.
    """
    # Check the NCBI Taxonomy Database
    check_NCBI_taxDB()

    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    main_app()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
