---
title: Collection: Queued, Running, Success
description: Every async operation exposes queued, running, success, failed and cancelled — with retry and cancel.
category: Investigations
order: 60
slug: investigations/collection
language: en
shots: [09-queued.png, 10-running.png, 11-completed.png]
---

# Collection: Queued, Running, Success

> Every async operation exposes queued, running, success, failed and cancelled — with retry and cancel.

Collection is asynchronous and honest: queued, running, success, failed or cancelled — each with attempts, errors, retry and cancel. (The UI toast says completed when the API records success; browser legs handed to workers report deferred until a worker picks them up.)

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![A newly created collection job on its scan page showing the queued state.](shot:09-queued.png)

![The same collection job running, with attempts accumulating on the scan page.](shot:10-running.png)

![The collection job finished with success, attempts, prices and changes attached.](shot:11-completed.png)

## Steps

1. Start the investigation and note the **queued** state on the scan page.
2. Watch jobs turn **running**; refresh the scan page to see attempts accumulate.
3. Wait for **success** (the toast calls it completed); read failures with their error and attempts.
4. Use **retry** for transient failures, **cancel** for mistakes.
5. Inspect the dead-letter queue for permanently failed work.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/dlq` | Dead Letters |
| `GET` | `/api/v1/jobs` | List Jobs |
| `POST` | `/api/v1/jobs` | Create Job |
| `GET` | `/api/v1/jobs/{job_id}` | Get Job |
| `DELETE` | `/api/v1/jobs/{job_id}` | Delete Job |
| `POST` | `/api/v1/jobs/{job_id}/cancel` | Cancel Job |
| `POST` | `/api/v1/jobs/{job_id}/retry` | Retry Job |
| `POST` | `/api/v1/jobs/{job_id}/run` | Run Job Now |
| `GET` | `/api/v1/operations` | List Operations |
| `POST` | `/api/v1/results` | Ingest Result |
| `GET` | `/api/v1/schedules` | List Schedules |
| `POST` | `/api/v1/schedules` | Create Schedule |
| `GET` | `/api/v1/schedules/{sid}` | Get Schedule |
| `PUT` | `/api/v1/schedules/{sid}` | Update Schedule |
| `DELETE` | `/api/v1/schedules/{sid}` | Delete Schedule |
| `POST` | `/api/v1/schedules/{sid}/disable` | Disable Schedule |
| `POST` | `/api/v1/schedules/{sid}/enable` | Enable Schedule |
| `POST` | `/api/v1/schedules/{sid}/run` | Run Schedule Now |
| `POST` | `/api/v1/worker/tick` | Worker Tick |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/jobs -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/jobs", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/jobs", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
```

_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. Never commit real tokens to documentation._

## Verification

- The new or changed record is visible in the list view.
- `GET /api/v1/audit?size=20` shows the action with your identity.
- Related views (graph, timeline, feed) reflect the change.

## Troubleshooting

- Empty list: run collection first — the platform shows real data only.
- 401: sign in or supply a key; see [Authentication](/docs/security/authentication).
- 429: slow down; see [Rate Limits](/docs/api/rate-limits).

> **Try it:** [Open in application](/#jobs) — opens the live view in the application.


## Related

- [Create an Investigation](/docs/investigations/create-investigation)
- [Target Types](/docs/investigations/target-types)
- [Choosing Scope](/docs/investigations/scope)
- [Projects, Targets & Sources](/docs/investigations/sources)
- [Investigation Profiles: Quick, Standard, Deep](/docs/investigations/profiles)
