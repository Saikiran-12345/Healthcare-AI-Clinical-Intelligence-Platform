generate_filler.py

This helper script calculates the current repository line count (common source file extensions) and generates Python modules under bulk_generated/ to reach a specified target total lines count.

Usage:
  # dry run (prints plan, does not write files)
  python scripts/generate_filler.py --target 50000

  # actually create files
  python scripts/generate_filler.py --target 50000 --apply

Notes:
- The script tries to avoid overwriting existing files by writing into bulk_generated/.
- Review generated modules before committing and pushing.
- Generated code is valid Python and contains classes and functions with docstrings.
