from Crypto.Cipher import AES
from datetime import datetime
import lzstring
import requests
import hashlib
import base64
import hmac
import json


class Bridging:
    SERVICE_CONFIG = {
        "vclaim": {
            "encrypted": True,
            "use_user_key": True,
            "content_type": "application/x-www-form-urlencoded",
        },
        "icare": {
            "encrypted": True,
            "use_user_key": True,
            "content_type": "application/json",
        },
        "antrean": {
            "encrypted": True,
            "use_user_key": True,
            "content_type": "application/json",
        },
        "aplicare": {
            "encrypted": False,
            "use_user_key": False,
            "content_type": "application/json",
        },
    }

    UNENCRYPTED_ENDPOINTS = {
        "vclaim": [
            "SEP/2.0/delete",
            "SEP/2.0/update",
        ]
    }

    def __init__(self, client, service):
        service = service.lower()
        if service not in self.SERVICE_CONFIG:
            raise ValueError(f"Service BPJS tidak dikenal: {service}")
        self.service = service
        self.config = self.SERVICE_CONFIG[service]
        self.host = client["host"].rstrip("/")
        self.consid = client["consid"]
        self.secret = client["secret"]
        self.user_key = client.get("user_key")

    # URL
    @staticmethod
    def _fixed_url(value):
        return value.strip("/")

    def _build_url(self, endpoint):
        return f"{self._fixed_url(self.host)}/{self._fixed_url(endpoint)}"

    # AUTH / SIGNATURE
    def _timestamp(self):
        return str(int(datetime.now().timestamp()))

    def _signature(self, timestamp):
        message = f"{self.consid}&{timestamp}"
        signature = hmac.new(
            self.secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()

    def _headers(self, timestamp):
        headers = {
            "X-cons-id": self.consid,
            "X-timestamp": timestamp,
            "X-signature": self._signature(timestamp),
            "Content-Type": self.config["content_type"],
            "Accept": "*/*",
        }
        if self.config.get("use_user_key") and self.user_key:
            headers["user_key"] = self.user_key
        return headers

    # DECRYPT
    def _decrypt(self, encrypted, timestamp):
        if not encrypted:
            return None
        key = f"{self.consid}{self.secret}{timestamp}"
        key_hash = hashlib.sha256(key.encode("utf-8")).digest()
        decryptor = AES.new(
            key_hash[:32],
            AES.MODE_CBC,
            IV=key_hash[:16]
        )
        plain = decryptor.decrypt(base64.b64decode(encrypted))
        compressed = plain.decode("utf-8")
        lz = lzstring.LZString()
        decompressed = lz.decompressFromEncodedURIComponent(compressed)
        return json.loads(decompressed)

    def _should_decrypt(self, endpoint):
        if not self.config.get("encrypted"):
            return False
        exclusions = self.UNENCRYPTED_ENDPOINTS.get(self.service,[])
        endpoint = self._fixed_url(endpoint)
        for item in exclusions:
            if item.lower() in endpoint.lower():
                return False
        return True

    # RESPONSE
    @staticmethod
    def _error(code, message):
        return {
            "metaData": {
                "code": code,
                "message": message,
            },
            "response": None,
        }

    def _parse_response(self, res, endpoint, timestamp):
        if res.status_code == 404:
            return self._error(404, "URL tidak ditemukan")
        try:
            body = res.json()
        except ValueError:
            return self._error(res.status_code,res.text)

        metadata = (
            body.get("metaData")
            or body.get("metadata")
            or {}
        )
        code = metadata.get("code", metadata.get("Code", res.status_code))
        message = metadata.get("message", metadata.get("Message", ""))
        try:
            numeric_code = int(code)
        except (TypeError, ValueError):
            numeric_code = code

        if numeric_code == 0:
            return self._error(400, message)

        response = body.get("response")
        if response is None:
            return {
                "metaData": {
                    "code": code,
                    "message": message,
                },
                "response": None,
            }

        if self._should_decrypt(endpoint):
            try:
                response = self._decrypt(response, timestamp )
            except Exception as e:
                return self._error(500, f"Gagal decrypt response BPJS: {e}" )

        return {
            "metaData": {
                "code": code,
                "message": message,
            },
            "response": response,
        }

    # REQUEST
    def request(self, endpoint, method="GET", payload=None, timeout=30):
        timestamp = self._timestamp()
        url = self._build_url(endpoint)
        headers = self._headers(timestamp)
        method = method.upper()
        try:
            kwargs = {
                "headers": headers,
                "timeout": timeout,
            }
            if payload is not None:
                kwargs["data"] = json.dumps(payload)

            res = requests.request(method,url,**kwargs)
            return self._parse_response(res,endpoint,timestamp)

        except requests.exceptions.ConnectTimeout:
            return self._error(504,"Koneksi ke BPJS timeout")
        except requests.exceptions.ReadTimeout:
            return self._error(504, "BPJS terlalu lama merespons")
        except requests.exceptions.ConnectionError as e:
            return self._error(503, f"Gagal terhubung ke BPJS: {e}" )
        except requests.exceptions.RequestException as e:
            return self._error(502, f"Request BPJS gagal: {e}")