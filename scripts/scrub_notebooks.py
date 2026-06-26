"""scripts/scrub_notebooks.py

Scan all notebooks under notebooks/ and:
 - insert a top code cell that defines BASE_DATA_DIR and default CorrFuncLOC and CorrFuncLoc2
 - replace absolute Windows drive-letter paths (like D:/... or E:\...) inside code cells by repo-relative paths built from BASE_DATA_DIR
 - clear all outputs

Usage:
    python scripts/scrub_notebooks.py --apply

Without --apply the script will do a dry-run and print proposed changes.

Environment:
 - honor GLOBROT_DATA env var as the base directory to map absolute paths into

NOTE: This script modifies notebooks in place. Review changes before committing.
"""
from pathlib import Path
import re
import json
import argparse
import nbformat

NOTEBOOKS_DIR = Path('notebooks')
DRIVE_RE = re.compile(r"([A-Za-z]):[\\/]+")

TOP_CELL_SOURCE = [
"import os",
"from pathlib import Path",
"# Configurable base directory for data and research files.\n",
"# Set GLOBROT_DATA environment variable to override the default.\n",
"BASE_DATA_DIR = Path(os.environ.get('GLOBROT_DATA', './Research/LangevinDynamics_RotationalDiffusion')).resolve()",
"# Common derived locations used in the notebooks (fall back to BASE_DATA_DIR-related defaults)\n",
"CorrFuncLOC = str(Path(os.environ.get('GLOBROT_DOCS', './Documents/Research/DiffusionTip4pDSoluteSize')).resolve()) + '/'",
"CorrFuncLoc2 = str(BASE_DATA_DIR) + '/'",
"\n",
"def _remap_drive_path(s):\n",
"    \"\"\"If s is a Windows absolute path (drive letter), remap it under BASE_DATA_DIR by stripping the drive.\"\"\"\n",
"    if not isinstance(s, str):\n",
"        return s\n",
"    m = DRIVE_RE.match(s)\n",
"    if not m:\n",
"        return s\n",
"    tail = DRIVE_RE.sub('', s)\n",
"    # Normalize separators and join to base\n",
"    tail = tail.replace('\\\\', '/').lstrip('/')\n",
"    return str(BASE_DATA_DIR.joinpath(tail))\n",
]


def scrub_notebook(nb_path: Path, apply: bool = False):
    nb = nbformat.read(str(nb_path), as_version=4)
    changed = False

    # Insert top cell if not present (detect by presence of BASE_DATA_DIR in first cell)
    first_src = ''.join(nb.cells[0].get('source', []) if nb.cells else []) if nb.cells else ''
    if 'BASE_DATA_DIR' not in first_src:
        top_cell = nbformat.v4.new_code_cell(source='\n'.join(TOP_CELL_SOURCE))
        nb.cells.insert(0, top_cell)
        changed = True

    # Iterate cells: clear outputs and remap drive-letter paths inside code cells
    for cell in nb.cells:
        if cell.cell_type == 'code':
            # join source
            src = ''.join(cell.get('source', []))
            new_src = src
            # find Windows drive absolute paths and remap them
            # simple heuristic: look for patterns like 'D:/...' or "E:\\..." inside strings
            def replace_match(m):
                s = m.group(0)
                rem = re.sub(r"^[A-Za-z]:[\\/]+", '', s)
                rem = rem.replace('\\\\', '/')
                # map to BASE_DATA_DIR at runtime by replacing literal with a call to _remap_drive_path
                # but to keep code simple, we replace with a call to _remap_drive_path('...')
                return "_remap_drive_path('" + s.replace("'", "\\'") + "')"

            # Replace occurrences inside the source (only if they are within quotes ideally). We'll replace bare occurrences too.
            # find patterns inside quotes first
            quoted_drive_re = re.compile(r"(['\"])" + r"[A-Za-z]:[\\/][^'\"]+" + r"\1")
            new_src = quoted_drive_re.sub(lambda m: replace_match(re.match(r"([\'\"])" + r"([A-Za-z]:[\\/][^'\"]+)" + r"\1", m.group(0))), new_src)

            # Also replace unquoted occurrences of drive paths
            unquoted_drive_re = re.compile(r"[A-Za-z]:[\\/][\w\d_./\\-]+")
            new_src = unquoted_drive_re.sub(lambda m: "_remap_drive_path('" + m.group(0).replace("'", "\\'") + "')", new_src)

            if new_src != src:
                cell.source = new_src
                changed = True

            # clear outputs
            if cell.get('outputs'):
                cell['outputs'] = []
                changed = True
            if cell.get('execution_count', None) is not None:
                cell['execution_count'] = None
                changed = True

    if changed and apply:
        nbformat.write(nb, str(nb_path))

    return changed, nb


def find_notebooks():
    return sorted(p for p in NOTEBOOKS_DIR.glob('*.ipynb'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Apply changes in place')
    args = parser.parse_args()

    nbs = find_notebooks()
    print(f'Found {len(nbs)} notebooks')
    any_changed = False
    for nbp in nbs:
        changed, nb = scrub_notebook(nbp, apply=args.apply)
        print(f'{nbp}: changed={changed}')
        if changed:
            any_changed = True
    if not any_changed:
        print('No changes suggested')
    else:
        if args.apply:
            print('Applied changes to notebooks')
        else:
            print('Dry-run complete. Run with --apply to modify files in place')

if __name__ == '__main__':
    main()
