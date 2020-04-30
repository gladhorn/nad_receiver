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


class SerialPortTransport:
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

    def __repr__(self):
        return f"SerialPortTransport<is_open:{self.ser.is_open}>"

    def _open_connection(self) -> None:
        if not self.ser.is_open:
            self.ser.open()
            _LOGGER.debug("serial open: %s", self.ser.is_open)

    def communicate(self, command: str) -> str:
        with self.lock:
            self._open_connection()

            self.ser.write(f"\r{command}\r".encode("utf-8"))
            # To get complete messages, always read until we get '\r'
            # Messages will be of the form '\rMESSAGE\r' which
            # pyserial handles nicely
            msg = self.ser.read_until("\r")
            assert isinstance(msg, bytes)
            return msg.strip().decode()


class TelnetTransport:
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
                self.telnet = telnetlib.Telnet(self.host, self.port, 3)
                # Some versions of the firmware report Main.Model=T787.
                # some versions do not, we want to clear that line
                self.telnet.read_until("\n".encode(), self.timeout)
                # Could raise eg. EOFError, UnicodeError
            except (EOFError, UnicodeError):
                pass

    def communicate(self, cmd: str) -> str:
        self._open_connection()
        assert self.telnet

        self.telnet.write(f"\r{cmd}\r".encode())
        msg = self.telnet.read_until(b"\r", self.timeout)
        return msg.strip().decode()
