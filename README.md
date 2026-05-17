# Tugas 6 - Week 11

**Mata Kuliah:** Pemrograman Visual

| Identitas |                |
|-----------|----------------|
| Nama      | Lalu Muhammad Farhan |
| NIM       | F1D02310119    |

---

Aplikasi **Post Manager** berbasis GUI menggunakan Python Tkinter yang terhubung ke REST API untuk melakukan operasi CRUD (Create, Read, Update, Delete) pada data *posts* beserta komentarnya.

## Daftar Isi

- [Fitur](#fitur)
- [Teknologi yang Digunakan](#teknologi-yang-digunakan)
- [Struktur Aplikasi](#struktur-aplikasi)
- [API Reference](#api-reference)
- [Cara Menjalankan](#cara-menjalankan)
- [Cara Penggunaan](#cara-penggunaan)
- [Penanganan Error](#penanganan-error)
- [Screenshot](#screenshot)

## Fitur

- **Menampilkan daftar post** — menampilkan seluruh post dalam bentuk tabel (ID, Title, Author, Status).
- **Menambah post baru** — form dialog untuk membuat post baru dengan field: title, body, author, slug, dan status.
- **Mengedit post** — mengubah data post yang sudah ada melalui form dialog yang terisi otomatis.
- **Menghapus post** — menghapus post beserta komentar terkait dengan konfirmasi terlebih dahulu.
- **Detail post & komentar** — menampilkan informasi lengkap post dan komentar di panel samping.
- **Validasi input form** — memastikan semua field tidak boleh kosong sebelum dikirim.
- **Async request dengan thread** — request API berjalan di background thread agar UI tetap responsif.
- **Loading indicator** — progress bar animasi saat proses request berlangsung.
- **Error handling** — menampilkan pesan error yang informatif untuk berbagai jenis kegagalan (timeout, koneksi, validasi 422).

## Teknologi yang Digunakan

| Teknologi    | Keterangan                          |
|--------------|-------------------------------------|
| Python 3     | Bahasa pemrograman utama            |
| Tkinter      | GUI toolkit bawaan Python           |
| `ttk`        | Themed Tkinter widgets              |
| `requests`   | HTTP client untuk komunikasi REST API |
| `threading`  | Menjalankan request API di thread terpisah |
| `queue`      | Komunikasi aman antar thread        |

## Struktur Aplikasi

```
T6-week11/
├── post_manager.py      # Aplikasi utama (GUI + logic)
├── README.md            # Dokumentasi
└── screenshots/         # Folder screenshot
    └── ...
```

### Struktur Kelas

| Kelas              | File:Baris  | Keterangan                                   |
|--------------------|-------------|----------------------------------------------|
| `APIError`         | `:11`       | Exception kustom untuk error API (termasuk 422) |
| `PostFormDialog`   | `:18`       | Jendela dialog untuk tambah/edit post        |
| `PostManagerApp`   | `:106`      | Aplikasi utama dengan GUI dan logic CRUD      |

### Metode Penting di `PostManagerApp`

| Method           | Keterangan                                    |
|------------------|-----------------------------------------------|
| `_setup_ui()`    | Membangun seluruh antarmuka pengguna          |
| `_run_async()`   | Menjalankan fungsi di background thread       |
| `_process_queue()`| Memproses callback dari queue di thread utama |
| `load_posts()`   | Mengambil dan menampilkan daftar post         |
| `_show_detail()` | Menampilkan detail post dan komentar          |
| `add_post()`     | Membuka form tambah post                      |
| `edit_post()`    | Membuka form edit post                        |
| `delete_post()`  | Menghapus post setelah konfirmasi             |

## API Reference

Aplikasi ini terhubung ke REST API di `https://api.pahrul.my.id/api/posts`.

| Method | Endpoint              | Keterangan              |
|--------|-----------------------|-------------------------|
| GET    | `/api/posts`          | Mendapatkan semua post  |
| GET    | `/api/posts/{id}`     | Detail post + komentar  |
| POST   | `/api/posts`          | Membuat post baru       |
| PUT    | `/api/posts/{id}`     | Mengupdate post         |
| DELETE | `/api/posts/{id}`     | Menghapus post          |

## Screenshot

| Tampilan          | Screenshot |
|-------------------|------------|
| Halaman Utama     | ![]() |
| Tambah Post       | ![]() |
| Edit Post         | ![]() |
| Detail & Komentar | ![]() |
| Validasi Form     | ![]() |
| Konfirmasi Hapus  | ![]() |
