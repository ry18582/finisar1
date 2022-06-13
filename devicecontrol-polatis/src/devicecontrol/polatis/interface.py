# -*- coding: utf-8 -*-
"""Abstract API for OXC"""

from abc import ABC as AbstractClass
from abc import abstractmethod as abstract


class OxcInterface(AbstractClass):
    @property
    @abstract
    def ports(self):
        """Return a tuple, the first element of the tuple is a list with the
        "input ports", the second element of the tuple is a list with the
        "output ports".

        (Obs.: OXCs are usually bidirectional, but the terminology
        "input/output" is used to differentiate between two groups that can be
        interconnected to each other but not internally.
        """
        raise NotImplementedError

    @property
    @abstract
    def connections(self):
        """Retrieve a dict representing all the active cross-connects"""
        raise NotImplementedError

    @connections.setter
    @abstract
    def connections(self, value):
        """Replace all the previous cross-connects with a new configuration

        Equivalent to ``disconnect_all`` + ``connect``
        """
        raise NotImplementedError

    @abstract
    def connect(self, connection_map):
        """Receives a dict representing the desired cross-connects and
        add them to the current configuration of the device
        """
        raise NotImplementedError

    @abstract
    def disconnect(self, connection_map):
        """Given a dict representing the desired cross-connects,
        remove them to the current configuration of the device
        """
        raise NotImplementedError

    @abstract
    def disconnect_all(self, connection_map):
        """Remove all the active cross-connects"""
        raise NotImplementedError

    @abstract
    def get_power(self, port_list):
        """Get the power levels of the ports on a given list"""
        raise NotImplementedError

    @property
    @abstract
    def power(self):
        """Get all power levels available.

        Returns a dict relating the port number and the power level
        """
        raise NotImplementedError
