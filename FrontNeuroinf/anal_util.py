import pandas as pd
import numpy as np
from scipy.stats import pearsonr

def load_npz(fname, tile):
    dat = np.load(fname)
    
    param = pd.DataFrame(list(dat['params']), columns=list(dat['paramnames']))
    
    print(param.columns, "FEATURES", dat['features'], len(dat['features'])) #names of columns
    #param.describe() #summary statistics
    #features=[feat.split('=')[0][0:-8] for feat in dat['features'][0:-1]]
    
    #THE TOTAL FEATURE IS 3RD FROM THE END
    
    features = [feat.split('=')[0] for feat in dat['features'][0:-3]]
    #treat last feature (total) differently because has neither = nor 'fitness'
    #features.append(dat['features'][-1].split(':')[0])
    
    features.append(dat['features'][-3].split(':')[0])
    
    print("FEATURES")
    print(features)
    
    #print("FITVALUES")
    #print(dat["fitvals"], "LENGTH", len(dat["fitvals"]), len(dat["fitvals"][0]))
    
    fit=pd.DataFrame(dat['fitvals'], columns=features)
    
    #print("FEATURES AND THEIR VALUES")
    #print(fit)
    
    fit.columns #names of columns
    #fit.describe() #summary statistics

    fit_param=pd.concat([param,fit],axis=1)

    thresh=fit_param.quantile(tile)['total'] #values of 10th percentile
    goodsamples=fit_param[fit_param['total']<thresh]
    goodsamples["neuron"] = dat['features'][-1].split("=")[1]
    goodsamples["model"] = dat['features'][-2].split("=")[1]
    
    print('cell', fname, 'percentile', tile, 'threshold', thresh, 'samples',len(goodsamples),'from',len(fit_param))
    return goodsamples,features

############## 
def calculate_pvalues_2file(df1,df2):
    #df1 is rows, df2 is columns
    pvalues = pd.DataFrame(index=df1.columns, columns=df2.columns)
    corr = pd.DataFrame(index=df1.columns, columns=df2.columns)
    for r in df1.columns:
        for c in df2.columns:
            if not (r == 'cell' or c == 'cell'):
                corr.loc[r,c] = round(pearsonr(df1[r], df2[c])[0], 4)
                pvalues.loc[r,c] = pearsonr(df1[r], df2[c])[1]
    return corr, pvalues

def calculate_pvalues(df1):
    df1_clean = df1.dropna()
    pvalues = pd.DataFrame(columns=df1_clean.columns,index=df1_clean.columns)
    corr=pd.DataFrame(columns=df1_clean.columns,index=df1_clean.columns)
    for i,r in enumerate(df1_clean.columns):
        for c in df1_clean.columns[i+1:]:
            if not (r == 'cell' or c == 'cell'):
                corr.loc[r,c] = round(pearsonr(df1_clean[r], df1_clean[c])[0], 4)
                pvalues.loc[r,c] = pearsonr(df1_clean[r], df1_clean[c])[1]
    return corr, pvalues

#extract only thoses correlations greater than some value (0.5) with sig> value
def create_sig_list(pvalues,corr,sigthresh,corrthresh):
    sig_list=[]
    for i in pvalues.index:
        for j in pvalues.columns:
            if (i != j and pvalues.loc[i,j] < sigthresh and corr.loc[i,j]*corr.loc[i,j]>corrthresh):
                sig_list.append([i,j,corr.loc[i,j]])
    return sig_list

#extract list of variables for scatter plot
def create_var_list(sig_list):
    varlist=[]
    for item in sig_list:
        varlist.append(item[0])
        varlist.append(item[1])
    return np.unique(varlist)

#combined cells into single df
def combined_df(fnames, tile, neurtype):
    df_list = []
    columnList = []
    for fn in fnames:
        cellname = fn.split('.')[0]
        good, features = load_npz(fn,tile)
        good['cell'] = cellname
        good["neurtype"] = neurtype
        
        df_list.append(good)
    
    columnList = []
    for df in df_list:
        columnList.append(set(df.columns))
        print(len(df.columns))
    commonCol = set.intersection(*columnList)
    commonCol = list(commonCol)
    print(len(commonCol))
    
    '''columnSet = set(df_list[0].columns)
    for index in range(1, len(df_list)):
        currSet = set(df_list[index].columns)
        columnSet = columnSet.intersection(currSet)
    print(columnSet)
    columnList = list(columnSet)'''
    
    for df in df_list:
        df = df[commonCol]
    
    ## join multiple dataFrames, e.g. join all the proto together    
    
    alldf=pd.concat(df_list)    
    
    #print(alldf)
    #print(alldf.columns)
        
    return alldf, df_list


