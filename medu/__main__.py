"""Lets you run `python -m medu ...` before the installer exists."""

import sys

from medu.cli import main

sys.exit(main())
