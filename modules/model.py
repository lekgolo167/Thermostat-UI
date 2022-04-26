import json
from collections import deque

class HeatingModel():
	def __init__(self, config_file_path) -> None:
		vals = self.load_config(config_file_path)
		self.set_values(vals)
		self.runtime = 0.0

	def load_config(self, config_file_path):
		with open(config_file_path, 'r') as config_file:
			config_obj = json.loads(config_file.read())
			return config_obj

	def set_values(self, vals) -> None:
			self.btu = vals.get('btu', 25.0)
			self.delta_time = vals.get('delta-time', 0.01)
			self.thresh_upper = vals.get('thresh-upper', 1.0)
			self.thresh_lower = vals.get('thresh-lower', 2.0)
			self.sample_avg = vals.get('sample-avg', 10)
			self.k1 = vals.get('k1', 0.08) # wall
			self.k2 = vals.get('k2', 0.18) # cieling
			self.k3 = vals.get('k3', 0.03) # roof
			self.f1 = vals.get('f1', 0.2) # uv walls
			self.f2 = vals.get('f2', 0.9) # uv roof
			self.rolling_avg_size = vals.get('rolling-avg-size', 250)

	def get_target_temp(self, time_hr, schedule) -> float:
		target = 0.0
		for _time, set_temp in schedule:
			if _time > time_hr:
				break
			target = set_temp

		return target

	def H(self, inside_t, target, furnace_on) -> float:
		if inside_t < target - self.thresh_lower or (furnace_on and inside_t < target + self.thresh_upper):
			self.runtime += self.delta_time
			return (self.btu, True)
		else:
			return (0.0, False)

	def simulate(self, start_temperature, sched,outsideTemperature, uvIndex):
		# time of day in hours
		time_hr = 0.0
		# if the furnace is on
		furnace_on = False

		# starting temperatures
		inside_t = start_temperature
		attic_t = start_temperature - 4.0
		
		# used for heat capacity calculations
		accum = (inside_t - 2.0)*self.rolling_avg_size
		heat_retension = deque([inside_t - 2.0 for _ in range(0, self.rolling_avg_size)])
		sample_arr = deque([inside_t for _ in range(0, self.sample_avg)])

		# data to return
		self.runtime = 0.0
		data = []

		while time_hr < 24.0:
			# extract variables
			hr = int(time_hr)
			outside_t = outsideTemperature[hr]
			uv = uvIndex[hr]

			data.append((inside_t, time_hr))

			# heat_retention update rolling average
			old = heat_retension.popleft()
			heat_retension.append(inside_t)
			accum = accum - old + inside_t

			sample_arr.popleft()
			sample_arr.append(inside_t)
			inside_avg = sum(sample_arr)/self.sample_avg
			
			target = self.get_target_temp(time_hr, sched)
			h, furnace_on = self.H(inside_avg, target, furnace_on)
			c = (accum/self.rolling_avg_size - inside_t)

			# calculate change in temperature
			delta_t1 = self.k1*(outside_t - inside_t) + self.k2*(attic_t - inside_t) + h + uv*self.f1 + c
			delta_t2 = self.k2*(inside_t - attic_t) + self.k3*(outside_t - attic_t) + uv*self.f2
			
			# scale the change in temperature
			delta_t1 *= self.delta_time
			delta_t2 *= self.delta_time

			# add the change in temperature
			inside_t += delta_t1
			attic_t += delta_t2

			# increment time
			time_hr += self.delta_time

		return data, self.runtime
