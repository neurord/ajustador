import moose

def print_moose_ele(neuron, ntype=None):
    ''' neuron ->  output of neurons from cell_proto.neuronclasses(model)
        ntype -> 'D1' Provide neuron type to print moose compartment values for
        a single neuron type.
    '''
    comptype='Compartment'
    chantype='HHChannel'
    catype='CaConc'
    print('Compartment')
    neur = ntype if ntype else list(neuron.keys())[0]
    print(neur)
    for comp in moose.wildcardFind('{}/#[TYPE={}]'.format(neur, comptype)):
          print('comp:',comp.name, 'Rm',comp.Rm, 'Cm=',comp.Cm, 'Ra=', 'tick',comp.tick,'dt',comp.dt, comp.className,'tick')
          for chan in moose.wildcardFind('{}/#[TYPE={}]'.format(comp.path,comptype)):
              print ('chan:', chan.name, 'Gbar',chan.Gbar,'X,Y power', chan.Xpower,chan.Ypower,'Ek',chan.Ek, 'class', chan.className,'tick', chan.tick, 'dt',chan.dt)
          chans=[m for m in comp.children if m.className==chantype]
          for chan in chans:
              print ('chan:', chan.name, 'Gbar',chan.Gbar,'X,Y power', chan.Xpower,chan.Ypower,'Ek',chan.Ek, 'class', chan.className,'tick', chan.tick, 'dt',chan.dt)
          capools=[m for m in comp.children if m.className==catype]
          for pool in capools:
              print ('pool:', pool.name, pool.CaBasal,pool.B,pool.tau,pool.thick,'class', pool.className,'tick', pool.tick, 'dt',pool.dt)
    for solve in moose.wildcardFind('{}/#[TYPE={}]'.format(neur,'HSolve')):
      print ('HSolve: ', solve.name,'caMax', solve.caMax,'caMin', solve.caMin,'tick', solve.tick, 'dt', solve.dt)

def print_moose_zele(neuron, ntype=None):
    ''' neuron ->  output of neurons from cell_proto.neuronclasses(model)
        ntype -> 'D1' Provide neuron type to print moose compartment values for
        a single neuron type.
    '''
    comptype='ZombieCompartment'
    chantype='ZombieHHChannel'
    catype='ZombieCaConc'
    print('ZombieCompartment')
    neur=neur = ntype if ntype else list(neuron.keys())[0]
    print(neur)
    for comp in moose.wildcardFind('{}/#[TYPE={}]'.format(neur, comptype)):
          print('comp:',comp.name, 'Rm',comp.Rm, 'Cm=',comp.Cm, 'Ra=', 'tick',comp.tick,'dt',comp.dt, comp.className,'tick')
          for chan in moose.wildcardFind('{}/#[TYPE={}]'.format(comp.path,comptype)):
              print ('chan:', chan.name, 'Gbar',chan.Gbar,'X,Y power', chan.Xpower,chan.Ypower,'Ek',chan.Ek, 'class', chan.className,'tick', chan.tick, 'dt',chan.dt)
          chans=[m for m in comp.children if m.className==chantype]
          for chan in chans:
              print ('chan:', chan.name, 'Gbar',chan.Gbar,'X,Y power', chan.Xpower,chan.Ypower,'Ek',chan.Ek, 'class', chan.className,'tick', chan.tick, 'dt',chan.dt)
          capools=[m for m in comp.children if m.className==catype]
          for pool in capools:
              print ('pool:', pool.name, pool.CaBasal,pool.B,pool.tau,pool.thick,'class', pool.className,'tick', pool.tick, 'dt',pool.dt)
    for solve in moose.wildcardFind('{}/#[TYPE={}]'.format(neur,'HSolve')):
      print ('HSolve: ', solve.name,'caMax', solve.caMax,'caMin', solve.caMin,'tick', solve.tick, 'dt', solve.dt)
