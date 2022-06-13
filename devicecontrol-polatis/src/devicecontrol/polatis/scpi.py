#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""High level API for interacting with SCPI interfaces.

The main class in this module (:obj:`~.ScpiInterface`) can be used as parent
class for implementing communication with different devices.
"""
import gc
import logging
from functools import wraps
from socket import AF_INET, SOCK_STREAM, socket

from pexpect import EOF, TIMEOUT
from pexpect.fdpexpect import fdspawn

from .lib import attr_reader, memoized


class ScpiError(RuntimeError):
    """Base class for SCPI exception hierarchy"""

    def __init__(self):
        super().__init__(self.__class__.__doc__)


class ScpiTimeout(ScpiError):
    """Timeout when communication with device"""


class ScpiDisconnected(ScpiError):
    """Communication channel with device suddenly disconnected"""


def translate_exceptions(method):
    """Translate pexpect excetions to the SCPI domain"""

    @wraps(method)
    def _guarded(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except TIMEOUT as ex:
            self._logger.error(ScpiTimeout.__doc__, exc_info=True)
            raise ScpiTimeout from ex
        except (ConnectionError, EOF) as ex:
            self._logger.error(ScpiDisconnected.__doc__, exc_info=True)
            raise ScpiDisconnected from ex

    return _guarded


@attr_reader("address", "timeout")
class ScpiInterface:
    """SCPI communication channel based on pexpect

    This simplified implementation assumes there are just 2 types of messages
    being sent the ones that expect a response (queries) and the ones that
    trigger a side-effect but don't expect any response (commands).

    Based on this assumption, we use the standard command ``*opc?`` to
    synchronize the communication with the device.
    Additionally all the responses are expected to be a single line.

    Arguments
    ---------
    host : str
        IP address of the device
    port : int
        (Optional) TCP port open in the device, waiting for connections.
        5025 by default.
    timeout : float
        Maximum number of seconds waiting for a response from the device
    """

    PORT = 5025  # Default port for SPCI
    TIMEOUT = 5  # Maximum delay accepted in seconds

    def __init__(self, host, port=PORT, timeout=TIMEOUT, logger=None):
        self._address = (host, port or self.PORT)
        self._timeout = timeout or self.TIMEOUT
        self._socket = None
        self._logger = logger or logging.getLogger(__name__)

    def __del__(self):
        if hasattr(self, "_session") and self._session:
            self._session.close()
            self._logger.debug("Session closed.")

    @property
    @memoized
    def session(self):
        """Internal object used for communicating with the device"""
        self._socket = socket(AF_INET, SOCK_STREAM)
        self._socket.connect(self.address)
        return _sync(fdspawn(self._socket.fileno(), timeout=self.timeout))

    def reconnect_session(self):
        """Re-establish SCPI connection"""
        try:
            if self._socket:
                self._socket.close()
        except:  # noqa
            pass
        try:
            # Delete cache to force reconnection
            self._socket = None
            self._session = None
            delattr(self, "_session")
            gc.collect()
        except:  # noqa
            pass
        return self.session

    @translate_exceptions
    def query(self, message):
        """Send a message that requires a response to the device.

        The response is expected to have just a single line
        """
        # *OPC? is used to synchronize the device (it blocks until all the
        # pending requests are processed) and as a end-of-command marker
        # (always return 1)
        try:
            self._logger.debug("Query%r: %s", self.address, message)
            self.session.sendline(message + "\r\n*opc?")
            self.session.expect_exact("\r\n1\r\n")
        except TIMEOUT as ex:
            try:
                self.session.expect_exact("1\r\n")
            except:  # noqa
                raise ex

        response = self.session.before.strip().decode("utf-8")
        self._logger.debug("Response: %s", response)
        return response

    @translate_exceptions
    def command(self, message):
        """Send a messages to the device that triggers a side-effect.

        The device is expected to not send anything back.
        """
        self._logger.debug("Command%r: %s", self.address, message)
        self.session.sendline(message + "\r\n*opc?")
        self.session.expect_exact("1\r\n")

    @property
    def idn(self):
        """Tuple containing the device identification::

            (<vendor>, <model number>, <serial number>, <software revision>)
        """
        return tuple(self.query("*idn?").split(","))

    def sync(self):
        """Ensure there is no pending message being processed/transmitted"""
        return _sync(self.session)


def _sync(session):
    """Auxiliary function to avoid recursion when initializing the serial"""
    session.sendline("*opc?")
    session.expect_exact("1\r\n")
    return session
