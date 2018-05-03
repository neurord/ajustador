import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from importlib import reload
import glob
import anal_util as au  #must be in FrontNeuroinf subdir for this to work
plt.ion()

pattern='/home/avrama/moose/gp_opt/*8/*.npz'
#pattern='/home/avrama/moose/SPN_opt/*8/*.npz'
fnames=glob.glob(pattern)
#list SPN fits since there are multiple ones

#separating them into classes is not necessary for outputting SAS files
#type1_names=[f for f in fnames if 'D1' in f]
#type2_names=[f for f in fnames if 'D2' in f]

type1_names=[f for f in fnames if 'arky' in f]
type2_names=[f for f in fnames if 'proto' in f]

#only return the best %tile of samples
tile=0.025

######## process all examples of one type, combine into one dataframe and list of data frames
type1df,type1df_list=au.combined_df(type1_names,tile)

######## process all examples of other type, combine into list of data frames
type2df,type2df_list=au.combined_df(type2_names,tile)

############## write total fitness to text file for plotting fit history
allcelldf,all_cells=au.combined_df(fnames,1.0)
fit_len=[np.shape(x)[0] for x in all_cells]
min_fit=min(fit_len)
#one file for all fits of same length
same_fits=[i for i,j in enumerate(fit_len) if j==min_fit]
fitness=np.zeros((min_fit,len(same_fits)))
for i in range(len(same_fits)):
    fitness[:,i]=all_cells[same_fits[i]].loc[0:min_fit,'total'].values
head=[all_cells[i].loc[:,'cell'].values[0] for i in same_fits]
fname=pattern.split('/')[0]+'_fitness.txt'
np.savetxt(fname,fitness,delimiter=',',header=' '.join(head),newline='\n')

#write separate files for longer fit histories
long_fits=[i for i,j in enumerate(fit_len) if j>min_fit]
for i in range(len(fit_len)):  #long_fits:
    long_fit_data=all_cells[i].loc[:,'total'].values
    fname=all_cells[i].loc[0,'cell']+'_fitness.txt'
    head=[all_cells[i].loc[:,'cell'].values[0]+'total']
    np.savetxt(fname,long_fit_data,delimiter=',',header=' '.join(head),newline='\n')
    
########## correlation among all columns for all of one type or other type
sig=0.0001
corrthresh=0.7
for celldf in [type1df,type2df]:
    corr,pvalues=au.calculate_pvalues(celldf)
    sig_list=au.create_sig_list(pvalues,corr,sig,corrthresh)
    print(celldf.loc[:,'cell'].values[0])
    for item in sig_list:
      print(item)
    varlist=au.create_var_list(sig_list)
    pd.plotting.scatter_matrix(celldf.loc[:,varlist])

#############output for SAS or for plotting in Igor
## note only outputting last 50 for each to make sure same number of samples for each cell

for celldf,fn in zip(type1df_list,type1_names):
    head=list(celldf.columns)
    fname=fn.split('/')[1]+str(tile)+'.txt'
    celldf[-50:].to_csv(fname, header=True, index=None,sep=',', mode='w')

for celldf,fn in zip(type2df_list,type2_names):
    head=list(celldf.columns)
    fname=fn.split('/')[1]+str(tile)+'.txt'
    celldf[-50:].to_csv(fname, header=True, index=None,sep=',', mode='w')

