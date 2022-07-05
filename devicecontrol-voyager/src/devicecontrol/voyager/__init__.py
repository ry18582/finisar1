# -*- coding: utf-8 -*-

import time

from devicecontrol.voyager.device import Device

ALLOWED_FREQUENCY_RANGE = (191.15,196.10) # in THz
COMMIT_TIMEOUT = 600.0
MAX_POWER = 9.0
INTERFACE_LIST = ["L1", "L2", "L3", "L4"]
# interface_dict = {"00": "L3", "01": "L4", "10": "L1", "11": "L2"}
MODULATION_FORMATS_LIST = ["pm-qpsk", "8-qam", "16-qam"]

VOYAGER_INTERFACE_DICT = {
    "L1": (1,0),
    "L2": (1,1),
    "L3": (0,0),
    "L4": (0,1)
}


class Voyager(Device):
    headers = {"Content-type": "application/json"}

    def __init__(self, name, ip, port="8080"):
        Device.name = name
        Device.type = "voyager"
        self.ip = ip
        self.port = port
        self.frequency_range = ALLOWED_FREQUENCY_RANGE
        self.max_power = MAX_POWER
        self.timeout = COMMIT_TIMEOUT
        self.set_auth("cumulus", "CumulusLinux!")
        self.set_interface_list(INTERFACE_LIST)
        self.set_modulation_list(MODULATION_FORMATS_LIST)
        self.base_url = "https://{}:{}/".format(self.ip, self.port)
        self.url = "https://{}:{}/nclu/v1/rpc".format(self.ip, self.port)

    def set_auth(self, user, pw):
        self.auth = (user, pw)

    def set_interface_list(self, interfaces):
        self.interface_list = interfaces

    def set_modulation_list(self, modulation_formats):
        self.modulation_format_list = modulation_formats

    def add_modulation(self, interface, modulation, verbose=True):
        if verbose:
            print(
                "\t{}: Setting {} interface's modulation as {} ... ".format(
                    self.name, interface, modulation
                ),
                end="", flush=True,
            )
        data = {"cmd": "add interface {} modulation {}".format(interface, modulation)}
        r = self.send_rest_post_request(data)
        if r.ok:
            if verbose:
                print("ok.")
                print(r.text)
        else:
            print("no success.")

    def abort(self, verbose=True):
        if verbose:
            print("\t{}: Sending abort... ".format(self.name), end="", flush=True)
        data = {"cmd": "abort"}
        r = self.send_rest_post_request(data)
        if r.ok:
            if verbose:
                print("ok.")
        else:
            print("no success.")

    def change_central_frequency(self, interface, central_frequency, verbose=True):
        if self.check_interface(interface):
            if self.check_central_frequency(central_frequency):
                if verbose:
                    print(
                        "\tChanging {}'s interface {} central frequency to {} THz".format(
                            self.name, interface, central_frequency
                        )
                    )
                data = {"cmd": "add interface {} frequency {}".format(
                    interface, central_frequency)}
                r = self.send_rest_post_request(data)
                # print(r)
                return r
        return None

    def change_launch_power(self, interface, power, verbose=True):
        if self.check_interface(interface):
            if self.check_power(power):
                if verbose:
                    print(
                        "\tChanging {}'s interface {} launch power to {}dBm".format(
                            self.name, interface, power
                        )
                    )
                data = {"cmd": "add interface {} power {}".format(interface, power)}
                r = self.send_rest_post_request(data)
                # print(r)
                return r
        return None

    def add_vlan_to_interface(self, interface, vid, verbose=True):
        if self.check_vlan(vid):
            if verbose:
                print("\t{}: Adding vid {} to interface {}... ".format(self.name, vid, interface), end="", flush=True)
            data = {"cmd": "add interface {} bridge vids {}".format(interface, vid)}
            r = self.send_rest_post_request(data)
            if r.ok:
                if verbose:
                    print("ok.")
            else:
                print("no success.")
        else:
            return None
    
    def del_vlan_to_interface(self, interface, vid, verbose=True):
        if self.check_vlan(vid):
            if verbose:
                print("\t{}: Deleting vid {} to interface {}... ".format(self.name, vid, interface), end="", flush=True)
            data = {"cmd": "del interface {} bridge vids {}".format(interface, vid)}
            r = self.send_rest_post_request(data)
            if r.ok:
                if verbose:
                    print("ok.")
            else:
                print("no success.")
        else:
            return None

    def change_modulation_format(self, interface, modulation, verbose=True):
        print("TODO - change_modulation_format")
        # # TODO: extra steps are needed to change to/from 8-qam.
        # # to 8-qam: delete all interfaces related to the pair L1-L2 or L3-L4.
        # # from 8-qam: remove all interfaces related to the pair and reasign
        # # the new modulation format to both interfaces of the pair.
        # if self.check_interface(interface):
        #     if self.check_modulation(modulation):
        #         swp_interface = "swp{}".format(interface)
        #         self.del_interface(swp_interface)
        #         swp_interface = "swp{}s0".format(interface)
        #         self.del_interface(swp_interface)
        #         swp_interface = "swp{}s1".format(interface)
        #         self.del_interface(swp_interface)
        #         # swp_interface = 'swp{}s2'.format(interface)
        #         # self.del_interface(swp_interface)
        #         self.commit()
        #         self.add_modulation(interface, modulation)
        #         # self.commit()

    def checkClass(self):
        print(self.name)
        print(self.ip)
        print(self.port)
        print(self.type)
        print(self.auth)
        print(self.base_url)
        print(self.url)
        print(self.verify)

    def check_central_frequency(self, frequency):
        if frequency >= self.frequency_range[0] and frequency <= self.frequency_range[1]:
            return True
        else:
            print(
                "Error: {}'s {} THz frequency target is out of limits.".format(
                    self.name, frequency)
            )
            return False

    def check_interface(self, interface):
        if interface in self.interface_list:
            return True
        else:
            print(
                "Error: {}'s interface {} does not exist.".format(self.name, interface)
            )
            return False

    def check_modulation(self, modulation):
        if modulation in self.modulation_format_list:
            return True
        else:
            print(
                "Error: {}'s interface {} does not exist.".format(self.name, modulation)
            )
            return False

    def check_power(self, power):
        if power <= self.max_power:
            return True
        else:
            print(
                "Error: {}'s {}dBm power target is too high.".format(self.name, power)
            )
            return False

    def check_vlan(self, vid):
        if vid >= 2 and vid <= 4094:
            return True
        else:
            print(
                "Error: {}'s vid {} is out of range (2-4094).".format(self.name, vid)
            )
            return False

    # by default, voyager returns a bad gateway (502) response after 30s without
    # communication. This methods keeps sending a commit message every 30s until
    # self.timeout / 30 trials expires.
    def commit(self, verbose=True):
        if verbose:
            print("\t{}: Sending commit... ".format(self.name), end="", flush=True)
        data = {"cmd": "commit"}
        re_trials = 0
        start = time.time()
        r = self.send_rest_post_request(data)

        while re_trials < self.timeout / 30:
            if r.ok:
                end = time.time()
                if verbose:
                    print("ok. {:.3f} s".format(end - start))
                return True
            else:
                re_trials += 1
                r = self.send_rest_post_request(data)

        if re_trials == 5:
            end = time.time()
            print("no success. {:.3f} s".format(end - start))
            if verbose:
                print(r.text)
                print(r)

    def del_interface(self, interface, verbose=True):
        if verbose:
            print("\t{}: Deleting interface {}... ".format(self.name, interface), end="",
                flush=True)
        data = {"cmd": "del interface {}".format(interface)}
        r = self.send_rest_post_request(data)
        if r.ok:
            if verbose:
                print("ok.")
        else:
            print("no success.")

    def pending(self, verbose=True):
        if verbose:
            print("{}: Getting pending... ".format(self.name), end="", flush=True)
        data = {"cmd": "pending"}
        r = self.send_rest_post_request(data)
        if r.ok:
            if verbose:
                print("ok.")
                if r.text:
                    print(r.text)
        else:
            print("no success.")

    def show_counters(self):
        # show counters json
        print("TODO: counters")

    def show_transponder(self, verbose=True):
        if verbose:
            print("{}: Show transponder... ".format(self.name), end="", flush=True)
        data = {"cmd": "show transponder json"}
        start = time.time()
        r = self.send_rest_post_request(data)
        end = time.time()
        if r.ok:
            if verbose:
                print("ok. {:.3f} s".format(end - start))
            return r.text, start
        else:
            print("no success. {:.3f} s".format(end - start))
            return False

    def show_configuration(self):
        print("TODO: config")

    def get_transponder_json(self):
        print("Retrieving {}'s transponders json.".format(self.name))
        data = {"cmd": "show transponder json"}
        r = self.send_rest_post_request(data)
        return(r)

    def check_connectivity(self):
        print("{}: Checking connectivity... ".format(self.name), end="", flush=True)
        r = self.send_rest_get_request()
        if r is not None:
            if r.text.split("rpc\"")[1].split("\"")[1] == "/nclu/v1/":
                print("ok.")
            else:
                print("can't connect to {}'s ({}) REST server.".format(self.name,self.ip))
        else:
            print("can't connect to {}'s ({}).".format(self.name,self.ip))
