#!/usr/bin/env python3

import csv
import io
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

SOURCE_URL = "https://www.guidetopharmacology.org/DATA/peptides.csv"
CATALOG_PATH = Path("data/peptides.jsonl")
METADATA_PATH = Path("data/catalog_metadata.json")

EXPECTED_COLUMNS = {
    "Ligand id",
    "Name",
    "Species",
    "Type",
    "Approved",
    "Withdrawn",
    "Single letter amino acid sequence",
}


def truthy(value):
    return str(value or "").strip().lower() in {"true", "yes", "1", "y"}


def split_values(value):
    if not value:
        return []
    return [part.strip() for part in str(value).split("|") if part.strip()]


def canonical_name(name, species):
    name = name.strip()
    species = species.strip()
    return f"{name} ({species})" if species else name


def fetch_source():
    request = urllib.request.Request(
        SOURCE_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; PeptideExplorerCatalog/1.0)",
            "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        content_type = response.headers.get_content_type()
        raw_data = response.read()
        final_url = response.geturl()

    if not raw_data:
        raise RuntimeError("GtoPdb peptide download returned an empty response")

    text = raw_data.decode("utf-8-sig", errors="replace")
    preview = text[:300].replace("\n", "\\n").replace("\r", "\\r")

    print(f"source URL: {SOURCE_URL}")
    print(f"final URL: {final_url}")
    print(f"HTTP content type: {content_type}")
    print(f"downloaded bytes: {len(raw_data)}")
    print(f"response preview: {preview}")

    lowered = text.lstrip().lower()
    if lowered.startswith("<!doctype html") or lowered.startswith("<html"):
        raise RuntimeError(
            "GtoPdb returned HTML instead of the peptide CSV. "
            "This may indicate an access, login, redirect, or service error."
        )

    return text


def prepare_csv(text):
    parsed_rows = list(csv.reader(io.StringIO(text)))
    parsed_rows = [row for row in parsed_rows if row and any(cell.strip() for cell in row)]

    if not parsed_rows:
        raise RuntimeError("GtoPdb response contained no CSV rows")

    source_release = "unknown"
    first_cell = parsed_rows[0][0].strip() if parsed_rows[0] else ""
    if first_cell.startswith("#"):
        source_release = first_cell.lstrip("#").strip()
        parsed_rows = parsed_rows[1:]

    if not parsed_rows:
        raise RuntimeError("GtoPdb response contained metadata but no CSV header/data rows")

    headers = [header.strip() for header in parsed_rows[0]]
    print(f"CSV headers ({len(headers)}): {headers}")

    missing_columns = sorted(EXPECTED_COLUMNS - set(headers))
    if missing_columns:
        raise RuntimeError(
            "GtoPdb peptide CSV is missing expected columns: "
            + ", ".join(missing_columns)
            + ". Actual headers: "
            + ", ".join(headers)
        )

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer, lineterminator="\n")
    writer.writerows(parsed_rows)
    csv_buffer.seek(0)
    reader = csv.DictReader(csv_buffer)

    return source_release, reader


def main():
    text = fetch_source()
    source_release, reader = prepare_csv(text)

    records = []
    seen = set()
    rows_processed = 0
    rows_without_name = 0

    for row in reader:
        rows_processed += 1
        name = (row.get("Name") or "").strip()
        if not name:
            rows_without_name += 1
            continue

        species = (row.get("Species") or "").strip()
        record_name = canonical_name(name, species)
        key = record_name.casefold()
        if key in seen:
            raise RuntimeError(f"duplicate canonical name after normalization: {record_name}")
        seen.add(key)

        peptide_type = (row.get("Type") or "").strip()
        is_endogenous = "endogenous" in peptide_type.lower()
        approved = truthy(row.get("Approved"))
        withdrawn = truthy(row.get("Withdrawn"))
        sequence = (row.get("Single letter amino acid sequence") or "").strip() or None

        status = []
        if approved:
            status.append("approved_drug")
        if withdrawn:
            status.append("withdrawn")
        if not status:
            status.append("endogenous" if is_endogenous else "documented_peptide")

        record = {
            "canonical_name": record_name,
            "display_name": name,
            "aliases": [],
            "primary_category": "endogenous peptide" if is_endogenous else "other characterized peptide",
            "secondary_tags": [],
            "description": None,
            "origin_or_species": split_values(species),
            "sequence": sequence,
            "sequence_length": len(sequence) if sequence and sequence.isalpha() else None,
            "mechanism_or_targets": [],
            "biological_role": None,
            "studied_uses": [],
            "approved_indications": [],
            "evidence_level": "E6" if approved else "E0",
            "evidence_summary": "Regulatory approval is recorded by GtoPdb." if approved else "Identity imported from the curated GtoPdb peptide catalog; evidence not yet enriched.",
            "meaningful_human_evidence": True if approved else None,
            "regulatory_status": status,
            "safety_summary": None,
            "identity_status": "verified_source_identity",
            "database_ids": {
                "gtopdb_ligand_id": (row.get("Ligand id") or "").strip() or None,
                "pubchem_sid": (row.get("PubChem SID") or "").strip() or None,
                "pubchem_cid": (row.get("PubChem CID") or "").strip() or None,
                "uniprot": split_values(row.get("UniProt id")),
                "ensembl": split_values(row.get("Ensembl id")),
            },
            "peptide_details": {
                "source_type": peptide_type or None,
                "inn": (row.get("INN") or "").strip() or None,
                "three_letter_sequence": (row.get("Three letter amino acid sequence") or "").strip() or None,
                "helm": (row.get("HELM") or "").strip() or None,
                "post_translational_modification": (row.get("Post-translational modification") or "").strip() or None,
                "chemical_modification": (row.get("Chemical modification") or "").strip() or None,
                "subunit_ids": split_values(row.get("Subunit ids")),
                "subunit_names": split_values(row.get("Subunit names")),
                "labelled": truthy(row.get("Labelled")),
                "radioactive": truthy(row.get("Radioactive")),
            },
            "sources": [{
                "name": "IUPHAR/BPS Guide to PHARMACOLOGY",
                "dataset": "complete peptide ligand list",
                "url": SOURCE_URL,
                "release": source_release,
                "retrieved_date": date.today().isoformat(),
            }],
            "last_verified": date.today().isoformat(),
        }
        records.append(record)

    print(f"CSV rows processed: {rows_processed}")
    print(f"rows without Name: {rows_without_name}")
    print(f"peptide records generated: {len(records)}")

    if len(records) < 2000:
        raise RuntimeError(
            f"unexpectedly small peptide import: {len(records)} records "
            f"from {rows_processed} CSV rows"
        )

    records.sort(key=lambda record: record["canonical_name"].casefold())
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CATALOG_PATH.open("w", encoding="utf-8") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

    metadata = {
        "format": "peptide-catalog-jsonl",
        "schema_version": 1,
        "record_count": len(records),
        "description": "Canonical peptide catalog for Peptide Explorer. One JSON object per line in peptides.jsonl.",
        "last_verified": date.today().isoformat(),
        "source_release": source_release,
        "source_url": SOURCE_URL,
        "import_method": "tools/import_gtopdb_peptides.py",
    }
    METADATA_PATH.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"imported {len(records)} peptide records from {source_release}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
