import sys
import warnings
from pathlib import Path
from denofo.utils.ncbiTaxDBcheck import check_NCBI_taxDB
from denofo.utils.helpers import infer_format_from_extension
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QPlainTextEdit,
)
from denofo.converter.convert import (
    load_from_json,
    load_from_pickle,
    load_from_fasta,
    load_from_gff,
    encode_short_str,
    decode_short_str,
    convert_to_json,
    convert_to_pickle,
    annotate_fasta,
    annotate_gff,
)


class DngfConverterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeNoFo Converter")
        self.setStyleSheet("background-color: #454746; color: white;")
        self.resize(600, 200)
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        label_width = 150  # Set a fixed width for all labels

        # Input file selection
        input_layout = QHBoxLayout()
        self.input_info_button = QPushButton("?")
        self.input_info_button.setFixedSize(16, 16)
        self.input_info_button.clicked.connect(
            lambda: self.show_help(
                "Input File",
                (
                    "Select the input file to be converted. This file has to "
                    "contain the DeNoFo annotation to be converted to another file "
                    "format. The input format will be automatically inferred from "
                    "the file extension if you choose a file with a known extension.\n"
                    "If you want to annotate sequences in a FASTA/GFF file, please "
                    "select the FASTA/GFF file to annotate in the 'Additional File' "
                    "section."
                ),
            )
        )
        self.input_label = QLabel("Input File:")
        self.input_label.setFixedWidth(label_width)
        input_layout.addWidget(self.input_info_button)
        input_layout.addWidget(self.input_label)
        self.input_path = QLineEdit()
        self.input_path.textChanged.connect(self.on_input_path_changed)
        input_button = QPushButton("Browse Input")
        input_button.clicked.connect(self.browse_input)
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(input_button)
        layout.addLayout(input_layout)

        # Input format selection
        format_layout = QHBoxLayout()
        self.input_format_info_button = QPushButton("?")
        self.input_format_info_button.setFixedSize(16, 16)
        self.input_format_info_button.clicked.connect(
            lambda: self.show_help(
                "Input Format",
                (
                    "Select the format of the input file.\n"
                    "The input format will be automatically inferred from the file "
                    "extension if you select a file with a known extension."
                ),
            )
        )
        self.input_format_label = QLabel("Input Format:")
        self.input_format_label.setFixedWidth(label_width)
        format_layout.addWidget(self.input_format_info_button)
        format_layout.addWidget(self.input_format_label)
        self.input_format = QComboBox()
        self.input_format.addItems(
            ["auto", "dngf", "pickle", "fasta", "gff", "shortstr"]
        )
        format_layout.addWidget(self.input_format)
        layout.addLayout(format_layout)

        # Output file selection
        output_layout = QHBoxLayout()
        self.output_info_button = QPushButton("?")
        self.output_info_button.setFixedSize(16, 16)
        self.output_info_button.clicked.connect(
            lambda: self.show_help(
                "Output File",
                (
                    "Select the destination for the converted file "
                    "(optional). If no output file is specified, the output will be "
                    "displayed in the text box below.\n"
                    "If you want to annotate sequences in a FASTA/GFF file, please "
                    "select the FASTA/GFF file to annotate in the 'Additional File' "
                    "section and either another file location as output file to keep "
                    "the original FASTA/GFF file unchanged (recommended) or select "
                    "the same file as output, which overwrites the original "
                    "FASTA/GFF file."
                ),
            )
        )
        self.output_label = QLabel("Output File:")
        self.output_label.setFixedWidth(label_width)
        output_layout.addWidget(self.output_info_button)
        output_layout.addWidget(self.output_label)
        self.output_path = QLineEdit()
        self.output_path.textChanged.connect(self.on_output_path_changed)
        output_button = QPushButton("Browse Output")
        output_button.clicked.connect(self.browse_output)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_button)
        layout.addLayout(output_layout)

        # Output format selection
        out_format_layout = QHBoxLayout()
        self.output_format_info_button = QPushButton("?")
        self.output_format_info_button.setFixedSize(16, 16)
        self.output_format_info_button.clicked.connect(
            lambda: self.show_help(
                "Output Format",
                (
                    "Select the desired format for the output file.\n"
                    "The output format will be automatically inferred from the file "
                    "extension if you choose a file with a known extension."
                ),
            )
        )
        self.output_format_label = QLabel("Output Format:")
        self.output_format_label.setFixedWidth(label_width)
        out_format_layout.addWidget(self.output_format_info_button)
        out_format_layout.addWidget(self.output_format_label)
        self.output_format = QComboBox()
        self.output_format.addItems(
            ["auto", "dngf", "pickle", "fasta", "gff", "shortstr"]
        )
        self.output_format.currentIndexChanged.connect(self.update_sections)
        out_format_layout.addWidget(self.output_format)
        layout.addLayout(out_format_layout)

        # Identifiers file (optional)
        self.identifiers_layout = QHBoxLayout()
        self.identifiers_info_button = QPushButton("?")
        self.identifiers_info_button.setFixedSize(16, 16)
        self.identifiers_info_button.clicked.connect(
            lambda: self.show_help(
                "Identifiers File",
                (
                    "Optional file containing sequence identifiers for annotation/"
                    "extraction in/from a FASTA/GFF file.\n"
                    "If not provided, all FASTA/GFF entries will be considered.\n"
                    "The file should contain one identifier per line.\n"
                    "In FASTA format, the identifiers are matched with sequence IDs at "
                    "the beginning of the fasta headers. In GFF format, existence of "
                    "given identifiers is checked in the 9th attributes column."
                ),
            )
        )
        self.identifiers_label = QLabel("Identifiers File:")
        self.identifiers_label.setFixedWidth(label_width)
        self.identifiers_layout.addWidget(self.identifiers_info_button)
        self.identifiers_layout.addWidget(self.identifiers_label)
        self.identifiers_path = QLineEdit()
        identifiers_button = QPushButton("Browse Identifiers")
        identifiers_button.setStyleSheet(
            """
            QPushButton:disabled {
                background-color: #454746;
                color: grey;
                }
            """
        )
        identifiers_button.clicked.connect(self.browse_identifiers)
        self.identifiers_layout.addWidget(self.identifiers_path)
        self.identifiers_layout.addWidget(identifiers_button)
        layout.addLayout(self.identifiers_layout)

        # Feature type for GFF
        self.feature_layout = QHBoxLayout()
        self.feature_info_button = QPushButton("?")
        self.feature_info_button.setFixedSize(16, 16)
        self.feature_info_button.clicked.connect(
            lambda: self.show_help(
                "Feature Type",
                (
                    "Specify the feature type for GFF annotation/extraction. "
                    "Only sequences with this feature type are considered "
                    "(default: gene)."
                ),
            )
        )
        self.feature_label = QLabel("Feature Type:")
        self.feature_label.setFixedWidth(label_width)
        self.feature_layout.addWidget(self.feature_info_button)
        self.feature_layout.addWidget(self.feature_label)
        self.feature_type = QLineEdit("gene")
        self.feature_type.setStyleSheet(
            """
            QLineEdit:disabled {
                color: grey;
            }
            """
        )
        self.feature_layout.addWidget(self.feature_type)
        layout.addLayout(self.feature_layout)

        # Additional Input file selection
        self.additional_layout = QHBoxLayout()
        self.additional_info_button = QPushButton("?")
        self.additional_info_button.setFixedSize(16, 16)
        self.additional_info_button.clicked.connect(
            lambda: self.show_help(
                "Additional File",
                (
                    "Select an additional input file if required by the output "
                    "format (only for FASTA or GFF).\n"
                    "If the output file is the same as the additional input file, "
                    "the original FASTA/GFF file will be overwritten with the "
                    "annotated version of the file. It is recommended to select a "
                    "different output file to keep the original FASTA/GFF file unchanged."
                ),
            )
        )
        self.additional_label = QLabel("Additional File:")
        self.additional_label.setFixedWidth(label_width)
        self.additional_layout.addWidget(self.additional_info_button)
        self.additional_layout.addWidget(self.additional_label)
        self.additional_path = QLineEdit()
        self.additional_path.textChanged.connect(self.update_sections)
        self.additional_button = QPushButton("Browse Additional File")
        self.additional_button.setStyleSheet(
            """
            QPushButton:disabled {
                background-color: #454746;
                color: grey;
                }
            """
        )
        self.additional_button.clicked.connect(self.browse_additional)
        self.additional_layout.addWidget(self.additional_path)
        self.additional_layout.addWidget(self.additional_button)
        layout.addLayout(self.additional_layout)

        # Convert button
        self.convert_button = QPushButton("Convert")
        self.convert_button.setStyleSheet(
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
        self.convert_button.clicked.connect(self.convert)
        self.convert_button.setEnabled(False)
        layout.addWidget(self.convert_button)

        # Output text box
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.centralWidget().layout().addWidget(self.output_text)

        # Initialize section states
        self.update_sections()

    def show_help(self, title, message):
        QMessageBox.information(self, title, message)

    def browse_input(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Input File")
        if filename:
            self.input_path.setText(filename)
            if self.input_format.currentText() == "auto":
                fmt = infer_format_from_extension(Path(filename))
                if fmt:
                    index = self.input_format.findText(fmt)
                    if index >= 0:
                        self.input_format.setCurrentIndex(index)
                else:
                    self.input_format.setCurrentIndex(
                        self.input_format.findText("auto")
                    )

    def browse_output(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Select Output File")
        if filename:
            self.output_path.setText(filename)
            if self.output_format.currentText() == "auto":
                fmt = infer_format_from_extension(Path(filename))
                if fmt:
                    index = self.output_format.findText(fmt)
                    if index >= 0:
                        self.output_format.setCurrentIndex(index)
                else:
                    self.output_format.setCurrentIndex(
                        self.output_format.findText("auto")
                    )

    def browse_identifiers(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Identifiers File")
        if filename:
            self.identifiers_path.setText(filename)

    def browse_additional(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Additional File")
        if filename:
            self.additional_path.setText(filename)

    def on_input_path_changed(self, text):
        inp_fmt = infer_format_from_extension(Path(self.input_path.text()))
        if inp_fmt:
            index = self.input_format.findText(inp_fmt)
            if index >= 0:
                self.input_format.setCurrentIndex(index)
        else:
            self.input_format.setCurrentIndex(self.input_format.findText("auto"))

        self.update_sections()

    def on_output_path_changed(self, text):
        out_fmt = infer_format_from_extension(Path(self.output_path.text()))
        if out_fmt:
            index = self.output_format.findText(out_fmt)
            if index >= 0:
                self.output_format.setCurrentIndex(index)
        else:
            self.output_format.setCurrentIndex(self.output_format.findText("auto"))

        self.update_sections()

    def update_sections(self):
        fmt = self.output_format.currentText()
        input_file_exists = (
            self.input_path.text() and Path(self.input_path.text()).is_file()
        )
        additional_input_selected = self.additional_path.text()

        if fmt == "gff":
            identifiers_enabled = True
            feature_enabled = True
            additional_enabled = True
            self.additional_label.setText("GFF File:")
            self.additional_button.setText("Browse GFF File")
        elif fmt == "fasta":
            identifiers_enabled = True
            feature_enabled = False
            additional_enabled = True
            self.additional_label.setText("FASTA File:")
            self.additional_button.setText("Browse FASTA File")
        else:
            identifiers_enabled = False
            feature_enabled = False
            additional_enabled = False
            self.additional_label.setText("Additional File:")
            self.additional_button.setText("Browse Additional File")

        self.identifiers_path.setEnabled(identifiers_enabled)
        self.identifiers_layout.itemAt(3).widget().setEnabled(identifiers_enabled)
        self.identifiers_label.setStyleSheet(
            "color: white;" if identifiers_enabled else "color: grey;"
        )
        self.feature_type.setEnabled(feature_enabled)
        self.feature_label.setStyleSheet(
            "color: white;" if feature_enabled else "color: grey;"
        )
        self.additional_path.setEnabled(additional_enabled)
        self.additional_layout.itemAt(3).widget().setEnabled(additional_enabled)
        self.additional_label.setStyleSheet(
            "color: white;" if additional_enabled else "color: grey;"
        )

        # Enable convert button if output_format is not 'auto', input file exists,
        # and if output_format is 'fasta' or 'gff', additional input file is selected
        if (
            fmt != "auto"
            and input_file_exists
            and (fmt not in ["fasta", "gff"] or additional_input_selected)
        ):
            self.convert_button.setEnabled(True)
        else:
            self.convert_button.setEnabled(False)

    def get_identifiers(self):
        identifiers = self.identifiers_path.text()
        if not identifiers:
            return None
        with open(identifiers, "r") as infile:
            return set(line.strip() for line in infile if line.strip())

    def convert(self):
        try:
            input_file = Path(self.input_path.text())
            output_file = (
                Path(self.output_path.text()) if self.output_path.text() else None
            )
            input_format = self.input_format.currentText()
            output_format = self.output_format.currentText()
            identifiers = self.get_identifiers()
            feature = self.feature_type.text()
            additional_input = self.additional_path.text()

            # Load input
            if input_format == "auto":
                input_format = infer_format_from_extension(input_file)
                if not input_format:
                    raise ValueError("Could not infer input format from file extension")

            model = None
            if input_format == "dngf":
                model = load_from_json(input_file)
            elif input_format == "pickle":
                model = load_from_pickle(input_file)
            elif input_format == "fasta":
                model = load_from_fasta(input_file)
            elif input_format == "gff":
                model = load_from_gff(input_file, feature=feature)
            elif input_format == "shortstr":
                model = decode_short_str(input_file)

            # Convert and save
            if output_format == "dngf":
                if output_file:
                    out_str = convert_to_json(model, output_file)
                else:
                    out_str = convert_to_json(model)
            elif output_format == "pickle":
                if output_file:
                    out_str = str(convert_to_pickle(model, output_file))
                else:
                    out_str = str(convert_to_pickle(model))
            elif output_format == "fasta":
                if output_file:
                    out_str = annotate_fasta(
                        model,
                        fasta_file=additional_input,
                        outf=output_file,
                        identifiers=identifiers,
                    )
                else:
                    out_str = annotate_fasta(
                        model, fasta_file=additional_input, identifiers=identifiers
                    )
            elif output_format == "gff":
                if output_file:
                    out_str = annotate_gff(
                        model,
                        gff_file=additional_input,
                        outf=output_file,
                        identifiers=identifiers,
                        feature=feature,
                    )
                else:
                    out_str = annotate_gff(
                        model,
                        gff_file=additional_input,
                        identifiers=identifiers,
                        feature=feature,
                    )
            elif output_format == "shortstr":
                out_str = encode_short_str(model)
                if output_file:
                    with open(output_file, "w") as outfile:
                        outfile.write(out_str)

            # Show output in text box
            self.output_text.setPlainText(out_str)

            if output_file:
                QMessageBox.information(
                    self,
                    "File saved",
                    (
                        "Conversion completed successfully!\n"
                        f"File was saved to:\n{output_file}"
                    ),
                )
            else:
                QMessageBox.information(
                    self, "Success", "Conversion completed successfully!"
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Quit",
            "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    # Check the NCBI Taxonomy Database
    check_NCBI_taxDB()

    warnings.filterwarnings("ignore")
    app = QApplication([])
    window = DngfConverterGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
