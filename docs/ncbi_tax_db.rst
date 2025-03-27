The NCBI Taxonomy Database
==========================

For some parts of the annotation format, DENOFO needs access to the NCBI Taxonomy 
Database through the ete3 library. When you first run a tool that needs the 
NCBI Taxonomy Database (e.g., ``denofo-questionnaire``) and the database could 
not be found, it will download and process it, which can take some minutes. 
This local database version will be used from now on without additional waiting times.

In case you want to update your local version of the NCBI Taxonomy Database, please run:

.. code-block:: bash

   update-ncbi-taxdb
   # or for uv
   uv run update-ncbi-taxdb