  #!/usr/bin/python

import warnings
warnings.filterwarnings("error")

import sys
import os
import glob
import time
import serial
import serial.tools.list_ports
import importlib
import random
from scipy import signal
import copy
from scipy.optimize import minimize
import pickle
import numpy as np
import pygame
from protocols.globalsPython3 import *
from lib.sliderPython3 import sliderUSB as slider

args = sys.argv

help = """
usage:
  experiment subject protocol [port]

data will be stored in
  data/subject

print available serial ports by running
  lib/print_serial
"""

if len(args) < 2:
  print ('\nABORT -- no subject specified')
  print (help)
  sys.exit(0)

if len(args) < 3:
  print ('\nABORT -- no protocol specified')
  print (help)
  sys.exit(0)

subject = args[1]
protocol = args[2]

subject_dir = os.path.join('data',subject)

# debugging
def dbg(s):
  print(s)

#COM_PORT = 'COM9'
#COM_PORT = '/dev/cu.usbmodem141131' # Sam home
#COM_PORT = '/dev/cu.usbmodem141111' # Sam office
COM_PORT = None
if len(args) >= 4:
  COM_PORT = args[3]
elif 0:
  arduinoPorts = [p.device
    for p in serial.tools.list_ports.comports()
    if 'Arduino' in p.description
  ]
  COM_PORT = arduinoPorts[0]


if COM_PORT is None:
  print ('WARN -- COM_PORT is None, using keyboard for input')
else:
  try:
    joy = slider(port=COM_PORT)
  except:
    print ('ABORT -- slider not detected at COM_PORT =',COM_PORT)
    sys.exit(0)

  dbg('COM_PORT='+COM_PORT)
  joy.startArduino()

if not os.path.exists(subject_dir):
  os.mkdir(subject_dir)

from protocols import dynamics
proto = importlib.import_module('protocols.'+protocol)

trial_gen = proto.trial_gen(subject,protocol)

# --- helper functions for output to command line and graphical display

# draw rectangle using frame-relative (x,y) coordinates
def draw_rect(scr, col, sizes, thk):
  x,y,w,h = sizes
  c,r = xy2px([[x,y]],size,SC)[0]
  cw,rh = xy2px([[x+w,y+h]],size,SC)[0]
  #return pygame.draw.rect(scr,col,(c,r,int(SC*w),int(SC*h)),int(SC*thk))
  return pygame.draw.rect(scr,col,(c,r,cw-c,rh-r),int(SC*thk))

def draw_circle(scr, col, sizes, r, thk):
  x,y = sizes
  px = xy2px([[x,y]],size,SC)[0]
  return pygame.draw.circle(scr,col,px,int(SC*r),int(SC*thk))

def draw_lines(scr, col, clo, pts, thk):
  pxs = xy2px(pts,size,SC)
  return pygame.draw.lines(scr,col,clo,pxs,int(SC*thk))

#def draw_line(scr, col, start_pos, end_pos, thk):
#  pxs = xy2px(pts,size,SC)
#  return pygame.draw.line(scr,col,start_pos,end_pos,pxs,int(SC*thk))

def draw_polygon(scr, col, pts, thk):
  pxs = xy2px(pts,size,SC)
  return pygame.draw.polygon(scr,col,pxs,int(SC*thk))

def draw_ref(scr, col, pts, thk):
  #return pygame.draw.lines(scr,WHITE,False,xy2px(pts,size,SC),10)
  pts = np.array(pts)
  diff = np.diff(pts,axis=0)
  perp = np.dot(diff,np.asarray([[0,1],[-1,0]]))
  nml = perp / np.sqrt(np.sum(perp**2,axis=1))[:,np.newaxis]
  pts_u = pts[:-1] + .2*thk * nml
  pts_d = pts[:-1] - .2*thk * nml
  pxs = xy2px(np.vstack((pts_u,pts_d[::-1])),size,SC)
  return pygame.draw.polygon(scr,col,pxs,0)

class Point:
  # constructed using a normal tuple
  def __init__(self, point_t = (0,0)):
    self.x = float(point_t[0])
    self.y = float(point_t[1])
  # define all useful operators
  def __add__(self, other):
    return Point((self.x + other.x, self.y + other.y))
  def __sub__(self, other):
    return Point((self.x - other.x, self.y - other.y))
  def __mul__(self, scalar):
    return Point((self.x*scalar, self.y*scalar))
  def __div__(self, scalar):
    return Point((self.x/scalar, self.y/scalar))
  def length(self):
    return int(np.sqrt(self.x**2 + self.y**2))
  # get back values in original tuple format
  def get(self):
      return (self.x, self.y)

def draw_dashed_line(surf, color, start_pos, end_pos, width=1, dash_length=10):
  origin = Point(xy2px([start_pos],size,SC)[0])
  target = Point(xy2px([end_pos],size,SC)[0])
  displacement = target - origin
  length = displacement.length()
  slope = displacement/length

  for index in range(0, length/dash_length, 2):
    start = origin + (slope *    index    * dash_length)
    end   = origin + (slope * (index + 1) * dash_length)
    pygame.draw.line(surf, color, start.get(), end.get(), width)

def datestring(t=None,sec=False):
  """
  Datestring

  Inputs:
    (optional)
    t - time.localtime()
    sec - bool - whether to include sec [SS] in output

  Outputs:
    ds - str - date in YYYYMMDD-HHMM[SS] format

  by Sam Burden 2012
  """
  if t is None:
    import time
    t = time.localtime()

  ye = '%04d'%t.tm_year
  mo = '%02d'%t.tm_mon
  da = '%02d'%t.tm_mday
  ho = '%02d'%t.tm_hour
  mi = '%02d'%t.tm_min
  se = '%02d'%t.tm_sec
  if not sec:
    se = ''

  return ye+mo+da+'-'+ho+mi+se

# --- set up graphical display window

# global variables
FULLSCREEN = False
#FULLSCREEN = True

REACT_NUM = 0

if FULLSCREEN:
  flags = pygame.FULLSCREEN #| pygame.DOUBLEBUF
else:
  os.environ['SDL_VIDEO_CENTERED'] = '1'
  os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d'%(0,0)
  flags = pygame.RESIZABLE #| pygame.DOUBLEBUF
screen = pygame.display.set_mode(size,flags)
screen.set_alpha(None)
fader = pygame.Surface(size, pygame.SRCALPHA)
pygame.display.set_caption("hcps v0.1")
pygame.event.set_allowed([pygame.QUIT,
                          pygame.KEYDOWN,
                          pygame.KEYUP,
                          pygame.VIDEORESIZE,
                          pygame.MOUSEBUTTONDOWN,
                          pygame.MOUSEBUTTONUP,
                         ])
pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS',30)
done = False
clock = pygame.time.Clock()

# --- variables and functions for ship and reference


oldrects = []

def rescale_inp(inp,MIN=SLIDER_MIN,MAX=SLIDER_MAX):
  return 2 * ( (inp - MIN) / (MAX - MIN) - .5) # rescale to [-1,1]

try:
  trial = trial_gen.__next__()
  if not ALLOW_DUPLICATES:
    while len(glob.glob(os.path.join(subject_dir,'*'+protocol+'_'+str(trial['id'])+'.npz'))) > 0:
      dbg('SKIP subject='+subject_dir+'; protocol='+protocol+'_'+str(trial['id']))
      trial = trial_gen.__next__()
    dbg('RUN subject='+subject_dir+'; protocol='+protocol+'_'+str(trial['id']))
except StopIteration:
  done = True

trial_run = trial

trial_reset = dict(duration=np.inf,
                   id=trial['id'],
                   scale=.5,
                   init=[0.],
                   dis=lambda t,x,_ : 0.,
                   out=lambda x : x[0],
                   ref=lambda t,_ : 0.*np.asarray(t),
                   vf='fo',
                   RAND_TIME=random.uniform(0,REACT_TIME-2.),
                   RAND_POINT=random.uniform(-.5,.5))

def init(trial):
  state = trial['init']
  steps = 0
  _time = steps * STEP
  time_ = [_time]
  realtime_ = [time.time()]
  state_ = [state] # y,y_dot
  inp_ = [inp(time_[-1],state_[-1])] #u_H human input
  dis_ = [trial['dis'](time_[-1],trial,state_[-1])] # distrubance
  out_ = [trial['out'](state)] #cursor position
  ref_ = [trial['ref'](time_[-1],trial)*SC_REF] # reference
  mach_ = list(np.zeros(n2,)) #u_I interface input
  return state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_,mach_

def save(sfx='',csv=True,**trial_data):
  di = subject_dir
  id = str(trial['id'])
  fi = protocol+'_'+id+sfx
  if glob.glob(os.path.join(di,'*'+fi+'.npz')):
    dbg('WARN -- trial repeated')
  ds = datestring(sec=True)
  fi = ds+'_'+fi
  dbg('SAVE '+os.path.join(di,fi))
  np.savez(os.path.join(di,fi),filename=fi,**trial_data) #TODO check to see if this is working
  #if not sfx:
  #  err = np.sqrt(np.mean((np.asarray(trial_data['ref_'])-np.asarray(trial_data['state_']))**2))
  #  print(err)
  if csv:
    time = trial_data['time_']
    realtime = trial_data['realtime_']
    ref = trial_data['ref_']
    inp = trial_data['inp_']
    dis = np.asarray(trial_data['dis_']).flatten()
    state = np.asarray(trial_data['state_'])
    if 'H_' in trial_data.keys():
      Hsave = np.zeros(np.asarray(time).shape,dtype=complex)
      Gsave = np.zeros(np.asarray(time).shape)
      Hsave[:len(trial_data['H_'])] = trial_data['H_']
      Gsave[:len(trial_data['G_'])] = trial_data['G_']
      mach = np.asarray(trial_data['mach_'])[-len(inp):]
      d = np.vstack((time,realtime,ref,inp,dis,state.T,mach,Hsave,Gsave)).T

    else:
      d = np.vstack((time,realtime,ref,inp,dis,state.T)).T
    np.savetxt(os.path.join(di,fi)+'.csv',d,delimiter=',',
               header='\n'.join(10*['']+['time,realtime,ref,inp,dis,state1,state2,machine_out,human,machine']),fmt='%s')

def savereact(sfx='',csv=True,**trial_data):
  di = subject_dir
  id = str(trial['id'])
  fi = protocol+'_'+id+sfx
  if glob.glob(os.path.join(di,'*'+fi+'.npz')):
    dbg('WARN -- trial repeated')
  ds = datestring(sec=True)
  fi = ds+'_'+fi
  dbg('SAVE '+os.path.join(di,fi))
  np.savez(os.path.join(di,fi),filename=fi,**trial_data) #TODO check to see if this is working
  #if not sfx:
  #  err = np.sqrt(np.mean((np.asarray(trial_data['ref_'])-np.asarray(trial_data['state_']))**2))
  #  print(err)
  if csv:
    time = trial_data['time_']
    realtime = trial_data['realtime_']
    ref = trial_data['ref_']
    inp = trial_data['inp_']
    reacttime = np.ones((len(time),))*trial_data['reacttime']
    reactpoint = np.ones((len(time),))*trial_data['reactpoint']
    dis = np.asarray(trial_data['dis_']).flatten()
    state = np.asarray(trial_data['state_'])
    d = np.vstack((time,realtime,ref,inp,dis,state.T,reacttime,reactpoint)).T
    np.savetxt(os.path.join(di,fi)+'.csv',d,delimiter=',',
               header='\n'.join(10*['']+['time,realtime,ref,inp,dis,state,reacttime,reactpoint...']))

# STUFF FOR MACHINE GAME
N = 2400 #length of time points
primes = np.asarray([2, 3, 5, 7, 11, 13, 17,19])# max =37
IX = primes*2 #stimulated index [ 4,  6, 10, 14, 22, 26, 34, 38] = np.round(freqs * N / sample_rate).astype(int)
# freq = np.linspace(0,599.5,1200)#refs.shape[0]/2)
amps = 0.5*(1/primes)*(0.5/primes).sum() # amplitude of disturbance signal
base_freq = 0.05
freqs = primes*base_freq
omegas = 2*np.pi*freqs
sample_rate = 60
sample_period = 1./sample_rate
s = lambda omega: 1j*omega # in continuous time, s = jw
z = lambda omega: np.exp(1j*omega*sample_period) # AMBER: in discrete time, z = exp(jwT)

# M IS s/(s^2 + s)
# a = np.array([1, 1, 0]) # s^2 + s + 0
# b = np.array([1])

# non-min phase M IS -2(s-2.2)/(s^2+3.6s+4)
a = np.array([1,3.6,4])
b = np.array([-2,4.4])

dt = 1./60
num, den, dt = signal.cont2discrete((b,a),dt)
num = num[0]

soM = (num[1]*z(omegas) + num[2])/(z(omegas)**2+den[1]*z(omegas)+den[2])
n2 = int(1) # how many a 
m2 = int(2) # how many b 

def zero(G):
    b = G[0]
    return np.asarray([b for omega in omegas])

def first(G):
    a,b0,b1= G[0],G[1],G[2]  # I = (b0*z+b1)/(z+a)
    return np.asarray([(b0*z(omega) + b1) / (z(omega)+a) for omega in omegas])

def second(G):
    a0, a1, b0, b1, b2 = G[0],G[1],G[2],G[3],G[4] 
    return np.asarray([(b0*(z(omega)**2) + b1*z(omega) + b2) / (z(omega)**2 + a0*z(omega) + a1) for omega in omegas])

# random disturbance signal
def polar2rec(A):
    P = np.random.rand(len(A))*2*np.pi
    return A*np.cos(P) + 1j*A*np.sin(P)
amps = 0.5*(1/primes)*(0.5/primes).sum() 

# AMBER: GRID SEARCH FOR 1st order G's parameters (b0*z+b1)/(z+a) 
# intial interface for 2-norm cost
with open('protocols/global_search_interfaces_2norm_cost.pkl', 'rb') as file:
    # global_search_interfaces = [G_star0, G_star1, G_star2, zero_order_Gs, first_order_Gs, second_order_Gs]
    _,G_init,_, _,G_find,_ = pickle.load(file)
# if using 2-norm cost: global_search_interfaces_2norm_cost.pkl
# if using inf-norm cost: global_search_interfaces_infnorm_cost.pkl  

passthrough = proto.passthrough # is it passthrough interface, true or false
self_defined_init = proto.self_defined_init # allow user to self defined initial machine, true or false
num_trials = proto.num_trials # total number of trials
countN_trials = 1 

# Initialization Interface G
if self_defined_init:
  user_input = input("Type in the last machine (eg 0 0 1); press enter to randomize: ")
  if user_input == "":
      import datetime
      dtnow = datetime.datetime.now()
      seq = int(dtnow.strftime("%Y%m%d%H%M%S"))
      # np.random.seed(seq%1000)
      temp_ = np.random.randint(0,len(G_find.T),(1,))
      G_est = np.squeeze(G_find[:,temp_])#[0,0,1.]#[0,0,1] # CHANGE THIS MANUALLY
  else:
      input_string = user_input.split()
      G_est = np.zeros((3,))
      for ix,xx in enumerate(input_string):
          G_est[ix] = float(xx)
else:
  if passthrough: 
      G_est = np.array([0,0,1]) #baseline interface = 1
  else:
      G_est = G_init # initial interface
print('initial G: ',G_est)

def loss(H, G):
    D = polar2rec(amps) # D = disturbance (freq) at stim freqs
    # D_all = np.zeros(N,dtype = complex) 
    # D_all[IX] = D
    # D_all[-IX] =  np.conjugate(D)
    # d = np.real(np.fft.ifft(D_all)*N) # time domain disturbance signal, shape = (2400,)

    G_ = first(G) # I = (b0*z+b1)/(z+a) # shape = (8,N*N*N)
    # DIST = D[IX]
    Y = [D[f]/(1+soM[f]*G_[f]*H[f]) for f in range(len(soM))] # when d is output disturbnace, Y = D/(1+MIH)
    Y = np.asarray(Y) #a function of G, shape = (8,100)

    # interface input and human input
    UH = [-Y[f]*H[f] for f in range(len(soM))] #U_H = -Y*H, (freq domain)
    UG = [-Y[f]*H[f]*G_[f] for f in range(len(soM))] #U_I = -Y*H*I, (freq domain)
    UH = np.asarray(UH) #a function of G, shape = (8,100)
    UG = np.asarray(UG)  #a function of G, shape = (8,100)

    # # create all freq domain signal of length N from stimulated freqs
    # N_reduce = N//2 #nyquist_frequency = sampling rate / 2 # N = 2400 timestamps
    # frequency_domain_y = np.zeros((N_reduce, Y.shape[1]), dtype=complex)
    # frequency_domain_uG = np.zeros((N_reduce, UG.shape[1]), dtype=complex)
    # frequency_domain_uH = np.zeros((N_reduce, UH.shape[1]), dtype=complex)
    # frequency_domain_y[IX, :] = Y # Assign values at stimulated frequencies
    # frequency_domain_uG[IX, :] = UG
    # frequency_domain_uH[IX, :] = UH
    # frequency_domain_y[-IX, :] = np.conjugate(frequency_domain_y[IX, :]) #conjugate symmetric part (negative freqs)
    # frequency_domain_uG[-IX, :] = np.conjugate(frequency_domain_uG[IX, :])
    # frequency_domain_uH[-IX, :] = np.conjugate(frequency_domain_uH[IX, :])

    # # inf norm loss
    # # IFFT and scale by N
    # y = np.real(np.fft.ifft(frequency_domain_y, axis=0) * N_reduce) #time_domain_y # shape = (2400,100)
    # uG = np.real(np.fft.ifft(frequency_domain_uG, axis=0) * N_reduce) #time_domain_uG # shape = (2400,100)
    # uH = np.real(np.fft.ifft(frequency_domain_uH, axis=0) * N_reduce) #time_domain_uH # shape = (2400,100)

    # # max {||y||_inf, lamG*||u_g||_inf, lamH*||u_h||_inf} / ||d||_inf in time domain
    # lamH = 0.3 #Hyperparameter for tradeoff between interface effort and human effort
    # lamG = 0.3
    # losses = np.maximum(np.maximum(np.max(abs(y),axis=0),lamG * np.max(abs(uG),axis=0)),lamH * np.max(abs(uH),axis=0)) / np.max(abs(d),axis=0) 
    # #np.maximum: element-wise maxima

    # 2-norm loss
    lamH = 1.5 #Hyperparameter for tradeoff between interface effort and human effort
    lamG = 0.5
    losses = np.sum(abs(Y)**2,axis=0) + lamH*np.sum(abs(UH)**2,axis=0) + lamG*np.sum(abs(UG)**2,axis=0)

    return losses

# -- initialize system
if COM_PORT is None:
  inp = lambda time,state : 0.
else:
  inp = lambda time,state : rescale_inp(joy.grabData()[1])
#
TRIAL_STATE = 'reset1'
trial = trial_reset
# DEBUG
#TRIAL_STATE = 'run'
#trial = trial_run
#
state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_,mach_ = init(trial)

# runge-kutta numerical integration assuming constant input
def rk_(vf,t,x,u,d=None,dt=1.):
  dx1 = vf( t, x, u, d ) * dt
  dx2 = vf( t+.5*dt, x+.5*dx1, u, d ) * dt
  dx3 = vf( t+.5*dt, x+.5*dx2, u, d ) * dt
  dx4 = vf( t+dt, x+dx3, u, d ) * dt
  dx = (1./6.)*( dx1 + 2*dx2 + 2*dx3 + dx4 )
  return x + dx


if PLOT:
  plt.ion()

  fig = plt.figure(1,figsize=(size[0]/100,size[1]/100))
  plt.clf()
  plt.grid('on'); plt.axis('equal')
  plt.xlim(RNG[:,0])
  plt.ylim(RNG[:,1])


# ---- game loop

while not done:
  # only handle events every SLIDER_SPT ticks
  if steps % SLIDER_SPT == 0:
    # --- handle events (keyboard / mouse input)
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        dbg("QUIT")
        done = True
      elif event.type == pygame.VIDEORESIZE:
        size = list(event.size)
        if ORIENTATION == 'portrait':
          WIDTH = size[0]
          size = (WIDTH,RATIO*WIDTH)
          SC = float(WIDTH) # modify SC to change lookahead
          SCi = WIDTH
          RNG = np.asarray(px2xy([[0.,0.],size],size,SC))
          SC_REF = (RNG[1,0]-RNG[0,0])
        else:
          HEIGHT = size[0]/RATIO
          size = (RATIO*HEIGHT,HEIGHT)
          SC = float(HEIGHT)
          SCi = HEIGHT
          RNG = np.asarray(px2xy([[0.,0.],size],size,SC))
          SC_REF = (RNG[1,1]-RNG[0,1])
        screen = pygame.display.set_mode(size,pygame.RESIZABLE)
        fader = pygame.Surface(size, pygame.SRCALPHA)
        dbg("RESIZE %s"%str(size))
      elif event.type == pygame.KEYDOWN:
        #dbg("KEYDOWN")
        if event.key in [pygame.K_SPACE,pygame.K_p]:
          if PAUSE:
            dbg("UNPAUSE")
          if not PAUSE:
            dbg("PAUSE")
          PAUSE = not PAUSE
        elif event.key == pygame.K_RIGHT:
          dbg("RIGHT")
          inp = lambda time,state : +ACCEL
        elif event.key == pygame.K_LEFT:
          dbg("LEFT")
          inp = lambda time,state : -ACCEL
        elif event.key == pygame.K_DOWN:
          dbg("DOWN")
          inp = lambda time,state : 0.
        elif event.key == pygame.K_g:
          pass
        elif event.key == pygame.K_f:
          if FULLSCREEN:
            screen = pygame.display.set_mode(size,pygame.RESIZABLE)
            FULLSCREEN = False
          else:
            screen = pygame.display.set_mode(size,pygame.FULLSCREEN)
            FULLSCREEN = True
        elif event.key == pygame.K_s and COM_PORT is not None:
          inp = lambda time,state : rescale_inp(joy.grabData()[1])
        elif event.key == pygame.K_r:
          # cmt = raw_input("> why reject? ")
          save(time_=time_,realtime_=realtime_,state_=state_,
               inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,
               sfx="_rej",cmt=cmt)
          trial = trial_reset
          state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_,mach_ = init(trial)
        elif event.key in [pygame.K_q,pygame.K_ESCAPE]:
          dbg("QUIT")
          done = True
      #elif event.type == pygame.KEYUP:
      #  #dbg("KEYUP")
      #  if event.key in [pygame.K_LEFT,pygame.K_RIGHT]:
      #    dbg("0.")
      #    inp = lambda time,state : 0.
      elif event.type == pygame.MOUSEBUTTONDOWN:
        pass
        #dbg("MOUSEBUTTONDOWN")
      elif event.type == pygame.MOUSEBUTTONUP:
        pass
        #dbg("MOUSEBUTTONUP")

  _inp = inp(time_[-1],state_[-1])
  _dis = trial['dis'](time_[-1],trial,state_[-1])

  if not PAUSE:
    # duration
    if TRIAL_STATE == 'run' and _time + SHIP_SHIFT > trial['duration']:

      # OBTAIN ESTIMATE OF HUMAN H
      trials = dict()
      fis = glob.glob(subject_dir+'\\*.npz')
      fis = [os.path.basename(fi) for fi in fis]
      ids = sorted(list(set([fi.strip('.npz') for fi in fis])))
      ids = [id for id in ids if ('rst2') not in id]
      ids = [id for id in ids if ('rst1') not in id]
      ids = [id for id in ids if ('rst0') not in id]
      ids = [id for id in ids if ('react') not in id]

      listofIDs = ids
      trials = dict()
      for id in listofIDs:
          fis = sorted(glob.glob(os.path.join(subject_dir,id+'.npz')))
          if len(fis) > 1:
              dbg('WARNING -- repeated trials for id ='+id)
          assert len(fis) > 0, 'ERROR -- no data for id ='+id
          fi = fis[-1]
          trials[id] = dict(np.load(fi,encoding="latin1",allow_pickle=True))
      countN_trials = len(listofIDs) + 1
      print('\n Number of trials ran: ',countN_trials)

      if countN_trials >= 3 and countN_trials < num_trials-3: 
        adaptive = True # next trial is adaptive 
      else:
        adaptive = False # fixed interface for first 3 and last 3 trials
      
      # calculate the H transfer function of the curretn trial
      T = int(2400) # length of time points
      dists = np.squeeze(dis_[-T:])
      inps = np.squeeze(inp_[-T:])
      outs = np.squeeze(out_[-T:])
      DISTS = np.fft.fft(dists)/N
      INPS = np.fft.fft(inps)/N
      OUTS = np.fft.fft(outs)/N
      # Tud = np.squeeze(DISTS[IX])/np.squeeze(INPS[IX])
      G_current = copy.deepcopy(G_est)
      # G_ = first(G_current) 
      # H_current = -1/(Tud+G_*soM)
      H_current = -INPS[IX]/OUTS[IX]
      print('\ncurrent machine: ',repr(G_current))
      print('current human: ',repr(H_current))
      
      if not passthrough: # adaptive conditions
          if countN_trials == 1: # the first trial
              H_est = H_current
          else: # trials after the first trial, calculate avg H model
              # find B of the previous one trial
              id = listofIDs[-1]
              # print('previous id:',id)
              H_previous = trials[id]['H_']

              # combine H from previous and current trials
              alphaH = 0.75
              H_est = alphaH*np.squeeze(H_previous) + (1-alphaH)*np.squeeze(H_current) # save the combined H as the H for this trial
              # print('avg human: ',repr(H_est)) # this is the linear comb of previous and current human

          if adaptive:
              # OBTAIN NEW MACHINE UPDATE VIA GLOBAL SEARCH
              losses = loss(H_est,G_find)
              idx_min = np.argmin(losses) # index of the min
              print('\nindex = ',idx_min)
              G_optimal = G_find[:,idx_min]
              alphaG = 0.75 # larger = slower adaptation rate 
              G_est = alphaG*np.squeeze(G_current) + (1-alphaG)*np.squeeze(np.asarray(G_optimal))  # the next G
              print('\nnext machine (updated) = ',repr(G_est))  # the new machine from smoothbatch is the linear comb of old and optimal
          else:
              G_est = G_init
              print('\nnext machine (fixed init) = ',repr(G_est))
      
      else: # control trials, just a passthrough of 1
          H_est = H_current
          print('\nnext machine (fixed passthrough) = ',repr(G_est))

      # at end of game
      save(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,mach_=mach_,H_=H_est,G_=G_current)

      try:
        trial = trial_gen.__next__()
        if not ALLOW_DUPLICATES:
          while len(glob.glob(os.path.join(subject_dir,'*'+protocol+'_'+str(trial['id'])+'.npz'))) > 0:
            dbg('SKIP subject='+subject_dir+'; protocol='+protocol+'_'+str(trial['id']))
            trial = trial_gen.__next__()
        dbg('RUN subject='+subject_dir+'; protocol='+protocol+'_'+str(trial['id']))
        TRIAL_STATE = 'reset0'
        trial_reset['init'] = [_inp]
        trial = trial_reset
        state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_,mach_ = init(trial)
      except StopIteration:
        done = True

    if TRIAL_STATE == 'reset0':
      if time_[-1] >= CONGRATULATIONS_TIME:
        save(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,sfx="_rst0")
        TRIAL_STATE = 'reset1'
        trial_reset['init'] = [_inp]
        trial = trial_reset
        state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_,mach_ = init(trial)
        FADE = -1

    if TRIAL_STATE == 'reset1':
      if (np.abs(out_[-FPS*SLIDER_SPT:]).max() > .5):
        save(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,sfx="_rst1")
        TRIAL_STATE = 'reset2'
        trial_reset['init'] = [_inp]
        trial = trial_reset
        state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_,mach_ = init(trial)
        FADE = -1

    if TRIAL_STATE == 'reset2':
      if (np.abs(out_[-FPS*SLIDER_SPT:]).max() < RAD_SYS):
        save(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,sfx="_rst2")
        if REACT_NUM < REACT_THRESH:
            TRIAL_STATE = 'react'
            REACT_NUM = REACT_NUM + 1
            trial_reset['init'] = [_inp]
            trial_reset['RAND_TIME']=random.uniform(0,REACT_TIME-2.)
            trial_reset['RAND_POINT']=random.uniform(-.5,.5)
            trial = trial_reset
        else:
            TRIAL_STATE = 'run'
            trial = trial_run
        state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_,mach_ = init(trial)
        FADE = -1

    if TRIAL_STATE == 'react': # test reaction time
      if time_[-1] >= REACT_TIME:
        savereact(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,
            out_=out_,ref_=ref_,reacttime=trial_reset['RAND_TIME'],reactpoint=trial_reset['RAND_POINT'],sfx="_react")
        TRIAL_STATE = 'reset1'
        trial_reset['init'] = [_inp]
        trial_reset['RAND_TIME']=random.uniform(0,REACT_TIME-2.)
        trial_reset['RAND_POINT']=random.uniform(-.5,.5)
        trial = trial_reset
        state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_,mach_ = init(trial)
        FADE = -1

    ## out of bounds
    #if np.abs(out_[-1]) > 0.5:
    #  save(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,sfx="_oob")
    #  state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_ = init(trial)
    #  PAUSE = True

    ## saturated input
    #if np.abs(_inp/(trial['scale']*3./2.)) > .95:
    #  save(time_=time_,realtime_=realtime_,state_=state_,inp_=inp_,dis_=dis_,out_=out_,ref_=ref_,sfx="_max")
    #  state,steps,_time,time_,realtime_,state_,inp_,dis_,out_,ref_ = init(trial)
    #  PAUSE = True

    if TRIAL_STATE in ['run','reset0','reset1','reset2','react']:
      steps += 1
      _time = steps * STEP

      # --- record human input state at time t
      inp_.append(_inp) #u_H # AMBER: moved it to before calculating interface dynamics, _inp = u_H[t]

      # --- update game state u_I[t]
      if TRIAL_STATE in 'run':
        a,b0, b1 = G_est[0],G_est[1],G_est[2]
        G_est_ = np.zeros((int(len(G_est)),))
        # denominator = z + a
        G_est_[0] = a
        # numerator = b0z + b1
        G_est_[1] = b0 
        G_est_[2] = b1 
        # AMBER: updated 1st order interface dynamics
        # mach_ is u_I[:t-1]; _mach=uI[t] (interface input); inp_ = u_H[:t] (human input)
        _mach = dynamics.higher_order_machine(t=_time,uH=inp_[-m2:],uG=mach_[-n2:],G=G_est_,n=n2,m=m2, order = 1) # machine adapts user input #Amber: added order 
        if len(out_)<3:
            y = 0#_mach
        else:
            # AMBER's note: this is when d is output disturbance
            y = -den[1]*(out_[-1]-dis_[-1]) - den[2]*(out_[-2]-dis_[-2]) + num[1]*(mach_[-1]) + num[2]*(mach_[-2]) + _dis
            state = y
        # state = rk_(eval('dynamics.'+trial['vf']),_time,state,_mach,_dis,STEP)  # this is only for continuous time      
      else:
        state = [_inp]
        _mach = 0.
        y = _inp
      # --- record game state at time t
      realtime_.append(time.time())
      time_.append(_time)
      state_.append(state)
      dis_.append(_dis)
      out_.append(y)#(trial['out'](state))
      ref_.append(trial['ref']([SHIP_SHIFT + _time,_time],trial)[0]*SC_REF)
      mach_.append(_mach) # interface's output u_I
      if not TRIAL_STATE == 'reset0':
        # --- compute error (MSE)
        err = np.sqrt(np.mean((np.asarray(ref_)-np.asarray(out_))**2))
        # --- compute error (total error)
        #err = np.sqrt(np.sum(np.asarray(ref_)-np.asarray(out_))**2)
        printed_mse = False

  # only draw every SLIDER_SPT ticks -- SPT = samples per tick
  if steps % SLIDER_SPT == 0 and not done:

    if TRIAL_STATE in ['run']:
      bg_color = BLACK
      ref_color = GOLD
      out_color = PURPLE
    elif TRIAL_STATE in ['reset0','reset1','reset2','react']:
      bg_color = BLACK
      ref_color = GOLD
      out_color = PURPLE

    # --- draw
    screen.fill(bg_color) # this will occlude any drawing above


    if SHOW_GRID:
      xticks = np.arange(-RATIO/2,RATIO/2,.5)
      for g in xticks:
        draw_dashed_line(screen, DARKGREY, (g,YRNG[0]), (g,YRNG[1]),
                         width=1, dash_length=10)
      #yticks = np.hstack((-np.arange(-(SHIP_SHIFT-GRID_SPACE),-(XRNG[0]-GRID_SPACE),GRID_SPACE)[::-1],np.arange(SHIP_SHIFT,XRNG[1]+GRID_SPACE,GRID_SPACE)))# - np.mod(_time,GRID_SPACE)
      yticks = np.arange(-1,1,.5)
      for g in yticks:
        draw_dashed_line(screen, DARKGREY, (XRNG[0],g), (XRNG[1],g),
                         width=1, dash_length=10)
    #
    rects = []
    if TRIAL_STATE in ['run']:
      #TIMES = np.linspace(XRNG[0]-2*THK_REF,XRNG[1]+THK_REF,size[0]/10)
      TIMES = np.linspace(-0.5-THK_REF,0.5+THK_REF,int(SCi/10))
      pts = np.vstack((trial['ref'](TIMES + _time,trial),TIMES)).T
      #pts = pts[np.all(np.logical_not(np.isnan(pts),),axis=1)]
      pts = pts[np.all(np.isfinite(pts),axis=1)]
      # reference curve
      if SHOW_REF:
        rects.append(draw_ref(screen, ref_color, pts, THK_REF))
      # reference glyph
      pts = [ref_[-1],0] + np.asarray([[-RAD_SYS,0],[0,RAD_SYS],[RAD_SYS,0],[0,-RAD_SYS]])
      rects.append(draw_polygon(screen, out_color, pts, THK_SYS))
      #rects.append(draw_rect(screen, ref_color, (ref_[-1]+SHIP_SHIFT-RAD_SYS,-RAD_SYS, 2*RAD_SYS, 2*RAD_SYS), THK_SYS))

      # error bars
      # instantaneous
      #rects.append(draw_rect(screen, out_color, (0,+THK_REF/2,-THK_REF,ref_[-1]), 0))
      rects.append(draw_rect(screen, out_color, (out_[-1],-THK_REF/4,ref_[-1]-out_[-1],THK_REF/2), 0))
      # MSE bar
      #rects.append(draw_lines(screen, WHITE, False, [(RATIO/2-THK_REF,-.5),(RATIO/2-THK_REF,-.5+np.arctan(err/MSE_SCALE)/(np.pi/2))], 2*THK_REF))
    elif TRIAL_STATE in ['reset0']:
      # MSE bar
      MSE = np.arctan(err/MSE_SCALE)/(np.pi/2)
      rects.append(draw_lines(screen, WHITE, False, [(RATIO/2-THK_REF,-.5),(RATIO/2-THK_REF,-.5+MSE)], 2*THK_REF))
      # MSE text
      text = font.render('%.1f !!!'%(100-100*MSE), False, WHITE)
      w,h = text.get_rect().width,text.get_rect().height
      screen.blit(text,[(size[0]-w)/2,size[1]/4])

      if not printed_mse:
        print('MSE = %.1f !!!'%(100-100*MSE)) # print MSE in terminal
        printed_mse = True

    elif TRIAL_STATE in ['react']:
      if time_[-1] > trial_reset['RAND_TIME']:
        rects.append(draw_rect(screen, out_color, (trial_reset['RAND_POINT'],-.5,2*RAD_SYS,+1.),THK_SYS))
        #pts = [out_[-1],0] + np.asarray([[-RAD_SYS,0],[0,RAD_SYS],[RAD_SYS,0],[0,-RAD_SYS]])
        #rects.append(draw_polygon(screen, out_color, pts, THK_SYS))
    elif TRIAL_STATE in ['reset1']:
      #rects.append(draw_rect(screen, ref_color, (-RATIO/2,0.5,RATIO/2-.5,1.),THK_SYS))
      #rects.append(draw_rect(screen, ref_color, (.5,1.,RATIO/2-.5,+RATIO/2),THK_SYS))
      rects.append(draw_rect(screen, ref_color, (-.5,-.5,-RATIO,1.),THK_SYS))
      rects.append(draw_rect(screen, ref_color, (+.5,-.5,+RATIO,1.),THK_SYS))
      #rects.append(draw_rect(screen, ref_color, (),THK_SYS))
    elif TRIAL_STATE in ['reset2','done']:
      #rects.append(draw_rect(screen, ref_color, (-RAD_SYS,1.,2*RAD_SYS,+2.),THK_SYS))
      rects.append(draw_rect(screen, ref_color, (-RAD_SYS,-.5,2*RAD_SYS,+1.),THK_SYS))
    # output glyph
    #rects.append(draw_rect(screen, out_color, (out_[-1]+SHIP_SHIFT-.5*RAD_SYS,1.5*RAD_SYS, 1*RAD_SYS, 3*RAD_SYS), THK_SYS))
    pts = [out_[-1],0] + np.asarray([[-RAD_SYS,0],[0,RAD_SYS],[RAD_SYS,0],[0,-RAD_SYS]])
    rects.append(draw_polygon(screen, out_color, pts, THK_SYS))
    if SHOW_INP:
      # input
      rects.append(draw_lines(screen, WHITE, False, [[0.,INP_SHIFT],[_inp/(trial['scale']),INP_SHIFT]], THK_INP))
    if SHOW_DIS:
      # input
      rects.append(draw_lines(screen, WHITE, False, [[0.,DIS_SHIFT],[_dis/(trial['scale']),DIS_SHIFT]], THK_DIS))

    activerects = rects + oldrects
    activerects = filter(bool, activerects)

    if PLOT:
      plt.clf()
      plt.grid('on'); plt.axis('equal')
      plt.plot(TIMES,trial['ref'](TIMES + _time,trial)*SC_REF,'.-',lw=10,color=_GOLD)
      plt.plot(SHIP_SHIFT,state[0],'.',ms=40,color=_PURPLE)
      if SHOW_GRID:
        plt.xticks(xticks)
      plt.xlim(XRNG)
      plt.ylim(YRNG)
      plt.yticks([])
      plt.draw()

    if FADE > 0:
      fader.fill((0.,0.,0.,FADE))
      screen.blit(fader,(0,0))
      FADE += 20
      if FADE >= 255:
        FADE = 0

    if FADE < 0:
      fader.fill((0.,0.,0.,255+FADE))
      screen.blit(fader,(0,0))
      FADE -= 20
      if FADE < -255:
        FADE = 0

    # --- update screen
    pygame.display.flip()

    #dbg('t = %0.1f, FPS = %0.1f' % (clock.get_time(),
    #                                clock.get_fps()))

  # --- limit update rate to FPS
  clock.tick(FPS*SLIDER_SPT)

  if (steps+1) % 60 == 0:
    dbg('%d t = %0.1f, FPS = %0.1f, inp = %0.1f, state = %s' %
        (len(inp_), time_[-1], clock.get_fps(), _inp, state))

MSE = np.arctan(err/MSE_SCALE)/(np.pi/2)
print('MSE = %.1f !!!'%(100-100*MSE))

if COM_PORT is not None:
  joy.stopArduino()
pygame.display.quit()
pygame.quit()
sys.exit(0)
