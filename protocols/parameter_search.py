import numpy as np
import scipy.signal as signal

# find range of parameters a0, a1 for the discrete system for 2nd orfder interface
def zero_order_interfaces(N_grid = 100):
    G_find = list(np.linspace(0.05,2.,N_grid))
    return G_find

def first_order_interfaces(N_grid = 10):
    wc = 2*np.pi*np.linspace(0.15,0.65,N_grid) #crossover frequency is 0.25Hz

    # low pass filter: wc/(s + wc)
    b0s = 0
    b1s = np.linspace(0.05,wc[-1],N_grid)
    a0s = wc
    A0, B0, B1 = np.meshgrid(a0s, b0s, b1s)
    G_find_low = []
    G_find_low.append(A0.flatten())
    G_find_low.append(B0.flatten())
    G_find_low.append(B1.flatten())
    G_find_low = np.asarray(G_find_low)

    # high pass filter:  s/(s + wc)
    b0s = np.linspace(0.05,wc[-1],N_grid)
    b1s = 0
    a0s = wc
    A0, B0, B1 = np.meshgrid(a0s, b0s, b1s)
    G_find_high = []
    G_find_high.append(A0.flatten())
    G_find_high.append(B0.flatten())
    G_find_high.append(B1.flatten())
    G_find_high = np.asarray(G_find_high)

    # join the two
    G_find_global = np.concatenate((G_find_low,G_find_high),axis=1)

    # convert to discrete time transfer function
    dt = 1./60
    G_find_dis = []
    for i in range(G_find_global.shape[1]):
        a = np.array([1,G_find_global[0,i]])
        if np.isclose(G_find_global[1,i],0, atol=1e-14):
            b = np.array([G_find_global[2,i]])
        else:
            b = np.array([G_find_global[1,i],G_find_global[2,i]])
        num, den, dt = signal.cont2discrete((b,a),dt)
        num = num[0]
        G_find_dis.append(np.array([den[1],num[0],num[1]])) # in discrete time domain
    G_find_dis = np.asarray(G_find_dis).T

    # keep the G that makes DC gain >= 0 (when z = 1), so the game is not inverted
    DCgain = np.sum(G_find_dis[1:,:],axis=0) / (1 + G_find_dis[0,:]) #numerator_value / denominator_value
    G_find = G_find_dis[:,DCgain>=0]
    return G_find

def second_order_interfaces(N_grid = 10):
    wc = 2*np.pi*np.linspace(0.15,0.65,N_grid) #crossover frequency is 0.25Hz
    zetas = np.linspace(0.5,1,N_grid) #Butterworth damping ratio

    # low pass filter: wc**2/(s**2 + 2*damp*wc*s + wc**2)
    b0s = 0
    b1s = np.linspace(0,wc[-1]**2,N_grid)
    b2s = wc**2
    a0s = 2*np.outer(wc, zetas).ravel()
    a1s = wc**2
    A0, A1, B0, B1, B2 = np.meshgrid(a0s, a1s, b0s, b1s, b2s)
    G_find_low = []
    G_find_low.append(A0.flatten())
    G_find_low.append(A1.flatten())
    G_find_low.append(B0.flatten())
    G_find_low.append(B1.flatten())
    G_find_low.append(B2.flatten())
    G_find_low = np.asarray(G_find_low)

    # high pass filter: s**2/(s**2 + 2*damp*wc*s + wc**2)
    b0s = np.linspace(0.05,2.,N_grid)
    b1s = np.linspace(0,wc[-1]**2,N_grid)
    b2s = 0
    a0s = 2*np.outer(wc, zetas).ravel()
    a1s = wc**2
    A0, A1, B0, B1, B2 = np.meshgrid(a0s, a1s, b0s, b1s, b2s)
    G_find_high = []
    G_find_high.append(A0.flatten())
    G_find_high.append(A1.flatten())
    G_find_high.append(B0.flatten())
    G_find_high.append(B1.flatten())
    G_find_high.append(B2.flatten())
    G_find_high = np.asarray(G_find_high)

    # combine the two
    G_find_global = np.concatenate((G_find_low,G_find_high),axis=1)

    # convert to discrete time transfer function
    dt = 1./60
    G_find_dis = []
    for i in range(G_find_global.shape[1]):
        a = np.array([1,G_find_global[0,i],G_find_global[1,i]])
        if np.isclose(G_find_global[2,i],0, atol=1e-14):
            if np.isclose(G_find_global[3,i],0, atol=1e-14):
                b = np.array([G_find_global[4,i]])
            else:
                b = np.array([G_find_global[3,i],G_find_global[4,i]])
        else:
            b = np.array([G_find_global[2,i],G_find_global[3,i],G_find_global[4,i]])
        num, den, dt = signal.cont2discrete((b,a),dt)
        num = num[0]
        G_find_dis.append(np.array([den[1],den[2],num[0],num[1],num[2]])) # in discrete time domain
    G_find_dis = np.asarray(G_find_dis).T

    # keep the G that makes DC gain >= 0 (when z = 1), so the game is not inverted
    DCgain = np.sum(G_find_dis[2:,:],axis=0) / (1 + np.sum(G_find_dis[:2,:],axis=0)) #numerator_value / denominator_value
    G_find = G_find_dis[:,DCgain>=0]
    return G_find


def set_of_a_parameters(N=100):
    # grid parameter a, find the a that satisfies the condition (i.e. makes the poles within 0.5~1.5)
    grid_a0 = np.linspace(-5,5,N)
    grid_a1 = np.linspace(-5,5,N)
    # I = (b0*s**2+b1*s+b2)/(s**2+a0*s+a1)
    parameter_a0_discrete = []
    parameter_a1_discrete = []
    eigens = []
    for a0 in grid_a0:
        for a1 in grid_a1:
            den = np.array([1,a0,a1])
            eigenvalues = np.roots(den)
            if np.all(np.abs(eigenvalues)<=1): # stable or marginally stable
                parameter_a0_discrete.append(den[1])
                parameter_a1_discrete.append(den[2])
                eigens.append(eigenvalues)

    parameter_as = np.array([parameter_a0_discrete,parameter_a1_discrete]).T
    return parameter_as 