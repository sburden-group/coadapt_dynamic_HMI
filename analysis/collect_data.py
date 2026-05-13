"""
Amber 11/16/2024: 
This code collects the raw npz files collected from experiment and make it into data arrays. 
Code based on Momona's supportFile2.py
"""
import sys
import os
import glob
import numpy as np
import math as m
from globalVars import *
from scipy import signal
from scipy.interpolate import interp1d

# find npz files for each trial
def findFilename(PATH, subject):
    fis = glob.glob(PATH+'/data/'+subject+'/*.npz')
    fis = [os.path.basename(fi) for fi in fis]

    ids = sorted(list(set([fi.strip('.npz') for fi in fis])))
    #ids = [id for id in ids if ('.csv') not in id[-4:]]
    ids = [id for id in ids if ('rst2') not in id]
    ids = [id for id in ids if ('rst1') not in id]
    ids = [id for id in ids if ('rst0') not in id]
    ids = [id for id in ids if ('react') not in id]
    return ids

# combine all functions to get variables of interest
def getrawdata(PATH,subject):
    listofIDs = findFilename(PATH,subject) # npz file names

    trials = dict()
    for id in listofIDs:
        fis = sorted(glob.glob(PATH+'/data/'+subject+'/'+id+'.npz'))
        if len(fis) > 1:
            dbg('WARNING -- repeated trials for id ='+id)
        assert len(fis) > 0, 'ERROR -- no data for id ='+id
        fi = fis[-1]
        #print('LOAD '+fi)
        trial = dict(np.load(fi,encoding="latin1",allow_pickle=True))
        trials[id] = trial
    
    timedomainvalues = {}
    timedomainvalues[listofIDs[0]] = {}
    times_ = [trials[listofIDs[0]]['time_']]
    refs_  = [trials[listofIDs[0]]['ref_']]
    outs_  = [trials[listofIDs[0]]['out_']]
    inps_  = [trials[listofIDs[0]]['inp_']]
    dists_ = [trials[listofIDs[0]]['dis_']]
    if 'H_' in trials[listofIDs[0]].keys():
        H_ = [trials[listofIDs[0]]['H_']]
        G_ = [trials[listofIDs[0]]['G_']]
        timedomainvalues[listofIDs[0]]['H_'] = np.hstack(H_)
        timedomainvalues[listofIDs[0]]['G_'] = np.hstack(G_)


    timedomainvalues[listofIDs[0]]['times'] = np.hstack(times_)[-N:] # take out first 5 sec
    timedomainvalues[listofIDs[0]]['refs'] = np.hstack(refs_)[-N:]
    timedomainvalues[listofIDs[0]]['outs'] = np.hstack(outs_)[-N:]
    timedomainvalues[listofIDs[0]]['inps'] = np.hstack(inps_)[-N:]
    timedomainvalues[listofIDs[0]]['dists'] = np.hstack(dists_)[-N:]

    for id in listofIDs[1:]:
        times_ = [trials[id]['time_']]
        refs_  = [trials[id]['ref_']]
        outs_  = [trials[id]['out_']]
        inps_  = [trials[id]['inp_']]
        dists_ = [trials[id]['dis_']]
        timedomainvalues[id] = {}
        timedomainvalues[id]['times'] = (np.hstack(times_)[-N:]) # take out first 5 sec
        timedomainvalues[id]['refs']=(np.hstack(refs_)[-N:])
        timedomainvalues[id]['outs']=(np.hstack(outs_)[-N:])
        timedomainvalues[id]['inps']=(np.hstack(inps_)[-N:])
        timedomainvalues[id]['dists']=(np.hstack(dists_)[-N:])
        if 'H_' in trials[id].keys():
            H_ = [trials[id]['H_']]
            G_ = [trials[id]['G_']]
            timedomainvalues[id]['H_'] = np.hstack(H_)
            timedomainvalues[id]['G_'] = np.hstack(G_)
    return timedomainvalues


# get all trial's data for each subject
def get_data(PATH,trial_name):
    time_so = {}
    keys = [trial_name]

    for key in keys:
        print('analyzing data for '+key)
        time_so[key] = getrawdata(PATH,key)
    
    # freq domain
    G_parameters = [] #interface parameters
    Gs = [] #interface
    Hs = [] #human
    Haccs = [] #accumulated human
    Bs = [] #calculated human
    Ds = [] #disturbance
    UHs = [] #human input
    UGs = [] #interface input
    Ys = [] #output
    
    # time domain
    ds = [] #disturbance
    uhs = [] #human input
    ugs = [] #interface input
    ys = [] #output
    errors = [] #time domain errors (MSE per trial)

    for key in keys:
        for i,trial in time_so[key].items():
            outs = trial['outs'][-N:] # cursor output 
            inps = trial['inps'][-N:]
            dists = trial['dists'][-N:] # output disturbance
            OUTS = np.fft.fft(outs)/N
            DISTS = np.fft.fft(dists)/N
            INPS = np.fft.fft(inps)/N
            G = trial['G_']
            H_acc = trial['H_'] # accumulated H

            # find G at 8 stimulated frequencies
            if len(G) == 5: #2nd order
                G_ = second(G)
            elif len(G) == 3: #1st order
                G_ = first(G)
            else: #0th order
                G_ = zero(G)
            # calculate H from exp data
            Tud = DISTS[IX]/INPS[IX] # actually Tdu, but match the name in actual experiment
            # H = -1/(Tud+G_*soM) 
            H = -INPS/OUTS # H = u_H/(-y)

            # find U_G (interface input), G_ was at stimulated frequencies
            UG = INPS * interpolate(G_) #UI = UH * I 
            ug = np.real(np.fft.ifft(UG,axis=0)*N) # time domain (2400,)

            G_parameters.append(G) # freq domain
            Gs.append(G_) # number of parameters
            Hs.append(H)  # freq domain
            Haccs.append(H_acc) # freq domain
            Ds.append(DISTS) # freq domain
            UHs.append(INPS) # freq domain
            UGs.append(UG[IX]) # freq domain
            Ys.append(OUTS) # freq domain
            ds.append(dists)
            uhs.append(inps) # time domain
            ugs.append(ug) # time domain
            ys.append(outs) # time domain
            errors.append(np.sum(abs(outs)**2)) #MSE
    G_parameters = np.asarray(G_parameters)
    Gs = np.asarray(Gs)
    Hs = np.asarray(Hs)
    Haccs = np.asarray(Haccs)
    Ds = np.asarray(Ds)
    UHs = np.asarray(UHs)
    UGs = np.asarray(UGs)
    Ys = np.asarray(Ys)
    ds = np.asarray(ds)
    uhs = np.asarray(uhs)
    ugs = np.asarray(ugs)
    ys = np.asarray(ys) # 11 gains 
    errors = np.asarray(errors)
    return G_parameters,Gs,Hs,Haccs,Ds,UHs,UGs,Ys,ds,uhs,ugs,ys,errors

def interpolate(G):
    G_all = np.zeros(N, dtype=complex)
    G_all[IX] = G # at stimulated frequencies
    G_all[-IX] = np.conjugate(G) # at negative frequencies
    
    # Linear interpolation
    known_indices = np.concatenate([IX, -IX % N])
    known_real = G_all[known_indices].real
    known_imag = G_all[known_indices].imag
    real_interp = interp1d(known_indices, known_real, kind='linear', fill_value="extrapolate")
    imag_interp = interp1d(known_indices, known_imag, kind='linear', fill_value="extrapolate")

    interp_indices = np.setdiff1d(np.arange(N), known_indices)
    G_all[interp_indices] = real_interp(interp_indices) + 1j * imag_interp(interp_indices)
    return G_all

# analyze data for each subject
def analyze(PATH,keys,trialID): 
    #(freq domain)
    G_parameters = [] #interface parameters
    Gs = [] #interface
    Hs = [] #human
    Haccs = [] #accumulated human
    Ds = [] #disturbances 
    UHs = [] #U_H user inputs
    UGs = [] #U_G interface inputs
    Ys = [] #output 
    
    #(time domain)
    ds = [] #disturbances (time domain)
    uhs = [] #U_H user inputs (time domain)
    ugs = [] #U_G interface inputs (time domain)
    ys = [] #output (time domain)
    errors = [] #time domain errors (MSE per trial)

    for key in keys:
        G_parameters_,Gs_,Hs_,Haccs_,Ds_,UHs_,UGs_,Ys_,ds_,uhs_,ugs_,ys_,errors_ = get_data(PATH,key+'/'+key+trialID)
        # Hs.append(Hs_[2::3]) # machine updates every three trials
        # Gs.append(Gs_[2::3])
        Hs.append(Hs_) # machine updates every trials
        Haccs.append(Haccs_)
        Gs.append(Gs_)
        G_parameters.append(G_parameters_)
        Ds.append(Ds_)
        UHs.append(UHs_)
        UGs.append(UGs_)
        Ys.append(Ys_)
        ds.append(ds_)
        uhs.append(uhs_)
        ugs.append(ugs_)
        ys.append(ys_)
        errors.append(errors_)
    G_parameters = np.asarray(G_parameters) # participants x number of trials x number of parameters
    Gs = np.asarray(Gs) # participants x number of updates x number of parameters
    Hs = np.asarray(Hs) # participants x number of updates x number of parameters
    Haccs = np.asarray(Haccs) # participants x number of updates x number of parameters
    Ds = np.asarray(Ds) # participants x number of trials x number of time points
    UHs = np.asarray(UHs) # participants x number of trials x number of time points
    UGs = np.asarray(UGs) # participants x number of trials x number of time points
    Ys = np.asarray(Ys) # participants x number of trials x number of time points
    ds = np.asarray(ds) # participants x number of trials x number of time points
    uhs = np.asarray(uhs) # participants x number of trials x number of time points
    ugs = np.asarray(ugs) # participants x number of trials x number of time points
    ys = np.asarray(ys) # participants x number of trials x number of time points
    errors = np.asarray(errors) # participants x number of trials
    return G_parameters,Gs,Hs,Haccs,Ds,UHs,UGs,Ys,ds,uhs,ugs,ys,errors