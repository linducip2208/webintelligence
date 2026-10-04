# Universal Intelligence Platform v2.11.0

> 🌐 **Languages:** [English](#-english) · [Indonesia](#-bahasa-indonesia) · [العربية](#-العربية)
>
> Dashboard UI: `English / Indonesia / العربية` (RTL supported) — switcher in sidebar, served by `GET /api/v1/i18n?lang=en|id|ar`.

DATA → INFORMATION → KNOWLEDGE → EVIDENCE → INTELLIGENCE → DECISION SUPPORT.

---

## 🇬🇧 English

### Overview
Web/API/document collection (**Go engine + Playwright**), extraction → normalization → quality → entity resolution → dedup → temporal snapshots → change/event detection → knowledge graph → evidence-grounded claims → research runs → findings → feed → watchlists → alerts → workflows → datasets → webhooks. AI via provider abstraction (**Muse Spark 1.3 default**). **MySQL 8.4 + Redis. aaPanel-ready, no Docker.**

Persistence is **write-through**: every mutation commits to MySQL when reachable, else a SQLite file (`DATA_DIR/webintel.db`), else memory — and hydrates on boot, so state survives restarts. Additive auto-migration heals stale dev databases. Tests force in-memory via conftest.

Security: SSRF guard + trusted-egress allowlist, token + scoped/expiring API-key auth, org isolation on every collection (IDOR-tested), HMAC webhook ingestion with replay window, per-IP rate limits (429), body-size guard (413), secret-redacted logs. Set `REQUIRE_AUTH=1` in production.

API surface: **143 versioned paths under `/api/v1`** (see `contracts/openapi/openapi.json`): orgs, roles, memberships, apikeys, projects, targets, jobs, results, prices, changes, articles, search (+semantic), analytics, intel (compare/reviews/news), entities, costs, ml (+predict), alerts (+check/send), reports (+export), ask, feed (+subscriptions), opportunities, research, watchlists, workflows, datasets, connectors, documents (+reviews), webhooks (+ingest/deliveries), i18n (`en|id|ar`), audit, dashboard, health, metrics, browser.

### Features
1. **Collection engine (Go + Python workers)** — concurrent HTTP/API collection, retries with backoff+jitter, circuit breaker, rate limiting, connection pooling, graceful shutdown. Collection strategy escalation: `DIRECT → API → BROWSER → OWN_PROXY → BRIGHT_DATA`.
2. **Headless browser (Playwright)** — pooled contexts (default 2), per-job timeout, media/font blocking, session-per-job, metadata capture (status, final URL, size, ms).
3. **Connectors** — RSS / paginated REST / CSV execution with `test` + `execute` endpoints; target `test-connection` with strategy recommendation.
4. **Target intelligence** — per-target profile (success rate, EWMA latency/cost, preferred strategy learning); respects robots.txt/ToS.
5. **Normalization & ETL** — products, companies, prices, reviews, articles, offers, websites, events, search results → typed tables with full provenance (`raw_document_id`, parser/schema versions).
6. **Entity resolution** — exact → normalized-string → domain/identifier → fuzzy (≥0.87 auto-link, 0.70–0.87 needs review) → optional AI assist; aliases, merge/split/reject, history, `needs_review` queue.
7. **Price intelligence** — history, change detection, volatility (stdev/mean), competitor comparison, `price_drop_pct` / `back_in_stock` alerts.
8. **Competitor / Market / Review / News intelligence** — evidence-backed compare (every claim cites `raw_document_id`), category trends, TF-based emerging topics, lexicon sentiment + complaint/praise themes, extractive news summaries.
9. **Change detection** — hash + field-level compare → `NEW / CHANGED / REMOVED / UNCHANGED`; diffs stored.
10. **Knowledge graph** — nodes/edges, traverse, shortest path, SVG render; events, evidence, claims verification, contradictions check, findings with lineage.
11. **Research & feed** — research planner + runs, findings, personalized feed + subscriptions, opportunities (z-score).
12. **Monitoring** — watchlists (keyword/company/domain) with evaluation, schedules (once/interval/hourly/daily/weekly/cron/event), alerts (in-app/email/HMAC webhook) with ack/resolve/bulk/check/send, workflows (trigger → action, pause/version/retry/cancel), incidents + SLA + maintenance windows.
13. **Analytics & ML** — descriptive, time-series, price, competitor/source compare, anomaly (z-score ≥ 3), Pearson correlation, 1-D k-means; forecast (EWMA/linear), classification, entity-match score; model registry with version+metrics.
14. **AI (multi-vendor)** — `AIProvider` abstraction: Muse Spark 1.3 (default), OpenAI, Anthropic, Google, Ollama, DB-configured; fallback chain, usage/cost tracking, prompt registry, injection defense. Evidence-grounded chat/ask (`evidence_ids` + citations).
15. **Search** — MySQL FULLTEXT (`search/query, scope`) + pagination; semantic-search abstraction (`EmbeddingProvider`/`VectorStore`, default noop, Pinecone/Milvus/Qdrant-ready); facets.
16. **Reports & datasets** — market/competitor/product/price/review/site/executive reports; web/PDF/CSV/JSON/XLSX + Markdown export; methodology/coverage/timestamps/evidence/limitations on every report. Datasets with per-dataset versioning, diff/rollback, CSV import.
17. **Dashboard (real data only)** — jobs, success/fail, workers, provider/target health, price moves, alerts, AI insights, quality, costs; empty states, never fake. Dark/light mode, toasts, executive view.
18. **Multilingual UI (EN/ID/AR)** — `GET /api/v1/i18n?lang=`; Arabic fully translated with RTL layout.
19. **Admin & governance** — orgs, users, roles, RBAC on all mutating routes, scoped/expiring API keys, commercial entitlements (plans/quotas/model allowlist, 402), feature flags (global/org/user), retention runner, PII detect/mask, audit trail, system doctor, backup/restore round-trip, webintel CLI.
20. **Reliability & observability** — Redis queue/leases/heartbeats/pubsub, DLQ, idempotency keys, restart recovery; JSON logs with trace IDs, Prometheus `/metrics`, `/healthz` + `/readyz`, cost tracking with budgets enforced pre-dispatch.
21. **Deployment** — aaPanel (Nginx HTTPS → 127.0.0.1:8000, systemd units for api/worker/browser/collector), no Docker required.

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

Permukaan API: **143 path berversi di bawah `/api/v1`** (lihat `contracts/openapi/openapi.json`): org, peran, keanggotaan, apikey, proyek, target, job, hasil, harga, perubahan, artikel, pencarian (+semantik), analitik, intel (banding/ulasan/berita), entitas, biaya, ml (+prediksi), peringatan (+cek/kirim), laporan (+ekspor), tanya, umpan (+langganan), peluang, riset, daftar pantau, alur kerja, dataset, konektor, dokumen (+ulasan), webhook (+ingest/pengiriman), i18n (`en|id|ar`), audit, dasbor, kesehatan, metrik, browser.

### Fitur-fitur
1. **Mesin koleksi (Go + worker Python)** — koleksi HTTP/API konkuren, retry dengan backoff+jitter, circuit breaker, rate limiting, connection pooling, graceful shutdown. Eskalasi strategi: `DIRECT → API → BROWSER → OWN_PROXY → BRIGHT_DATA`.
2. **Browser headless (Playwright)** — pool konteks (default 2), timeout per-job, blokir media/font, sesi per-job, capture metadata (status, URL akhir, ukuran, ms).
3. **Konektor** — eksekusi RSS / REST berpaginasi / CSV dengan endpoint `test` + `execute`; `test-connection` target dengan rekomendasi strategi.
4. **Intelijen target** — profil per-target (tingkat sukses, latensi/biaya EWMA, pembelajaran strategi terbaik); menghormati robots.txt/ToS.
5. **Normalisasi & ETL** — produk, perusahaan, harga, ulasan, artikel, penawaran, situs, peristiwa, hasil pencarian → tabel bertipe dengan provenance penuh.
6. **Resolusi entitas** — eksak → string ternormalisasi → domain/identifier → fuzzy (≥0,87 auto-link, 0,70–0,87 perlu review) → bantuan AI opsional; alias, merge/split/reject, riwayat, antrean `needs_review`.
7. **Intelijen harga** — riwayat, deteksi perubahan, volatilitas, perbandingan kompetitor, peringatan `price_drop_pct` / `back_in_stock`.
8. **Intelijen kompetitor / pasar / ulasan / berita** — perbandingan berbasis bukti (setiap klaim mengutip `raw_document_id`), tren kategori, topik emerging berbasis TF, sentimen leksikon + tema keluhan/pujian, ringkasan berita ekstraktif.
9. **Deteksi perubahan** — hash + perbandingan level-field → `NEW / CHANGED / REMOVED / UNCHANGED`; diff tersimpan.
10. **Knowledge graph** — node/edge, traversal, jalur terpendek, render SVG; event, bukti, verifikasi klaim, cek kontradiksi, temuan dengan lineage.
11. **Riset & umpan** — perencana + run riset, temuan, umpan personal + langganan, peluang (z-score).
12. **Pemantauan** — daftar pantau (keyword/perusahaan/domain) dengan evaluasi, jadwal (sekali/interval/per jam/harian/mingguan/cron/event), peringatan (in-app/email/webhook HMAC) dengan ack/resolve/bulk/cek/kirim, workflow (pemicu → aksi, jeda/versi/retry/batal), insiden + SLA + jendela pemeliharaan.
13. **Analitik & ML** — deskriptif, time-series, harga, banding kompetitor/sumber, anomali (z-score ≥ 3), korelasi Pearson, k-means 1-D; forecast (EWMA/linear), klasifikasi, skor entity-match; registry model dengan versi+metrik.
14. **AI (multi-vendor)** — abstraksi `AIProvider`: Muse Spark 1.3 (default), OpenAI, Anthropic, Google, Ollama, konfigurasi-DB; fallback chain, pelacakan usage/biaya, registry prompt, pertahanan injeksi. Chat/tanya berbasis bukti (`evidence_ids` + sitasi).
15. **Pencarian** — MySQL FULLTEXT + paginasi; abstraksi pencarian semantik (default noop, siap Pinecone/Milvus/Qdrant); faset.
16. **Laporan & dataset** — laporan pasar/kompetitor/produk/harga/ulasan/situs/eksekutif; ekspor web/PDF/CSV/JSON/XLSX + Markdown; setiap laporan memuat metodologi/cakupan/timestamp/bukti/keterbatasan. Dataset dengan versioning per-dataset, diff/rollback, impor CSV.
17. **Dasbor (hanya data nyata)** — job, sukses/gagal, worker, kesehatan provider/target, pergerakan harga, peringatan, wawasan AI, kualitas, biaya; empty state, tidak pernah palsu. Mode gelap/terang, toast, tampilan eksekutif.
18. **UI multibahasa (EN/ID/AR)** — `GET /api/v1/i18n?lang=`; Arab diterjemahkan penuh dengan tata letak RTL.
19. **Admin & tata kelola** — org, pengguna, peran, RBAC di semua rute mutasi, API key berskop/kedaluwarsa, entitlements komersial (paket/kuota/allowlist model, 402), feature flag (global/org/user), retention runner, deteksi/masking PII, audit trail, system doctor, backup/restore, CLI webintel.
20. **Reliabilitas & observabilitas** — antrean/lease/heartbeat/pubsub Redis, DLQ, idempotency key, pemulihan restart; log JSON dengan trace ID, `/metrics` Prometheus, `/healthz` + `/readyz`, pelacakan biaya dengan budget yang ditegakkan sebelum dispatch.
21. **Deployment** — aaPanel (Nginx HTTPS → 127.0.0.1:8000, unit systemd untuk api/worker/browser/collector), tanpa Docker.

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

سطح API: **143 مسارًا مُصدَرًا تحت `/api/v1`** (انظر `contracts/openapi/openapi.json`): المنظمات، الأدوار، العضويات، مفاتيح API، المشاريع، الأهداف، المهام، النتائج، الأسعار، التغييرات، المقالات، البحث (+دلالي)، التحليلات، الاستخبارات (مقارنة/مراجعات/أخبار)، الكيانات، التكاليف، تعلم الآلة (+تنبؤ)، التنبيهات (+فحص/إرسال)، التقارير (+تصدير)، السؤال، الموجز (+اشتراكات)، الفرص، البحث، قوائم المراقبة، سير العمل، مجموعات البيانات، الموصلات، المستندات (+مراجعات)، الويب هوك (+استقبال/تسليم)، i18n (`en|id|ar`)، التدقيق، لوحة التحكم، الصحة، المقاييس، المتصفح.

### الميزات
1. **محرك الجمع (Go + عمال Python)** — جمع HTTP/API متزامن، إعادة محاولة مع backoff+jitter، قاطع دائرة، تحديد معدل، تجميع اتصالات، إيقاف سلس. تصعيد الاستراتيجية: `DIRECT ← API ← BROWSER ← OWN_PROXY ← BRIGHT_DATA`.
2. **متصفح headless (Playwright)** — تجمع سياقات (افتراضي 2)، مهلة لكل مهمة، حظر الوسائط/الخطوط، جلسة لكل مهمة، التقاط البيانات الوصفية (الحالة، URL النهائي، الحجم، المدة).
3. **الموصلات** — تنفيذ RSS / REST مُرقّم / CSV مع نقطتي `test` + `execute`؛ و`test-connection` للأهداف مع توصية استراتيجية.
4. **استخبارات الأهداف** — ملف لكل هدف (معدل النجاح، زمن/تكلفة EWMA، تعلم أفضل استراتيجية)؛ احترام robots.txt/شروط الاستخدام.
5. **التطبيع و ETL** — المنتجات، الشركات، الأسعار، المراجعات، المقالات، العروض، المواقع، الأحداث، نتائج البحث ← جداول مُنظّمة مع provenance كامل.
6. **حل الكيانات** — مطابق تمام ← نص مُطبّع ← نطاق/معرف ← ضبابي (≥0.87 ربط تلقائي، 0.70–0.87 يحتاج مراجعة) ← مساعدة AI اختيارية؛ أسماء بديلة، دمج/تقسيم/رفض، سجل، قائمة `needs_review`.
7. **استخبارات الأسعار** — السجل، كشف التغيير، التقلب، مقارنة المنافسين، تنبيهات `price_drop_pct` / `back_in_stock`.
8. **استخبارات المنافسين / السوق / المراجعات / الأخبار** — مقارنة موثقة بالأدلة (كل ادعاء يستشهد بـ `raw_document_id`)، اتجاهات الفئات، مواضيع ناشئة (TF)، مشاعر معجمية + موضوعات الشكاوى/المديح، ملخصات إخبارية استخراجية.
9. **كشف تغييرات المواقع** — بصمة + مقارنة على مستوى الحقول ← `NEW / CHANGED / REMOVED / UNCHANGED`؛ الفروقات مخزنة.
10. **الرسم المعرفي** — عقد/حواف، اجتياز، أقصر مسار، عرض SVG؛ أحداث، أدلة، تحقق الادعاءات، فحص التناقضات، نتائج مع النسب.
11. **البحث والموجز** — مخطط + جولات بحث، نتائج، موجز مخصص + اشتراكات، فرص (z-score).
12. **المراقبة** — قوائم مراقبة (كلمة/شركة/نطاق) مع تقييم، جداول (مرة/فاصل/ساعي/يومي/أسبوعي/cron/حدث)، تنبيهات (داخلية/بريد/ويب هوك HMAC) مع إقرار/حل/جماعي/فحص/إرسال، سير عمل (محفز ← إجراء، إيقاف/إصدار/إعادة/إلغاء)، حوادث + SLA + نوافذ صيانة.
13. **التحليلات وتعلم الآلة** — وصفي، سلاسل زمنية، أسعار، مقارنة منافسين/مصادر، شذوذ (z-score ≥ 3)، ارتباط Pearson، k-means أحادي؛ تنبؤ (EWMA/خطي)، تصنيف، درجة مطابقة الكيانات؛ سجل نماذج بالإصدار+المقاييس.
14. **الذكاء الاصطناعي (متعدد المزودين)** — تجريد `AIProvider`: Muse Spark 1.3 (افتراضي)، OpenAI، Anthropic، Google، Ollama، مُكوَّن من DB؛ سلسلة احتياطية، تتبع الاستخدام/التكلفة، سجل prompts، دفاع ضد الحقن. دردشة/سؤال موثق بالأدلة (`evidence_ids` + استشهادات).
15. **البحث** — MySQL FULLTEXT + ترقيم؛ تجريد البحث الدلالي (افتراضي noop، جاهز لـ Pinecone/Milvus/Qdrant)؛ أوجه.
16. **التقارير ومجموعات البيانات** — تقارير السوق/المنافسين/المنتجات/الأسعار/المراجعات/المواقع/التنفيذية؛ تصدير web/PDF/CSV/JSON/XLSX + Markdown؛ كل تقرير يشمل المنهجية/التغطية/الأوقات/الأدلة/القيود. مجموعات بيانات بإصدارات لكل مجموعة، diff/rollback، استيراد CSV.
17. **لوحة التحكم (بيانات حقيقية فقط)** — المهام، نجاح/فشل، العمال، صحة المزودين/الأهداف، تحركات الأسعار، التنبيهات، رؤى AI، الجودة، التكاليف؛ حالات فارغة، لا تزييف أبدًا. وضع داكن/فاتح، تنبيهات toast، عرض تنفيذي.
18. **واجهة متعددة اللغات (EN/ID/AR)** — `GET /api/v1/i18n?lang=`؛ العربية مترجمة بالكامل مع تخطيط RTL.
19. **الإدارة والحوكمة** — منظمات، مستخدمون، أدوار، RBAC في كل المسارات المعدِّلة، مفاتيح API محددة النطاق/منتهية، استحقاقات تجارية (خطط/حصص/قائمة نماذج، 402)، أعلام ميزات (عام/منظمة/مستخدم)، احتفاظ تلقائي، كشف/إخفاء PII، سجل تدقيق، طبيب النظام، نسخ احتياطي/استعادة، CLI.
20. **الموثوقية والمراقبة** — قائمة Redis/leases/نبضات/pubsub، DLQ، مفاتيح عدم التكرار، تعافٍ بعد إعادة التشغيل؛ سجلات JSON بمعرفات تتبع، `/metrics` لبروميثيوس، `/healthz` + `/readyz`، تتبع التكاليف بميزانيات تُفرض قبل الإرسال.
21. **النشر** — aaPanel (Nginx HTTPS ← 127.0.0.1:8000، وحدات systemd لـ api/worker/browser/collector)، بدون Docker.

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
