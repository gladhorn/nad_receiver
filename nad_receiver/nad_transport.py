import abc
import codecs
import serial  # type: ignore
import telnetlib
import threading
import time
import socket

from typing import Optional

import logging

logging.basicConfig()
_LOGGER = logging.getLogger("nad_receiver.transport")
_LOGGER.setLevel(logging.DEBUG)

# One second should be enough for write/read
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

    def _open_connection(self) -> None:
        if not self.ser.is_open:
            self.ser.open()
            _LOGGER.debug("serial open: %s", self.ser.is_open)

    def communicate(self, command: str) -> str:
        with self.lock:
            self._open_connection()

            self.ser.write(f"\r{command}\r".encode("utf-8"))
            # To get complete messages, always read until we get '\r'
            # Messages will be of the form '\rMESSAGE\r' which pyserial handles nicely
            msg = self.ser.read_until("\r")
            assert isinstance(msg, bytes)
            return msg.strip().decode()


class TelnetTransport:
    """
    Support NAD amplifiers that use telnet for communication.
    Supports all commands from the RS232 base class

    Known supported model: Nad T787.
    """

    def __init__(
        self, host: str, port: int = 23, timeout: int = DEFAULT_TIMEOUT
    ) -> None:
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
                self.telnet.read_until("\r".encode(), self.timeout)
                # Could raise eg. EOFError, UnicodeError
            except (EOFError, UnicodeError):
                pass

    def communicate(self, cmd: str) -> str:
        self._open_connection()
        assert self.telnet

        self.telnet.write(f"\r{cmd}\r".encode())
        msg = self.telnet.read_until(b"\r", self.timeout)
        return msg.strip().decode()


class TcpTransport:
    """
    Support NAD amplifiers that use tcp for communication.

    Known supported model: Nad D 7050.
    """

    # POLL_VOLUME = "0001020204"
    # POLL_POWER = "0001020209"
    # POLL_MUTED = "000102020a"
    # POLL_SOURCE = "0001020203"

    # CMD_POWERSAVE = "00010207000001020207"
    # CMD_OFF = "0001020900"
    # CMD_ON = "0001020901"
    # CMD_VOLUME = "00010204"
    # CMD_MUTE = "0001020a01"
    # CMD_UNMUTE = "0001020a00"
    # CMD_SOURCE = "00010203"

    # SOURCES = {
    #     "Coaxial 1": "00",
    #     "Coaxial 2": "01",
    #     "Optical 1": "02",
    #     "Optical 2": "03",
    #     "Computer": "04",
    #     "Airplay": "05",
    #     "Dock": "06",
    #     "Bluetooth": "07",
    # }
    # SOURCES_REVERSED = {value: key for key, value in SOURCES.items()}

    # PORT = 50001
    # BUFFERSIZE = 1024

    # def __init__(self, host):
    #     """Setup globals."""
    #     self._host = host

    # def _send(self, message, read_reply=False):
    #     """Send a command string to the amplifier."""
    #     sock = None
    #     for tries in range(0, 3):
    #         try:
    #             sock = socket.create_connection((self._host, self.PORT), timeout=5)
    #             break
    #         except socket.timeout:
    #             print("Socket connection timed out.")
    #             return
    #         except (ConnectionError, BrokenPipeError):
    #             if tries == 2:
    #                 print("socket connect failed.")
    #                 return
    #             sleep(0.1)
    #     sock.send(codecs.decode(message, "hex_codec"))
    #     if read_reply:
    #         sleep(0.1)
    #         reply = ""
    #         tries = 0
    #         max_tries = 20
    #         while len(reply) < len(message) and tries < max_tries:
    #             try:
    #                 reply += codecs.encode(sock.recv(self.BUFFERSIZE), "hex").decode(
    #                     "utf-8"
    #                 )
    #             except (ConnectionError, BrokenPipeError):
    #                 pass
    #             tries += 1
    #         sock.close()
    #         if tries >= max_tries:
    #             return
    #         return reply
    #     sock.close()

    # def status(self):
    #     """
    #     Return the status of the device.

    #     Returns a dictionary with keys 'volume' (int 0-200) , 'power' (bool),
    #      'muted' (bool) and 'source' (str).
    #     """
    #     nad_reply = self._send(
    #         self.POLL_VOLUME + self.POLL_POWER + self.POLL_MUTED + self.POLL_SOURCE,
    #         read_reply=True,
    #     )
    #     if nad_reply is None:
    #         return

    #     # split reply into parts of 10 characters
    #     num_chars = 10
    #     nad_status = [
    #         nad_reply[i : i + num_chars] for i in range(0, len(nad_reply), num_chars)
    #     ]

    #     return {
    #         "volume": int(nad_status[0][-2:], 16),
    #         "power": nad_status[1][-2:] == "01",
    #         "muted": nad_status[2][-2:] == "01",
    #         "source": self.SOURCES_REVERSED[nad_status[3][-2:]],
    #     }

    # def power_off(self):
    #     """Power the device off."""
    #     status = self.status()
    #     if status["power"]:  # Setting power off when it is already off can cause hangs
    #         self._send(self.CMD_POWERSAVE + self.CMD_OFF)

    # def power_on(self):
    #     """Power the device on."""
    #     status = self.status()
    #     if not status["power"]:
    #         self._send(self.CMD_ON, read_reply=True)
    #         sleep(0.5)  # Give NAD7050 some time before next command

    # def set_volume(self, volume):
    #     """Set volume level of the device. Accepts integer values 0-200."""
    #     if 0 <= volume <= 200:
    #         volume = format(volume, "02x")  # Convert to hex
    #         self._send(self.CMD_VOLUME + volume)

    # def mute(self):
    #     """Mute the device."""
    #     self._send(self.CMD_MUTE, read_reply=True)

    # def unmute(self):
    #     """Unmute the device."""
    #     self._send(self.CMD_UNMUTE)

    # def select_source(self, source):
    #     """Select a source from the list of sources."""
    #     status = self.status()
    #     if status["power"]:  # Changing source when off may hang NAD7050
    #         if (
    #             status["source"] != source
    #         ):  # Setting the source to the current source will hang the NAD7050
    #             if source in self.SOURCES:
    #                 self._send(self.CMD_SOURCE + self.SOURCES[source], read_reply=True)

    # def available_sources(self):
    #     """Return a list of available sources."""
    #     return list(self.SOURCES.keys())
