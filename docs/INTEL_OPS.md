# Intelligence Operations (as implemented)

## Investigations & cases
- `POST / GET /api/v1/investigations`, `/{iid}` detail (linked
  targets/entities/findings/evidence), `PUT`, `DELETE`, `/notes`, `/tasks`,
  `/tasks/{tid}/toggle`, `/links` (typed id lists, deduped), `/members`,
  `/views` (named graph node-sets: save/list/delete).
- Cases: same shape plus assignee, UPPER lifecycle, investigation/alert
  links, and an `audit_trail` assembled from `audit_logs` refs.
- UI: Intelligence → investigations/cases, 9–10 tab detail pages
  (Overview/Graph/Entities/Findings/Evidence/[Alerts]/Timeline/Notes/
  Tasks/Reports). Status filters, delete confirmations, no fake buttons.

## STIX 2.1 (subset, honest)
- Export (`POST /stix/export`): identity + SCOs (domain/ip/url/email/file/
  software/vuln/actor/campaign/malware/tool/location/ASN/user/cert/port/
  indicator) + relationships (typed, fallback `related-to`) + findings as
  reports with object_refs. Deterministic v5 ids; unmapped kinds are
  counted in `stats.skipped`, never invented.
- Validate (`POST /stix/validate`), import (`POST /stix/import`, two-pass
  with dedupe + provenance evidence record).
- Unsupported types are reported, never silently dropped. Docs of the exact
  mapping live in `app/services/stix.py`.

## MISP compatibility
- Export (`GET /misp/export`): findings/entities → Event with Attributes
  (type/category/value/to_ids from severity), Tags, Sightings list.
- Import (`POST /misp/import`): attributes → entities (dedupe by value),
  sightings counted, Galaxy clusters → threat_actor entities.
- STIX ↔ internal ↔ MISP conversions preserve provenance; unsupported
  mappings are documented in code, not hidden.

## Transformations (pivot)
`GET /transforms` catalog, `POST /transforms/run` — read-only pivots over
stored recon + graph: domain→IPs, IP→domains, domain→cert, cert→domains,
domain→tech, email→domain, entity→related, domain→subdomains. UI:
Knowledge → Pivot. No live probing here; collection stays in scans.

## Timeline
`GET /timeline` merges scans/findings/alerts/events/changes/evidence
chronologically with type/date/text filters. UI: Intelligence → Timeline.

## Risk (explainable)
`services/risk.py`: 0–100 from documented factors (finding severity,
unresolved alerts, hostile changes ≤30d, linked infrastructure, leak
evidence, collection blind spots), each with points + why + evidence refs.
`GET /risk/target/{id}`, `/risk/entity/{id}`; UI panels on both pages.
AI never overrides these numbers; AI chat is evidence-grounded and labels
inference as inference.
