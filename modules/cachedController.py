from datetime import datetime, timedelta, date
from distutils.command.config import config
import time as cTime
import json
import logging

from modules.model import HeatingModel
from modules.weather import get_weather_data, weather_data_from_file
try:
	from modules.simulation_cpp import simulation
except:
	pass

class ChachedDaysController():
	def __init__(self, config_file_path, log_handler, log_level):
		self.logger = logging.getLogger(type(self).__name__)
		self.logger.addHandler(log_handler)
		self.logger.setLevel(log_level)
		self.apiKey = None
		self.lat = None
		self.lon = None
		self.get_weather = None
		self.heating_model = HeatingModel(config_file_path, log_handler, log_level)
		self.days_data = [DayData(d) for d in range(8)]
		self.selected_day = 1
		self.temporary_temperature = 0.0
		self.load_config(config_file_path)
	
	def init(self, get_cycles):
		today = date.today().strftime('%Y-%m-%d')
		for x in range(0,8):
			day = self.days_data[x]
			day.start_temperature = 69.0
			self.update_weather(today, day)
			cycles = get_cycles(x)
			self.update_schedule(cycles, day)

	def load_config(self, config_file_path):
		self.logger.debug(f'Loading configuration from file: {config_file_path}')
		with open(config_file_path, 'r') as config_file:
			config_obj = json.loads(config_file.read())
			self.apiKey = config_obj.get('api-key', 'null')
			self.lat = str(config_obj.get('lat', 0.0))
			self.lon = str(config_obj.get('lon', 0.0))
			# if config_obj.get('use-cpp-sim', False):
			# 	self.simulate = simulation.simulate
			# else:
			# 	self.simulate = simulate
			if config_obj.get('debug-enabled', False):
				self.get_weather = weather_data_from_file
			else:
				self.get_weather = get_weather_data

	def update_sim_params(self):
		self.logger.debug('Reloading simulation parameters')
		vals = self.heating_model.load_config('config.json')
		self.heating_model.set_values(vals)

	def get_day(self):
		return self.days_data[self.selected_day]

	def set_start_temperature(self, temperature):
		day = self.days_data[self.selected_day]
		self.logger.debug(f'Setting simulation initial temperature to: {temperature} for day: {day}')
		day.start_temperature = temperature
		self.update_inside_temperature(day)
	
	def check_dates(self):
		today = date.today().strftime('%Y-%m-%d')
		for day in range(0,7):
			if self.days_data[day].last_updated < int(cTime.time()) - 43200: # 12 hrs
				self.logger.debug(f'Updating simulation day: {day} with date: {today}')
				self.update_weather(today, self.days_data[day])
				self.update_inside_temperature(self.days_data[day])

	def update_schedule(self, cycles, day=None):
		if day is None:
			day = self.days_data[self.selected_day]

		day.g_schedule = []
		day.sim_schedule = []

		for cycle in cycles:
			# generate list for graphing the schedule
			timestamp = str(cycle.h,).zfill(2) + ':' + str(cycle.m).zfill(2)
			day.g_schedule.append({'x': timestamp, 'y': cycle.t})
			hr = cycle.h + (cycle.m / 60)
			day.sim_schedule.append((hr, cycle.t))

		# This is so the chartjs shows the graph all the way to the end
		day.g_schedule.append({'x': '23:59', 'y': 60.0})

		self.update_inside_temperature(day)

	def update_weather(self, _date, day=None):
		if day is None:
			day = self.days_data[self.selected_day]

		outside_t = []
		uv =[]
		outside_t, uv = self.get_weather(self.logger, _date, self.apiKey, self.lat, self.lon)

		day.outside_temperatures = outside_t
		day.uv_indices = uv
		day.last_updated = int(cTime.time())
		day.g_outside_temperatures = []
		day.days_date = _date

		for hr in range(0,24):
			# generate list for graphing the outside temperature
			timestamp = str(hr).zfill(2) + ':00'
			day.g_outside_temperatures.append({'x': timestamp, 'y': outside_t[hr]})


	def update_inside_temperature(self, day=None):
		if day is None:
			day = self.days_data[self.selected_day]

		day.g_inside_temperatures = []
		sim_inside_t, day.runtime = self.heating_model.simulate(day.start_temperature, day.sim_schedule, day.outside_temperatures, day.uv_indices)

		index = 0
		peak = False
		trough = False
		prev = sim_inside_t[0][0]
		next = sim_inside_t[2][0]

		# reduce the number of points to graph by a factor of 20, while perserving peaks and troughs
		for inside_t, hr in sim_inside_t[1:-2]:

			if prev > inside_t and inside_t < next:
				trough = True
				peak = False
			elif prev < inside_t and inside_t >  next:
				peak = True
				trough = False
			else:
				peak = False
				trough = False

			if (index % 20 == 0) or peak or trough:
				h = int(hr)
				m = int((hr - h)*60)

				# generate list for graphing the inside temperature
				timestamp = str(h).zfill(2) + ':' + str(m).zfill(2)
				day.g_inside_temperatures.append({'x': timestamp, 'y': inside_t})

			index += 1
			prev = inside_t
			next = sim_inside_t[index+2][0]

		# append last element
		inside_t, hr = sim_inside_t[-1]
		h = int(hr)
		m = int((hr - h)*60)
		timestamp = str(h).zfill(2) + ':' + str(m).zfill(2)
		day.g_inside_temperatures.append({'x': timestamp, 'y': inside_t})

class DayData():
	def __init__(self, d):
		day = date.today()+timedelta(d)
		self.days_date = day.strftime('%Y-%m-%d')
		self.last_updated = 0
		self.outside_temperatures = []
		self.uv_indices = []
		self.sim_schedule = []
		self.g_schedule = []
		self.g_outside_temperatures = []
		self.g_inside_temperatures = []
		self.runtime = -1
		self.start_temperature = 70.0
