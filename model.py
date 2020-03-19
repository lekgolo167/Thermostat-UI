#/usr/bin/python
import math

time = 0.0
deltaTime = 0.01
BTU = 55.0
heating = False
thresh = 2.0
runtime = 0.0
sched = []
goal = []

def calulateModel(s,outsideTemperature, uvIndex):
  global time, heating, runtime, sched
  runtime = 0.0
  time = 0.0
  heating = False
  k1 = 0.16 # wall
  k2 = 0.45 # cieling
  k3 = 0.12 # roof
  x1 = 71.0
  x2 = 65.0
  sched = s
  data = []
  lastHeating = heating
  counter = 0
  countUp = 0
  cool = False

  while time < 23.95:
    data.append((x1, time))
    T = outsideTemperature[int(time)]
    dx1 = k1*(T - x1) + k2*(x2 - x1) + H(x1, time) + uvIndex[int(time)]*0.55
    dx2 = k2*(x1 - x2) + k3*(T - x2) + uvIndex[int(time)] *1.45
    
    if not heating:
      dx1 *= deltaTime * 0.17
    else:
      countUp += 1
      #0.6
      dx1 *= deltaTime * 0.53

    x1 += dx1 + 0.0005*(72-x1)
    x2 += dx2 * deltaTime + 0.0005*(69-x2)

    if not heating and lastHeating:
      runtime += 0.02
      cool = True

    if cool:
      deltaCool = (outsideTemperature[int(time)] - x1) * 0.00257
      counter += 1
      x1 += deltaCool

      if countUp+13 == counter or counter >= 37:
        countUp = 0
        counter = 0
        cool = False

    time += deltaTime
    lastHeating = heating

  return data, runtime


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