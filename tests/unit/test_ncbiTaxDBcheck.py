import sqlite3
import pytest
from denofo.utils import ncbiTaxDBcheck
from ete3 import NCBITaxa


class DummyNCBITaxa:
    def __init__(self, update_called):
        self.update_called = update_called

    def update_taxonomy_database(self):
        self.update_called[0] = True


def test_check_NCBI_taxDB_no_warning(monkeypatch, recwarn):
    # Simulate a valid NCBI taxonomy database: is_taxadb_up_to_date returns True
    monkeypatch.setattr(ncbiTaxDBcheck, "is_taxadb_up_to_date", lambda: True)
    db = ncbiTaxDBcheck.check_NCBI_taxDB()
    # No warning should be raised when the db is up-to-date.
    assert len(recwarn) == 0
    # Check that we get an instance of NCBITaxa.
    assert isinstance(db, NCBITaxa)


@pytest.mark.parametrize(
    "exception",
    [
        sqlite3.OperationalError("error"),
        ValueError("error"),
        IndexError("error"),
        TypeError("error"),
    ],
)
def test_check_NCBI_taxDB_exception_warning(monkeypatch, exception):
    # Simulate exception in is_taxadb_up_to_date: function will warn and continue
    def faulty_func():
        raise exception

    monkeypatch.setattr(ncbiTaxDBcheck, "is_taxadb_up_to_date", faulty_func)
    with pytest.warns(ncbiTaxDBcheck.NCBITAXDBWarning) as record:
        db = ncbiTaxDBcheck.check_NCBI_taxDB()
    assert record
    assert isinstance(db, NCBITaxa)


def test_check_NCBI_taxDB_warning_when_not_up_to_date(monkeypatch):
    # Simulate is_taxadb_up_to_date returning False triggering a warning.
    monkeypatch.setattr(ncbiTaxDBcheck, "is_taxadb_up_to_date", lambda: False)
    with pytest.warns(ncbiTaxDBcheck.NCBITAXDBWarning) as record:
        db = ncbiTaxDBcheck.check_NCBI_taxDB()
    assert record
    warning_message = record[0].message.args[0]
    assert "No valid NCBI Taxonomy Database found" in warning_message
    assert isinstance(db, NCBITaxa)


def test_update_NCBI_taxDB(monkeypatch):
    # Test that update_NCBI_taxDB warns and calls update_taxonomy_database.
    update_called = [False]

    # Create a dummy NCBITaxa that records when update_taxonomy_database is called.
    def dummy_NCBITaxa():
        return DummyNCBITaxa(update_called)

    monkeypatch.setattr(ncbiTaxDBcheck, "NCBITaxa", dummy_NCBITaxa)
    with pytest.warns(ncbiTaxDBcheck.NCBITAXDBWarning) as record:
        ncbiTaxDBcheck.update_NCBI_taxDB()
    # Check that warning was raised.
    assert record
    warning_message = record[0].message.args[0]
    assert "Updating NCBI Taxonomy Database..." in warning_message
    # Check that update_taxonomy_database was called.
    assert update_called[0]
