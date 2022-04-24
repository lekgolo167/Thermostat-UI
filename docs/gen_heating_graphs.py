import numpy as np
import matplotlib.pyplot as plt

def simple_case():
	delta_t = 0.01
	k1 = 0.35
	k2 = 0.46
	k3 = 0.28
	T = 35.0
	x1 = 35.0
	x2 = 35.0
	time = 0.0
	house_temp = []
	attic_temp = []
	x = []
	iters = 0
	def H():
		return 20

	while iters < 2500:
		dx1 = k1*(T- x1) + k2*(x2 - x1) + H()
		dx2 = k2*(x1 - x2) + k3*(T- x2)

		x1 += dx1*delta_t
		x2 += dx2*delta_t
		time += delta_t

		x.append(time)
		house_temp.append(x1)
		attic_temp.append(x2)

		iters += 1
		
	fig, ax = plt.subplots()
	ax.set_ylabel('Temperature')
	ax.set_xlabel('time')
	plt.plot(x, house_temp, label='house')
	plt.plot(x, attic_temp, label='attic')
	plt.axhline(y=68.0, color='r', linestyle='-.', label='68')
	plt.legend()
	#plt.show()
	plt.title('Figure 2')
	plt.savefig('./images/simple_case.png')

def more_realistic_case():
	delta_t = 0.01
	k1 = 0.35
	k2 = 0.46
	k3 = 0.28
	T = 35.0
	x1 = 35.0
	x2 = 35.0
	time = 0.0
	house_temp = []
	attic_temp = []
	out_temp = []
	x = []
	iters = 0

	def H(temp):
		if temp < 68.0:
			return 20.0
		else:
			return 0.0

	def T(time):
		return -17.5 * np.sin((np.pi/12)*(time + 3)) +47

	while iters < 2500:
		t = T(time)
		dx1 = k1*(t- x1) + k2*(x2 - x1) + H(x1)
		dx2 = k2*(x1 - x2) + k3*(t- x2)

		x1 += dx1*delta_t
		x2 += dx2*delta_t
		time += delta_t

		x.append(time)
		house_temp.append(x1)
		attic_temp.append(x2)
		out_temp.append(t)

		iters += 1

	fig, ax = plt.subplots()
	ax.set_ylabel('Temperature')
	ax.set_xlabel('time')
	plt.plot(x, house_temp, label='house')
	plt.plot(x, attic_temp, label='attic')
	plt.plot(x, out_temp, label='outside')
	plt.legend()
	#plt.show()
	plt.title('Figure 3')
	plt.savefig('./images/more_realistic_case.png')

def thermostat_on_off_case():
	delta_t = 0.01
	k1 = 0.35
	k2 = 0.46
	k3 = 0.28
	T = 35.0
	x1 = 35.0
	x2 = 35.0
	time = 0.0
	house_temp = []
	attic_temp = []
	out_temp = []
	x = []
	f_state = False
	iters = 0

	def H(temp, furnace_on):
		if temp < 65.0 or (furnace_on and temp < 70.0):
			return (20.0, True)
		else:
			return (0.0, False)

	def T(time):
		return -17.5 * np.sin((np.pi/12)*(time + 3)) + 47

	while iters < 2500:
		t = T(time)
		h, f_state = H(x1, f_state)
		dx1 = k1*(t- x1) + k2*(x2 - x1) + h
		dx2 = k2*(x1 - x2) + k3*(t- x2)

		x1 += dx1*delta_t
		x2 += dx2*delta_t
		time += delta_t

		x.append(time)
		house_temp.append(x1)
		attic_temp.append(x2)
		out_temp.append(t)

		iters += 1

	fig, ax = plt.subplots()
	ax.set_ylabel('Temperature')
	ax.set_xlabel('time')
	plt.plot(x, house_temp, label='house')
	plt.plot(x, attic_temp, label='attic')
	plt.plot(x, out_temp, label='outside')
	plt.axhline(y=68.0, color='r', linestyle='-.', label='set to 68')
	plt.legend()
	#plt.show()
	plt.title('Figure 4')
	plt.savefig('./images/thermostat_on_off_case.png')

def schedule_case():
	delta_t = 0.01
	k1 = 0.045
	k2 = 0.056
	k3 = 0.038
	T = 35.0
	x1 = 68.0
	x2 = 60.0
	time = 0.0
	house_temp = []
	attic_temp = []
	target_temp = []
	out_temp = []
	x = []
	f_state = False
	iters = 0

	def H(temp, target, furnace_on):
		if temp < target - 2.0 or (furnace_on and temp < target + 2.0):
			return (20.0, True)
		else:
			return (0.0, False)

	def T(time):
		return -17.5 * np.sin((np.pi/12)*(time + 3)) + 47

	def schedule(time):
		if time < 10.0:
			return 60.0
		elif time < 14.0:
			return 70.0
		else:
			return 68.0

	while iters < 2500:
		t = T(time)
		target = schedule(time)
		h, f_state = H(x1, target, f_state)
		dx1 = k1*(t- x1) + k2*(x2 - x1) + h
		dx2 = k2*(x1 - x2) + k3*(t- x2)

		x1 += dx1*delta_t
		x2 += dx2*delta_t
		time += delta_t

		x.append(time)
		house_temp.append(x1)
		attic_temp.append(x2)
		target_temp.append(target)
		out_temp.append(t)

		iters += 1

	fig, ax = plt.subplots()
	ax.set_ylabel('Temperature')
	ax.set_xlabel('time')
	plt.plot(x, house_temp, label='house')
	plt.plot(x, attic_temp, label='attic')
	plt.plot(x, out_temp, label='outside')
	plt.plot(x, target_temp, label='schedule', linestyle='-.')
	plt.legend()
	#plt.show()
	plt.title('Figure 5')
	plt.savefig('./images/schedule_case.png')

def sunlight_case():
	delta_t = 0.01
	k1 = 0.045
	k2 = 0.056
	k3 = 0.038
	f1 = 0.2
	f2 = 0.9
	T = 35.0
	x1 = 68.0
	x2 = 60.0
	time = 0.0
	house_temp = []
	attic_temp = []
	target_temp = []
	out_temp = []
	x = []
	f_state = False
	iters = 0

	def H(temp, target, furnace_on):
		if temp < target - 2.0 or (furnace_on and temp < target + 2.0):
			return (20.0, True)
		else:
			return (0.0, False)

	def UV(time):
		if time < 8.0:
			return 0.0
		elif time < 10.0:
			return 1.0
		elif time < 12.0:
			return 2.0
		elif time < 14.0:
			return 4.0
		elif time < 16.0:
			return 3.0
		elif time < 19.0:
			return 1.0
		else:
			return 0.0

	def T(time):
		return -17.5 * np.sin((np.pi/12)*(time + 3)) + 47

	def schedule(time):
		if time < 10.0:
			return 60.0
		elif time < 14.0:
			return 70.0
		else:
			return 68.0

	while iters < 2500:
		t = T(time)
		target = schedule(time)
		h, f_state = H(x1, target, f_state)
		dx1 = k1*(t- x1) + k2*(x2 - x1) + h + UV(time)*f1
		dx2 = k2*(x1 - x2) + k3*(t- x2) + UV(time)*f2

		x1 += dx1*delta_t
		x2 += dx2*delta_t
		time += delta_t

		x.append(time)
		house_temp.append(x1)
		attic_temp.append(x2)
		target_temp.append(target)
		out_temp.append(t)

		iters += 1

	fig, ax = plt.subplots()
	ax.set_ylabel('Temperature')
	ax.set_xlabel('time')
	plt.plot(x, house_temp, label='house')
	plt.plot(x, attic_temp, label='attic')
	plt.plot(x, out_temp, label='outside')
	plt.plot(x, target_temp, label='schedule', linestyle='-.')
	plt.legend()
	#plt.show()
	plt.title('Figure 6')
	plt.savefig('./images/sunlight_case.png')


def heat_capacity_case():
	delta_t = 0.01
	k1 = 0.065
	k2 = 0.076
	k3 = 0.058
	f1 = 0.2
	f2 = 0.9
	T = 35.0
	x1 = 68.0
	x2 = 60.0
	time = 0.0
	house_temp = []
	attic_temp = []
	target_temp = []
	out_temp = []
	x = []
	f_state = False
	iters = 0

	# used for heat capacity calculations
	N = 250
	index = 0
	accum = (x1 - 2.0)*N
	heat_retension = [x1 - 2.0 for x in range(0,N)]

	def H(temp, target, furnace_on):
		if temp < target - 2.0 or (furnace_on and temp < target + 2.0):
			return (20.0, True)
		else:
			return (0.0, False)

	def UV(time):
		if time < 8.0:
			return 0.0
		elif time < 10.0:
			return 1.0
		elif time < 12.0:
			return 2.0
		elif time < 14.0:
			return 4.0
		elif time < 16.0:
			return 3.0
		elif time < 19.0:
			return 1.0
		else:
			return 0.0

	def T(time):
		return -17.5 * np.sin((np.pi/12)*(time + 3)) + 47

	def schedule(time):
		if time < 10.0:
			return 60.0
		elif time < 14.0:
			return 70.0
		else:
			return 68.0

	while iters < 2500:
		t = T(time)
		target = schedule(time)
		h, f_state = H(x1, target, f_state)
		dx1 = k1*(t- x1) + k2*(x2 - x1) + h + UV(time)*f1
		dx2 = k2*(x1 - x2) + k3*(t- x2) + UV(time)*f2

		x1 += dx1*delta_t
		x2 += dx2*delta_t
		time += delta_t

		# heat_retention update rolling average
		if index >= N:
			index = 0
		old = heat_retension[index]
		heat_retension[index] = x1
		accum = accum - old + x1
		
		pen = (accum/N - x1) * delta_t
		x1 += pen

		x.append(time)
		house_temp.append(x1)
		attic_temp.append(x2)
		target_temp.append(target)
		out_temp.append(t)

		iters += 1
		index += 1

	fig, ax = plt.subplots()
	ax.set_ylabel('Temperature')
	ax.set_xlabel('time')
	plt.plot(x, house_temp, label='house')
	plt.plot(x, attic_temp, label='attic')
	plt.plot(x, out_temp, label='outside')
	plt.plot(x, target_temp, label='schedule', linestyle='-.')
	plt.legend()
	#plt.show()
	plt.title('Figure 7')
	plt.savefig('./images/heat_capacity_case.png')

simple_case()
more_realistic_case()
thermostat_on_off_case()
schedule_case()
sunlight_case()
heat_capacity_case()