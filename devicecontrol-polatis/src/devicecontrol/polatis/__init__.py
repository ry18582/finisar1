#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Software entity responsible for interacting the device counterpart of
the Polatis Optical Cross-conector
"""
import re
from functools import lru_cache
from itertools import chain
from pkg_resources import DistributionNotFound, get_distribution

from .interface import OxcInterface
from .scpi import ScpiInterface

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = "devicecontrol-polatis"
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = "unknown"
finally:
    del get_distribution, DistributionNotFound


PORT_NUMBER_REGEX = re.compile(r"-(\d+)x(\d+)-", re.I)
_MAX_POWER_READINGS = 256
_PROD_CODE_WITH_INPUT_PHOTODETECTORS = ["N-VST-192x192-LU1-DMHNV-801"]


class Oxc(ScpiInterface, OxcInterface):
    """Interacts with a Polatis Optical Cross Connector using SCPI"""

    @property
    @lru_cache(1)
    def product_code(self):
        return self.idn[1]

    @property
    @lru_cache(1)
    def number_of_ports(self):
        """Returns a tuple with the number of inputs and output ports
        respectively"""
        match = PORT_NUMBER_REGEX.findall(self.product_code)
        if not match:
            msg = "Device {}:{} {} does not seem to be a Polatis OXC".format(
                *self.address, self.idn
            )
            self._logger.debug(msg)
            raise SystemError(msg)
        return (int(match[0][0]), int(match[0][1]))

    @property
    def ports(self):
        """Tuple (list of "input" ports, list of "output" ports)"""
        num = self.number_of_ports
        return (list(range(1, num[0] + 1)), list(range(num[0] + 1, sum(num) + 1)))

    @property
    def network_config(self):
        """Retrieve a dict with the device network configuration"""
        response = self.query(":syst:comm:netw:addr?")
        pairs = (pair.split("=") for pair in response.split())
        return {key.strip(" \t"): value.strip('" \t') for key, value in pairs}

    @property
    def connections(self):
        """Retrieve a dict representing all the active cross-connects"""
        return _decode(self.query("oxc:swit:conn:stat?"))

    @connections.setter
    def connections(self, connection_map):
        """Replace all the previous cross-connects with a new configuration

        Equivalent to ``disconnect_all`` + ``connect``
        """
        return self.command("oxc:swit:conn:only " + _encode(connection_map))

    def connect(self, connection_map):
        """Receives a dict representing the desired cross-connects and
        add them to the current configuration of the device
        """
        if connection_map:
            return self.command("oxc:swit:conn:add " + _encode(connection_map))

    def disconnect(self, connection_map):
        """Given a dict representing the desired cross-connects,
        remove them to the current configuration of the device
        """
        if connection_map:
            return self.command("oxc:swit:conn:sub " + _encode(connection_map))

    def disconnect_all(self):
        """Remove all the active cross-connects"""
        return self.command("oxc:swit:disc:all")

    def get_power(self, port_list):
        """Get the power levels of the ports on a given list"""

        pc = self.product_code
        if "I-OST" in pc:
            msg = "OXC {}:{} ({}) does not implement power readings".format(
                *self.address, pc
            )
            self._logger.debug(msg)
            raise NotImplementedError(msg)

        port_list = list(port_list)
        return dict(
            # Since Polatis can ready just a few power levels for every command
            # we need to split it into chunks
            chain.from_iterable(
                self._get_power(port_list[i : i + _MAX_POWER_READINGS])  # noqa
                for i in range(0, len(port_list), _MAX_POWER_READINGS)
            )
        )

    def _get_power(self, port_list):
        response = self.query(":pmon:pow? " + _encode_list(port_list))
        power_levels = [float(p) for p in response.strip("()").split(",") if p]
        return zip(port_list, power_levels)

    @property
    def power(self):
        """Get all power levels available.

        Returns a dict relating the port number and the power level
        """
        in_ports, out_ports = self.ports
        ports = out_ports
        if self.product_code in _PROD_CODE_WITH_INPUT_PHOTODETECTORS:
            ports = [*in_ports, *ports]

        return self.get_power(ports)


def _encode(connection_map):
    """Transform an dictionary mapping the cross connections
    (input => output port), into the SCPI representation::

        (@i1,i2,i3,...,iN),(@o1,o2,o3,...,oN)

    Where ``iX`` corresponds to the input port number X, and ``oX`` corresponds
    to the output port number X.
    """
    connection_map = _sort_pairs(connection_map)
    in_ports = map(str, connection_map.keys())
    out_ports = map(str, connection_map.values())
    return "(@{}),(@{})".format(",".join(in_ports), ",".join(out_ports))


def _decode(message):
    """Transform a string representing the crossconnects coming from the SCPI
    into a dict (input => output port). The SCPI format is::

        (@i1,i2,i3,...,iN),(@o1,o2,o3,...,oN)

    Where ``iX`` corresponds to the input port number X, and ``oX`` corresponds
    to the output port number X.
    """
    in_ports, out_ports = [
        [int(port.strip(" \t")) for port in part.strip("(@)").split(",") if port]
        for part in message.split("),(")
    ]
    return dict(zip(in_ports, out_ports))


def _encode_list(port_list):
    """Transform a list of ports, into the SCPI representation::

        (@p1,p2,p3,...,pN)

    Where ``pX`` corresponds to the port number X.
    """
    ports = map(str, port_list)
    return "(@{})".format(",".join(ports))


def _sort_pairs(connection_map):
    """Sort pairs to make sure that the port list follows the IN_PORT:OUT_PORT
    order.
    IN_PORT should always be < than OUT_PORT.
    """
    connections = ((int(k), int(v)) for k, v in (connection_map or {}).items())
    return dict([sorted(pair) for pair in connections])
