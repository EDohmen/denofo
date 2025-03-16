import sys
import warnings
from pathlib import Path
from denofo.utils.ncbiTaxDBcheck import check_NCBI_taxDB
from denofo.comparator.compare import write_comparison
from denofo.converter.convert import load_from_json
from denofo.utils.helpers import compare_two_models, add_extension
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QFileDialog,
    QButtonGroup,
    QMessageBox,
)


class DNGFCompareGUI(QMainWindow):
    """
    The main window of the DeNoFo Comparator GUI.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeNoFo Compararator")
        self.setStyleSheet("background-color: #454746; color: white;")
        self.setMinimumWidth(600)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Input file 1
        file1_layout = QHBoxLayout()
        self.input1_info_button = QPushButton("?")
        self.input1_info_button.setFixedSize(16, 16)
        self.input1_info_button.clicked.connect(
            lambda: self.show_help(
                "Input File 1",
                (
                    "Select the first DNGF file to compare to another DNGF file. "
                    "The file has to be in DNGF format. If you have other file formats, "
                    "you can convert them to DNGF using the DeNoFo Converter tool."
                ),
            )
        )
        self.file1_input = QLineEdit()
        self.file1_input.setPlaceholderText("Select first DNGF file...")
        file1_button = QPushButton("Browse")
        file1_button.clicked.connect(lambda: self.browse_file(self.file1_input))
        file1_layout.addWidget(self.input1_info_button)
        file1_layout.addWidget(QLabel("Input 1:"))
        file1_layout.addWidget(self.file1_input)
        file1_layout.addWidget(file1_button)
        layout.addLayout(file1_layout)

        # Name 1
        name1_layout = QHBoxLayout()
        self.name1_info_button = QPushButton("?")
        self.name1_info_button.setFixedSize(16, 16)
        self.name1_info_button.clicked.connect(
            lambda: self.show_help(
                "Name 1",
                (
                    "The name of the first DNGF file. This name will be used in "
                    "the comparison output to clarify which annotation belongs to "
                    "which file. For example, the name can be authors and year of "
                    "the study: 'Grandchamp et al. (2021)'. "
                    "If you don't provide a name, the default name will be 'dngf_1'. "
                    "Name 1 and Name 2 have to be different and cannot be empty or the same."
                ),
            )
        )
        self.name1_input = QLineEdit()
        self.name1_input.setText("dngf_1")
        name1_layout.addWidget(self.name1_info_button)
        name1_layout.addWidget(QLabel("Name 1:"))
        name1_layout.addWidget(self.name1_input)
        layout.addLayout(name1_layout)

        # Input file 2
        file2_layout = QHBoxLayout()
        self.file2_info_button = QPushButton("?")
        self.file2_info_button.setFixedSize(16, 16)
        self.file2_info_button.clicked.connect(
            lambda: self.show_help(
                "Input File 2",
                (
                    "Select the second DNGF file to compare to the first DNGF file. "
                    "The file has to be in DNGF format. If you have other file formats, "
                    "you can convert them to DNGF using the DeNoFo Converter tool."
                ),
            )
        )
        self.file2_input = QLineEdit()
        self.file2_input.setPlaceholderText("Select second DNGF file...")
        file2_button = QPushButton("Browse")
        file2_button.clicked.connect(lambda: self.browse_file(self.file2_input))
        file2_layout.addWidget(self.file2_info_button)
        file2_layout.addWidget(QLabel("Input 2:"))
        file2_layout.addWidget(self.file2_input)
        file2_layout.addWidget(file2_button)
        layout.addLayout(file2_layout)

        # Name 2
        name2_layout = QHBoxLayout()
        self.name2_info_button = QPushButton("?")
        self.name2_info_button.setFixedSize(16, 16)
        self.name2_info_button.clicked.connect(
            lambda: self.show_help(
                "Name 2",
                (
                    "The name of the second DNGF file. This name will be used in "
                    "the comparison output to clarify which annotation belongs to "
                    "which file. For example, the name can be authors and year of "
                    "the study: 'Grandchamp et al. (2021)'. "
                    "If you don't provide a name, the default name will be 'dngf_2'. "
                    "Name 1 and Name 2 have to be different and cannot be empty or the same."
                ),
            )
        )
        self.name2_input = QLineEdit()
        self.name2_input.setText("dngf_2")
        name2_layout.addWidget(self.name2_info_button)
        name2_layout.addWidget(QLabel("Name 2:"))
        name2_layout.addWidget(self.name2_input)
        layout.addLayout(name2_layout)

        # Mode selection
        mode_layout = QHBoxLayout()
        self.mode_info_button = QPushButton("?")
        self.mode_info_button.setFixedSize(16, 16)
        self.mode_info_button.clicked.connect(
            lambda: self.show_help(
                "Mode",
                (
                    "Select the mode of comparison: 'Differences' or 'Similarities'. "
                    "Differences will show all differences between the two annotations, "
                    "Similarities will show all similarities between the two annotations."
                ),
            )
        )
        mode_layout.addWidget(self.mode_info_button)
        mode_layout.addWidget(QLabel("Mode:   "))
        self.mode_group = QButtonGroup()
        diff_radio = QRadioButton("Differences")
        diff_radio.setStyleSheet(
            """
            QRadioButton {
                color: white;
                background-color: #73403F;
            }
            QRadioButton:unchecked {
                color: grey;
                background-color: #454746;
            }
            QRadioButton:checked {
                color: white;
                background-color: #73403F;
            }
        """
        )
        diff_radio.setChecked(True)

        sim_radio = QRadioButton("Similarities")
        sim_radio.setStyleSheet(
            """
            QRadioButton {
            color: white;
            background-color: #4F6B90;
            }
            QRadioButton:unchecked {
            color: grey;
            background-color: #454746;
            }
            QRadioButton:checked {
            color: white;
            background-color: #4F6B90;
            }
        """
        )
        self.mode_group.addButton(diff_radio, 0)
        self.mode_group.addButton(sim_radio, 1)
        mode_layout.addWidget(diff_radio, stretch=1)
        mode_layout.addWidget(sim_radio, stretch=1)
        layout.addLayout(mode_layout)

        # Output file
        output_layout = QHBoxLayout()
        self.output_info_button = QPushButton("?")
        self.output_info_button.setFixedSize(16, 16)
        self.output_info_button.clicked.connect(
            lambda: self.show_help(
                "Output File",
                (
                    "Select the output file to save the comparison results. "
                    "If no output file is selected, the results will be only "
                    "displayed in the GUI and not saved in a file."
                ),
            )
        )
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Select output file (optional)...")
        output_button = QPushButton("Browse")
        output_button.clicked.connect(lambda: self.browse_save_file(self.output_input))
        output_layout.addWidget(self.output_info_button)
        output_layout.addWidget(QLabel("Output:"))
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(output_button)
        layout.addLayout(output_layout)

        # Compare button
        self.compare_button = QPushButton("Compare")
        self.compare_button.setStyleSheet(
            """
            QPushButton {
                background-color: #545A61;
                color: white;
                }
            QPushButton:disabled {
                background-color: #454746;
                color: grey;
             }
            QPushButton:enabled {
                background-color: #545A61;
                color: white;
            }
            """
        )
        self.compare_button.setEnabled(False)
        self.compare_button.clicked.connect(self.compare_files)
        layout.addWidget(self.compare_button)

        # Connect input fields to update function
        self.file1_input.textChanged.connect(self.update_compare_button)
        self.file2_input.textChanged.connect(self.update_compare_button)
        self.name1_input.textChanged.connect(self.update_compare_button)
        self.name2_input.textChanged.connect(self.update_compare_button)

        # Results display
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        layout.addWidget(self.results_display)

    def show_help(self, title, message):
        QMessageBox.information(self, title, message)

    # Function to update Compare button state
    def update_compare_button(self):
        enabled = all(
            [
                self.file1_input.text().strip(),
                self.file2_input.text().strip(),
                self.name1_input.text().strip(),
                self.name2_input.text().strip(),
                self.name1_input.text() != self.name2_input.text(),
            ]
        )
        self.compare_button.setEnabled(enabled)

    def browse_file(self, line_edit):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select DNGF File", "", "DNGF Files (*.dngf);;All Files (*)"
        )
        if filename:
            line_edit.setText(filename)

    def browse_save_file(self, line_edit):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Comparison As", "", "Text Files (*.txt);;All Files (*)"
        )
        if filename:
            line_edit.setText(str(add_extension(Path(filename))))

    def compare_files(self):
        try:
            # Get input parameters
            input1 = Path(self.file1_input.text())
            input2 = Path(self.file2_input.text())
            name1 = self.name1_input.text()
            name2 = self.name2_input.text()
            mode = "differences" if self.mode_group.checkedId() == 0 else "similarities"
            output = self.output_input.text()
            output_path = Path(output) if output else None

            # Load and compare files
            dngf1 = load_from_json(input1)
            dngf2 = load_from_json(input2)
            comparison = compare_two_models(dngf1, dngf2, mode)
            outstr = write_comparison(comparison, mode, None, name1, name2)
            if output_path:
                with open(output_path, "w") as f:
                    f.write(outstr)
                # Display File saved message
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText(f"File was saved to {output_path}")
                msg.setWindowTitle("Success")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()

            # Display results
            self.results_display.setText(outstr)

        except Exception as e:
            self.results_display.setText(f"Error: {str(e)}")

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Quit",
            "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    """Main function to run the GUI. Entry point for the application."""
    # Check the NCBI Taxonomy Database
    check_NCBI_taxDB()

    warnings.filterwarnings("ignore")
    app = QApplication([])
    window = DNGFCompareGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
