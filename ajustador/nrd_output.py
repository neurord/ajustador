#!/usr/bin/python
# -*- coding:utf-8 -*-

r"""
Wrapper which makes reading neurord HDF5 output easier to use

>>> from neurord.output import Output
>>> out = Output('model.h5')

Units: concentrations are expressed in nM and volumes in cubic microns.
So, in these units, one Litre is 10¹⁵ and a 1M solution is 10⁹.
The conversion factor between concentrations and particle number is therefore

.. math::
    N = 6.022…\cdot10²³ \times V/10¹⁵ \times c/10⁹

i.e.

.. math ::
    c = N / 0.6022… / V
"""

from __future__ import print_function, division, unicode_literals

import operator
import enum
import math
import tables
import h5py
import functools
import numpy as np
import pandas as pd
from lxml import etree
import os
from ajustador.nrd_fitness import basal as nrd_basal
from ajustador.nrd_fitness import peak as nrd_peak

AVOGADRO = 6.02214179
"""Avogadro constant from CODATA 2006"""
PUVC = AVOGADRO / 10
"""Converts concentrations to particle numbers"""

def nrd_output_conc(sim_output,specie):
    #may need to add specification of trial and/or voxel
    df=sim_output.population
    specie_index=df.index.names.index('specie')
    voxel_index=df.index.names.index('voxel')
    #print('type',type(df),'size',len(df),'columns',df.columns)
    #print('index',df.index.names,'which level',specie_index)
    pop1count = df.xs(specie,level=specie_index)
    volumes=sim_output.vols
    tot_vol=np.sum(volumes)
    pop1conc=pop1count.sum(axis=0,level=voxel_index)/tot_vol/PUVC  #sum across voxels, level=0 sums across time
    return pop1conc

def decode_species_names(array):
    return list(sp.decode('utf-8') for sp in array)

class EventType(enum.IntEnum):
    """Event types matching IGridCalc.EventType enumeration"""
    REACTION = 0
    DIFFUSION = 1
    STIMULATION = 2

class EventKind(enum.IntEnum):
    """Event types matching IGridCalc.EventKind enumeration"""
    EXACT = 0
    LEAP = 1

class Dependencies(object):
    """Raw information about the dependency graph

    >>> out = Output('model.h5')
    >>> deps = out.model.dependencies
    >>> for t, e, d, dep in zip(deps.types(),
    ...                         deps.elements(),
    ...                         deps.descriptions(),
    ...                         deps.dependent()):
    ...     print('type {} in voxel {} "{}" dependent: {}'.format(t, e[0], d, dep))
    type 0 in voxel 0 "Reaction el.0 A+B→C" dependent: [1]
    type 0 in voxel 0 "Reaction el.0 2×C→D" dependent: [2]
    type 0 in voxel 0 "Reaction el.0 D→2×C" dependent: [1]
    type 2 in voxel 0 "Stimulation el.0 B" dependent: [0]
    """
    def __init__(self, element):
        self._element = element

    def indices(self):
        "Numbers of the elements"
        return range(self._element['descriptions'].shape[0])

    def descriptions(self):
        "A generator of descriptions of nodes (by index)"
        # pytables bug?
        for row in self._element['descriptions'][:]:
            yield row.decode('utf-8')

    def elements(self):
        """The numbers of voxels events are attached to

        In case of diffusion, those are the originating voxels.
        """
        return self._element['elements']

    def types(self):
        # pytables bug?
        for row in self._element['types'][:]:
            yield EventType(row)
    '''
    def dependent(self):
        "A generator of lists of dependent nodes (by index)"
        # pytables bug?
        for row in self._element.dependent[:]:  #doesn't exist!!!
            yield list(n for n in row if n >= 0)
    '''
class Reactions(object):
    """Raw information about reactions

    >>> out = Output('model.h5')
    >>> reactions = out.model.reactions
    >>> list(reactions.reactants())
    [[0, 1], [2], [3]]
    >>> list(reactions.reactant_stoichiometry())
    [[1, 1], [2], [1]]
    >>> list(reactions.products())
    [[2], [3], [2]]
    >>> list(reactions.product_stoichiometry())
    [[1], [1], [2]]
    >>> list(reactions.rates())
    [1.0000000000000001e-05, 9.9999999999999995e-07, 1.0000000000000001e-05]
    """
    def __init__(self, element):
        self._element = element

    def reactants(self):
        "A generator of lists of reactants (by index)"
        for row in self._element['reactants'][:]:
            yield list(n for n in row if n >= 0)
 
    def reactant_stoichiometry(self):
        "A generator of lists of stoichiometries (by index)"
        for row in self._element['reactant_stoichiometry'][:]:
            yield list(n for n in row if n >= 0)

    def products(self):
        "A generator of lists of products (by index)"
        for row in self._element['products'][:]:
            yield list(n for n in row if n >= 0)

    def product_stoichiometry(self):
        "A generator of lists of stoichiometries (by index)"
        for row in self._element['product_stoichiometry'][:]:
            yield list(n for n in row if n >= 0)

    def rates(self):
        "Rates of the reactions"
        return self._element['rates']

    def reversible_pairs(self):
        """Mapping to reverse reactions

        For reaction i which has a reverse reaction, reversible_pairs()[i]
        gives the index of the reverse reaction. Reactions which do not have
        a reverse are not included.
        """
        indices = self._element['reversible_pairs']
        mapping = {i:indices[i] for i in range(len(indices))
                   if indices[i] >= 0}
        return mapping

class Model(object):
    """Information about the model, same for all trials
    """
    def __init__(self, element):
        self._element = element
        try:
            self.dependencies = Dependencies(self._element['events'])
        except KeyError as e:
            self.dependencies = None
        self.reactions=Reactions(self._element['reactions'])

    def species(self, indices=None):
        """List of specie names

        Species are order the same as in other tables, so this table can be used to map species
        indices to actual names.

        >>> model = Output('model.h5').model
        >>> model.species()
        ['A', 'B', 'C', 'D']
        """
        what = self._element['species'][indices] if indices is not None else self._element['species']
        return decode_species_names(what)

    def grid(self):
        """Voxels of the simulation

        Returns an recarray containing points defining the voxels and their volumes and regions.

        >>> model = Output('model.h5').model
        >>> grid = model.grid()

        >>> import textwrap
        >>> names = grid.dtype.names
        >>> print(textwrap.fill(' '.join(names), width=40))
        x0 y0 z0 x1 y1 z1 x2 y2 z2 x3 y3 z3
        volume deltaZ label region type group

        >>> grid.volume
        array([ 2.])

        """
        #return np.array(self._element['grid'])
        return self._element['grid'][:].view(np.recarray)
        
    def volumes(self):
        grid = self.grid()
        #volume_index=grid.dtype.names.index('volume')
        #volume=[e[volume_index] for e in grid[:]]
        #return volume
        return grid.volume

    def element_regions(self):
        "Names of regions of elements (by index)"
        #region_index=self.element['grid'].dtype.names.index('region')
        #region_nums=[grid[region_index] for grid in element['grid']]
        regions = np.array(self.region_names())
        return regions[self.grid().region]
        #return regions[region_nums]

    def indices(self):
        "Numbers of the elements"
        return range(self._element['grid'].shape[0])

    def neighbors(self):
        "A generator of lists of neighboring nodes (by index)"
        # pytables bug?
        for row in self._element['neighbors'][:]:
            yield list(n for n in row if n >= 0)

    def couplings(self):
        "A generator of coupling strengths to neighboring nodes (by index)"
        coupl = self._element['couplings']
        for i, neigh in enumerate(self.neighbors()):
            yield list(coupl[i][:len(neigh)])

    def region_names(self, indices=None):
        "Region names (by index)"
        what = self._element['regions'][indices] if indices is not None else self._element['regions']
        return [row.decode('utf-8') for row in what]

    def output_group(self, name='__main__'):
        if name == '__main__':
            try:
                group = self._element['output']
            except KeyError:
                # fall back to old tree
                element = self._element
            else:
                element = group[name]
        else:
            # no fallback
            element = self._element['output'][name]

        return ModelOutputGroup(element, self)

class ModelOutputGroup(object):
    def __init__(self, element, model):
        self._element = element
        self._model = model

    def species(self, indices=None):
        """List of species in this output group

        Species are ordered the same as in other output tables, so this table can be
        used to map species indices to actual names.

        >>> output_model = Output('model.h5').model.output_group('__main__')
        >>> output_model.species()
        ['A', 'B', 'C', 'D']
        """
        what = self._element['species'][indices] if indices is not None else self._element['species']
        return decode_species_names(what)

    def elements(self):
        """List of element indices in this output group
        """
        try:
            return self._element['elements'][:] #indices of elements
        except KeyError: # FIXME nothing called dependencies.
            grid = self._model.grid()
            element_labels=[r.decode('utf-8') for r in grid.labels]
            return range(len(element_labels))
            #return self._element['dependencies']['elements'][:]

    def volumes(self):
        """Volumes of elements in this output group
        """
        elements = self.elements()
        grid = self._model.grid()
        #volume_index=grid.dtype.names.index('volume')
        #volumes=[e[volume_index] for e in grid[:]]
        volumes = grid[elements].volume
        return volumes

class OutputGroup(object):
    def __init__(self, element, output_model):
        self._element = element
        self._output_model = output_model

    def times(self):
        times = self._element['times'][:] #file['trial0']['output']['__main__']['times']
        diff = times[1] - times[0]
        return np.round(times, decimals=max(-math.floor(math.log10(diff)), 0))

    def counts(self):
        try:
            data = self._element['population'][:] #file['trial0']['output']['__main__']['population']
        except KeyError:
            # fall back to old tree
            data = self._element['concentrations'][:]
        ''' Panel depracated
        panel = pd.Panel(data.read(),  #(times,voxel,species, e.g. (501,3,7)
                         items=self.times(),
-                         major_axis=self._output_model.elements(),
-                         minor_axis=self.species())
        frame = panel.transpose(2, 1, 0).to_frame()
        #transpose: items=species, major=voxels,minor=times
        #to_frame: columns=item = species; index = majoraxis + minor axis = voxels+times
        '''
        voxels=self._output_model.elements()
        assert len(voxels)==np.shape(data)[1]
        assert len(self.times())==np.shape(data)[0]
        data2D=data.T.reshape(len(self.species()),len(voxels)*len(self.times()))
        # above: transpose to species 1st, e.g. (7,3,501), then reshape to ((7,1503);
        # below: transpose to (times/voxels) as rows and species as columns
        frame=pd.DataFrame(data2D.T,columns=self.species(), 
                           index=pd.MultiIndex.from_product([voxels,self.times()]))
        frame.index.names = ['voxel', 'time']
        #print('######### OutputGroup.counts frame',frame)
        return frame

    def concentrations(self):
        "Counts converted to concentrations using voxel volumes"
        counts = self.counts(output_group)
        volumes = self._output_model.volumes() * PUVC
        print('######### OutputGroup.concs volumes,counts.index, .size',volumes,counts.index, counts.index.size)
        # blow up volumes to match the size of the counts index
        volumes = np.repeat(volumes, counts.index.size/volumes.size)
        ans = counts.divide(volumes, axis=0)
        ans.rename(columns={'count':'concentration'}, inplace=1)
        return ans

    def species(self):
        """List of specie names present in this output group
        """
        return self._output_model.species()

class Simulation(object):
    """Information about the results of a trial
    """
    def __init__(self, node, element, model):
        #print('** Simulation: element',element,'model',model)
        self._element = element #file['trial0']
        self.number = int(node[5:])
        self.model = model

    def config(self):
        """lxml etree of de-serialized config the simulation was run with

        Accessing serialized config

        >>> out = Output('model.h5')
        >>> xml = out.simulation(0).config()
        >>> xml
        <Element {http://stochdiff.textensor.org}SDRun at 0x...>
        >>> xml.find('./ns:geometry', {'ns':'http://stochdiff.textensor.org'}).text
        '2D'
        """

        xml = self.model.model['serialized_config']
        # FIXME: overwrite seed?
        return etree.fromstring(xml.read()[0])

    @functools.lru_cache()
    def output_group(self, name='__main__'):
        if name == '__main__':
            try:
                group = self._element['output']
            except KeyError:
                # fall back to old tree
                element = self._element['simulation']
            else:
                element = group[name]
        else:
            # no fallback
            element = self._element['output'][name]
        return OutputGroup(element, self.model.output_group(name))

    def times(self, output_group='__main__'):
        return self.output_group(output_group).times()

    def counts(self, output_group='__main__'):
        return self.output_group(output_group).counts()

    def concentrations(self, output_group='__main__'):
        return self.output_group(output_group).concentrations()

    def events(self):
        "A full history of events"  #no longer included
        times = self._element.events.times[:]
        waited = self._element.events.waited[:]
        original = self._element.events.original_wait[:]
        events = self._element.events.events[:]
        extents = self._element.events.extents[:]
        kinds = self._element.events.kinds[:]
        df = pd.DataFrame(dict(time=times,
                               waited=waited,
                               original=original,
                               event=events,
                               extent=extents,
                               kind=kinds))
        df.set_index('time', inplace=True)
        return df.reindex_axis('waited original event kind extent'.split(), axis=1)

class Output(object):
    """The output for a single model, 0 or more experiments

    >>> out = Output('model.h5')
    """
    def __init__(self, filename,stim_time):
        #self.file = tables.open_file(filename)
        self.file=h5py.File(filename,mode='r')
        try:
            #element = self.file.root.model
            element=self.file['model']
        except KeyError:
            #element = self.file.root.trial0.model
            element=self.file['trial0']['model']
        self.model = Model(element)
         #add injection to object to allow aju.drawing to work,
        #and also to allow set of files with different stimulation
        fname=os.path.basename(filename)
        if '-' in fname:
            fname_parts=fname.split('-')
            self.injection=fname_parts[-1].split('.h5')[0]
            #print('Extracting injection',filename,fname,fname_parts,self.injection)
        else:
            self.injection=0

        self.vols=self.model.volumes()
        self.specie_names=self.model.species()
        self.population=self.counts()
        self.stim_time=stim_time
        self.norm=None
        self._attributes = {'injection':self.injection,'stim_time':stim_time}

    ########## Basal and peak, as well as imports, can probably be deleted #########
    def basal(self,mol):
        conc=nrd_output_conc(self,mol)
        start,base=nrd_basal(conc.index.values,conc.values,self.stim_time)
        return {'stim_pt':start,'basal':base}
        
    def peak(self,mol):
        conc=nrd_output_conc(self,mol)
        start,base=nrd_basal(conc.index.values,conc,self.stim_time)
        peaktime,peak=nrd_peak(conc.index.values,conc.values,start)
        return {'peaktime':peaktime,'peak':peak}
        
    def __getattr__(self, name):
        if name != '_attributes' and name in self._attributes:
            return getattr(self._attributes[name], name)
        raise AttributeError(name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.file.close()

    def simulation(self, num):
        """Get simulation by number

        >>> out = Output('model.h5')
        >>> sim = out.simulation(0)
        >>> sim.number
        0
        >>> sim.config()
        <Element {http://stochdiff.textensor.org}SDRun at 0x...>
        """
        #trial = self.file.get_node('/trial{}'.format(num))
        trial = self.file['/trial{}'.format(num)]
        return Simulation(trial, self.model)

    @functools.lru_cache()
    def simulations(self):
        #print('********** self.file',self.file)
        nodes = self.file.keys() #self.file.list_nodes('/')
        sims = [Simulation(node, self.file[node], self.model) for node in nodes
                if node.startswith('trial')]
        sims.sort(key=operator.attrgetter('number'))
        return sims

    @functools.lru_cache()
    def counts(self, output_group='__main__'):
        """Aggregated table of particle counts

        >>> out = Output('model.h5')
        >>> counts = out.counts()
        >>> counts.head(1)
                                 count
        voxel time specie trial       
        0     0.0  A      0       1264

        Calculate average over trials

        >>> gb = counts.groupby(level='voxel time  specie'.split())
        >>> gb.mean().head(1)
                             count
        voxel time specie         
        0     0.0  A       1264.63

        Calculate mean and standard deviation

        >>> import numpy as np
        >>> gb.aggregate([np.mean, np.std]).head(3)
                             count          
                              mean       std
        voxel time specie                   
        0     0.0  A       1264.63  0.485237
                   B       1204.51  0.502418
                   C          0.00  0.000000
        """
        sims = self.simulations()
        #sims.counts executes OutputGroup.counts
        '''  using Panel, which has been deprecated
        #returns df with rows=times*voxels and columns = species
        data = dict((i, sim.counts(output_group))
                    for (i, sim) in enumerate(sims))
        #print('******* Output.counts, data dict',data)
        panel = pd.Panel(data) 
        series = panel.to_frame().stack()
        series.index.names = 'voxel time specie trial'.split()
        #items = i (sim number), major axis=species, minor axis=times*voxels?
        #to_frame combines major and minor axis into multi-index
        #stack reshape dataframe with mutli-index
        '''
        #sim.counts(output_group).stack() produces series with multi-index=[voxel time species]
        #need to add another level to multiindex which is sim number
        #### FIXME: trial is now before specie - may cause problems????
        alldf=[]
        for (i,sim) in enumerate(sims):
            df=sim.counts(output_group)
            newdf=df.assign(trial=i).set_index('trial',append=True)
            alldf.append(newdf.stack())
        series=pd.concat(alldf)
        series.index.names = 'voxel time trial specie'.split() 
        frame = pd.DataFrame(dict(count=series))
        return frame

    @functools.lru_cache()
    def concentrations(self, output_group='__main__'):
        """Counts converted to concentrations using voxel volumes

        >>> out = Output('model.h5')
        >>> out.counts().head(1)
                                 count
        voxel time specie trial       
        0     0.0  A      0       1264
        >>> out.concentrations().head(1)
                                 concentration
        voxel time specie trial               
        0     0.0  A      0        1049.460511
        """
        counts = self.counts(output_group)
        volumes = self.model.volumes()*PUVC
        #print('******* Output.conc volumes:', volumes)#,'\noutput counts',counts)
        new_vols=np.repeat(volumes, counts.index.size/volumes.size)
        #print('******* Output.conc new_vols', np.shape(new_vols), np.shape(counts))
        ans=counts.divide(new_vols, axis=0)
        #ans = counts / volumes.sum() / PUVC
        ans.rename(columns={'count':'concentration'}, inplace=1)
        return ans

    def volumes(self, output_group='__main__'):
        volumes = self.model.volumes()
        return volumes
    
    @functools.lru_cache()
    def events(self):
        "A log of events from all simulations"
        sims = self.simulations()
        data = dict((i, sim.events())
                    for (i, sim) in enumerate(sims))
        return pd.concat(data)
