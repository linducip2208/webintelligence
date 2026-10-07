# Web Intelligence — Performance Audit (baseline, app v2.14.0)

_Median/max of 5 in-process runs (TestClient, in-memory backend). Regression baseline only — not production hardware figures._

| Endpoint | Median ms | Max ms | Budget |
|---|---|---|---|
| dashboard | 6.1 | 7.0 | 250 ms (OK) |
| search keyword | 8.7 | 34.0 | 250 ms (OK) |
| search hybrid | 7.8 | 9.6 | 250 ms (OK) |
| entities list | 6.2 | 6.9 | 250 ms (OK) |
| graph traverse | 6.4 | 10.9 | 250 ms (OK) |
| findings list | 5.2 | 10.3 | 250 ms (OK) |
| risk target | 5.8 | 8.9 | 1000 ms (OK) |
| healthz | 3.3 | 5.7 | 250 ms (OK) |
| readyz | 6.5 | 8.5 | 250 ms (OK) |
| ai inventory | 8.3 | 13.3 | 250 ms (OK) |
| ai health | 5.3 | 7.1 | 250 ms (OK) |
| docs search | 11.0 | 985.1 | 1000 ms (OK) |
| docs page | 12.3 | 16.5 | 1000 ms (OK) |
| settings system | 12.4 | 212.2 | 250 ms (OK) |

## Notes

- Pagination enforced on list endpoints (max size 100).
- Graph traversal bounded (depth + limit); full universe never loads by default.
- AI health aggregate performs no live calls; tests are explicit buttons.
- Docs screenshots lazy-load with dimensions (no layout shift).
