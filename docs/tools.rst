Tools
=====

The DENOFO toolkit comprises three main tools, each available in both a 
command-line interface (CLI) and a graphical user interface (GUI):

1. **denofo-questionnaire:** Interactively guides the user through a series 
   of questions, saving the resulting annotation in a ``*.dngf`` file.
2. **denofo-converter:** Converts annotations between different file types. 
   For example, it can annotate sequences in a ``*.fasta`` or ``*.gff`` file 
   with an existing ``*.dngf`` annotation file using a short string encoding.
3. **denofo-comparator:** Compares two annotation files, highlighting similarities 
   and differences in methodology.

Both CLI and GUI versions are provided to cater to different user needs and 
environments. The CLI tools are suitable for remote servers, HPC environments 
without display, and automated pipelines. The GUI tools offer an intuitive 
interface for users without extensive command-line experience.