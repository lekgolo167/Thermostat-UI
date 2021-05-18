#/usr/bin/python
import math

time_hr = 0.0
delta_time = 0.01
BTU = 25.0
heat_on = False
thresh = 2.0
runtime = 0.0
sched = []
x1 = 0.0

def simulate(start_temperature, sched,outsideTemperature, uvIndex):
  global time_hr, heat_on, runtime
  # time of day in hours
  time_hr = 0.0
  # if the furnace is on
  heat_on = False
  last_Heating = False
  # insulation
  k1 = 0.08 # wall
  k2 = 0.18 # cieling
  k3 = 0.03 # roof
  # starting temperatures
  inside_t = start_temperature
  attic_t = start_temperature - 4.0
  
  # used for heat capacity calculations
  N = 250
  index = 0
  accum = (inside_t - 2.0)*N
  heat_retension = [inside_t - 2.0 for x in range(0,N)]
  # data to return
  save_every_other = True
  runtime = 0.0
  data = []

  while time_hr < 23.99:
    # extract variables
    hr = int(time_hr)
    T = outsideTemperature[hr]
    uv = uvIndex[hr]

    # not every data point needs to be graphed
    if save_every_other:
      data.append((inside_t, time_hr))
    save_every_other = not save_every_other

    # calculate change in temperature
    delta_t1 = k1*(T - inside_t) + k2*(attic_t - inside_t) + H(inside_t, sched) + uv*0.2
    delta_t2 = k2*(inside_t - attic_t) + k3*(T - attic_t) + uv *0.9
    
    # scale the change in temperature
    delta_t1 *= delta_time
    delta_t2 *= delta_time

    # heat_retention update rolling average
    if index >= N:
      index = 0
    old = heat_retension[index]
    heat_retension[index] = inside_t
    accum = accum - old + inside_t
    if not heat_on:
      pen = (accum/N - inside_t) * delta_time
      delta_t1 += pen*2.7

    # add the change in temperature plus heat from the neighbors wall
    inside_t += delta_t1 + 0.0005*(72-inside_t)
    attic_t += delta_t2 + 0.0005*(69-attic_t)

    # if the heater just turned off, add a little time for it to shutdown
    if not heat_on and last_Heating:
      runtime += 0.01

    # increment time
    time_hr += delta_time
    last_Heating = heat_on
    index += 1

  return data, runtime


def findSCH(sched):
  global time_hr
  target = 0.0
  for _time, set_temp in sched:

    if _time > time_hr:
      break
    target = set_temp

  return target


def H(temp, sched):
  global heat_on, delta_time, runtime, BTU
  target = findSCH(sched)

  if temp <= target - thresh:
    runtime += delta_time
    heat_on = True
    return BTU

  elif temp <= target + thresh and heat_on:
    runtime += delta_time
    return BTU

  else:
    heat_on = False

    return 0
