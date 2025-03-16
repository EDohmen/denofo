from ete3 import NCBITaxa
from ete3.ncbi_taxonomy.ncbiquery import is_taxadb_up_to_date
import sqlite3
import warnings


class NCBITAXDBWarning(UserWarning):
    """
    Warning raised when NCBI Taxonomy Database is newly built or updated
    """

    pass


def check_NCBI_taxDB() -> NCBITaxa:
    """
    Check if NCBI Taxonomy Database exists and is valid or build it if not

    :return: NCBI Taxonomy Database object
    :rtype: NCBITaxa
    """
    try:
        if not is_taxadb_up_to_date():
            warnings.warn(
                "No valid NCBI Taxonomy Database found. Building NCBI Taxonomy "
                "Database. This might take a while...",
                NCBITAXDBWarning,
            )
    except (sqlite3.OperationalError, ValueError, IndexError, TypeError):
        warnings.warn(
            "No valid NCBI Taxonomy Database found. Building NCBI Taxonomy "
            "Database. This might take a while...",
            NCBITAXDBWarning,
        )

    ncbi = NCBITaxa()
    return ncbi


def update_NCBI_taxDB():
    """
    Update NCBI Taxonomy Database
    """
    warnings.warn("Updating NCBI Taxonomy Database...", NCBITAXDBWarning)
    ncbi = NCBITaxa()
    ncbi.update_taxonomy_database()
