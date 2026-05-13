import numpy as np

def fo(t,x,u,d=None):
  """
  first-order
  """
  q = x
  dq = u
  if d is not None:
    dq += d
  return np.asarray([dq])

def so(t,x,u,d=None):
  """
  second-order
  """
  # TODO make this compatible with natural frequency
  b = 1.0
  q,dq = x
  ddq = u
  if d is not None:
    ddq += d
  return np.asarray([dq,ddq - b*dq])

def gain_machine(t,uH,uG,G,n,m): #0th order interface 
  """
  machine intervention for just gain
  G = constant
  """

  output_G = G*uH
  return output_G


def higher_order_machine(t,uH,uG,G,n,m,order): # AMBER: updated 1st or 2nd order interface
  """
  machine intervention
  # 1st order machine
  G = a, b0, b1 
  output: uG[t] = - a*uG[t-1] + b0*uH[t] + b1*uH[t-1]

  G = a0, a1, b0, b1, b2 # 2nd order machine
  output = uG[t] = - a0*uG[t-1] - a1*uG[t-2] + b0*uH[t] + b1*uH[t-1] + b2*uH[t-2]
  """
  # AMBER: added order condition for an extra b coefficient
  if order == 2: # 2nd order interface 
    a = np.asarray(G[:2]) # coeff of denominators (2), a0, a1
    b = np.asarray(G[-3:]) # coeff of numberators (3), b0, b1, b2
  else: # 1st order interface
    a = np.asarray([G[0]]) # coeff of denominators (1), a # make it 1d array for dot product
    b = np.asarray(G[-2:]) # coeff of numberators (2), b0, b1

  if len(uG) < n or len(uH) < m: #n = how many a; m = how many b
    return 0 #uH[-1]
  else:
    output_G = -a.dot(np.flip(np.asarray(uG),axis=0)) + b.dot(np.flip(np.asarray(uH),axis=0))
    #AMBER's note: np.flip so that the first element is the most recent (uH[t], uH[t-1], uH[t-2])
    return output_G #this is u_I[t] 

def machine(t,uH,uG,G,n,m): # previous code for 1st and 2nd order interface 
  """
  machine intervention
  G = a1, a2, b # 1st order machine
  G = a1, a2, a3, b1, b2 # 2nd order machine
  output = - a2[0]*u2[t-1] - a2[1]*u2[t-2] - a2[2]*u1[t-3] \
                + b2[0]*u1[t-1] + b2[1]*u1[t-2]
  """
  a = np.asarray(G[:-1])
  b = np.asarray(G[-1])

  if len(uG) < n or len(uH) < m:
    return 0 #uH[-1]
  else:
    output_G = -a[1:].dot(np.flip(np.asarray(uG[-n:]),axis=0)) + b.dot(np.flip(np.asarray(uH[-m:]),axis=0))
    return output_G

def zd11(t,x,u,d=None):
  """
  first-order system dynamics
  first-order zero dynamics

  dxi = u
  dzeta = -c * (xi - zeta)
  """
  c = -1.
  x1,x2 = x
  return np.asarray([ u - c*x2, u + c*x2 ])

def zd12(t,x,u,d=None): # USE THIS ONE!
  """
  first-order system dynamics
  second-order zero dynamics

  dxi = u
  ddzeta = c_1 (xi-zeta) + c_2 dzeta
  """
  c1, c2 = -1.,-1.
  xi,zeta,dzeta = x
  #return np.asarray([ u, dzeta, c1*zeta + c2*dzeta ])
  return np.asarray([ u, dzeta, -c1*(xi-zeta) + c2*dzeta ])

  #c1, c2 = -1.,-1.
  #x1,x2,x3 = x
  #return np.asarray([ u + x3, u - x3, c1*x2 + c2*x3 ])
