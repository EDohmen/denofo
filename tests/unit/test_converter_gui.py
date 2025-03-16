from pathlib import Path
import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox
from denofo.converter.converter_gui import DngfConverterGUI


# Ensure a QApplication exists for the tests.
@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


@pytest.fixture
def gui(qapp, tmp_path, monkeypatch):
    # Override close confirmation dialog to auto-confirm.
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
    # Create an instance of the GUI.
    window = DngfConverterGUI()
    # Hide the window during tests.
    window.hide()
    yield window
    window.close()


def test_update_sections_disables_convert_when_input_missing(gui):
    # Initially, input file is empty so convert button should be disabled.
    gui.input_path.setText("")
    gui.output_format.setCurrentIndex(gui.output_format.findText("dngf"))
    gui.update_sections()
    assert not gui.convert_button.isEnabled()


def test_update_sections_enables_convert_when_input_exists(tmp_path, gui):
    # Create a temporary input file.
    input_file = tmp_path / "input.txt"
    input_file.write_text("dummy content")
    gui.input_path.setText(str(input_file))
    # Set output format to one that doesn't require an additional file.
    gui.output_format.setCurrentIndex(gui.output_format.findText("dngf"))
    # Since output file is optional for 'dngf', update_sections should enable convert.
    gui.update_sections()
    assert gui.convert_button.isEnabled()


def test_get_identifiers(tmp_path, gui):
    # Create a temporary identifiers file.
    id_file = tmp_path / "ids.txt"
    id_file.write_text("id1\nid2\nid3\n")
    gui.identifiers_path.setText(str(id_file))
    ids = gui.get_identifiers()
    assert isinstance(ids, set)
    assert ids == {"id1", "id2", "id3"}


def test_convert_dngf_json(tmp_path, monkeypatch, gui):
    # Create temporary input and output files.
    input_file = tmp_path / "input.dngf.json"
    input_file.write_text('{"dummy": "data"}')
    output_file = tmp_path / "output.dngf.json"

    # Set the paths and formats in the GUI.
    gui.input_path.setText(str(input_file))
    gui.output_path.setText(str(output_file))
    # Force input format to "dngf" and output to "dngf"
    gui.input_format.setCurrentIndex(gui.input_format.findText("dngf"))
    gui.output_format.setCurrentIndex(gui.output_format.findText("dngf"))

    # Create dummy functions to override the conversion functions.
    def dummy_load_from_json(file_path):
        # Just return a dummy model.
        return {"model": "dummy"}

    def dummy_convert_to_json(model, outfile=None):
        out_str = '{"converted": "dummy"}'
        if outfile:
            with open(outfile, "w") as f:
                f.write(out_str)
        return out_str

    monkeypatch.setattr(
        "denofo.converter.converter_gui.load_from_json", dummy_load_from_json
    )
    monkeypatch.setattr(
        "denofo.converter.converter_gui.convert_to_json", dummy_convert_to_json
    )

    # Override QMessageBox.information to avoid modal dialogs in tests.
    info_called = []

    def dummy_information(parent, title, message):
        info_called.append((title, message))

    monkeypatch.setattr(QMessageBox, "information", dummy_information)

    # Ensure input file exists.
    assert Path(gui.input_path.text()).is_file()

    # Call conversion.
    gui.convert()

    # Check that the output text was set correctly.
    assert gui.output_text.toPlainText() == '{"converted": "dummy"}'
    # Verify that the output file was written.
    with open(output_file, "r") as f:
        assert f.read() == '{"converted": "dummy"}'
    # Verify that an information message was shown.
    assert any("Conversion completed successfully" in msg for _, msg in info_called)
