# BPJS Encrypted Request Generator (Web.py)

Skrip ini digunakan untuk menghasilkan signature request untuk API BPJS Kesehatan (VClaim) menggunakan metode HMAC dan enkripsi AES.

## 🔧 Teknologi
- Python 3.x
- Web.py
- hashlib, hmac, base64, datetime, dan lain-lain

## ✨ Fitur
- Generate X-Signature untuk API VClaim
- Output dalam format header untuk kebutuhan request HTTP
- Sederhana dan bisa dijalankan di local/CLI

## 📦 Cara Menjalankan
```bash
python3 index.py

## 📚 Credit

Sebagian besar kode enkripsi berasal dari [repo ini](https://github.com/morizbebenk/flask-bpjs), dengan beberapa modifikasi untuk kebutuhan Web.py.
