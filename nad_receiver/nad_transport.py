import abc
import serial  # type: ignore
import telnetlib
import threading

from typing import Optional

import logging

logging.basicConfig()
_LOGGER = logging.getLogger("nad_receiver.transport")


DEFAULT_TIMEOUT = 1


class NadTransport(abc.ABC):
    @abc.abstractmethod
    def communicate(self, command: str) -> str:
        pass


class SerialPortTransport(NadTransport):
    """Transport for NAD protocol over RS-232."""

    def __init__(self, serial_port: str) -> None:
        """Create RS232 connection."""
        self.ser = serial.Serial(
            serial_port,
            baudrate=115200,
            timeout=DEFAULT_TIMEOUT,
            write_timeout=DEFAULT_TIMEOUT,
        )
        self.lock = threading.Lock()
        self.error_count = 0

    def _open_connection(self) -> None:
        if self.error_count > 10:
            self.ser.close()
            self.error_count = 0
        if not self.ser.is_open:
            self.ser.open()
            _LOGGER.debug("serial open: %s", self.ser.is_open)

    def communicate(self, command: str) -> str:
        with self.lock:
            self._open_connection()

            # Empty the buffer, as recommended by the documentation
            self.ser.read_all()

            self.ser.write(f"\r{command}\r".encode("utf-8"))
            # To get complete messages, always read until we get '\r'
            # Messages will be of the form '\rMESSAGE\r' which
            # pyserial handles nicely
            msg = self.ser.read_until("\r")
            if not msg.strip():  # discard '\r' if it was sent
                msg = self.ser.read_until("\r")
            assert isinstance(msg, bytes)
            reply = msg.strip().decode()
            if reply:
                self.error_count = 0
            else:
                self.error_count += 1
            return reply


class TelnetTransport(NadTransport):
    """
    Support NAD amplifiers that use telnet for communication.
    Supports all commands from the RS232 base class

    Known supported model: Nad T787.
    """

    def __init__(self, host: str, port: int, timeout: int) -> None:
        """Create NADTelnet."""
        self.telnet: Optional[telnetlib.Telnet] = None
        self.host = host
        self.port = port
        self.timeout = timeout

    def _open_connection(self) -> None:
        if not self.telnet:
            try:
                self.telnet = telnetlib.Telnet(self.host, self.port, self.timeout)
            except Exception as e:
                _LOGGER.debug("Connection failed to open: %s" % e)
                return

            # On initial connection
            # some firmwares sends nothing
            # some firmwares sends e.g. b'\rMain.Model=T787\r\n'
            # some firmwares sends multiple lines (BlueOS settings dump ?)
            #    including blank lines between data lines
            # At least clear the row "\rMain.Model=T787\r\n"
            try:
                self.telnet.read_until("\n".encode(), self.timeout)
                # Could raise eg. EOFError, UnicodeError
            except EOFError as cc:
                # Connection closed, no recovery
                _LOGGER.debug("Connection closed: %s", cc)
                self.telnet = None
                return
            except UnicodeError as ue:
                _LOGGER.debug("Unicode error: %s", ue)
                return

    def communicate(self, cmd: str) -> str:
        self._open_connection()
        if not self.telnet:
            return ""

        try:
            _LOGGER.debug("Sending command: %s", cmd)
            self.telnet.write(f"\n{cmd}\r".encode())

            # Notice NAD response to command ends with \r and starts with \n
            # E.g. b'\nMain.Power=On\r'
            msg = self.telnet.read_until(b"\r", self.timeout)
            _LOGGER.debug("Read response: %s", str(msg))
        except EOFError as cc:
            # Connection closed
            _LOGGER.debug("Connection closed: %s", cc)
            self.telnet = None
            return ""
        except UnicodeError as ue:
            _LOGGER.debug("Unicode error: %s", ue)
            return ""

        return msg.strip().decode()
