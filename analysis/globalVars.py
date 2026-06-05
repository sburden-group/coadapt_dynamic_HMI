import numpy as np
import math as m
from scipy import signal
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import sys
import os
import glob
import importlib
import numpy as np
import pylab as plt
import matplotlib
import math as m
from matplotlib import rc
import sys
from scipy.optimize import curve_fit
import seaborn as sns
# from supportFile2 import findFFT,plotThingsEO,findFilename,geterr #Momona's code for even and odd trials
# from collect_data import findFilename, getrawdata, get_data, analyze
fmts = ['svg','pdf']
import pandas as pd
from scipy.stats import wilcoxon, ttest_rel, friedmanchisquare, shapiro
import pickle as pickle
from scipy import signal, fft
from scipy import stats
font = {'family' : 'DejaVu Sans',
        'weight' : 'bold',
        'size'   : 12}
matplotlib.rc('font', **font)
takeAvgBA = True
prop_cycle = plt.rcParams['axes.prop_cycle']
python_colors = prop_cycle.by_key()['color'] # python default color cycle

N = 2400 #length of time points
primes = np.asarray([2, 3, 5, 7, 11, 13, 17,19])# max =37
IX = primes*2 #stimulated frequencies index = np.round(freqs * N / sample_rate).astype(int)
base_freq = 0.05
freqs = primes*base_freq # stimulated frequencies
omegas = 2*np.pi*freqs
T = 40 # 40 seconds trial
t = np.linspace(0, T, N) #time vector
fs = 60 #game sampling rate, update rate 60 Hz
dt = 1./fs #sample period
xf_all = np.fft.fftfreq(N, 1./ fs)       #freq (x-axis) both + and - terms, shape (N,)
xf = np.fft.fftfreq(N, 1./ fs)[:N//2]    #freq (x-axis) positive-frequency terms, shape (N//2,)
s = lambda omega: 1j*omega # in continuous time, s = jw
z = lambda omega: np.exp(1j*omega*dt) # AMBER: in discrete time, z = exp(jwT)

# M IS -2(s-2.2)/(s^2+3.6s+4)
a = np.array([1,3.6,4])
b = np.array([-2,4.4])
dt = 1./60
num, den, dt = signal.cont2discrete((b,a),dt)
num = num[0]

# continuous time machine IS -2(s-2.2)/(s^2+3.6s+4)
M = -2*(s(omegas)-2.2)/(s(omegas)**2+3.6*s(omegas)+4)
# diecrete time machine transfer function
soM = (num[1]*z(omegas) + num[2])/(z(omegas)**2+den[1]*z(omegas)+den[2])

def zero(G):
    b = G
    return np.asarray([b for omega in omegas])

def first(G):
    a,b0,b1= G[0],G[1],G[2]  # I = (b0*z+b1)/(z+a)
    return np.asarray([(b0*z(omega) + b1) / (z(omega)+a) for omega in omegas])

def second(G):
    a0, a1, b0, b1, b2 = G[0],G[1],G[2],G[3],G[4] #I = (b0*z^2+b1z+b2)/(z^2+a0z+a1)
    return np.asarray([(b0*(z(omega)**2) + b1*z(omega) + b2) / (z(omega)**2 + a0*z(omega) + a1) for omega in omegas])

condition_orders = ['0th','1st','2nd']

# random disturbance signal
def polar2rec(A):
    P = np.random.rand(len(A))*2*np.pi
    return A*np.cos(P) + 1j*A*np.sin(P)
amps = 0.5*(1/primes)*(0.5/primes).sum() 
D = polar2rec(amps) # freq domain at stim freqs
D_all = np.zeros(N,dtype = complex) 
D_all[IX] = D
D_all[-IX] =  np.conjugate(D)
d = np.real(np.fft.ifft(D_all)*N) # time domain disturbance signal