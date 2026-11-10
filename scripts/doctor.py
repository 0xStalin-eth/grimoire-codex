#!/usr/bin/env python3
"""Report optional workflow tools without installing packages, models or services."""
import importlib.util
import json
import shutil

TOOLS = {
    'core': ['python3', 'bash', 'git'],
    'annotation': ['uv'],
    'librarian-index / librarian-library-search': ['uv'],
    'GitHub findings and mitigation helpers': ['gh', 'jq'],
    'smart-contract PoCs (target dependent)': ['forge'],
    'static detectors (optional)': ['semgrep', 'slither'],
}
if __name__ == '__main__':
    print(json.dumps({group: {tool: bool(shutil.which(tool)) for tool in names} for group, names in TOOLS.items()}, indent=2))
    print('Optional Python packages and models are declared in each script. No dependency was installed.')
