import json
import requests

def is_up(server_ip, server_port):
    r = requests.get("http://{}:{}/".format(server_ip, server_port))
    return r.ok


def idn(oxc_ip, server_ip, server_port):
    data = {
        "oxc_ip": oxc_ip
    }
    r = requests.post("http://{}:{}/idn".format(server_ip, server_port),
        data=json.dumps(data))
    if r.ok:
        return json.loads(r.text)['response']
    else:
        return False

def connections(oxc_ip, server_ip, server_port):
    data = {
        "oxc_ip": oxc_ip
    }
    r = requests.post("http://{}:{}/connections".format(server_ip, server_port),
        data=json.dumps(data))
    if r.ok:
        return json.loads(r.text)['response']
    else:
        return False

def connect(oxc_ip, connection_dict, server_ip, server_port):
    data = {
        "oxc_ip": oxc_ip,
        "connection_dict": connection_dict
    }
    r = requests.post("http://{}:{}/connect".format(server_ip, server_port),
        data=json.dumps(data))
    if r.ok:
        return json.loads(r.text)['response']
    else:
        return False

def disconnect(oxc_ip, connection_dict, server_ip, server_port):
    data = {
        "oxc_ip": oxc_ip,
        "connection_dict": connection_dict
    }
    r = requests.post("http://{}:{}/disconnect".format(server_ip, server_port),
        data=json.dumps(data))
    if r.ok:
        return json.loads(r.text)['response']
    else:
        return False

def disconnectall(oxc_ip, server_ip, server_port):
    data = {
        "oxc_ip": oxc_ip
    }
    r = requests.post("http://{}:{}/disconnectall".format(server_ip, server_port),
        data=json.dumps(data))
    if r.ok:
        return json.loads(r.text)['response']
    else:
        return False

def get_power(oxc_ip, port_list, server_ip, server_port):
    data = {
        "oxc_ip": oxc_ip,
        "port_list": port_list
    }
    r = requests.post("http://{}:{}/power".format(server_ip, server_port),
        data=json.dumps(data))
    if r.ok:
        return json.loads(r.text)['response']
    else:
        return False