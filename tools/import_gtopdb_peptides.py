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


def main():
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
        text = response.read().decode("utf-8-sig")

    lines = text.splitlines()
    source_release = lines[0].lstrip("#").strip() if lines and lines[0].startswith("#") else "unknown"
    csv_text = "\n".join(line for line in lines if not line.startswith("#"))
    reader = csv.DictReader(io.StringIO(csv_text))

    records = []
    seen = set()
    for row in reader:
        name = (row.get("Name") or "").strip()
        if not name:
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
                "ensembl": split_values(row.get("Ensembl id"))
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
                "radioactive": truthy(row.get("Radioactive"))
            },
            "sources": [{
                "name": "IUPHAR/BPS Guide to PHARMACOLOGY",
                "dataset": "complete peptide ligand list",
                "url": SOURCE_URL,
                "release": source_release,
                "retrieved_date": date.today().isoformat()
            }],
            "last_verified": date.today().isoformat()
        }
        records.append(record)

    if len(records) < 2000:
        raise RuntimeError(f"unexpectedly small peptide import: {len(records)} records")

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
        "import_method": "tools/import_gtopdb_peptides.py"
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"imported {len(records)} peptide records from {source_release}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
