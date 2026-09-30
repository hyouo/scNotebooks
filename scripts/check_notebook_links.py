"""Validate local Markdown/Notebook navigation without executing scientific cells.

Development-only dependency: markdown-it-py. External resources are not fetched.
"""
import json
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
parser = MarkdownIt()
errors = []
checked = 0
for path in sorted([*ROOT.rglob('*.md'), *ROOT.rglob('*.ipynb')]):
    if '.git' in path.parts:
        continue
    if path.suffix == '.ipynb':
        notebook = json.loads(path.read_text(encoding='utf-8'))
        sources = [''.join(cell['source']) for cell in notebook['cells'] if cell['cell_type'] == 'markdown']
    else:
        sources = [path.read_text(encoding='utf-8')]
    for text in sources:
        for block in parser.parse(text):
            for token in block.children or []:
                target = token.attrGet('href') if token.type == 'link_open' else token.attrGet('src') if token.type == 'image' else None
                if target is None:
                    continue
                parts = urlsplit(target)
                if parts.scheme or parts.netloc or not parts.path:
                    continue
                checked += 1
                if not (path.parent / unquote(parts.path)).exists():
                    errors.append(f'{path.relative_to(ROOT)}: {target}')
for error in errors:
    print(error, file=sys.stderr)
print(f'Checked {checked} local links; {len(errors)} missing. No notebook cells executed.')
raise SystemExit(bool(errors))
