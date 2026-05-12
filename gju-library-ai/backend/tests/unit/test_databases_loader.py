import os
from pathlib import Path

from ingest.databases_loader import load_databases_yaml

_DATA = Path(os.environ.get("DATA", "/data"))


def test_loads_yaml_into_records_and_passages():
    records, passages = load_databases_yaml(_DATA / "seeds/subscription_databases.yaml")
    assert len(records) == 15
    ieee = next(r for r in records if r["slug"] == "ieee")
    assert "Engineering" in ieee["subjects"]
    ieee_passages = [p for p in passages if p.source_ref == "db:ieee"]
    langs = {p.lang for p in ieee_passages}
    assert {"en", "ar", "de"} <= langs
