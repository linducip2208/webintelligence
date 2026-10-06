# Universal Intelligence Platform v2.11.0

> 🌐 **Languages:** [English](#-english) · [Indonesia](#-bahasa-indonesia) · [العربية](#-العربية)
>
> Dashboard UI: `English / Indonesia` — switcher in sidebar, served by `GET /api/v1/i18n?lang=en|id`.
> (Trilingual EN/ID/AR applies to this README documentation only.)

DATA → INFORMATION → KNOWLEDGE → EVIDENCE → INTELLIGENCE → DECISION SUPPORT.

---

## 🇬🇧 English

### Overview
Web/API/document collection (**Go engine + Playwright**), extraction → normalization → quality → entity resolution → dedup → temporal snapshots → change/event detection → knowledge graph → evidence-grounded claims → research runs → findings → feed → watchlists → alerts → workflows → datasets → webhooks. AI via provider abstraction (**Muse Spark 1.3 default**). **MySQL 8.4 + Redis. aaPanel-ready, no Docker.**

Persistence is **write-through**: every mutation commits to MySQL when reachable, else a SQLite file (`DATA_DIR/webintel.db`), else memory — and hydrates on boot, so state survives restarts. Additive auto-migration heals stale dev databases. Tests force in-memory via conftest.

Security: SSRF guard + trusted-egress allowlist, token + scoped/expiring API-key auth, org isolation on every collection (IDOR-tested), HMAC webhook ingestion with replay window, per-IP rate limits (429), body-size guard (413), secret-redacted logs. Set `REQUIRE_AUTH=1` in production.

API surface: **143 versioned paths under `/api/v1`** (verified against `contracts/openapi/openapi.json`; full catalog below).

### Feature catalog (recorded from implementation)

#### 1. Collection & job execution
| Feature | Key endpoints |
|---|---|
| Create / list collection jobs | `POST / GET /api/v1/jobs` |
| Run now, cancel, retry a job | `POST /api/v1/jobs/{job_id}/run`, `/cancel`, `/retry` |
| Result ingestion (Go collector + Python workers post here) | `POST /api/v1/results` |
| Dead-letter queue inspection | `GET /api/v1/dlq` |
| Schedules (once/interval/hourly/daily/weekly/cron/event) + manual tick | `POST / GET /api/v1/schedules`, `POST /api/v1/worker/tick` |
| Collection strategy decision engine (`DIRECT → API → BROWSER → OWN_PROXY → BRIGHT_DATA`) | `POST /api/v1/strategy/decide` |
| Go collector engine (concurrent HTTP/API, retries + backoff/jitter, circuit breaker, rate limit, pooling) | `build/linux/collector` (from `source/go/collector`) |
| Headless browser pool (Playwright, 2 contexts, per-job timeout, media/font blocking) | `GET /api/v1/browser/health` |
| Own-proxy pool health; Bright Data connection test | `GET /api/v1/proxies/health`, `POST /api/v1/brightdata/test` |

#### 2. Sources, targets & connectors
| Feature | Key endpoints |
|---|---|
| Projects | `POST / GET /api/v1/projects` |
| Targets + test-connection (with strategy recommendation) | `POST / GET /api/v1/targets`, `POST /api/v1/targets/{tid}/test` |
| Connectors (RSS / paginated REST / CSV) + match / test / execute | `POST / GET /api/v1/connectors`, `/match`, `/{cid}/test`, `/{cid}/execute` |
| Target reliability score (success rate, latency, stability) | `GET /api/v1/reliability/targets` |
| Per-target learning profile (EWMA latency/cost, preferred strategy); robots.txt/ToS respected | `services/targets.py` |

#### 3. Price, market, review & news intelligence
| Feature | Key endpoints |
|---|---|
| Price points + price correlation | `GET /api/v1/prices`, `POST /api/v1/correlate/prices` |
| Price analytics + market trends / emerging topics | `GET /api/v1/analytics/prices`, `/analytics/trends` |
| Data-quality scoring | `POST /api/v1/quality/score`, `GET /api/v1/analytics/quality` |
| Website change feed + change classification | `GET /api/v1/changes`, `POST /api/v1/changes/classify` |
| Opportunities (z-score) | `GET /api/v1/opportunities` |
| News articles | `POST / GET /api/v1/articles` |
| Reviews: CSV import, summary (avg rating, sentiment, themes), moderation queue | `POST /api/v1/reviews/import`, `GET /api/v1/reviews/summary`, `/reviews/queue` |
| Competitor compare (evidence-backed), review intel, news summarization | `POST /api/v1/intel/competitors/compare`, `/intel/reviews`, `/intel/news/summarize` |

#### 4. Knowledge graph, evidence & research
| Feature | Key endpoints |
|---|---|
| Graph nodes / edges, traverse, shortest path, SVG render | `POST /api/v1/graph/nodes`, `/edges`, `GET /traverse`, `/path`, `/render` |
| Events, evidence store, claims + verification, contradiction check | `POST / GET /api/v1/events`, `/evidence`, `/claims`, `/claims/verify`, `/contradictions/check` |
| Findings + data lineage | `POST / GET /api/v1/findings`, `GET /findings/{fid}`, `/lineage/{fid}` |
| Intelligence feed + subscriptions + personalized feed | `GET /api/v1/feed`, `/feed/personalized`, `POST /api/v1/feed/subscriptions` |
| Research: plan, runs, AI analyze, finish, compare, markdown export | `POST /api/v1/research/plan`, `/runs`, `/runs/{rid}/analyze`, `/finish`, `/compare`, `/export` |
| Entities: list / detail / resolve / merge / split / reject / aliases / history | `GET / POST /api/v1/entities...` (8 paths) |

#### 5. Monitoring: watchlists, alerts, workflows, webhooks
| Feature | Key endpoints |
|---|---|
| Watchlists (keyword/company/domain) + global check + per-item evaluate | `POST / GET /api/v1/watchlists`, `/check`, `/{wid}/evaluate`, `DELETE /{wid}` |
| Alerts: create/list, ack, resolve, bulk, rule check, send, incidents | `POST / GET /api/v1/alerts`, `/{alert_id}/ack`, `/resolve`, `/bulk`, `/check`, `/send`, `/incidents` |
| Workflows (trigger → action): CRUD, run, idempotent retry, cancel | `POST / GET /api/v1/workflows`, `/{wid}`, `/run`, `/retry`, `/cancel` |
| Maintenance windows + disable | `POST / GET /api/v1/maintenance`, `/{mid}/disable` |
| Outbound webhooks: CRUD, test, delivery log + replay | `POST / GET /api/v1/webhooks`, `/{wid}/test`, `/deliveries`, `/deliveries/{did}/replay` |
| Inbound webhook ingestion (HMAC-signed, replay window) | `POST /api/v1/ingest/webhook` |

#### 6. Datasets, documents & reports
| Feature | Key endpoints |
|---|---|
| Datasets: CRUD, per-dataset versions, diff, rollback, CSV import, export, publish, archive | `POST / GET /api/v1/datasets`, `/{did}/versions`, `/diff`, `/rollback`, `/import`, `/export`, `/publish`, `/archive` |
| Document ingestion (txt/html/csv; pdf via pypdf) | `POST / GET /api/v1/documents` |
| Reports (market/competitor/product/price/review/site/executive) + export (web/PDF/CSV/JSON/XLSX/markdown) | `POST / GET /api/v1/reports`, `GET /api/v1/reports/{rep_id}/export` |

#### 7. AI, search & ask
| Feature | Key endpoints |
|---|---|
| AI providers (env + DB-configured), disable, models, health, usage/cost, prompt registry | `GET /api/v1/ai/providers`, `/providers/db`, `/{pid}/disable`, `/models`, `/health`, `/usage`, `/prompts` |
| Evidence-grounded chat + ask (`evidence_ids` + citations) | `POST /api/v1/ai/chat`, `POST /api/v1/ask` |
| FULLTEXT search + semantic search abstraction | `GET /api/v1/search`, `/search/semantic` |
| ML: model registry + prediction (forecast, anomaly, classification, clustering) | `POST /api/v1/ml/register`, `GET /api/v1/ml/models`, `POST /api/v1/ml/predict` |

#### 8. Admin, billing & governance
| Feature | Key endpoints |
|---|---|
| Organizations + white-label branding, members, builtin + custom roles (RBAC), login disable | `POST / GET /api/v1/orgs`, `/orgs/{oid}/branding`, `/memberships`, `/roles`, `/users/{email}/disable` |
| Full management CRUD: projects/targets/jobs/schedules/alerts/workflows/webhooks/connectors/datasets/documents detail pages, bulk ops, CSV export | see `/docs` (Settings view) + `contracts/openapi/openapi.json` (178 paths) |
| Scoped/expiring API keys + revoke | `POST / GET /api/v1/apikeys`, `POST /api/v1/apikeys/{kid}/revoke` |
| Auth: login (Bearer), OIDC login/callback/providers | `POST /api/v1/auth/login`, `/auth/oidc/login`, `/callback`, `/providers` |
| Commercial billing: plans, current plan, usage/quotas (402 on exceed) | `GET /api/v1/billing/plans`, `/plan`, `/usage` |
| Feature flags (global/org/user) | `GET / POST /api/v1/flags` |
| Industry vertical templates + apply | `GET /api/v1/verticals`, `/{name}`, `POST /{name}/apply` |
| Retention runner, cost summary, budget set/check | `POST /api/v1/admin/retention/run`, `GET /api/v1/costs/summary`, `POST /api/v1/costs/budget`, `GET /budget/check` |
| Audit trail, system doctor | `GET /api/v1/audit`, `/api/v1/system/doctor` |

#### 9. Platform (non-API)
| Feature | Notes |
|---|---|
| Dashboard (real data only, dark/light, EN/ID, toasts, executive view) | `GET /`, `GET /api/v1/dashboard` |
| i18n (English, Indonesia) | `GET /api/v1/i18n?lang=en\|id` |
| Version, liveness, readiness, Prometheus metrics | `GET /api/version`, `/healthz`, `/readyz`, `/metrics` |
| Persistence / security / reliability / deployment / CLI / backup-restore / PII masking | see Overview; `source/python/cli.py`, `deploy/` |

### Quick start (Windows dev / Linux same, minus service files)
```bat
cd source\python
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m pytest tests -q
venv\Scripts\python -m uvicorn app.main:app --port 8000
```
Go collector:
```bat
cd source\go\collector
go test ./...
go build -o ..\..\..\build\linux\collector .\cmd\collector
```
Open http://127.0.0.1:8000/ for the dashboard (real data only).

### Deploy (aaPanel)
See `deploy/aaPanel/README.md` and `deploy/scripts/deploy_aapanel.sh`. Nginx: `deploy/nginx/webintel.conf`. systemd units: `deploy/systemd/`.

### Live credentials required for
- Bright Data (`BRIGHTDATA_API_KEY`, `BRIGHTDATA_ZONE`) — adapter + `POST /api/v1/brightdata/test` work; live crawl tests skip without creds.
- Muse Spark 1.3 (`MUSE_SPARK_BASE_URL`, `MUSE_SPARK_API_KEY`) — provider + health endpoint work; live chat test requires creds.
- MySQL/Redis URLs for integration runs.

See `docs/MASTER_BUILD_SPEC.md` for the full architecture.

---

## 🇮🇩 Bahasa Indonesia

### Ringkasan
Pengumpulan data Web/API/dokumen (**mesin Go + Playwright**), ekstraksi → normalisasi → kualitas → resolusi entitas → dedup → snapshot temporal → deteksi perubahan/peristiwa → knowledge graph → klaim berbasis bukti → riset → temuan → umpan → daftar pantau → peringatan → alur kerja → dataset → webhook. AI melalui abstraksi provider (**default Muse Spark 1.3**). **MySQL 8.4 + Redis. Siap aaPanel, tanpa Docker.**

Persistensi **write-through**: setiap perubahan tersimpan ke MySQL jika terjangkau, jika tidak ke file SQLite (`DATA_DIR/webintel.db`), jika tidak ke memori — dan dimuat ulang saat boot, sehingga status tetap bertahan setelah restart. Auto-migrasi aditif memperbaiki database dev yang usang. Tes memaksa mode in-memory via conftest.

Keamanan: pelindung SSRF + allowlist egress tepercaya, auth token + API-key berskop/kedaluwarsa, isolasi org di setiap koleksi (teruji IDOR), ingest webhook HMAC dengan jendela replay, rate limit per-IP (429), penjaga ukuran body (413), log yang menyensor rahasia. Setel `REQUIRE_AUTH=1` di produksi.

Permukaan API: **143 path berversi di bawah `/api/v1`** (terverifikasi terhadap `contracts/openapi/openapi.json`; katalog lengkap di bawah).

### Katalog fitur (dicatat dari implementasi)

#### 1. Koleksi & eksekusi job
| Fitur | Endpoint utama |
|---|---|
| Buat / lihat daftar job koleksi | `POST / GET /api/v1/jobs` |
| Jalankan sekarang, batalkan, ulangi job | `POST /api/v1/jobs/{job_id}/run`, `/cancel`, `/retry` |
| Penampungan hasil (kolektor Go + worker Python melapor ke sini) | `POST /api/v1/results` |
| Inspeksi antrean gagal (dead-letter queue) | `GET /api/v1/dlq` |
| Jadwal (sekali/interval/per jam/harian/mingguan/cron/event) + tick manual | `POST / GET /api/v1/schedules`, `POST /api/v1/worker/tick` |
| Mesin keputusan strategi koleksi (`DIRECT → API → BROWSER → OWN_PROXY → BRIGHT_DATA`) | `POST /api/v1/strategy/decide` |
| Mesin kolektor Go (HTTP/API konkuren, retry + backoff/jitter, circuit breaker, rate limit, pooling) | `build/linux/collector` (dari `source/go/collector`) |
| Pool browser headless (Playwright, 2 konteks, timeout per-job, blokir media/font) | `GET /api/v1/browser/health` |
| Kesehatan pool proxy sendiri; tes koneksi Bright Data | `GET /api/v1/proxies/health`, `POST /api/v1/brightdata/test` |

#### 2. Sumber, target & konektor
| Fitur | Endpoint utama |
|---|---|
| Proyek | `POST / GET /api/v1/projects` |
| Target + tes koneksi (dengan rekomendasi strategi) | `POST / GET /api/v1/targets`, `POST /api/v1/targets/{tid}/test` |
| Konektor (RSS / REST berpaginasi / CSV) + cocokkan / tes / eksekusi | `POST / GET /api/v1/connectors`, `/match`, `/{cid}/test`, `/{cid}/execute` |
| Skor keandalan target (tingkat sukses, latensi, stabilitas) | `GET /api/v1/reliability/targets` |
| Profil belajar per-target (latensi/biaya EWMA, strategi terbaik); menghormati robots.txt/ToS | `services/targets.py` |

#### 3. Intelijen harga, pasar, ulasan & berita
| Fitur | Endpoint utama |
|---|---|
| Titik harga + korelasi harga | `GET /api/v1/prices`, `POST /api/v1/correlate/prices` |
| Analitik harga + tren pasar / topik emerging | `GET /api/v1/analytics/prices`, `/analytics/trends` |
| Skoring kualitas data | `POST /api/v1/quality/score`, `GET /api/v1/analytics/quality` |
| Arus perubahan situs + klasifikasi perubahan | `GET /api/v1/changes`, `POST /api/v1/changes/classify` |
| Peluang (z-score) | `GET /api/v1/opportunities` |
| Artikel berita | `POST / GET /api/v1/articles` |
| Ulasan: impor CSV, ringkasan (rating, sentimen, tema), antrean moderasi | `POST /api/v1/reviews/import`, `GET /api/v1/reviews/summary`, `/reviews/queue` |
| Banding kompetitor (berbasis bukti), intel ulasan, ringkasan berita | `POST /api/v1/intel/competitors/compare`, `/intel/reviews`, `/intel/news/summarize` |

#### 4. Knowledge graph, bukti & riset
| Fitur | Endpoint utama |
|---|---|
| Node/edge graf, traversal, jalur terpendek, render SVG | `POST /api/v1/graph/nodes`, `/edges`, `GET /traverse`, `/path`, `/render` |
| Peristiwa, bank bukti, klaim + verifikasi, cek kontradiksi | `POST / GET /api/v1/events`, `/evidence`, `/claims`, `/claims/verify`, `/contradictions/check` |
| Temuan + silsilah data (lineage) | `POST / GET /api/v1/findings`, `GET /findings/{fid}`, `/lineage/{fid}` |
| Umpan intelijen + langganan + umpan personal | `GET /api/v1/feed`, `/feed/personalized`, `POST /api/v1/feed/subscriptions` |
| Riset: rencana, run, analisis AI, selesaikan, bandingkan, ekspor markdown | `POST /api/v1/research/plan`, `/runs`, `/runs/{rid}/analyze`, `/finish`, `/compare`, `/export` |
| Entitas: daftar / detail / resolve / gabung / pisah / tolak / alias / riwayat | `GET / POST /api/v1/entities...` (8 path) |

#### 5. Pemantauan: daftar pantau, peringatan, workflow, webhook
| Fitur | Endpoint utama |
|---|---|
| Daftar pantau (keyword/perusahaan/domain) + cek global + evaluasi per-item | `POST / GET /api/v1/watchlists`, `/check`, `/{wid}/evaluate`, `DELETE /{wid}` |
| Peringatan: buat/daftar, ack, resolve, bulk, cek aturan, kirim, insiden | `POST / GET /api/v1/alerts`, `/{alert_id}/ack`, `/resolve`, `/bulk`, `/check`, `/send`, `/incidents` |
| Workflow (pemicu → aksi): CRUD, jalankan, retry idempoten, batal | `POST / GET /api/v1/workflows`, `/{wid}`, `/run`, `/retry`, `/cancel` |
| Jendela pemeliharaan + nonaktifkan | `POST / GET /api/v1/maintenance`, `/{mid}/disable` |
| Webhook keluar: CRUD, tes, log pengiriman + ulangi | `POST / GET /api/v1/webhooks`, `/{wid}/test`, `/deliveries`, `/deliveries/{did}/replay` |
| Ingest webhook masuk (bertanda HMAC, jendela replay) | `POST /api/v1/ingest/webhook` |

#### 6. Dataset, dokumen & laporan
| Fitur | Endpoint utama |
|---|---|
| Dataset: CRUD, versi per-dataset, diff, rollback, impor CSV, ekspor, publikasi, arsip | `POST / GET /api/v1/datasets`, `/{did}/versions`, `/diff`, `/rollback`, `/import`, `/export`, `/publish`, `/archive` |
| Ingest dokumen (txt/html/csv; pdf via pypdf) | `POST / GET /api/v1/documents` |
| Laporan (pasar/kompetitor/produk/harga/ulasan/situs/eksekutif) + ekspor (web/PDF/CSV/JSON/XLSX/markdown) | `POST / GET /api/v1/reports`, `GET /api/v1/reports/{rep_id}/export` |

#### 7. AI, pencarian & tanya
| Fitur | Endpoint utama |
|---|---|
| Provider AI (env + konfigurasi-DB), nonaktifkan, model, kesehatan, usage/biaya, registry prompt | `GET /api/v1/ai/providers`, `/providers/db`, `/{pid}/disable`, `/models`, `/health`, `/usage`, `/prompts` |
| Chat + tanya berbasis bukti (`evidence_ids` + sitasi) | `POST /api/v1/ai/chat`, `POST /api/v1/ask` |
| Pencarian FULLTEXT + abstraksi pencarian semantik | `GET /api/v1/search`, `/search/semantic` |
| ML: registry model + prediksi (forecast, anomali, klasifikasi, clustering) | `POST /api/v1/ml/register`, `GET /api/v1/ml/models`, `POST /api/v1/ml/predict` |

#### 8. Admin, billing & tata kelola
| Fitur | Endpoint utama |
|---|---|
| Organisasi + branding white-label, anggota, role bawaan + custom (RBAC), disable login | `POST / GET /api/v1/orgs`, `/orgs/{oid}/branding`, `/memberships`, `/roles`, `/users/{email}/disable` |
| CRUD manajemen penuh: detail project/target/job/schedule/alert/workflow/webhook/connector/dataset/dokumen, bulk ops, ekspor CSV | lihat `/docs` (view Settings) + `contracts/openapi/openapi.json` (178 path) |
| API key berskop/kedaluwarsa + revoke | `POST / GET /api/v1/apikeys`, `POST /api/v1/apikeys/{kid}/revoke` |
| Auth: login (Bearer), OIDC login/callback/providers | `POST /api/v1/auth/login`, `/auth/oidc/login`, `/callback`, `/providers` |
| Billing komersial: paket, paket aktif, usage/kuota (402 jika lewat) | `GET /api/v1/billing/plans`, `/plan`, `/usage` |
| Feature flag (global/org/user) | `GET / POST /api/v1/flags` |
| Template vertikal industri + terapkan | `GET /api/v1/verticals`, `/{name}`, `POST /{name}/apply` |
| Retention runner, ringkasan biaya, set/cek budget | `POST /api/v1/admin/retention/run`, `GET /api/v1/costs/summary`, `POST /api/v1/costs/budget`, `GET /budget/check` |
| Audit trail, system doctor | `GET /api/v1/audit`, `/api/v1/system/doctor` |

#### 9. Platform (non-API)
| Fitur | Catatan |
|---|---|
| Dasbor (hanya data nyata, gelap/terang, EN/ID, toast, tampilan eksekutif) | `GET /`, `GET /api/v1/dashboard` |
| i18n (Inggris, Indonesia) | `GET /api/v1/i18n?lang=en\|id` |
| Versi, liveness, readiness, metrik Prometheus | `GET /api/version`, `/healthz`, `/readyz`, `/metrics` |
| Persistensi / keamanan / reliabilitas / deployment / CLI / backup-restore / masking PII | lihat Ringkasan; `source/python/cli.py`, `deploy/` |

### Mulai cepat
```bat
cd source\python
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m pytest tests -q
venv\Scripts\python -m uvicorn app.main:app --port 8000
```
Kolektor Go:
```bat
cd source\go\collector
go test ./...
go build -o ..\..\..\build\linux\collector .\cmd\collector
```
Buka http://127.0.0.1:8000/ untuk dasbor (hanya data nyata).

### Deploy (aaPanel)
Lihat `deploy/aaPanel/README.md` dan `deploy/scripts/deploy_aapanel.sh`. Nginx: `deploy/nginx/webintel.conf`. Unit systemd: `deploy/systemd/`.

### Kredensial live yang dibutuhkan
- Bright Data (`BRIGHTDATA_API_KEY`, `BRIGHTDATA_ZONE`) — adapter + `POST /api/v1/brightdata/test` berfungsi; tes crawl live dilewati tanpa kredensial.
- Muse Spark 1.3 (`MUSE_SPARK_BASE_URL`, `MUSE_SPARK_API_KEY`) — provider + endpoint kesehatan berfungsi; tes chat live butuh kredensial.
- URL MySQL/Redis untuk uji integrasi.

Lihat `docs/MASTER_BUILD_SPEC.md` untuk arsitektur lengkap.

---

## 🇸🇦 العربية

### نظرة عامة
جمع بيانات الويب / API / المستندات (**محرك Go + Playwright**)، استخراج ← تطبيع ← جودة ← حل الكيانات ← إزالة التكرار ← لقطات زمنية ← كشف التغييرات/الأحداث ← الرسم المعرفي ← ادعاءات موثقة بالأدلة ← جولات بحث ← نتائج ← موجز ← قوائم مراقبة ← تنبيهات ← سير عمل ← مجموعات بيانات ← ويب هوك. الذكاء الاصطناعي عبر تجريد المزودين (**Muse Spark 1.3 افتراضيًا**). **MySQL 8.4 + Redis. جاهز لـ aaPanel، بدون Docker.**

الثبات **write-through**: كل تعديل يُحفظ في MySQL عند توفرها، وإلا في ملف SQLite (`DATA_DIR/webintel.db`)، وإلا في الذاكرة — ويُحمَّل عند الإقلاع، فتبقى الحالة بعد إعادة التشغيل. الترحيل التلقائي الإضافي يعالج قواعد بيانات التطوير القديمة. الاختبارات تفرض وضع الذاكرة عبر conftest.

الأمان: حماية SSRF + قائمة egress موثوقة، مصادقة بالرمز + مفاتيح API محددة النطاق ومنتهية الصلاحية، عزل المنظمات في كل مجموعة (مختبر ضد IDOR)، استقبال ويب هوك بتوقيع HMAC مع نافذة إعادة، حدود معدل لكل IP (429)، حد حجم الجسم (413)، سجلات تُخفي الأسرار. اضبط `REQUIRE_AUTH=1` في الإنتاج.

سطح API: **143 مسارًا مُصدَرًا تحت `/api/v1`** (تم التحقق مقابل `contracts/openapi/openapi.json`؛ الفهرس الكامل أدناه).

### فهرس الميزات (موثق من التنفيذ)

#### 1. الجمع وتنفيذ المهام
| الميزة | نقاط النهاية الرئيسية |
|---|---|
| إنشاء / عرض مهام الجمع | `POST / GET /api/v1/jobs` |
| تشغيل فوري، إلغاء، إعادة المحاولة | `POST /api/v1/jobs/{job_id}/run`، `/cancel`، `/retry` |
| استقبال النتائج (يُرسل إليها جامع Go وعمال Python) | `POST /api/v1/results` |
| فحص قائمة الرسائل الفاشلة | `GET /api/v1/dlq` |
| الجداول (مرة/فاصل/ساعي/يومي/أسبوعي/cron/حدث) + تشغيل يدوي | `POST / GET /api/v1/schedules`، `POST /api/v1/worker/tick` |
| محرك قرار استراتيجية الجمع (`DIRECT ← API ← BROWSER ← OWN_PROXY ← BRIGHT_DATA`) | `POST /api/v1/strategy/decide` |
| محرك الجمع Go (متزامن، إعادة محاولة، قاطع دائرة، تحديد معدل، تجميع اتصالات) | `build/linux/collector` (من `source/go/collector`) |
| تجمع المتصفح headless (Playwright، سياقان، مهلة لكل مهمة، حظر الوسائط) | `GET /api/v1/browser/health` |
| صحة تجمع البروكسي؛ اختبار اتصال Bright Data | `GET /api/v1/proxies/health`، `POST /api/v1/brightdata/test` |

#### 2. المصادر والأهداف والموصلات
| الميزة | نقاط النهاية الرئيسية |
|---|---|
| المشاريع | `POST / GET /api/v1/projects` |
| الأهداف + اختبار الاتصال (مع توصية استراتيجية) | `POST / GET /api/v1/targets`، `POST /api/v1/targets/{tid}/test` |
| الموصلات (RSS / REST مُرقّم / CSV) + مطابقة / اختبار / تنفيذ | `POST / GET /api/v1/connectors`، `/match`، `/{cid}/test`، `/{cid}/execute` |
| درجة موثوقية الأهداف (معدل النجاح، الزمن، الاستقرار) | `GET /api/v1/reliability/targets` |
| ملف تعلم لكل هدف؛ احترام robots.txt/الشروط | `services/targets.py` |

#### 3. استخبارات الأسعار والسوق والمراجعات والأخبار
| الميزة | نقاط النهاية الرئيسية |
|---|---|
| نقاط الأسعار + ارتباط الأسعار | `GET /api/v1/prices`، `POST /api/v1/correlate/prices` |
| تحليلات الأسعار + اتجاهات السوق / المواضيع الناشئة | `GET /api/v1/analytics/prices`، `/analytics/trends` |
| تقييم جودة البيانات | `POST /api/v1/quality/score`، `GET /api/v1/analytics/quality` |
| موجز تغييرات المواقع + تصنيف التغييرات | `GET /api/v1/changes`، `POST /api/v1/changes/classify` |
| الفرص (z-score) | `GET /api/v1/opportunities` |
| المقالات الإخبارية | `POST / GET /api/v1/articles` |
| المراجعات: استيراد CSV، ملخص، قائمة مراجعة | `POST /api/v1/reviews/import`، `GET /api/v1/reviews/summary`، `/reviews/queue` |
| مقارنة المنافسين (موثقة)، استخبارات المراجعات، تلخيص الأخبار | `POST /api/v1/intel/competitors/compare`، `/intel/reviews`، `/intel/news/summarize` |

#### 4. الرسم المعرفي والأدلة والبحث
| الميزة | نقاط النهاية الرئيسية |
|---|---|
| العقد/الحواف، الاجتياز، أقصر مسار، عرض SVG | `POST /api/v1/graph/nodes`، `/edges`، `GET /traverse`، `/path`، `/render` |
| الأحداث، مخزن الأدلة، الادعاءات + التحقق، فحص التناقضات | `POST / GET /api/v1/events`، `/evidence`، `/claims`، `/claims/verify`، `/contradictions/check` |
| النتائج + نسب البيانات | `POST / GET /api/v1/findings`، `GET /findings/{fid}`، `/lineage/{fid}` |
| الموجز + الاشتراكات + الموجز المخصص | `GET /api/v1/feed`، `/feed/personalized`، `POST /api/v1/feed/subscriptions` |
| البحث: خطة، جولات، تحليل AI، إنهاء، مقارنة، تصدير markdown | `POST /api/v1/research/plan`، `/runs`، `/runs/{rid}/analyze`، `/finish`، `/compare`، `/export` |
| الكيانات: عرض/تفصيل/حل/دمج/تقسيم/رفض/بدائل/سجل | `GET / POST /api/v1/entities...` (8 مسارات) |

#### 5. المراقبة: قوائم المراقبة والتنبيهات وسير العمل والويب هوك
| الميزة | نقاط النهاية الرئيسية |
|---|---|
| قوائم المراقبة + فحص شامل + تقييم لكل عنصر | `POST / GET /api/v1/watchlists`، `/check`، `/{wid}/evaluate`، `DELETE /{wid}` |
| التنبيهات: إنشاء/عرض، إقرار، حل، جماعي، فحص القواعد، إرسال، حوادث | `POST / GET /api/v1/alerts`، `/{alert_id}/ack`، `/resolve`، `/bulk`، `/check`، `/send`، `/incidents` |
| سير العمل (محفز ← إجراء): CRUD، تشغيل، إعادة غير مكررة، إلغاء | `POST / GET /api/v1/workflows`، `/{wid}`، `/run`، `/retry`، `/cancel` |
| نوافذ الصيانة + تعطيل | `POST / GET /api/v1/maintenance`، `/{mid}/disable` |
| الويب هوك الصادر: CRUD، اختبار، سجل التسليم + إعادة | `POST / GET /api/v1/webhooks`، `/{wid}/test`، `/deliveries`، `/deliveries/{did}/replay` |
| استقبال الويب هوك (بتوقيع HMAC) | `POST /api/v1/ingest/webhook` |

#### 6. مجموعات البيانات والمستندات والتقارير
| الميزة | نقاط النهاية الرئيسية |
|---|---|
| مجموعات البيانات: CRUD، إصدارات، diff، rollback، استيراد CSV، تصدير، نشر، أرشفة | `POST / GET /api/v1/datasets`، `/{did}/versions`، `/diff`، `/rollback`، `/import`، `/export`، `/publish`، `/archive` |
| استقبال المستندات (txt/html/csv؛ pdf عبر pypdf) | `POST / GET /api/v1/documents` |
| التقارير (سوق/منافسين/منتجات/أسعار/مراجعات/مواقع/تنفيذية) + تصدير (web/PDF/CSV/JSON/XLSX/markdown) | `POST / GET /api/v1/reports`، `GET /api/v1/reports/{rep_id}/export` |

#### 7. الذكاء الاصطناعي والبحث والسؤال
| الميزة | نقاط النهاية الرئيسية |
|---|---|
| مزودو AI (env + DB)، تعطيل، نماذج، صحة، استخدام/تكلفة، سجل prompts | `GET /api/v1/ai/providers`، `/providers/db`، `/{pid}/disable`، `/models`، `/health`، `/usage`، `/prompts` |
| دردشة + سؤال موثق بالأدلة | `POST /api/v1/ai/chat`، `POST /api/v1/ask` |
| بحث FULLTEXT + تجريد البحث الدلالي | `GET /api/v1/search`، `/search/semantic` |
| تعلم الآلة: سجل النماذج + تنبؤ | `POST /api/v1/ml/register`، `GET /api/v1/ml/models`، `POST /api/v1/ml/predict` |

#### 8. الإدارة والفوترة والحوكمة
| الميزة | نقاط النهاية الرئيسية |
|---|---|
| المنظمات + branding، الأعضاء، أدوار مدمجة + مخصصة (RBAC)، تعطيل الدخول | `POST / GET /api/v1/orgs`، `/orgs/{oid}/branding`، `/memberships`، `/roles`، `/users/{email}/disable` |
| إدارة CRUD كاملة: صفحات تفصيل project/target/job/schedule/alert/workflow/webhook/connector/dataset/document، عمليات جماعية، تصدير CSV | انظر `/docs` + `contracts/openapi/openapi.json` (178 مسارًا) |
| مفاتيح API محددة النطاق/منتهية + إلغاء | `POST / GET /api/v1/apikeys`، `POST /api/v1/apikeys/{kid}/revoke` |
| المصادقة: دخول (Bearer)، OIDC | `POST /api/v1/auth/login`، `/auth/oidc/login`، `/callback`، `/providers` |
| الفوترة: الخطط، الخطة الحالية، الاستخدام/الحصص (402 عند التجاوز) | `GET /api/v1/billing/plans`، `/plan`، `/usage` |
| أعلام الميزات (عام/منظمة/مستخدم) | `GET / POST /api/v1/flags` |
| قوالب القطاعات + تطبيق | `GET /api/v1/verticals`، `/{name}`، `POST /{name}/apply` |
| الاحتفاظ التلقائي، ملخص التكاليف، ضبط/فحص الميزانية | `POST /api/v1/admin/retention/run`، `GET /api/v1/costs/summary`، `POST /api/v1/costs/budget`، `GET /budget/check` |
| سجل التدقيق، طبيب النظام | `GET /api/v1/audit`، `/api/v1/system/doctor` |

#### 9. المنصة (غير API)
| الميزة | ملاحظات |
|---|---|
| لوحة التحكم (بيانات حقيقية فقط، داكن/فاتح، EN/ID، عرض تنفيذي) | `GET /`، `GET /api/v1/dashboard` |
| i18n (الإنجليزية، الإندونيسية) | `GET /api/v1/i18n?lang=en\|id` |
| الإصدار، الحيوية، الجاهزية، مقاييس بروميثيوس | `GET /api/version`، `/healthz`، `/readyz`، `/metrics` |
| الثبات / الأمان / الموثوقية / النشر / CLI / النسخ الاحتياطي / إخفاء PII | انظر النظرة العامة؛ `source/python/cli.py`، `deploy/` |

### بداية سريعة
```bat
cd source\python
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m pytest tests -q
venv\Scripts\python -m uvicorn app.main:app --port 8000
```
جامع Go:
```bat
cd source\go\collector
go test ./...
go build -o ..\..\..\build\linux\collector .\cmd\collector
```
افتح http://127.0.0.1:8000/ للوحة التحكم (بيانات حقيقية فقط).

### النشر (aaPanel)
انظر `deploy/aaPanel/README.md` و `deploy/scripts/deploy_aapanel.sh`. ‏Nginx: `deploy/nginx/webintel.conf`. وحدات systemd: `deploy/systemd/`.

### بيانات الاعتماد الحية المطلوبة
- Bright Data (`BRIGHTDATA_API_KEY`، `BRIGHTDATA_ZONE`) — المحول + `POST /api/v1/brightdata/test` يعملان؛ تُتخطى اختبارات الزحف الحية بدون بيانات.
- Muse Spark 1.3 (`MUSE_SPARK_BASE_URL`، `MUSE_SPARK_API_KEY`) — المزود + نقطة الصحة يعملان؛ اختبار الدردشة الحية يحتاج بيانات.
- روابط MySQL/Redis لاختبارات التكامل.

انظر `docs/MASTER_BUILD_SPEC.md` للمعمارية الكاملة.
