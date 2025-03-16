import pytest
from PyQt6.QtWidgets import QMessageBox
from denofo.comparator.comparator_gui import DNGFCompareGUI


# Dummy functions to replace actual implementations during testing.
def dummy_load_from_json(file_path):
    # Return a dummy model regardless of input.
    return {"dummy": "model"}


def dummy_compare_two_models(model1, model2, mode):
    # Return a dummy comparison dictionary.
    return {"differences": "dummy_comparison", "similarities": "dummy_comparison"}


def dummy_write_comparison(comparison, mode, extra, name1, name2):
    # Format a dummy output string.
    return f"Comparison result for {name1} vs {name2}: {comparison[mode]}"


@pytest.fixture
def gui(qtbot, monkeypatch):
    monkeypatch.setenv("UNIT_TESTING", "true")  # ensure tests mode if needed
    # Bypass the close confirmation popup on exit.
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
    )
    widget = DNGFCompareGUI()
    qtbot.addWidget(widget)
    return widget


def test_update_compare_button_enabled(qtbot, gui, monkeypatch):
    # Initially set fields to empty or invalid values.
    monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.Yes)
    gui.file1_input.setText("")
    gui.file2_input.setText("")
    gui.name1_input.setText("dngf_1")
    gui.name2_input.setText("dngf_2")
    gui.update_compare_button()
    assert not gui.compare_button.isEnabled()

    # Fill all fields with valid and distinct names.
    gui.file1_input.setText("/path/to/file1.dngf")
    gui.file2_input.setText("/path/to/file2.dngf")
    gui.name1_input.setText("Model1")
    gui.name2_input.setText("Model2")
    gui.update_compare_button()
    assert gui.compare_button.isEnabled()


def test_compare_files_no_output(qtbot, tmp_path, monkeypatch, gui):
    # Patch add_extension to return the passed path unchanged.
    monkeypatch.setattr("denofo.utils.helpers.add_extension", lambda p: p)
    # Bypass any modal dialogs.
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
    )
    monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.Yes)

    # Create temporary dummy DNGF files.
    file1 = tmp_path / "file1.dngf"
    file2 = tmp_path / "file2.dngf"
    file1.write_text("{}")
    file2.write_text("{}")

    gui.file1_input.setText(str(file1))
    gui.file2_input.setText(str(file2))
    gui.name1_input.setText("Model1")
    gui.name2_input.setText("Model2")
    gui.output_input.setText("")  # No output file provided.

    # Replace functions with dummy implementations.
    monkeypatch.setattr(
        "denofo.comparator.comparator_gui.load_from_json", dummy_load_from_json
    )
    monkeypatch.setattr(
        "denofo.comparator.comparator_gui.compare_two_models", dummy_compare_two_models
    )
    monkeypatch.setattr(
        "denofo.comparator.comparator_gui.write_comparison", dummy_write_comparison
    )

    gui.compare_files()

    expected_output = "Comparison result for Model1 vs Model2: dummy_comparison"
    # Check that results are displayed in the text area.
    assert gui.results_display.toPlainText() == expected_output


def test_compare_files_with_output(qtbot, tmp_path, monkeypatch, gui):
    # Patch add_extension to return the passed path unchanged.
    monkeypatch.setattr("denofo.utils.helpers.add_extension", lambda p: p)
    # Bypass any modal dialogs.
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
    )
    # Bypass QMessageBox.exec to prevent blocking or error.
    monkeypatch.setattr(QMessageBox, "exec", lambda self: None)

    # Create temporary dummy DNGF files.
    file1 = tmp_path / "file1.dngf"
    file2 = tmp_path / "file2.dngf"
    output_file = tmp_path / "output.txt"
    file1.write_text("{}")
    file2.write_text("{}")

    gui.file1_input.setText(str(file1))
    gui.file2_input.setText(str(file2))
    gui.name1_input.setText("Model1")
    gui.name2_input.setText("Model2")
    gui.output_input.setText(str(output_file))  # Provide output file.

    # Replace functions with dummy implementations.
    monkeypatch.setattr(
        "denofo.comparator.comparator_gui.load_from_json", dummy_load_from_json
    )
    monkeypatch.setattr(
        "denofo.comparator.comparator_gui.compare_two_models", dummy_compare_two_models
    )
    monkeypatch.setattr(
        "denofo.comparator.comparator_gui.write_comparison", dummy_write_comparison
    )

    # Bypass QMessageBox.exec to prevent blocking the test.
    monkeypatch.setattr(QMessageBox, "exec", lambda self: None)

    gui.compare_files()

    expected_output = "Comparison result for Model1 vs Model2: dummy_comparison"
    # Check that results are displayed in the text area.
    assert gui.results_display.toPlainText() == expected_output
    # Verify that the output file has been written with the expected content.
    written = output_file.read_text()
    assert written == expected_output
