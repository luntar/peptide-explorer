# Peptide Catalog Data

`peptides.jsonl` is the canonical Peptide Explorer catalog.

Each non-empty line is one independent JSON object representing one peptide molecular entity. JSONL is used so records remain easy to append, diff, review, stream, and migrate into a database later.

## Minimum record

A catalog record must contain:

```json
{"canonical_name":"example peptide","primary_category":"synthetic research peptide","evidence_level":"E2"}
```

Useful optional fields include:

- `aliases`
- `development_codes`
- `brand_names`
- `secondary_tags`
- `description`
- `origin`
- `sequence`
- `mechanism_or_targets`
- `biological_role`
- `studied_uses`
- `approved_indications`
- `evidence_summary`
- `human_evidence`
- `regulatory_status`
- `safety_summary`
- `database_ids`
- `sources`
- `last_verified`
- `identity_status`

Unknown values should be omitted or represented explicitly as `null` or an empty collection. Do not invent values.

## Evidence levels

- `E0`: identity only
- `E1`: biochemical / cell
- `E2`: preclinical
- `E3`: early human
- `E4`: controlled human
- `E5`: strong clinical
- `E6`: regulatory approval

Evidence applies to the specific molecule, not merely to its family or mechanism.

## Identity rule

Merge true aliases into one record, but keep materially different molecules separate. Sequence substitutions, lipidation, PEGylation, cyclization, amidation, conjugation, or other meaningful chemical changes may require distinct records.

## Validate

From the repository root:

```bash
python3 tools/validate_catalog.py
```

The validator checks JSON syntax, required fields, evidence levels, and duplicate canonical names.

## Workflow

1. Research a peptide using authoritative sources.
2. Resolve its identity and aliases.
3. Assign category and evidence level.
4. Add one JSON object as one line in `peptides.jsonl`.
5. Run the validator.
6. Review the Git diff and commit the change.

The catalog is educational research data, not treatment guidance.
