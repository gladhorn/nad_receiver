"""
NAD has an RS232 interface to control the receiver.

Not all receivers have all functions.
Functions can be found on the NAD website: http://nadelectronics.com/software
"""

from nad_receiver.nad_transport import (
    NadTransport,
    SerialPortTransport,
    TelnetTransport,
    TcpTransport,
)
from nad_receiver.nad_commands import CMDS
from typing import Any, Optional

import logging

logging.basicConfig()
_LOGGER = logging.getLogger("nad_receiver.main")
_LOGGER.setLevel(logging.DEBUG)


class NADReceiver:
    """NAD receiver."""

    def __init__(self, transport: NadTransport) -> None:
        self._transport = transport

    def __getattr__(self, name: str) -> Any:
        class _CallHandler:
            _operator_map = {
                "get": "?",
                "set": "=",
                "increase": "+",
                "decrease": "-",
            }

            def __init__(
                self,
                transport: NadTransport,
                domain: str,
                command: Optional[str] = None,
                op: Optional[str] = None,
            ):
                self._transport = transport
                self._domain = domain
                self._command = command
                self._op = op

            def __repr__(self) -> str:
                command = f".{self._command}" if self._command else ""
                op = f".{self._op}" if self._op else ""
                return f"NADReceiver.{self._domain}{command}{op}"

            def __getattr__(self, attr: str) -> Any:
                if attr.startswith("_"):
                    return
                if not self._command:
                    if attr in CMDS.get(self._domain):  # type: ignore
                        return _CallHandler(self._transport, self._domain, attr)
                    raise TypeError(f"{attr}")
                if self._op:
                    raise TypeError(f"{self} has no attribute {attr}")
                return _CallHandler(self._transport, self._domain, self._command, attr)

            def __call__(self, value: Optional[str] = None) -> Optional[str]:
                """Executes the command.

                Returns a string when possible or None.
                Throws a ValueError in case the command was not successful."""
                if not self._op:
                    raise TypeError(f"{self} is not callable.")

                function_data = CMDS.get(self._domain).get(self._command)  # type: ignore
                op = _CallHandler._operator_map.get(self._op, None)
                if not op or op not in function_data.get("supported_operators"):  # type: ignore
                    raise TypeError(
                        f"{self} does not support '{self._op}', try one of {_CallHandler._operator_map.keys()}"
                    )

                cmd = f"{function_data.get('cmd')}{op}{value if value else ''}"  # type: ignore
                reply = self._transport.communicate(cmd)
                _LOGGER.debug(f"command: {cmd} reply: {reply}")
                if not reply:
                    raise ValueError(f"Did not receive reply from receiver for {self}.")
                if reply:
                    # Try to return the new value
                    index = reply.find("=")
                    if index < 0:
                        if reply == cmd:
                            # On some models, no value, but the command is returned.
                            # That means success, but the receiver cannot report the state.
                            return None
                        raise ValueError(
                            f"Unexpected reply from receiver for {self}: {reply}."
                        )
                    reply = reply[index + 1 :]
                return reply

        if name not in CMDS:
            raise TypeError(f"{self} has not attribute {name}")
        return _CallHandler(self._transport, name)
