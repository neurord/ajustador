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
    # TODO add testing code.
    '''@Unittest: proper split of channel settings string.
    '''
    from ajustador.regulate_chan_kinetics import chan_setting
    assert chan_setting('NaF,vshift,X=123.4') == ('NaF', 'vshift', 'X', 123.4)

class TestTauMultiplier(object):
	def test_x_gate_taumul(self):
	    # TODO add testing code.
	    from ajustador.regulate_chan_kinetics import scale_voltage_dependents_tau_muliplier
	    assert chan_setting(sample) == #something

	def test_y_gate_taumul(self):
	    # TODO add testing code.
	    from ajustador.regulate_chan_kinetics import scale_voltage_dependents_tau_muliplier
	    assert chan_setting(sample) == #something

	def test_z_gate_normal_taumul(self):
	    # TODO add testing code.
	    from ajustador.regulate_chan_kinetics import scale_voltage_dependents_tau_muliplier
	    assert chan_setting(sample) == #something

	def test_z_gate_special_taumul(self):
	    # TODO add testing code.
	    from ajustador.regulate_chan_kinetics import scale_voltage_dependents_tau_muliplier
	    assert chan_setting(sample) == #something

class TestVshiftMembrane(object):
	def test_x_gate_vshift():
	    # TODO add testing code.
	    from ajustador.regulate_chan_kinetics import offset_voltage_dependents_vshift
	    assert chan_setting(sample) == #something

	def test_y_gate_vshift():
	    # TODO add testing code.
	    from ajustador.regulate_chan_kinetics import offset_voltage_dependents_vshift
	    assert chan_setting(sample) == #something

	def test_z_gate_normal_ca_shift():
	    # TODO add testing code.
	    from ajustador.regulate_chan_kinetics import offset_voltage_dependents_vshift
	    assert chan_setting(sample) == #something

	def test_z_gate_special_ca_shift():
	    # TODO add testing code.
	    from ajustador.regulate_chan_kinetics import offset_voltage_dependents_vshift
	    assert chan_setting(sample) == #something
