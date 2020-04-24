import re
import pytest  # type: ignore
import serial  # type: ignore

import nad_receiver

ON = "On"
OFF = "Off"


class Fake_NAD_C_356BE(nad_receiver.NadTransport):
    def __init__(self):
        self._toggle = {
            "Power": False,
            "Mute": False,
            "Tape1": False,
            "SpeakerA": True,
            "SpeakerB": False,
        }
        self._model = "C356BEE"
        self._version = "V1.02"
        self._sources = "CD TUNER DISC/MDC AUX TAPE2 MP".split()
        self._source = "CD"
        self._command_regex = re.compile(
            r"(?P<component>\w+)\.(?P<function>\w+)(?P<operator>[=\?\+\-])(?P<value>.*)"
        )

    def _toggle_property(self, property: str, operator: str, value: str) -> str:
        assert value in ["", "On", "Off"]
        val = self._toggle[property]
        if operator in ("+", "-"):
            val = not val
        if operator == "=":
            val = value == "On"
        self._toggle[property] = val
        return "On" if val else "Off"

    def communicate(self, command: str) -> str:
        match = self._command_regex.fullmatch(command)
        if not match or match.group("component") != "Main":
            return ""
        component = match.group("component")
        function = match.group("function")
        operator = match.group("operator")
        value = match.group("value")

        response = lambda val: f"{component}.{function}{'=' + val if val else ''}"

        if function == "Version" and operator == "?":
            return response(self._version)
        if function == "Model" and operator == "?":
            return response(self._model)

        if function == "Power":
            return response(self._toggle_property(function, operator, value))

        if not self._toggle["Power"]:
            # Except for power, all other functions return "" when power is off.
            return ""

        if function in self._toggle.keys():
            return response(self._toggle_property(function, operator, value))

        if function == "Volume":
            # this thing doesn't report volume, but increase/decrease works and we do get the original command back
            if operator in ("+", "-"):
                return response(None) + operator

        if function == "Source":
            index = self._sources.index(self._source)
            assert index >= 0
            if operator == "+":
                index += 1
            if operator == "-":
                index -= 1
            if operator == "=":
                index = self._sources.index(value)
            if index < 0:
                index = len(self._sources) - 1
            if index == len(self._sources):
                index = 0
            self._source = self._sources[index]
            return response(self._source)

        return ""


def test_NAD_C_356BE():
    # transport = nad_receiver.SerialPortTransport("/dev/ttyUSB0")
    transport = Fake_NAD_C_356BE()
    receiver = nad_receiver.NADReceiver(transport)
    assert receiver.main.power.get() in (ON, OFF)

    # switch off
    assert receiver.main.power.set(OFF) == OFF
    assert receiver.main.power.get() == OFF
    assert receiver.main.power.increase() == ON
    assert receiver.main.power.increase() == OFF
    assert receiver.main.power.get() == OFF

    # C 356BE does not reply for commands other than power when off
    with pytest.raises(ValueError):
        receiver.main.mute.get()

    assert receiver.main.power.set(ON) == ON
    assert receiver.main.power.get() == ON

    assert receiver.main.mute.set(OFF) == OFF
    assert receiver.main.mute.get() == OFF

    # Not a feature for this amp
    with pytest.raises(ValueError):
        receiver.main.dimmer.get()

    # Stepper motor and this thing has no idea about the volume
    with pytest.raises(ValueError):
        receiver.main.volume.get()

    # No exception
    assert receiver.main.volume.increase() is None
    assert receiver.main.volume.decrease() is None

    # assert receiver.main.ir.set(???) == ""

    # whatever that may be
    assert receiver.main.version.get() == "V1.02"

    assert receiver.main.model.get() == "C356BEE"

    # Here the RS232 NAD manual seems to be slightly off / maybe the model is different
    # The manual claims:
    # CD Tuner Video Disc Ipod Tape2 Aux
    # My Amp:
    # CD Tuner Disc/MDC Aux Tape2 MP
    assert receiver.main.source.set("AUX") == "AUX"
    assert receiver.main.source.get() == "AUX"
    assert receiver.main.source.set("CD") == "CD"
    assert receiver.main.source.get() == "CD"
    assert receiver.main.source.increase() == "TUNER"
    assert receiver.main.source.decrease() == "CD"
    assert receiver.main.source.increase() == "TUNER"
    assert receiver.main.source.increase() == "DISC/MDC"
    assert receiver.main.source.increase() == "AUX"
    assert receiver.main.source.increase() == "TAPE2"
    assert receiver.main.source.increase() == "MP"
    assert receiver.main.source.increase() == "CD"
    assert receiver.main.source.decrease() == "MP"

    # Tape monitor / tape 1 is independent of sources
    assert receiver.main.tape_monitor.set(OFF) == OFF
    assert receiver.main.tape_monitor.get() == OFF
    assert receiver.main.tape_monitor.set(ON) == ON
    assert receiver.main.tape_monitor.increase() == OFF

    assert receiver.main.speaker_a.set(OFF) == OFF
    assert receiver.main.speaker_a.get() == OFF
    assert receiver.main.speaker_a.set(ON) == ON
    assert receiver.main.speaker_a.get() == ON
    assert receiver.main.speaker_a.increase() == OFF
    assert receiver.main.speaker_a.increase() == ON
    assert receiver.main.speaker_a.decrease() == OFF
    assert receiver.main.speaker_a.decrease() == ON

    assert receiver.main.speaker_b.set(OFF) == OFF
    assert receiver.main.speaker_b.get() == OFF

    assert receiver.main.power.set(OFF) == OFF


def test_NAD_C_356BE_new_API():
    # transport = nad_receiver.SerialPortTransport("/dev/ttyUSB0")
    transport = Fake_NAD_C_356BE()
    receiver = nad_receiver.NADReceiver(transport)

    print("main: ", receiver.main)
    print("main: ", receiver.main.power)

    print("main: ", receiver.main)
    with pytest.raises(TypeError):
        receiver.main.power()

    receiver.main.power.get()
    receiver.main.power.set("On")
    receiver.main.power.set("Off")
    # receiver.main.power.on()
    # receiver.main.power.off()
    receiver.main.power.increase()
    receiver.main.power.decrease()

    with pytest.raises(TypeError):
        print("main: ", receiver.foo)
    with pytest.raises(TypeError):
        print("main: ", receiver.main.bar)

    with pytest.raises(TypeError):
        receiver.main.power()


def test_invalid_serial_port():
    # Fixme, we don't really want an exception here
    with pytest.raises(serial.SerialException):
        transport = nad_receiver.SerialPortTransport("/dev/does_not_exist")
