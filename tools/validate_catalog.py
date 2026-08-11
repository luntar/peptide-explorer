#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


required_fields = {
    "record_id",
    "canonical_name",
    "primary_category",
    "evidence_level",
}

valid_evidence_levels = {f"E{level}" for level in range(7)}


def validate_record(record, line_number, record_ids):
    errors = []

    if not isinstance(record, dict):
        return [f"line {line_number}: record must be a JSON object"]

    missing_fields = sorted(required_fields - record.keys())
    if missing_fields:
        errors.append(
            f"line {line_number}: missing required fields: {', '.join(missing_fields)}"
        )

    record_id = record.get("record_id")
    if record_id is not None:
        if not isinstance(record_id, str) or not record_id.strip():
            errors.append(f"line {line_number}: record_id must be a non-empty string")
        else:
            normalized_record_id = record_id.strip().casefold()
            if normalized_record_id in record_ids:
                errors.append(f"line {line_number}: duplicate record_id '{record_id}'")
            record_ids.add(normalized_record_id)

    canonical_name = record.get("canonical_name")
    if canonical_name is not None:
        if not isinstance(canonical_name, str) or not canonical_name.strip():
            errors.append(f"line {line_number}: canonical_name must be a non-empty string")

    evidence_level = record.get("evidence_level")
    if evidence_level is not None and evidence_level not in valid_evidence_levels:
        errors.append(
            f"line {line_number}: evidence_level must be one of "
            f"{', '.join(sorted(valid_evidence_levels))}"
        )

    aliases = record.get("aliases")
    if aliases is not None and not isinstance(aliases, list):
        errors.append(f"line {line_number}: aliases must be an array when present")

    sources = record.get("sources")
    if sources is not None and not isinstance(sources, list):
        errors.append(f"line {line_number}: sources must be an array when present")

    return errors


def validate_catalog(catalog_path):
    record_ids = set()
    errors = []
    record_count = 0

    with catalog_path.open("r", encoding="utf-8") as catalog_file:
        for line_number, raw_line in enumerate(catalog_file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                errors.append(f"line {line_number}: invalid JSON: {error.msg}")
                continue

            record_count += 1
            errors.extend(validate_record(record, line_number, record_ids))

    return record_count, errors


def main():
    parser = argparse.ArgumentParser(description="Validate the Peptide Explorer JSONL catalog")
    parser.add_argument(
        "catalog",
        nargs="?",
        default="data/peptides.jsonl",
        help="path to the peptide JSONL catalog",
    )
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.is_file():
        print(f"catalog not found: {catalog_path}", file=sys.stderr)
        return 2

    record_count, errors = validate_catalog(catalog_path)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"catalog validation failed: {len(errors)} error(s)", file=sys.stderr)
        return 1

    print(f"catalog valid: {record_count} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
