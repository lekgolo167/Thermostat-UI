#/usr/bin/python
import math

time = 0.0
deltaTime = 0.01
BTU = 50.0
heating = False
thresh = 2.0
runtime = 0.0
sched = []
goal = []

def calulateModel(startTemp, s,outsideTemperature, uvIndex):
  global time, heating, runtime, sched
  runtime = 0.0
  time = 0.0
  heating = False
  k1 = 0.17 # wall
  k2 = 0.44 # cieling
  k3 = 0.14 # roof
  x1 = startTemp
  x2 = startTemp - 4.0
  sched = s
  data = []
  penalty = [x1 - x*0.03 for x in range(0,250)]
  lastHeating = heating
  counter = 0
  countUp = 0
  cool = False

  while time < 23.95:

    penalty = penalty[-1:] + penalty[:-1]
    
    penalty[0] = x1
    pen = (sum(penalty)/250 - x1) * deltaTime

    data.append((x1, time))
    T = outsideTemperature[int(time)]
    dx1 = k1*(T - x1) + k2*(x2 - x1) + H(x1, time) + uvIndex[int(time)]*0.50
    dx2 = k2*(x1 - x2) + k3*(T - x2) + uvIndex[int(time)] *1.30
    
    if not heating:
      dx1 *= deltaTime * 0.17
      dx1 += pen
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
      deltaCool = (outsideTemperature[int(time)] - x1) * 0.00157
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
