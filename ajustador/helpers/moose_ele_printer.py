import moose

def print_moose_ele(model, neuron, ntype=None):
    ''' neuron ->  output of neurons from cell_proto.neuronclasses(model)
        ntype -> 'D1' Provide neuron type to print moose compartment values for
        a single neuron type.
    '''

    if model.calYN and list(model.param_ca_plas.CaShellModeDensity.values())[0]>0:
        catypes = ['DifShell', 'DifBuffer', 'MMPump']

    neur = ntype if ntype else list(neuron.keys())[0]
    print('Compartment')
    if model.calYN and list(model.param_ca_plas.CaShellModeDensity.values())[0]>0:
        catypes = ['DifShell', 'DifBuffer', 'MMPump']
    else:
        catypes=['CaConc']
    print_moose_compartment(neur, 'Compartment', 'HHChannel', catypes)
    print('ZombieCompartment')
    if model.calYN and list(model.param_ca_plas.CaShellModeDensity.values())[0]>0:
        catypes = ['DifShell', 'DifBuffer', 'MMPump']
    else:
        catypes=['ZombieCaConc']
    print_moose_compartment(neur,'ZombieCompartment','ZombieHHChannel', catypes)

def print_moose_compartment(neur, comptype, chantype, catypes):
    for comp in moose.wildcardFind('{}/#[TYPE={}]'.format(neur, comptype)):
        print('comp:',comp.name, 'Rm',comp.Rm, 'Cm=',comp.Cm, 'Ra=', 'tick',comp.tick,'dt',comp.dt, comp.className,'tick')
        for chan in moose.wildcardFind('{}/#[TYPE={}]'.format(comp.path,comptype)): # compartnents
          print ('chan:', chan.name, 'Gbar',chan.Gbar,'X,Y power', chan.Xpower,chan.Ypower,'Ek',chan.Ek, 'class', chan.className,'tick', chan.tick, 'dt',chan.dt)
        chans=[m for m in comp.children if m.className==chantype]
        for chan in chans: # channels
          print ('chan:', chan.name, 'Gbar',chan.Gbar,'X,Y power', chan.Xpower,chan.Ypower,'Ek',chan.Ek, 'class', chan.className,'tick', chan.tick, 'dt',chan.dt)

        for caclass in catypes:
            for pool in moose.wildcardFind('{}/#[TYPE={}]'.format(comp.path, caclass)):
                if 'CaConc' in pool.className:
                    print('CaConc: ',pool.name, pool.className, 'caBasal', pool.CaBasal, 'B', pool.B, 'Tau', pool.tau, 'thickness', pool.thick,'tick',pool.tick, 'dt', pool.dt)
                elif 'DifShell' in pool.className:
                    print('DiffShell: ', pool.name, pool.className, 'Ceq', pool.Ceq,'D', pool.D, 'volume', pool.volume, 'thickness', pool.thickness, 'innerArea', pool.innerArea, 'outerArea', pool.outerArea, 'diameter', pool.diameter,'tick',pool.tick, 'dt', pool.dt)
                elif 'Buffer' in pool.className:
                    print('Buff shell: ', pool.name, pool.className, 'bTot', pool.bTot, 'kb',pool.kb, 'kf',pool.kf, 'D',pool.D,'volume',pool.volume, 'thickness',pool.thickness, 'innerArea',pool.innerArea, 'outerArea',pool.outerArea,'diameter', pool.diameter, 'tick',pool.tick, 'dt', pool.dt)
                else:
                    print ('Pump: ', pool.name, pool.className, 'tick', pool.tick,'dt', pool.dt, 'kd', pool.kd, 'Vmax', pool.Vmax)


    for solve in moose.wildcardFind('{}/#[TYPE={}]'.format(neur,'HSolve')):
      print ('HSolve: ', solve.name,'caMax', solve.caMax,'caMin', solve.caMin,'tick', solve.tick, 'dt', solve.dt)
