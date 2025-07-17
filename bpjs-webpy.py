import web
import json
import base64
import hashlib
import hmac
import requests
from Crypto.Cipher import AES
from datetime import datetime
import lzstring
from dotenv import dotenv_values, load_dotenv

load_dotenv()

def check_data_exist(array):
    return all(data is not None and data != '' for data in array)

def decrypt_data(keys, encrypts):
    if encrypts is None:
        return None

    x = lzstring.LZString()
    key_hash = hashlib.sha256(keys.encode('utf-8')).digest()
    decryptor = AES.new(key_hash[:32], AES.MODE_CBC, IV=key_hash[:16])
    plain = decryptor.decrypt(base64.b64decode(encrypts))
    return json.loads(x.decompressFromEncodedURIComponent(plain.decode('utf-8')))

def check_json(str_json):
    try:
        json.loads(str_json)
        return True
    except ValueError:
        return False

def fixed_url(url):
    return url.strip('/')

def rest_bpjs(consid, secret, user_key, url, method, payload, timestamp):
    message = consid + "&" + timestamp
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    encoded_signature = base64.b64encode(signature).decode()

    headers = {
        'X-cons-id': consid,
        'X-timestamp': timestamp,
        'X-signature': encoded_signature,
        'user_key': user_key,
        'Content-Type': 'Application/x-www-form-urlencoded',
        'Accept': '*/*'
    }

    if not payload:
        payload = 0
    try:
        payload = web.data()
        data = json.loads(payload)
    except json.JSONDecodeError:
        web.ctx.status = '400 Bad Request'
        return json.dumps({"metadata":{"code":400, "message":"Invalid JSON format"}})

    try:
        method = method.lower()
        if method == 'post':
            res = requests.post(url, data=payload if payload else None, headers=headers)
        elif method == 'put':
            res = requests.put(url, data=payload if payload else None, headers=headers)
        elif method == 'delete':
            res = requests.delete(url, data=payload if payload else None, headers=headers)
        else:
            res = requests.get(url, params=payload if payload else None, headers=headers)

        return res
    except Exception as e:
        return {
            'metaData': {
                'code': 400,
                'message': "Ada kesalahan request data, cek kembali",
                'error': str(e)
            },
            'response': None
        }

class Bridging:
    def GET(self):
        data = {
            'metaData': {
                'code': 200,
                'message': f"Selamat datang di {web.ctx.home} Webservice yang digunakan untuk menangani proses dekripsi data response dari bridging BPJS VCLAIM-REST 2.0 (Encrypted Version). Support VCLAIM v1 dan API JKN (Antrean RS).",
                'note': f"Catatan perubahan tersedia di {web.ctx.home}/change_log"
            },
            'response': None
        }
        web.ctx.status = '405 Method Not Allowed'
        return web.header('Content-Type', 'application/json') or json.dumps(data)

    def POST(self):
        headers = web.ctx.env
        try:
            content_length = int(headers.get('CONTENT_LENGTH', 0))
        except:
            content_length = 0

        body = web.data()
        try:
            body = body.decode('utf-8')
        except AttributeError:
            pass

        content_type = headers.get("CONTENT_TYPE", "")
        if "application/json" not in content_type:
            data = {
                'metaData': {
                    'code': 400,
                    'message': "Pastikan format body json dan menggunakan header Content-Type: application/json",
                },
                'response': None
            }
            web.ctx.status = '400 Bad Request'
            return web.header('Content-Type', 'application/json') or json.dumps(data)

        try:
            data_json = json.loads(body)
        except:
            data = {
                'metaData': {
                    'code': 400,
                    'message': "Body JSON tidak valid.",
                },
                'response': None
            }
            web.ctx.status = '400 Bad Request'
            return web.header('Content-Type', 'application/json') or json.dumps(data)

        if not all(k in data_json for k in ['url', 'method', 'payload']):
            data = {
                'metaData': {
                    'code': 400,
                    'message': "Pastikan mengirim url, method dan payload. Jika tidak ada data, gunakan payload : '' (string kosong)",
                },
                'response': None
            }
            web.ctx.status = '400 Bad Request'
            return web.header('Content-Type', 'application/json') or json.dumps(data)

        config = dotenv_values(".env")
        header = lambda k: web.ctx.env.get('HTTP_' + k.upper().replace('-', '_'))

        host = header('x-host') or config.get('HOST_BPJS')
        consid = header('x-consid') or config.get('CONSID')
        secret = header('x-secret') or config.get('SECRET')
        user_key = header('x-user_key') or config.get('USER_KEY')
        is_encrypt = int(header('x-is_encrypt') or config.get('IS_ENCRYPT', 0))

        full_url = fixed_url(host) + "/" + fixed_url(data_json['url'])
        timestamp = str(int(datetime.today().timestamp()))
        res = rest_bpjs(consid, secret, user_key, full_url, data_json['method'], data_json['payload'], timestamp)

        if isinstance(res, dict) and 'metaData' in res:
            web.ctx.status = '400 Bad Request'
            return web.header('Content-Type', 'application/json') or json.dumps(res)

        if not check_json(res.text):
            data = {
                'metaData': {
                    'code': res.status_code,
                    'message': res.text,
                },
                'response': None
            }
            web.ctx.status = str(res.status_code)
            web.header('Content-Type', 'application/json')
            return json.dumps(data)

        res_json = res.json()
        metadata = 'metaData' if 'metaData' in res_json else 'metadata'
        code = 'code' if 'code' in res_json[metadata] else 'Code'

        if res_json[metadata][code] == 0:
            data = {
                'metaData': {
                    'code': 400,
                    'message': res_json[metadata]['message'],
                },
                'response': None
            }
            web.ctx.status = '400 Bad Request'
            web.header('Content-Type', 'application/json') 
            return json.dumps(data)

        response = res_json.get('response', None)
        if is_encrypt == 1 and response:
            keys = consid + secret + timestamp
            if not any(unc in data_json['url'] for unc in ["SEP/2.0/delete", "SEP/2.0/update"]):
                response = decrypt_data(keys, response)

        final_data = {
            'metaData': {
                'code': res_json[metadata][code],
                'message': res_json[metadata]['message'],
            },
            'response': response
        }

        status_code = int(res_json[metadata][code])
        status_messages = {
            200: "OK",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error"
        }
        status_message = status_messages.get(status_code, "Unknown")
        web.ctx.status = f"{status_code} {status_message}"
        web.header('Content-Type', 'application/json')
        
        res = json.dumps(final_data)
        # print('Response dari BPJS: ', res)
        
        return json.dumps(final_data)

    def other(self):
        data = {
            'metaData': {
                'code': 405,
                'message': "Method dilarang, gunakan method POST",
            },
            'response': None
        }
        web.ctx.status = '405 Method Not Allowed'
        web.header('Content-Type', 'application/json') 
        return json.dumps(data)

    def PUT(self): return self.other()
    def DELETE(self): return self.other()
    def PATCH(self): return self.other()
    def OPTIONS(self): return self.other()
    def HEAD(self): return self.other()


class AntreanRS:
    def GET(self):
        data = {
            'metaData': {
                'code': 200,
                'message': f"Selamat datang di {web.ctx.home} Webservice yang digunakan untuk menangani proses dekripsi data response dari bridging BPJS VCLAIM-REST 2.0 (Encrypted Version). Support VCLAIM v1 dan API JKN (Antrean RS).",
                'note': f"Catatan perubahan tersedia di {web.ctx.home}/change_log"
            },
            'response': None
        }
        web.ctx.status = '405 Method Not Allowed'
        web.header('Content-Type', 'application/json')
        return json.dumps(data)

    def POST(self):
        headers = web.ctx.env
        try:
            content_length = int(headers.get('CONTENT_LENGTH', 0))
        except:
            content_length = 0

        body = web.data()
        try:
            body = body.decode('utf-8')
        except AttributeError:
            pass
        
        content_type = headers.get("CONTENT_TYPE", "")
        if "application/json" not in content_type:
            data = {
                'metaData': {
                    'code': 400,
                    'message': "Pastikan format body json dan menggunakan header Content-Type: application/json",
                },
                'response': None
            }
            web.ctx.status = '400 Bad Request'
            web.header('Content-Type', 'application/json')
            return json.dumps(data)

        try:
            data_json = json.loads(body)
            
        except:
            data = {
                'metaData': {
                    'code': 400,
                    'message': "Body JSON tidak valid.",
                },
                'response': None
            }
            web.ctx.status = '400 Bad Request'
            web.header('Content-Type', 'application/json') 
            return json.dumps(data)

        if not all(k in data_json for k in ['url', 'method', 'payload']):
            data = {
                'metaData': {
                    'code': 400,
                    'message': "Pastikan mengirim url, method dan payload. Jika tidak ada data, gunakan payload : '' (string kosong)",
                },
                'response': None
            }
            web.ctx.status = '400 Bad Request'
            web.header('Content-Type', 'application/json') 
            return json.dumps(data)

        config = dotenv_values(".env")
        header = lambda k: web.ctx.env.get('HTTP_' + k.upper().replace('-', '_'))
        
        host = header('x-host') or config.get('HOST_ANTROL_RS')
        consid = header('x-consid') or config.get('CONSID_ANTROL')
        secret = header('x-secret') or config.get('SECRET_ANTROL')
        user_key = header('x-user_key') or config.get('USERKEY_ANTROL')
        is_encrypt = int(header('x-is_encrypt') or config.get('IS_ENCRYPT', 0))

        full_url = fixed_url(host) + "/" + fixed_url(data_json['url'])
        timestamp = str(int(datetime.today().timestamp()))
        res = rest_bpjs(consid, secret, user_key, full_url, data_json['method'], data_json['payload'], timestamp)

        if isinstance(res, dict) and 'metaData' in res:
            web.ctx.status = '400 Bad Request'
            return web.header('Content-Type', 'application/json') or json.dumps(res)

        if not check_json(res.text):
            data = {
                'metaData': {
                    'code': res.status_code,
                    'message': res.text,
                },
                'response': None
            }
            web.ctx.status = str(res.status_code)
            web.header('Content-Type', 'application/json')
            return json.dumps(data)

        res_json = res.json()
        metadata = 'metaData' if 'metaData' in res_json else 'metadata'
        code = 'code' if 'code' in res_json[metadata] else 'Code'

        if res_json[metadata][code] != 200:
            data = {
                'metaData': {
                    'code': 400,
                    'message': res_json[metadata]['message'],
                },
                'response': None
            }
            web.ctx.status = '400 Bad Request'
            web.header('Content-Type', 'application/json') 
            return json.dumps(data)

        response = res_json.get('response', None)
        if is_encrypt == 1 and response:
            keys = consid + secret + timestamp
            if not any(unc in data_json['url'] for unc in ["SEP/2.0/delete", "SEP/2.0/update"]):
                response = decrypt_data(keys, response)

        final_data = {
            'metaData': {
                'code': res_json[metadata][code],
                'message': res_json[metadata]['message'],
            },
            'response': response
        }

        status_code = int(res_json[metadata][code])
        status_messages = {
            200: "OK",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error"
        }
        status_message = status_messages.get(status_code, "Unknown")
        web.ctx.status = f"{status_code} {status_message}"
        web.header('Content-Type', 'application/json')
        return json.dumps(final_data)

    def other(self):
        data = {
            'metaData': {
                'code': 405,
                'message': "Method dilarang, gunakan method POST",
            },
            'response': None
        }
        web.ctx.status = '405 Method Not Allowed'
        web.header('Content-Type', 'application/json') 
        return json.dumps(data)

    def PUT(self): return self.other()
    def DELETE(self): return self.other()
    def PATCH(self): return self.other()
    def HEAD(self): return self.other()
    def OPTIONS(self):
        web.header("Access-Control-Allow-Origin", "*")
        web.header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        web.header("Access-Control-Allow-Headers", "Content-Type, x-host, x-consid, x-secret, x-user_key, x-is_encrypt")
        return ""
    
class ChangeLog:
    def GET(self):
        try:
            with open('change_log.json') as f:
                data = json.load(f)
        except FileNotFoundError:
            web.ctx.status = '404 Not Found'
            return json.dumps({"metadata": {"code": 404, "message": "Change log file not found"}})
        except json.JSONDecodeError:
            web.ctx.status = '500 Internal Server Error'
            return json.dumps({"metadata": {"code": 500, "message": "Failed to parse change log file"}})


    def POST(self): return self.method_not_allowed()
    def PUT(self): return self.method_not_allowed()
    def DELETE(self): return self.method_not_allowed()
    def PATCH(self): return self.method_not_allowed()
    def OPTIONS(self): return self.method_not_allowed()
    def HEAD(self): return self.method_not_allowed()

    def method_not_allowed(self):
        data = {
            'metaData': {
                'code': 405,
                'message': "Method dilarang, gunakan method GET",
            },
            'response': None
        }
        web.ctx.status = '405 Method Not Allowed'
        web.header('Content-Type', 'application/json')
        return json.dumps(data)

