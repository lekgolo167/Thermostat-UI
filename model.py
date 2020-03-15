#/usr/bin/python
import math
from matplotlib import pyplot as plt

time = 0.0
deltaTime = 0.01
BTU = 40.0
heating = False
thresh = 2.0
runtime = 0.0
sched = []
goal = []

def calulateModel(s,t):
  global time, heating, runtime, sched
  runtime = 0.0
  time = 0.0
  heating = False
  k1 = 0.18 # wall
  k2 = 0.45 # cieling
  k3 = 0.12 # roof
  x1 = 70.0 
  x2 = 65.0
  outsideTemperature = t
  sched = s

  #T = []
  #x = []
  data = []


  while time < 23.9:
    #T.append(outsideTemperature[int(time)])
    data.append((x1, time))
    #x.append(time)

    dx1 = k1*(outsideTemperature[int(time)] - x1) + k2*(x2 - x1) + H(x1, time)
    dx2 = k2*(x1 - x2) + k3*(outsideTemperature[int(time)] - x2)
    
    if not heating:
      dx1 *= deltaTime * 0.175
    else:
      dx1 *= deltaTime * 0.55

    x1 += dx1
    x2 += dx2 * deltaTime

    time += deltaTime

  print(runtime)
  return data
  #plt.plot(x, T, x, y1, x, goal)
  #plt.show()


def findSCH(time):
  global sched
  tar = 0.0
  for t, f in sched:

    if t > time:
      break
    tar = f

  return tar


def H(temp, time):
  global heating
  global deltaTime, runtime, BTU
  target = findSCH(time)
  goal.append(target)
  if temp <= target - thresh:
    runtime += deltaTime
    heating = True
    return BTU
  elif temp <= target + thresh and heating:
    runtime += deltaTime
    return BTU
  else:
    heating = False

    return 0