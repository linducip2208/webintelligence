---
title: Menggunakan Dasbor
description: Baca dasbor hero: KPI, tren, risiko, pratinjau graf dan aktivitas — semuanya data nyata.
category: Memulai
order: 15
slug: getting-started/dashboard
language: id
shots: [02-dashboard.png]
---

# Menggunakan Dasbor

> Baca dasbor hero: KPI, tren, risiko, pratinjau graf dan aktivitas — semuanya data nyata.

## Membaca dasbor

Dasbor menjawab satu pertanyaan: **apa yang butuh perhatian saya sekarang?** Setiap angka berasal dari data live — nol berarti belum ada kejadian, bukan berarti rusak.

![Dasbor](shot:02-dashboard.png)

### Yang dilakukan

1. Buka `/` dan tekan **Refresh**.
2. Pindai baris KPI: job (sukses/gagal), peringatan terbuka, titik harga, peluang, kualitas data, panggilan AI.
3. Periksa **Overall Risk** dan **Recent Alerts** dulu — diurutkan berdasarkan severity.
4. Buka pratinjau **Intelligence Graph**, lalu **Explore** untuk tampilan penuh.
5. Baca **Intelligence Activity** — peristiwa umpan terbaru dengan stempel WIB.

### Yang diperiksa

- Footer menampilkan versi aplikasi asli dari `GET /api/version`.
- Pengalih bahasa (English / Indonesia / العربية) memberi label ulang navigasi; Arab membalik layout ke RTL.
- Tombol tema berputar terang → gelap → sistem; terang adalah default.

### Kesalahan umum

Menganggap dasbor kosong sebagai error. Di database fresh itu benar: buat proyek, tambah target, jalankan job — lalu refresh. Lihat [5 Menit ke Hasil Pertama](/docs/id/getting-started/5-minute-investigation).

## Terkait

- [Proyek, Target & Sumber](/docs/id/investigations/sources)
- [Status koleksi](/docs/id/investigations/collection)
- [Kesehatan Sistem](/docs/id/administration/system-health)
