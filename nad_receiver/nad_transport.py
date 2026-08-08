import abc
import serial  # type: ignore
from telnetlib3.telnetlib import Telnet  # type: ignore
import threading

from typing import Optional, List

import logging

logging.basicConfig()
_LOGGER = logging.getLogger("nad_receiver.transport")


DEFAULT_TIMEOUT = 1


class NadTransport(abc.ABC):
    @abc.abstractmethod
    def communicate(self, command: str) -> str:
        pass

    def communicate_multiline(self, command: str) -> str:
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

    def _open_connection(self) -> None:
        if not self.ser.is_open:
            self.ser.open()
            _LOGGER.debug("serial open: %s", self.ser.is_open)

    def communicate(self, command: str) -> str:
        with self.lock:
            self._open_connection()

            self.ser.reset_input_buffer()
            self.ser.write(f"\r{command}\r".encode("utf-8"))
            # To get complete messages, always read until we get '\r'
            # Messages will be of the form '\rMESSAGE\r' which
            # pyserial handles nicely
            msg = self.ser.read_until(serial.CR)
            if not msg.strip():  # discard '\r' if it was sent
                msg = self.ser.read_until(serial.CR)
            assert isinstance(msg, bytes)
            return msg.strip().decode()


# TelnetTransport wrapper
# A class to wrap the TelnetTransport in such
# a way that e.g. Home Assistant will not
# receive any exceptions
class TelnetTransportWrapper(NadTransport):
    def __init__(self, host: str, port: int, timeout: int) -> None:
        """Create NADTelnet."""
        self.nad_telnet = TelnetTransport(host, port, timeout)

    def __del__(self) -> None:
        """Destroy NADTelnet."""
        if self.nad_telnet:
            del self.nad_telnet

    def _pre_read(self) -> bool:
        # On initial connection
        # some firmwares sends nothing
        # some firmwares sends e.g. b'\rMain.Model=T787\r\n'
        # some firmwares sends multiple lines (BlueOS settings dump ?)
        #    including blank lines between data lines
        # At least clear the row "\rMain.Model=T787\r\n"
        try:
            self.nad_telnet.read_until("\n".encode())
            # Could raise eg. EOFError, UnicodeError
        except EOFError as cc:
            # Connection closed, no recovery
            _LOGGER.debug("Connection closed: %s", cc)
            self.nad_telnet.close_connection()
            return False
        except UnicodeError as ue:
            # Some unicode error, but connection is open
            _LOGGER.debug("Unicode error: %s", ue)
            return True

        return True

    def _open_connection(self) -> bool:
        if self.nad_telnet.is_open():
            return True

        try:
            self.nad_telnet.open_connection()
        except Exception as e:
            _LOGGER.debug("Connection failed to open: %s" % e)
            return False

        return self._pre_read()

    def communicate(self, cmd: str) -> str:
        rsp = ""
        if not self._open_connection():
            return rsp

        try:
            rsp = self.nad_telnet.communicate(cmd)
        except (EOFError,BrokenPipeError, ConnectionResetError) as cc:
            # Connection closed
            _LOGGER.debug("Connection closed: %s", cc)
            self.nad_telnet.close_connection()
        except UnicodeError as ue:
            # Some unicode error, but connection is open
            _LOGGER.debug("Unicode error: %s", ue)

        return rsp

    def communicate_multiline(self, cmds: List[str]) -> List[str]:
        rsp = ""
        if not self._open_connection():
            return rsp

        try:
            rsp = self.nad_telnet.communicate_multiline(cmds)
        except EOFError as cc:
            # Connection closed
            _LOGGER.debug("Connection closed: %s", cc)
            self.nad_telnet.close_connection()
        except UnicodeError as ue:
            # Some unicode error, but connection is open
            _LOGGER.debug("Unicode error: %s", ue)

        return rsp

class TelnetTransport(NadTransport):
    """
    Support NAD amplifiers that use telnet for communication.
    Supports all commands from the RS232 base class

    Known supported model: Nad T787.
    """

    def __init__(self, host: str, port: int, timeout: int) -> None:
        """Create NADTelnet."""
        self.telnet: Optional[Telnet] = None
        self.host = host
        self.port = port
        self.timeout = timeout

    def __del__(self) -> None:
        try:
            self.close_connection()
        except Exception:
            pass

    def is_open(self) -> bool:
        return True if self.telnet else False

    def open_connection(self) -> None:
        if self.telnet:
            raise Exception("Connection already open for host '%s:%s'" % (self.host, self.port))

        _LOGGER.debug("Open connection to: '%s:%s'" % (self.host, self.port))
        self.telnet = Telnet(self.host, self.port, self.timeout)

    def close_connection(self) -> None:
        telnet = self.telnet
        self.telnet = None
        if telnet:
            _LOGGER.debug("Close connection to: '%s:%s'" % (self.host, self.port))
            telnet.close()

    def read_until(self, data) -> None:
        if not self.telnet:
            raise Exception("Connection is closed")

        self.telnet.read_until(data, self.timeout)

    def communicate(self, cmd: str) -> str:
        if not self.telnet:
            raise Exception("Connection is closed")

        _LOGGER.debug("Sending command: '%s'", cmd)
        self.telnet.write(f"\n{cmd}\r".encode())

        # Notice NAD response to command ends with \r and starts with \n
        # E.g. b'\nMain.Power=On\r'
        rsp = self.telnet.read_until(b"\r", self.timeout)
        _LOGGER.debug("Read response: '%s'", str(rsp))
        return rsp.strip().decode()

    def communicate_multiline(self, cmds: List[str]) -> List[str]:
        if not self.telnet:
            raise Exception("Connection is closed")

        _LOGGER.debug("Sending commands: '%s'", cmds)
        cmd = b"".join([f"\n{cmd}\r".encode() for cmd in cmds])
        self.telnet.write(cmd)

        rsp_lines = []
        while True:
            # Notice NAD response to command ends with \r and starts with \n
            # E.g. b'\nMain.Power=On\r'
            rsp = self.telnet.read_until(b"\r", self.timeout)
            _LOGGER.debug("Read response: '%s'", str(rsp))
            rsp = rsp.strip().decode()
            if len(rsp) > 1:
                rsp_lines.append(rsp)
            else:
                break

        return rsp_lines