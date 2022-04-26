from datetime import datetime, timedelta, date
from distutils.command.config import config
import time as cTime
import json

from modules.model import HeatingModel
from modules.weather import get_weather_data, weather_data_from_file
try:
	from modules.simulation_cpp import simulation
except:
	pass

class ChachedDaysController():
	def __init__(self, config_file_path, debug=False):
		with open(config_file_path, 'r') as config_file:
			config_obj = json.loads(config_file.read())
			self.apiKey = config_obj.get('api-key', 'null')
			self.lat = str(config_obj.get('lat', 0.0))
			self.lon = str(config_obj.get('lon', 0.0))
			# if config_obj.get('use-cpp-sim', False):
			# 	self.simulate = simulation.simulate
			# else:
			# 	self.simulate = simulate
		self.heating_model = HeatingModel(config_file_path)
		self.debug = debug
		self.days_data = [DayData(d) for d in range(8)]
		self.selected_day = 1
		self.temporary_temperature = 0.0
		self.setup = False
	
	def init(self, get_cycles):
		if self.setup:
			return
		self.setup = True
		today = date.today().strftime('%Y-%m-%d')
		for x in range(0,8):
			day = self.days_data[x]
			day.start_temperature = 69.0
			self.update_weather(today, day)
			cycles = get_cycles(x)
			self.update_schedule(cycles, day)

	def update_sim_params(self):
		vals = self.heating_model.load_config('config.json')
		self.heating_model.set_values(vals)

	def get_day(self):
		return self.days_data[self.selected_day]

	def set_start_temperature(self, temperature):
		day = self.days_data[self.selected_day]
		day.start_temperature = temperature
		self.update_inside_temperature(day)
	
	def check_dates(self):
		#print("CHECKING DATES")
		today = date.today().strftime('%Y-%m-%d')
		for day in range(0,7):
			if self.days_data[day].last_updated < int(cTime.time()) - 43200: # 12 hrs
				self.update_weather(today, self.days_data[day])
				self.update_inside_temperature(self.days_data[day])

	def update_schedule(self, cycles, day=None):
		if day is None:
			day = self.days_data[self.selected_day]
		#print("UPDATING SCHEDULE FOR: ", day.days_date)

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
		#print("UPDATING WEATHER FOR: ", day.days_date)

		outside_t = []
		uv =[]
		if self.debug:
			outside_t, uv = weather_data_from_file()
		else:
			outside_t, uv = get_weather_data(_date, self.apiKey, self.lat, self.lon)

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
		#print("UPDATING INSIDE TEMPERATURES FOR: ", day.days_date)

		day.g_inside_temperatures = []
		sim_inside_t, day.runtime = self.heating_model.simulate(day.start_temperature, day.sim_schedule, day.outside_temperatures, day.uv_indices)

		for inside_t, hr in sim_inside_t[::3]:
			h = int(hr)
			m = int((hr - h)*60)

			# generate list for graphing the inside temperature
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
