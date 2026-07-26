import re
import pytest  # type: ignore

import nad_receiver
from nad_receiver.nad_fake_transport import Fake_NAD_C_356BE_Transport

ON = "On"
OFF = "Off"


class Fake_NAD_C_356BE(nad_receiver.NADReceiver):
    """NAD Receiver with fake transport for testing."""
    def __init__(self) -> None:
        self.transport = Fake_NAD_C_356BE_Transport()


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        ("-40", -40.0),
        ("-40.5dB", -40.5),
        ("-40.5 arbitrary suffix", -40.5),
        ("NaN", None),
        ("40", None)
    ],
)
def test_main_volume_parses_leading_negative_decimal(
    monkeypatch: pytest.MonkeyPatch, response: str, expected: float
) -> None:
    """Tests to check returned Main.Volume conversion."""
    receiver = Fake_NAD_C_356BE()
    monkeypatch.setattr(receiver, "exec_command", lambda *args: response)

    assert receiver.main_volume("?") == expected


def test_NAD_C_356BE() -> None:
    # This test can be run with the real amplifier, just instantiate
    # the real transport instead of the fake one
    receiver = Fake_NAD_C_356BE()
    assert receiver.main_power("?") in (ON, OFF)

    # switch off
    assert receiver.main_power("=", OFF) == OFF
    assert receiver.main_power("?") == OFF
    assert receiver.main_power("+") == ON
    assert receiver.main_power("+") == OFF
    assert receiver.main_power("?") == OFF

    # C 356BE does not reply for commands other than power when off
    assert receiver.main_mute("?") is None

    assert receiver.main_power("=", ON) == ON
    assert receiver.main_power("?") == ON

    assert receiver.main_mute("=", OFF) == OFF
    assert receiver.main_mute("?") == OFF

    # Not a feature for this amp
    assert receiver.main_dimmer("?") is None

    # Stepper motor and this thing has no idea about the volume
    assert receiver.main_volume("?") is None

    # No exception
    assert receiver.main_volume("+") is None
    assert receiver.main_volume("-") is None

    assert receiver.main_version("?") == "V1.02"
    assert receiver.main_model("?") == "C356BEE"

    # Here the RS232 NAD manual seems to be slightly off / maybe the model is different
    # The manual claims:
    # CD Tuner Video Disc Ipod Tape2 Aux
    # My Amp:
    # CD Tuner Disc/MDC Aux Tape2 MP
    # Protocol V2 represents sources as strings, we should get these:
    assert receiver.main_source("=", "AUX") == "AUX"
    assert receiver.main_source("?") == "AUX"
    assert receiver.main_source("=", "CD") == "CD"
    assert receiver.main_source("?") == "CD"
    assert receiver.main_source("+") == "TUNER"
    assert receiver.main_source("-") == "CD"
    assert receiver.main_source("+") == "TUNER"
    assert receiver.main_source("+") == "DISC/MDC"
    assert receiver.main_source("+") == "AUX"
    assert receiver.main_source("+") == "TAPE2"
    assert receiver.main_source("+") == "MP"
    assert receiver.main_source("+") == "CD"
    assert receiver.main_source("-") == "MP"

    # Tape monitor / tape 1 is independent of sources
    assert receiver.main_tape_monitor("=", OFF) == OFF
    assert receiver.main_tape_monitor("?") == OFF
    assert receiver.main_tape_monitor("=", ON) == ON
    assert receiver.main_tape_monitor("+") == OFF

    assert receiver.main_speaker_a("=", OFF) == OFF
    assert receiver.main_speaker_a("?") == OFF
    assert receiver.main_speaker_a("=", ON) == ON
    assert receiver.main_speaker_a("?") == ON
    assert receiver.main_speaker_a("+") == OFF
    assert receiver.main_speaker_a("+") == ON
    assert receiver.main_speaker_a("-") == OFF
    assert receiver.main_speaker_a("-") == ON

    assert receiver.main_speaker_b("=", OFF) == OFF
    assert receiver.main_speaker_b("?") == OFF

    assert receiver.main_power("=", OFF) == OFF
