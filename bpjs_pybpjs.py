import web 
import json
from pybpjs import bpjs
from dotenv import load_dotenv
import os

load_dotenv()
credential = {
    "host": os.getenv("HOST_BPJS"),
    "consid": os.getenv("CONSID"),
    "secret": os.getenv("SECRET"),
    "user_key": os.getenv("USER_KEY"),
    "is_encrypt": os.getenv("IS_ENCRYPT", "1")
}
antrol_rs = {
    "host": os.getenv("HOST_ANTROL_RS"),
    "consid": os.getenv("CONSID_ANTROL"),
    "secret": os.getenv("SECRET_ANTROL"),
    "user_key": os.getenv("USERKEY_ANTROL"),
    "is_encrypt": os.getenv("IS_ENCRYPT", "1")
}
class Vclaim:
    def POST(self):
        web.header('Content-Type', 'application/json')
        try:
            raw_data = web.data()
            data = json.loads(raw_data)
            endpoint = data.get("endpoint")
            method = data.get("method", "get").lower()
            payload = data.get("payload", "")
            result = bpjs.bridging(credential, endpoint, method, payload)
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "metaData": {"code": "500", "message": "Internal Server Error"}
            })
            
class Antrol:
    def POST(self):
        web.header('Content-Type', 'application/json')
        try:
            raw_data = web.data()
            data = json.loads(raw_data)
            endpoint = data.get("endpoint")
            method = data.get("method", "get").lower()
            payload = data.get("payload", "")
            result = bpjs.bridging(antrol_rs, endpoint, method, payload)
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "metaData": {"code": "500", "message": "Internal Server Error"}
            })