#!/usr/bin/env python3

import json
from collections import Counter
from pathlib import Path

CATALOG_PATH = Path("data/peptides.jsonl")
METADATA_PATH = Path("data/catalog_metadata.json")
SUMMARY_PATH = Path("data/catalog_summary.json")


def main():
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))

    total_records = 0
    category_counts = Counter()
    evidence_counts = Counter()
    approved_records = 0
    withdrawn_records = 0

    with CATALOG_PATH.open("r", encoding="utf-8") as catalog_file:
        for line_number, raw_line in enumerate(catalog_file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise RuntimeError(
                    f"invalid JSONL at line {line_number}: {error.msg}"
                ) from error

            total_records += 1
            category_counts[record.get("primary_category") or "unknown"] += 1
            evidence_counts[record.get("evidence_level") or "unknown"] += 1

            regulatory_status = record.get("regulatory_status") or []
            if "approved_drug" in regulatory_status:
                approved_records += 1
            if "withdrawn" in regulatory_status:
                withdrawn_records += 1

    expected_records = metadata.get("record_count")
    if expected_records != total_records:
        raise RuntimeError(
            "catalog integrity failure: metadata record_count "
            f"is {expected_records}, but peptides.jsonl contains {total_records} non-empty JSON lines"
        )

    summary = {
        "total_records": total_records,
        "source_release": metadata.get("source_release"),
        "last_verified": metadata.get("last_verified"),
        "identity_key": metadata.get("identity_key"),
        "duplicate_canonical_name_groups": metadata.get("duplicate_canonical_name_groups", 0),
        "approved_records": approved_records,
        "withdrawn_records": withdrawn_records,
        "category_counts": dict(sorted(category_counts.items())),
        "evidence_counts": dict(sorted(evidence_counts.items())),
    }

    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"catalog integrity verified: {total_records} JSONL records")
    print(f"catalog summary written: {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
