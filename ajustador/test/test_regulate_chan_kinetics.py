'''
@Description: Unit test script for channel voltage depenends kinetics parameters.
@Package: ajustador
@Module: regulate_chan_kinetics.py
@Test command: $python3 -m pytest test_regulate_chan_kinetics.py -v
@Author: Sri Ram Sagar Kappagantula
@email: k.sriramsagar@gmail.com
@date: 21st JUN, 2018.
'''

def test_chan_setting():
    '''@Test: proper split of channel settings string.
    '''
    from ajustador.regulate_chan_kinetics import chan_setting
    assert chan_setting('NaF,vshift,X=123.4') == ('NaF', 'vshift', 'X', 123.4)

