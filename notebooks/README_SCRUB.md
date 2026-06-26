Notebooks scrub: instructions

This branch adds a script scripts/scrub_notebooks.py that will:

- Insert a top cell into each notebook under notebooks/ which defines a configurable BASE_DATA_DIR and default CorrFuncLOC / CorrFuncLoc2.
- Replace Windows absolute (drive-letter) paths found inside code cells with calls to a runtime helper _remap_drive_path('D:/...') which will map them to BASE_DATA_DIR when the notebook is executed.
- Clear notebook outputs and execution counts to avoid leaking local machine paths in outputs.

How to use

1. (Optional) Set GLOBROT_DATA to the base directory you want absolute paths remapped under, for example:

   export GLOBROT_DATA="./Research/LangevinDynamics_RotationalDiffusion"

2. Dry-run to see suggested changes:

   python scripts/scrub_notebooks.py

3. Apply changes in-place:

   python scripts/scrub_notebooks.py --apply

After running with --apply, review notebooks and commit the changes (or push this branch's changes). The script will modify notebooks in-place.
