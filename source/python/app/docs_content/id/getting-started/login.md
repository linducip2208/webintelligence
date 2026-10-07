---
title: Masuk & Autentikasi
description: Masuk dengan token Bearer atau kunci API, atau berjalan terbuka di pengembangan lokal.
category: Memulai
order: 10
slug: getting-started/login
language: id
shots: [01-login.png]
---

# Masuk & Autentikasi

> Masuk dengan token Bearer atau kunci API, atau berjalan terbuka di pengembangan lokal.

## Cara kerja masuk

Dua mode:

- **Pengembangan (default):** terbuka. Tanpa `REQUIRE_AUTH`, UI dan API bekerja tanpa kredensial.
- **Produksi:** setel `REQUIRE_AUTH=1`. Setiap route `/api/v1/*` membutuhkan **token Bearer** (dari login) atau **X-API-Key** (berskop, kedaluwarsa, bisa dicabut).

## Masuk dari UI

1. Buka aplikasi dan klik **Login** di footer sidebar.
2. Masukkan email dan password. Token sesi hanya disimpan di memori — tidak pernah di localStorage.
3. Chip pengguna berubah dari `anonymous` menjadi `● signed in`.

![Masuk](shot:01-login.png)

### Yang diperiksa

- Setelah masuk, view yang diproteksi tidak lagi 401.
- **Kesalahan umum:** memakai kunci API (`wi_…`) di kolom password. Kunci API masuk ke kotak token atau header `X-API-Key`.

## Masuk dari API

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@local","password":"PASSWORD_ANDA"}'
```

```python
import httpx
r = httpx.post("http://127.0.0.1:8000/api/v1/auth/login",
               json={"email": "admin@local", "password": "PASSWORD_ANDA"})
headers = {"Authorization": f"Bearer {r.json()['token']}"}
```

## Yang terjadi

- Kredensial benar mengembalikan token dan mencatat audit.
- Kredensial salah mengembalikan `401 bad credentials` plus audit kegagalan.
- Token Bearer stateless HMAC: **logout** membuang token klien dan mencatat peristiwa.

## Terkait

- [Autentikasi API](/docs/id/api/authentication)
- [Kunci API](/docs/id/administration/api-keys)
- [RBAC & Isolasi Organisasi](/docs/id/security/rbac)
