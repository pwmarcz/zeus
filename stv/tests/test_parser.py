from stv.parser import STVParser

# The sample is completely nonsensical and serves only to cover the
# STVParser well.

SAMPLE = '''\
^THRESHOLD 11
~ZOMBIES 7 = 0.0;1
@ROUND 1
.COUNT 5 = 10;6 = 10;7 = 10;8 = 10
*RANDOM 5 from ['5', '6'] to -ELIMINATE
-ELIMINATE 5 = 10
@ROUND 2
.COUNT 6 = 20.0
+ELECT 6 = 20.0
!QUOTA 6 = 0.
~ZOMBIES 7 = 0.0;1
>TRANSFER from 6 to 7 2*3.5=7.0
'''

def test_parse():
    parser = STVParser(SAMPLE)
    rounds = list(parser.rounds())
    assert rounds == [
        (None, {'candidates': {7: {'actions': [], 'votes': '0.0'}}}),
        (1,
         {'candidates': {5: {'actions': [('random', (5, [5, 6], '-ELIMINATE')),
                                         ('eliminate', (5, '10'))],
                             'votes': '10'},
                         6: {'actions': [('random', (5, [5, 6], '-ELIMINATE'))],
                             'votes': '10'},
                         7: {'actions': [], 'votes': '10'},
                         8: {'actions': [], 'votes': '10'}}}),
        (2,
         {'candidates': {6: {'actions': [('elect', (6, 20.0)),
                                         ('quota', (6, '0.'))],
                             'votes': '20.0'},
                         7: {'actions': [('transfer', [7, 6, '2', '3.5', '7.0'])],
                             'votes': '0.0'}}}),
    ]
