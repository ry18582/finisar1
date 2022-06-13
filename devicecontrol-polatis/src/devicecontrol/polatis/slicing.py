#!/usr/bin/env python
"""
Adds slicing capability on top of a regular Oxc object
"""  # noqa
import logging
import sys
from io import StringIO
from itertools import filterfalse, tee, zip_longest
from json import dumps

from .interface import OxcInterface

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
_handler = logging.StreamHandler(stream=sys.stdout)
_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] "
    "%(name)s(%(lineno)s):\n%(message)s\n------------------------------"
)
_handler.setFormatter(_formatter)
LOGGER.addHandler(_handler)


def json(x):
    return dumps(x, indent=2)


def join_text(text1, text2):
    """Print 2 texts, side by side"""
    buf = StringIO()
    # Calculate Maximum horizontal length
    lines1 = text1.split("\n")
    lines2 = text2.split("\n")
    horizontal = max(len(l) for l in lines1)

    for l1, l2 in zip_longest(lines1, lines2, fillvalue=""):
        buf.write(l1.ljust(horizontal) + " | " + l2 + "\n")

    try:
        return buf.getvalue()
    finally:
        buf.close()


def log_real_vs_virtual(title, node, real, virtual):
    LOGGER.debug(
        "\n%s\n%s",
        title,
        join_text(
            "Real device:\n\n" + json(dict(real)),
            "Virtual device:\n%s\n%s" % (node, json(dict(virtual))),
        ),
    )


def partition(predicate, iterable):
    """Create two derived iterators from a single one
    The first iterator created will loop thought the values where the function
    predicate is True, the second one will iterate over the values where it is
    false.
    """
    iterable1, iterable2 = tee(iterable)
    return filter(predicate, iterable2), filterfalse(predicate, iterable1)


def validate_port(name, port, pmin, pmax):
    if not (pmin <= port <= pmax):
        raise ValueError(
            "Expecting %d <= port (%s) <= %d, but found %d" % (pmin, name, pmax, port),
            "{}-port".format(name),
        )


def validate_port_in(name, port, port_list):
    if port not in port_list:
        raise ValueError(
            "Port %d (%s) not in %r" % (port, name, port_list), "{}-port".format(name)
        )


class PortMapping(object):
    """Maps real and virtual OXC ports

    Arguments
        input_ports: list of input port numbers of the real device to be
            controlled by the virtual device.
        output_ports: list of output port numbers of the real device to be
            controlled by the virtual device


    Ports are always integers greater than 0 (starting from 1).
    """

    def __init__(self, input_ports, output_ports):
        self._input_ports = input_ports
        self._output_ports = output_ports

    @property
    def input_number(self):
        return len(self._input_ports)

    @property
    def output_number(self):
        return len(self._output_ports)

    @property
    def port_number(self):
        return self.input_number + self.output_number

    @property
    def last_input(self):
        return self.input_number

    @property
    def first_output(self):
        return self.last_input + 1

    @property
    def last_output(self):
        return self.last_input + self.output_number

    def real_input(self, port):
        port = int(port)
        validate_port("input", port, 1, self.last_input)
        return self._input_ports[port - 1]

    def real_output(self, port):
        port = int(port)
        validate_port("output", port, self.first_output, self.last_output)
        return self._output_ports[port - self.first_output]

    def real_port(self, port):
        port = int(port)
        if 1 <= port <= self.last_input:
            return self.real_input(port)
        return self.real_output(port)

    def virtual_input(self, port):
        port = int(port)
        validate_port_in("input", port, self._input_ports)
        return self._input_ports.index(port) + 1

    def virtual_output(self, port):
        port = int(port)
        validate_port_in("output", port, self._output_ports)
        return self._output_ports.index(port) + self.first_output

    def virtual_port(self, port):
        port = int(port)
        if port in self._input_ports:
            return self.virtual_input(port)
        return self.virtual_output(port)

    def has_pair(self, port_in, port_out):
        port_in = int(port_in)
        port_out = int(port_out)
        return port_in in self._input_ports and port_out in self._output_ports

    def filter_connections(self, connections):
        own, others = partition(lambda c: self.has_pair(*c), dict(connections).items())

        return dict(own), dict(others)

    def filter_real_ports(self, ports):
        plist = (int(p) for p in ports)
        return (p for p in plist if p in self._input_ports or p in self._output_ports)

    def virtual_connections(self, connections):
        own, _ = self.filter_connections(connections)
        return {
            self.virtual_input(port_in): self.virtual_output(port_out)
            for port_in, port_out in own.items()
        }

    def real_connections(self, connections):
        return {
            self.real_input(port_in): self.real_output(port_out)
            for port_in, port_out in dict(connections).items()
        }


class VirtualOxc(OxcInterface):
    """Take control of some ports inside the OXC, simulating a smaller device.

    Arguments
        underlay (OxcInterface): another instance of the OXC, to which
            the real commands will be delegated
        input_ports: list of input port numbers of the real device to be
            controlled by the virtual device.
        output_ports: list of output port numbers of the real device to be
            controlled by the virtual device


    Ports are always integers greater than 0 (starting from 1).
    """

    def __init__(self, underlay, input_ports, output_ports):
        self._input_ports = [int(p) for p in input_ports]
        self._output_ports = [int(p) for p in output_ports]
        self.mapping = PortMapping(self._input_ports, self._output_ports)
        self._underlay = underlay

    def __str__(self):
        return "<{}://{}:{}/{}|{}>".format(
            self.__class__.__name__,
            *self._underlay.address,
            ",".join(str(p) for p in self._input_ports),
            ",".join(str(p) for p in self._output_ports),
        )

    @property
    def idn(self):
        parent = self._underlay.idn
        return ("Sliced", *parent, str(self))

    @property
    def number_of_ports(self):
        return self.mapping.input_number, self.mapping.output_number

    @property
    def ports(self):
        return (
            list(range(1, self.mapping.last_input + 1)),
            list(range(self.mapping.first_output, self.mapping.last_output + 1)),
        )

    def connect(self, connection_map):
        if not connection_map:
            return

        real = self.mapping.real_connections(connection_map)
        log_real_vs_virtual("connect", str(self), real, connection_map)
        self._underlay.connect(real)

    def disconnect(self, connection_map):
        if not connection_map:
            return

        real = self.mapping.real_connections(connection_map)
        log_real_vs_virtual("disconnect", str(self), real, connection_map)
        self._underlay.disconnect(real)

    def disconnect_all(self):
        self.disconnect(self.connections)

    @property
    def connections(self):
        real = self._underlay.connections
        virtual = self.mapping.virtual_connections(self._underlay.connections)
        log_real_vs_virtual("connections", str(self), real, virtual)
        return virtual

    @connections.setter
    def connections(self, value):
        new_connections = {(int(k), int(v)) for k, v in value.items()}
        curr_connections = self.mapping.virtual_connections(self._underlay.connections)
        curr_connections = {(int(k), int(v)) for k, v in curr_connections.items()}

        remove = curr_connections - new_connections
        add = new_connections - curr_connections

        self.disconnect(remove)
        self.connect(add)

    def get_power(self, port_list):
        ports = (self.mapping.real_port(p) for p in port_list)
        real = self._underlay.get_power(ports)
        virtual = {self.mapping.virtual_port(k): v for k, v in real.items()}
        log_real_vs_virtual("get_power", str(self), real, virtual)
        return virtual

    @property
    def power(self):
        real = self._underlay.power
        real_ports = self.mapping.filter_real_ports(real.keys())
        virtual = {self.mapping.virtual_port(k): real[k] for k in real_ports}
        log_real_vs_virtual("power", str(self), real, virtual)
        return virtual
