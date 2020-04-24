"""
Commands and operators used by NAD.

CMDS[domain][function]
"""
CMDS = {
    'main':
        {
            'dimmer':
                {'cmd': 'Main.Dimmer',
                 'supported_operators': ['+', '-', '=', '?']
                 },
            'mute':
                {'cmd': 'Main.Mute',
                 'supported_operators': ['+', '-', '=', '?']
                 },
            'power':
                {'cmd': 'Main.Power',
                 'supported_operators': ['+', '-', '=', '?']
                 },
            'volume':
                {'cmd': 'Main.Volume',
                 'supported_operators': ['+', '-', '=', '?']
                 },
            'ir':
                {'cmd': 'Main.IR',
                 'supported_operators': ['=']
                 },
            'listeningmode':
                {'cmd': 'Main.ListeningMode',
                 'supported_operators': ['+', '-']
                 },
            'sleep':
                {'cmd': 'Main.Sleep',
                 'supported_operators': ['+', '-']
                 },
            'source':
                {'cmd': 'Main.Source',
                 'supported_operators': ['+', '-', '=', '?']
                 },
            'SpeakerA':
                {'cmd': 'Main.SpeakerA',
                 'supported_operators': ['+', '-', '=', '?']
                 },
            'SpeakerB':
                {'cmd': 'Main.SpeakerB',
                 'supported_operators': ['+', '-', '=', '?']
                 },
            'tape1':
                {'cmd': 'Main.Tape1',
                 'supported_operators': ['+', '-', '=', '?']
                 },
            'version':
                {'cmd': 'Main.Version',
                 'supported_operators': ['?']
                 },
            'model':
                {'cmd': 'Main.Model',
                 'supported_operators': ['?']
                 },
        },
    'tuner':
        {
            'am_frequency':
                {'cmd': 'Tuner.AM.Frequency',
                 'supported_operators': ['+', '-']
                 },
            'am_preset':
                {'cmd': 'Tuner.AM.Preset',
                 'supported_operators': ['+', '-', '=', '?']
                 },
            'band':
                {'cmd': 'Tuner.Band',
                 'supported_operators': ['+', '-', '=', '?']
                 },
            'fm_frequency':
                {'cmd': 'Tuner.FM.Frequency',
                 'supported_operators': ['+', '-']
                 },
            'fm_mute':
                {'cmd': 'Tuner.FM.Mute',
                 'supported_operators': ['+', '-', '=', '?']
                 },
            'fm_preset':
                {'cmd': 'Tuner.FM.Preset',
                 'supported_operators': ['+', '-', '=', '?']
                 }
        }
}
