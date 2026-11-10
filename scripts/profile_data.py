"""Run with .venv/Scripts/python.exe -m scripts.profile_data."""
import json
from pathlib import Path
from qualityops.catalog import Catalog

if __name__ == '__main__':
    catalog = Catalog(Path(__file__).resolve().parents[1])
    catalog.write_reports()
    print(json.dumps({'files': len(catalog.entries), 'tables': {
        k: {'source': catalog.sources[k], 'rows': len(v), 'first': v[:1]} for k, v in catalog.tables.items()
    }, 'documents': [p for p, _ in catalog.documents]}, ensure_ascii=False, indent=2))
