#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import pandas as pd
from voyager import Voyager

# import sys


device_list = ("voyager1", "voyager2")

_headers = {
    "Content-type": "application/json"
    # "Accept": "application/json",
    # 'Cache-Control': 'no-cache'
}
device_list = ("voyager1", "voyager2")
device_auth_dict = {
    "voyager1": ("cumulus", "CumulusLinux!"),
    "voyager2": ("cumulus", "CumulusLinux!"),
}
device_ip_dict = {"voyager1": "137.222.204.212", "voyager2": "137.222.204.213"}
device_type_dict = {"voyager1": "voyager", "voyager2": "voyager"}
device_url_dict = {
    "voyager1": "https://137.222.204.212:8080/nclu/v1/rpc",
    "voyager2": "https://137.222.204.213:8080/nclu/v1/rpc",
}


# def set_launch_power(device, interface, power):
#     # send command
#     if device in device_list and device_type_dict[device] == 'voyager':
#         data = {'cmd': 'add interface {} power {}'.format(interface, power)}
#         print(data['cmd'])
#         r = send_post_request(device_url_dict[device], device_auth_dict[device], data,
#  _headers, False)
#         # print(r)
#         return r
#     else:
#         print('Error: device {} is not registred in the device_list.'.format(device))
#         sys.exit()


# def get_launch_power(device, interface):
#     if device in device_list and device_type_dict[device] == 'voyager':
#         data = {'cmd': 'show transponder'}
#         print(data['cmd'])
#         r = send_post_request(device_url_dict[device], device_auth_dict[device], data,
#  _headers, False)
#         # print(r)
#         return r
#     else:
#         print('Error: device {} is not registred in the device_list.'.format(device))
#         sys.exit()


# def get_pending(device):
#     if device in device_list and device_type_dict[device] == 'voyager':
#         data = {'cmd': 'pending'}
#         print(data['cmd'])
#         r = send_post_request(device_url_dict[device], device_auth_dict[device], data,
#  _headers, False)
#         # print(r)
#         return r
#     else:
#         print('Error: device {} is not registred in the device_list.'.format(device))
#         sys.exit()


# def send_test(modeladmin, request, queryset):
# def send_test(url,username, password, r_data):
#     # for i in queryset:
#     try:
#         print("{} {} {} {}".format(
#             url,
#             username,
#             password,
#             r_data
#             )
#         )
#         # Create the session and set the proxies.
#         response = req.post(
#             url,
#             auth=(username, password),
#             data=json.dumps(r_data),
#             headers=_headers,
#             verify=False)
#         # messages.success(request, "Successfully updated: {}".format(response.text))
#         r = response.text
#         print(r.split())
#     except req.ConnectionError as error:
#         print("Error")
#         # messages.error(
#         #     request,
#         #     'Error message: {}'.format(error))
#         print('Error message: {}'.format(error))
#     print(json.dumps(r_data))


def power_test():
    voyager1 = Voyager("voyager1", "137.222.204.212")
    voyager1.abort()
    voyager1.change_launch_power("L5", -2.0)
    voyager1.change_launch_power("L1", 10.0)
    voyager1.change_launch_power("L1", -4.0)
    voyager1.pending()
    voyager1.commit()
    voyager1.pending()


def modulation_test():
    voyager1 = Voyager("voyager1", "137.222.204.212")
    voyager1.pending()
    # voyager1.change_modulation_format('L10', '16-qam')
    # voyager1.change_modulation_format('L1', '64-qam')
    voyager1.change_modulation_format("L1", "16-qam")
    # voyager1.change_modulation_format('L1', 'pm-qpsk')
    # voyager1.change_modulation_format('L2', 'pm-qpsk')
    voyager1.commit()
    # voyager1.change_modulation_format('L1', '8-qam')


def get_json_test():
    voyager1 = Voyager("voyager1", "137.222.204.212")
    r, timestamp = voyager1.show_transponder()
    js = json.loads(r)

    with open(str(timestamp) + ".json", "w") as f:
        json.dump(js, f)


interface_dict = {"10": "L3", "11": "L4", "20": "L1", "21": "L2"}


def offline_json_test():
    df = pd.DataFrame(
        columns=[
            "timestamp",
            "interface",
            "current_input_power",
            "current_ber",
            "uncorrectable_fec",
        ]
    )
    file_list = [1553798078.8828683, 1553804573.7838838, 1553804574.7838838]
    for timestamp in file_list:
        with open(str(timestamp) + ".json", "r") as f:
            js = json.load(f)

            # js['modules'][i]['network_interfaces'][j]
            # i = 0 j = 0 == L3
            # i = 0 j = 1 == L4
            # i = 1 j = 0 == L1
            # i = 1 j = 1 == L2

            # data_js = []
            for module in js["modules"]:
                for net_interface in module["network_interfaces"]:
                    interface = interface_dict[
                        "{}{}".format(module["location"], net_interface["index"])
                    ]
                    entry = {
                        "timestamp": timestamp,
                        "interface": interface,
                        "current_input_power": net_interface["current_input_power"],
                        "current_ber": net_interface["current_ber"],
                        "uncorrectable_fec": net_interface["uncorrectable_fec"],
                    }
                    df = pd.DataFrame.append(df, entry, ignore_index=True)

            # df = pd.DataFrame.append(df, data_js, ignore_index=True)
            # print(df)
            # df2 = pd.DataFrame(data_js)
            # print(df2)
            # df = pd.concat([df,df2])
            # print(df)
            # print(df.head())
            # print(data_js)
            # sys.exit()
            # df_headers = 'timestamp interface current_input_power current_ber
            # uncorrectable_fec'.split()
            # df = pd.DataFrame('''index=['timestamp'], '''columns=df_headers)

            # left = pd.DataFrame({'key': ['K0', 'K1', 'K2', 'K3'],
            #              'A': ['A0', 'A1', 'A2', 'A3'],
            #              'B': ['B0', 'B1', 'B2', 'B3']})
            # print(df.head())
    print(df)
    # module + index
    # grid_spacing
    # output_power
    # current_output_power
    # laser_frequency
    # modulation
    # fec_mode
    # current_input_power
    # current_ber
    # uncorrectable_fec


def monitor_voyagers(monitoring_interval=1.0, experiment_rounds=20):
    voyager1 = Voyager("voyager1", "137.222.204.212")
    voyager2 = Voyager("voyager2", "137.222.204.213")

    # for
    r, timestamp = voyager1.show_transponder()
    js = json.loads(r)
    with open(voyager1.name + "_" + str(timestamp) + ".json", "w") as f:
        json.dump(js, f)

    r, timestamp = voyager2.show_transponder()
    js = json.loads(r)
    with open(voyager2.name + "_" + str(timestamp) + ".json", "w") as f:
        json.dump(js, f)


if __name__ == "__main__":
    # power_test()
    # modulation_test()
    get_json_test()
    # offline_json_test()
    # monitor_voyagers()
    # voyager1 = Voyager('voyager1', '137.222.204.212')
    # voyager1.change_modulation_format('L1', 'pm-qpsk')
    # voyager1.change_modulation_format('L1', '16-qam')
