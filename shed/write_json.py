import json


config = {
    "name": "pi3",
    "server": "http://192.168.0.14",
    "port": 80,
    "key": "blahblahblah",
    "local": False,
    "api": "/api"
}

with open("config.json", "w") as write_out:
    json.dump(config, write_out)