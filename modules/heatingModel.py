import json
import logging
from logging import Handler
from collections import deque
try:
	from modules.simulation_cpp import simulation
except:
	print('WARNING: No CPP simulation library found!')


class HeatingModel():
	def __init__(self, config_file_path: str, log_handler: Handler, log_level: int | str) -> None:
		self.logger = logging.getLogger(type(self).__name__)
		self.logger.addHandler(log_handler)
		self.logger.setLevel(log_level)
		# applying defaults
		self.btu = 25.0
		self.delta_time = 0.01
		self.thresh_upper = 1.0
		self.thresh_lower = 2.0
		self.sample_avg = 10
		self.k1 = 0.08 # wall
		self.k2 = 0.18 # ceiling
		self.k3 = 0.03 # roof
		self.f1 = 0.2 # uv walls
		self.f2 = 0.9 # uv roof
		self.rolling_avg_size = 250
		# applying config values
		vals = self.load_config(config_file_path)
		self.set_values(vals)
		self.runtime = 0.0

	def load_config(self, config_file_path: str) -> dict[str, int | float]:
		self.logger.debug(f'Loading from config file: {config_file_path}')
		with open(config_file_path, 'r') as config_file:
			config_obj = json.loads(config_file.read())
			if config_obj.get('use-cpp-sim', False):
				self.simulate = simulation.simulate_using_cpp
			else:
				self.simulate = self.simulate_using_py
			return config_obj

	def set_values(self, vals: dict[str, int | float]) -> None:
			self.btu = float(vals.get('btu', self.btu))
			self.delta_time = float(vals.get('delta-time', self.delta_time))
			self.thresh_upper = float(vals.get('thresh-upper', self.thresh_upper))
			self.thresh_lower = float(vals.get('thresh-lower', self.thresh_lower))
			self.sample_avg = int(vals.get('sample-avg', self.sample_avg))
			self.k1 = float(vals.get('k1', self.k1)) # wall
			self.k2 = float(vals.get('k2', self.k2)) # ceiling
			self.k3 = float(vals.get('k3', self.k3)) # roof
			self.f1 = float(vals.get('f1', self.f1)) # uv walls
			self.f2 = float(vals.get('f2', self.f2)) # uv roof
			self.rolling_avg_size = int(vals.get('rolling-avg-size', self.rolling_avg_size))
	
	def get_values(self) -> dict[str, int | float]:
		vals = {}
		vals['btu'] = self.btu
		vals['delta-time'] = self.delta_time
		vals['thresh-upper'] = self.thresh_upper
		vals['thresh-lower'] = self.thresh_lower
		vals['sample-avg'] = self.sample_avg
		vals['k1'] = self.k1
		vals['k2'] = self.k2
		vals['k3'] = self.k3
		vals['f1'] = self.f1
		vals['f2'] = self.f2
		vals['rolling-avg-size'] = self.rolling_avg_size

		return vals

	def get_target_temp(self, time_hr: float, schedule: list[tuple[float, float]]) -> float:
		target = 0.0
		for _time, set_temp in schedule:
			if _time > time_hr:
				break
			target = set_temp

		return target

	def H(self, inside_t: float, target: float, furnace_on: bool) -> float:
		if inside_t < target - self.thresh_lower or (furnace_on and inside_t < target + self.thresh_upper):
			self.runtime += self.delta_time
			return (self.btu, True)
		else:
			return (0.0, False)

	def simulate_using_py(self, start_temperature: float, sched: list[tuple[float, float]], outsideTemperature: list[float], uvIndex: list[float]) -> tuple[list[tuple[float, float]], float]:
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
