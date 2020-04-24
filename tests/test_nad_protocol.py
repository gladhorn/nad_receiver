
import nad_receiver

ON = 'On'
OFF = 'Off'

def test_NAD_C_356BE():
    receiver = nad_receiver.NADReceiver("/dev/ttyUSB0")
    assert receiver.main_power("?") in (ON, OFF)

    # switch off
    assert receiver.main_power("=", OFF) == OFF
    assert receiver.main_power("?") in (ON, OFF)

    # C 356BE returns "" for other commands when off
    reply = receiver.main_mute("?")
    assert reply is None

    assert receiver.main_power("=", ON) == ON
    assert receiver.main_power("?") == ON

    assert receiver.main_mute("=", OFF) == OFF
    assert receiver.main_mute("?") == OFF

    # Not a feature for this amp
    assert receiver.main_dimmer("?") == None
    # Stepper motor and this thing has no idea about the volume
    assert receiver.main_volume("?") == None

    # No feedback, we must assume this works (it does in practice)
    assert receiver.main_volume("+") == None
    assert receiver.main_volume("-") == None

    # assert receiver.main_ir("=", ???) == None

    # whatever that may be
    assert receiver.main_version("?") == 'V1.02'

    reply = receiver.main_model()
    assert reply == 'C356BEE'

# Here the RS232 NAD manual seems to be slightly off / maybe the model is different
# The manual claims:
# CD Tuner Video Disc Ipod Tape2 Aux
# My Amp:
# CD Tuner Disc/MDC Aux Tape2 MP
    assert receiver.main_source("=", "AUX") == 'AUX'
    assert receiver.main_source("?") == 'AUX'
    assert receiver.main_source("=", "CD") == 'CD'
    assert receiver.main_source("?") == 'CD'
    assert receiver.main_source("+") == 'TUNER'
    assert receiver.main_source("-") == 'CD'
    assert receiver.main_source("+") == 'TUNER'
    assert receiver.main_source("+") == 'DISC/MDC'
    assert receiver.main_source("+") == 'AUX'
    assert receiver.main_source("+") == 'TAPE2'
    assert receiver.main_source("+") == 'MP'
    assert receiver.main_source("+") == 'CD'
    assert receiver.main_source("-") == 'MP'

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
