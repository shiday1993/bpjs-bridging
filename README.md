# BPJS Python Client

Unofficial Python client untuk integrasi API BPJS Kesehatan.

Library ini menyediakan interface sederhana untuk melakukan request ke beberapa layanan BPJS Kesehatan seperti **VClaim, iCare, Antrean RS, dan Aplicare**, termasuk pembuatan signature dan dekripsi response pada service yang membutuhkannya.

> Project ini bukan library resmi dari BPJS Kesehatan.

## Fitur
- Generate `X-Signature` menggunakan HMAC SHA-256
- Generate header autentikasi BPJS
- Dekripsi response terenkripsi menggunakan AES
- Dekompresi response menggunakan LZString
- Mendukung beberapa service:
  - VClaim
  - iCare
  - Antrean RS
  - Aplicare
- Interface request yang sama untuk setiap service
- Mendukung GET, POST, PUT, dan DELETE
- Normalisasi response BPJS

## Instalasi
```bash
pip install bpjs-bridging
```

## Penggunaan
```python
from bpjs import Bridging

config = {
    "consid": "your_consid",
    "secret": "your_secret",
    "user_key": "your_userkey",
    "host": "base_url",
}

vclaim = Bridging(config, "vclaim")

response = vclaim.request("referensi/propinsi")

print(response)
```

### POST Request
```python
payload = {
    "param": "0000000000000",
    "kodedokter": 123456,
}

response = icare.request(
    "api/rs/validate",
    method="post",
    payload=payload,
)

print(response)
```

## Service
Service ditentukan ketika membuat instance `Bridging`.

```python
vclaim = Bridging(config, "vclaim")
icare = Bridging(config, "icare")
antrean = Bridging(config, "antrean")
aplicare = Bridging(config, "aplicare")
```

Setiap konfigurasi `config` membawa host service yang akan digunakan.

## Konfigurasi
```python
config = {
    "host": "SERVICE_HOST",
    "consid": "consid",
    "secret": "secret",
    "user_key": "userkey",
}
```

Jangan menyimpan credential BPJS secara langsung di source code pada aplikasi production. Gunakan environment variable atau mekanisme secret management lainnya.

## Credit
Implementasi awal mekanisme signature dan dekripsi response
dikembangkan berdasarkan:

[morizbebenk/pybpjs](https://github.com/morizbebenk/pybpjs)

Project ini kemudian direfaktor dan dikembangkan lebih lanjut
untuk mendukung beberapa service BPJS melalui interface berbasis class.

## Sumber Daya
- https://dvlp.bpjs-kesehatan.go.id:8888/trust-mark/portal.html

## Lisensi
- Aplikasi ini open source dengan lisensi [MIT](LICENSE).

## Disclaimer
Project ini merupakan library pihak ketiga dan tidak berafiliasi, didukung, atau dikelola oleh BPJS Kesehatan.

Pengguna bertanggung jawab atas penggunaan credential dan kepatuhan terhadap ketentuan API BPJS Kesehatan.