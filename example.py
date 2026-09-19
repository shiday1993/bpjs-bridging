from src.bpjs import Bridging

config ={
    "consid": "your_consid",
    "secret": "your_secret",
    "user_key": "your_userkey",
    "host" : "base_url"
}

vclaim = Bridging(config, 'vclaim')

res = vclaim.request("referensi/propinsi")

print(res)