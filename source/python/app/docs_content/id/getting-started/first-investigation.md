---
title: Investigasi Pertama Anda
description: Panduan 20 langkah dari domain hingga laporan, dengan tangkapan layar asli di setiap langkah.
category: Memulai
order: 20
slug: getting-started/first-investigation
language: id
shots: [03-new-investigation.png, 04-target-type.png, 05-target.png, 06-scope.png, 08-review.png, 09-queued.png, 10-running.png, 11-completed.png, 12-findings.png, 14-graph.png, 15-risk.png, 17-evidence.png, 18-case.png, 19-report.png, 20-watchlist.png, 21-alert.png, 22-workflow.png]
---

# Investigasi Pertama Anda

> Panduan 20 langkah dari domain hingga laporan, dengan tangkapan layar asli di setiap langkah.

Bisa diikuti pembaca non-teknis. Setiap langkah menunjukkan layar asli, apa yang dilakukan, apa respons platform, apa yang diverifikasi, dan kesalahan yang umum terjadi.

> Keamanan: gunakan `example.com` atau sistem milik Anda yang berizin untuk langkah-langkah ini. Jangan pernah memindai target yang tidak berizin.

### Langkah 1 — Buka Web Intelligence

![Dasbor](shot:02-dashboard.png)

**Yang dilakukan:** Buka aplikasi di browser dan masuk bila server memintanya.

**Yang terjadi:** Dasbor hero tampil. Di database fresh isinya mostly nol — itu benar dan jujur.

**Yang diperiksa:** Footer menampilkan versi aplikasi dan stempel waktu WIB.

**Kesalahan umum:** Menempel kredensial atau token ke kotak pencarian global.

### Langkah 2 — Buka Investigasi Baru

![Wizard Investigasi Baru](shot:03-new-investigation.png)

**Yang dilakukan:** Klik **+ New Investigation** di header halaman.

**Yang terjadi:** Wizard 5 langkah terbuka: What, Target, Scope, Sources, Review. Proyek ruang kerja di-resolve lewat API — tidak pernah silent project_id=1.

**Yang diperiksa:** Proyek akan di-resolve (wizard memakai ulang workspace Investigations atau membuatnya via API).

**Kesalahan umum:** Mulai tanpa memeriksa proyek sehingga hasil masuk ke workspace yang salah.

### Langkah 3 — Pilih Website / Domain

![Tipe target](shot:04-target-type.png)

**Yang dilakukan:** Pilih tipe target **Website / Domain**.

**Yang terjadi:** Wizard beradaptasi: target domain membuka opsi cakupan DNS, subdomain dan sertifikat. Delapan tipe tersedia: domain, URL, IP, organisasi, email, identitas, kata kunci dan custom.

**Yang diperiksa:** Opsi domain tersorot.

**Kesalahan umum:** Memilih keyword untuk domain sehingga kolektor DNS dan TLS hilang.

### Langkah 4 — Masukkan target

![Masukkan target](shot:05-target.png)

**Yang dilakukan:** Ketik `example.com` — domain demonstrasi yang aman dan dicadangkan IANA.

**Yang terjadi:** Validasi nyata berjalan per tipe: domain harus berbentuk domain, URL butuh skema, IP harus ter-parse, email harus ter-parse.

**Yang diperiksa:** Target diterima (error validasi muncul inline bila salah).

**Kesalahan umum:** Memasukkan hostname intranet, IP privat atau data pelanggan di demo bersama.

### Langkah 5 — Pilih cakupan (profil mengikuti otomatis)

![Cakupan](shot:06-scope.png)

**Yang dilakukan:** Centang DNS, Subdomain, TLS / Sertifikat, Teknologi Web, Konten Web, Infrastruktur, Entitas Terkait, Dokumen, Threat Intelligence dan Analisis Risiko. Tidak ada pemilih kedalaman terpisah: cakupan infrastruktur berarti run deep, subdomain/TLS/teknologi/konten berarti standard, yang lebih kecil berarti quick.

**Yang terjadi:** Setiap cakupan memetakan ke kolektor dan penganalisis nyata; yang tidak dipilih tidak berjalan. Hanya kolektor nyata yang terkonfigurasi yang dicantumkan.

**Yang diperiksa:** Minimal DNS dan TLS terpilih untuk domain, dan baca profil scan yang diturunkan otomatis.

**Kesalahan umum:** Memilih semuanya di run pertama sehingga hasil sulit dibaca.

### Langkah 6 — Periksa sumber

![Sumber](shot:07-sources.png)

**Yang dilakukan:** Baca layar sumber: kolektor terkonfigurasi dan status sistem live, lalu Continue.

**Yang terjadi:** Yang belum dikonfigurasi harus disiapkan di Connectors — tidak ada yang dipalsukan di sini.

**Yang diperiksa:** Kolektor yang dibutuhkan berstatus siap.

**Kesalahan umum:** Menganggap kolektor yang belum dikonfigurasi tetap akan berjalan.

### Langkah 7 — Review

![Review](shot:08-review.png)

**Yang dilakukan:** Baca layar review: tipe, target, cakupan dan profil. Tertulis persis apa yang akan dilakukan Start: membuat investigasi, mendaftarkan target, mengantrekan job koleksi, menjalankan recon, menautkan target ke investigasi.

**Yang terjadi:** Ini kesempatan murah terakhir memperbaiki typo sebelum koleksi mulai.

**Yang diperiksa:** Target dan cakupan sesuai niat.

**Kesalahan umum:** Melewatkan review sehingga mengoleksi target yang salah.

### Langkah 8 — Mulai investigasi

![Antre](shot:09-queued.png)

**Yang dilakukan:** Tekan **Start Investigation** dan perhatikan drawer Operations.

**Yang terjadi:** Wizard bekerja melalui lima tahap terlihat — membuat investigasi, mendaftarkan target, mengantrekan job koleksi, menjalankan recon, menautkan hasil — lalu melaporkan hasil dan membuka investigasi. Badge halaman scan berbunyi queued selagi job menunggu.

**Yang diperiksa:** Tiap tahap bercentang di Operations; bila gagal, error tampil inline, bukan toast sukses.

**Kesalahan umum:** Menutup tab di tengah run memang aman (koleksi lanjut di server), tetapi pesan kegagalan akan terlewat.

### Langkah 9 — Saksikan berjalan

![Berjalan](shot:10-running.png)

**Yang dilakukan:** Tetap di halaman detail atau kembali nanti; tekan Refresh.

**Yang terjadi:** Job berpindah ke **running** dan attempts bertambah saat kolektor melapor. Halaman Scan menampilkan badge status live dengan aksi Run, Retry dan Cancel.

**Yang diperiksa:** Badge status berbunyi running dan daftar attempts bertambah.

**Kesalahan umum:** Menghantam Run berulang — job duplikat tidak mempercepat koleksi.

### Langkah 10 — Tunggu success

![Selesai](shot:11-completed.png)

**Yang dilakukan:** Biarkan setiap job mencapai status akhir.

**Yang terjadi:** **Success** berarti hasil masuk (toast penyelesaian menyebutnya completed). Job gagal menampilkan error, attempts dan tombol retry — kegagalan dilaporkan, tidak disembunyikan.

**Yang diperiksa:** Setiap job success atau failed beralasan.

**Kesalahan umum:** Menganggap success sebagai kebenaran terverifikasi — temuan tetap butuh triase.

### Langkah 11 — Buka Temuan

![Temuan](shot:12-findings.png)

**Yang dilakukan:** Buka tab **Findings**.

**Yang terjadi:** Korelasi menghasilkan temuan kandidat dengan severity, confidence dan tautan bukti.

**Yang diperiksa:** Setiap temuan menaut ke minimal satu catatan bukti.

**Kesalahan umum:** Me-resolve semuanya tanpa membaca bukti dulu.

### Langkah 12 — Buka graf entitas

![Graf](shot:14-graph.png)

**Yang dilakukan:** Buka **Intelligence Graph**.

**Yang terjadi:** Domain, IP, perusahaan dan teknologi tampil sebagai node tertaut. Traverse, pivot, dan cari jalur terpendek antara dua node mana pun.

**Yang diperiksa:** Domain target terhubung ke minimal satu node IP atau teknologi.

**Kesalahan umum:** Memuat seluruh graf tanpa filter pada investigasi besar — lambat; filter dulu.

### Langkah 13 — Baca analisis risiko

![Risiko](shot:15-risk.png)

**Yang dilakukan:** Buka **Risk Analysis** untuk target.

**Yang terjadi:** Skor 0–100 yang bisa dijelaskan dengan faktor dan bukti di balik tiap faktor. Risiko adalah sinyal prioritas, bukan bukti aktivitas jahat.

**Yang diperiksa:** Setiap faktor mengutip bukti.

**Kesalahan umum:** Mengutip skor risiko ke pihak ketiga sebagai vonis.

### Langkah 14 — Amankan bukti

![Bukti](shot:17-evidence.png)

**Yang dilakukan:** Buka **Evidence** dan verifikasi tangkapan.

**Yang terjadi:** Setiap catatan membawa sumber, stempel waktu, hash dan snippet — provenance yang akan dikutip laporan.

**Yang diperiksa:** Hash hadir sebelum mengutip apa pun ke eksternal.

**Kesalahan umum:** Tangkapan layar UI adalah ilustrasi, bukan bukti. Kutip catatan bukti.

### Langkah 15 — Buat kasus

![Kasus](shot:18-case.png)

**Yang dilakukan:** Buat **Case** dari investigasi.

**Yang terjadi:** Catatan, tugas, anggota dan tautan ke entitas, temuan dan bukti tinggal di sini. Di sinilah analisis menjadi pekerjaan yang ditugaskan.

**Yang diperiksa:** Kasus menaut balik ke investigasi.

**Kesalahan umum:** Kerja kasus di thread chat yang tak bisa diaudit kemudian.

### Langkah 16 — Buat laporan

![Laporan](shot:19-report.png)

**Yang dilakukan:** Buat **Report** dari kasus.

**Yang terjadi:** Web, PDF, CSV, JSON, XLSX atau Markdown — semuanya dari data berbasis bukti yang sama.

**Yang diperiksa:** Laporan mencantumkan referensi buktinya.

**Kesalahan umum:** Mengedit laporan menjadi bunyi yang tidak didukung bukti.

### Langkah 17 — Tambahkan target ke watchlist

![Watchlist](shot:20-watchlist.png)

**Yang dilakukan:** Tambahkan domain ke **Watchlist**.

**Yang terjadi:** Penyebutan, perubahan dan kecocokan di masa depan muncul otomatis.

**Yang diperiksa:** Entri lolos evaluasi dengan Evaluate.

**Kesalahan umum:** Watchlist kata kunci terlalu luas menciptakan noise peringatan.

### Langkah 18 — Konfigurasi peringatan

![Peringatan](shot:21-alert.png)

**Yang dilakukan:** Buat aturan **Alert** di watchlist.

**Yang terjadi:** Severity, kanal dan siklus acknowledge/resolve included. Peringatan mengantrekan perhatian manusia.

**Yang diperiksa:** Peringatan uji tiba melalui kanal yang dikonfigurasi.

**Kesalahan umum:** Me-route semua severity ke paging — cadangkan paging untuk critical.

### Langkah 19 — Konfigurasi workflow

![Workflow](shot:22-workflow.png)

**Yang dilakukan:** Buat **Workflow**: trigger → aksi.

**Yang terjadi:** Contoh: saat temuan high, buka kasus dan notifikasi webhook. Run, retry idempoten dan cancel semuanya terlihat.

**Yang diperiksa:** Run manual selesai dan muncul di riwayat run.

**Kesalahan umum:** Mengotomatiskan aksi ireversibel tanpa langkah persetujuan manual.

### Langkah 20 — Lihat seluruh siklus

![Selesai](shot:11-completed.png)

**Yang dilakukan:** Baca ulang [Siklus Hidup Investigasi](/docs/id/investigations/investigation-lifecycle) dengan kasus selesai Anda.

**Yang terjadi:** Anda telah menyentuh keempat belas tahap: dari pencarian hingga pemantauan.

**Yang diperiksa:** Anda bisa menjelaskan tiap tahap ke kolega memakai kasus sendiri sebagai contoh.

**Kesalahan umum:** Berhenti di temuan dan tidak pernah membangun kasus atau laporan.
