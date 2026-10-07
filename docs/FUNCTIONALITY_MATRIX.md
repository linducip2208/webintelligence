# Web Intelligence — Functionality Matrix

_Generated from views.js, the live OpenAPI contract (227 paths), service modules and the STORE. v2.14.0_

| Feature | Menu | Frontend route | API endpoints | Service | Persistence | External dep | Status |
|---|---|---|---|---|---|---|---|
| Dashboard | ? | `#dashboard` | 1 paths | api/dashboard | jobs, findings, alerts | none | WORKING |
| Global Search | Investigate | `#search` | 2 paths | search/service, search/semantic | targets, entities, findings | none | WORKING |
| New Investigation | Investigate | `#new-investigation` | 18 paths | services/recon, services/targets | investigations, targets, jobs | none | WORKING |
| Investigations | Investigate | `#investigations` | 9 paths | api/routers/cases | investigations | none | WORKING |
| Cases | Investigate | `#cases` | 6 paths | api/routers/cases | cases | none | WORKING |
| Entities | Investigate | `#entities` | 8 paths | services/entity_resolution, services/entityops | entities | none | WORKING |
| Intelligence Graph | Investigate | `#graph` | 5 paths | services/graph | nodes, edges | none | WORKING |
| Timeline | Investigate | `#timeline` | 1 paths | services/temporal | events | none | WORKING |
| Targets | Discover | `#targets` | 5 paths | services/targets, services/reliability | targets | none | WORKING |
| Attack Surface | Discover | `#attack` | 1 paths | services/recon | targets | none | WORKING |
| Reconnaissance | Discover | `#recon` | 5 paths | services/recon, services/pipeline | jobs, attempts | none | WORKING |
| Collection Runs | Discover | `#jobs` | 7 paths | services/pipeline, orchestration/orchestrator | jobs, attempts | go-collector, browser | WORKING |
| Collectors | Discover | `#collectors` | 2 paths | services/decision, collectors/brightdata | targets | brightdata, proxies | WORKING |
| Connectors | Discover | `#connectors` | 7 paths | services/connectors, connectors/runners | connectors | none | WORKING |
| Findings | Intelligence | `#findings` | 4 paths | services/correlate | findings | none | WORKING |
| Indicators | Intelligence | `#indicators` | 3 paths | services/infracorr | findings | none | WORKING |
| Risk Analysis | Intelligence | `#risk` | 2 paths | services/risk | findings, targets | none | WORKING |
| Threat Intelligence | Intelligence | `#threat` | 4 paths | services/feed, services/stix | articles, findings, alerts, feed_subs | none | WORKING |
| Intelligence Feed | Intelligence | `#intel-feed` | 3 paths | services/feed | articles, findings, alerts, feed_subs | none | WORKING |
| Watchlists | Monitor | `#watchlists` | 4 paths | services/watchlists | watchlists | none | WORKING |
| Alerts | Monitor | `#alerts` | 8 paths | alerts/service, services/alertlife | alerts | smtp/webhook | WORKING |
| Workflows | Monitor | `#workflows` | 8 paths | services/workflows | workflows | none | WORKING |
| Evidence | Evidence | `#evidence` | 4 paths | services/evidence | evidence, claims | none | WORKING |
| Documents | Evidence | `#documents` | 11 paths | services/documents, services/datasets | documents, datasets | none | WORKING |
| Reports | Evidence | `#reports` | 4 paths | reports/builder | reports | none | WORKING |
| STIX / MISP | Integrations | `#stix` | 5 paths | services/stix | nodes, edges, entities, findings | none | WORKING |
| External APIs | Integrations | `#external-apis` | 3 paths | auth/service, services/webhooks | apikeys | none | WORKING |
| Security Tools | Integrations | `#security-tools` | 1 paths | collectors/brightdata | — | brightdata, proxies, browser | WORKING |
| AI Providers | Integrations | `#ai-providers` | 18 paths | ai/factory, ai/registry, ai/safety | ai_providers | ai-vendors | WORKING |
| Users & Roles | Administration | `#users` | 6 paths | services/rbac, auth/service | memberships, orgs | oidc | WORKING |
| Settings | Administration | `#settings` | 2 paths | services/flags | repo-kv | none | WORKING |
| Audit Log | Administration | `#audit` | 1 paths | api/shared | audit | none | WORKING |
| System Health | Administration | `#health` | 3 paths | services/health | — | mysql, redis, browser | WORKING |
| Research | Intelligence | `#research` | 6 paths | services/research | research | ai-vendors | WORKING |
| Webhooks | Monitor | `#webhooks` | 7 paths | services/webhooks | webhooks, deliveries | none | WORKING |
| Operations | Discover | `#operations` | 1 paths | api/shared | jobs, workflows, deliveries, wfruns | redis | WORKING |
| Schedules | Discover | `#schedules` | 6 paths | services/scheduler, workers | schedules | redis | WORKING |

_Docs: contextual help covers 68 views._
