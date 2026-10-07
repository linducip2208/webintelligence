---
title: 5 Menit ke Hasil Pertama
description: Pahami seluruh produk dalam lima menit: masuk hingga laporan dalam sepuluh langkah.
category: Memulai
order: 25
slug: getting-started/5-minute-investigation
language: id
shots: [03-new-investigation.png, 11-completed.png, 14-graph.png, 15-risk.png, 19-report.png]
---

# 5 Menit ke Hasil Pertama

> Pahami seluruh produk dalam lima menit: masuk hingga laporan dalam sepuluh langkah.

> Keamanan: gunakan `example.com` atau sistem milik Anda yang berizin.

### Langkah 1 — Login

**Yang dilakukan:** Buka aplikasi dan masuk bila diminta.

**Yang terjadi:** Dasbor hero tampil dengan data live.

**Yang diperiksa:** Chip pengguna menunjukkan Anda masuk.

**Kesalahan umum:** Menempel kunci API di kolom password.

### Langkah 2 — Dasbor

**Yang dilakukan:** Pindai KPI, risiko keseluruhan dan peringatan terbaru.

**Yang terjadi:** Anda tahu apa yang butuh perhatian sebelum mulai.

**Yang diperiksa:** Footer versi tampil.

**Kesalahan umum:** Panik melihat nol di database fresh — itu benar.

### Langkah 3 — Investigasi Baru

![Investigasi Baru](shot:03-new-investigation.png)

**Yang dilakukan:** Klik **+ New Investigation**.

**Yang terjadi:** Wizard 5 langkah terbuka dengan proyek ter-resolve lewat API.

**Yang diperiksa:** Proyek benar.

**Kesalahan umum:** Proyek salah, hasil nyasar.

### Langkah 4 — Domain

**Yang dilakukan:** Pilih tipe domain dan ketik `example.com`.

**Yang terjadi:** Validasi mengonfirmasi target.

**Yang diperiksa:** Target tervalidasi tampil kembali.

**Kesalahan umum:** Memindai sistem tanpa izin.

### Langkah 5 — Cakupan

**Yang dilakukan:** Centang cakupan (minimal DNS + TLS); profil scan diturunkan otomatis.

**Yang terjadi:** Kolektor yang tepat dijadwalkan.

**Yang diperiksa:** Profil turunan terbaca.

**Kesalahan umum:** Deep untuk segalanya.

### Langkah 6 — Mulai

**Yang dilakukan:** Review lalu tekan **Start**.

**Yang terjadi:** Job masuk **queued**, lalu **running**.

**Yang diperiksa:** Badge berbunyi queued — bukan completed.

**Kesalahan umum:** Menutup tab karena khawatir; koleksi lanjut di server.

### Langkah 7 — Hasil

![Selesai](shot:11-completed.png)

**Yang dilakukan:** Tunggu **success**, buka temuan.

**Yang terjadi:** Korelasi menghasilkan temuan ber-severity dan ber-bukti.

**Yang diperiksa:** Temuan menaut ke bukti.

**Kesalahan umum:** Me-resolve tanpa membaca bukti.

### Langkah 8 — Graf

![Graf](shot:14-graph.png)

**Yang dilakukan:** Buka graf, traverse dari domain ke IP.

**Yang terjadi:** Relasi yang tak terlihat di tabel menjadi jelas.

**Yang diperiksa:** Domain terhubung ke node lain.

**Kesalahan umum:** Memuat semua tanpa filter.

### Langkah 9 — Risiko

![Risiko](shot:15-risk.png)

**Yang dilakukan:** Baca skor 0–100 beserta faktornya.

**Yang terjadi:** Sinyal prioritas yang bisa dijelaskan.

**Yang diperiksa:** Tiap faktor mengutip bukti.

**Kesalahan umum:** Mengutip skor sebagai vonis.

### Langkah 10 — Laporan

![Laporan](shot:19-report.png)

**Yang dilakukan:** Buat kasus, buat laporan, tambahkan domain ke watchlist.

**Yang terjadi:** Analisis menjadi pekerjaan, laporan, dan pengawasan berkelanjutan.

**Yang diperiksa:** Laporan mencantumkan bukti; watchlist lolos Evaluate.

**Kesalahan umum:** Berhenti di temuan.

### Hasil yang diharapkan

Investigasi selesai dengan temuan, graf kecil, skor risiko dan laporan — plus entri watchlist yang mengawasi domain setelah Anda pergi.
