from datetime import datetime, time, date
import time as cTime

from model import calulateModel
from weather import getWeatherData

class ChachedDaysController():
	def __init__(self, get_cycles):

		self.days_data = [DayData() for _ in range(8)]
		self.selected_day = 0

		today = date.today().strftime('%Y-%m-%d')
		for x in range(8):
			day = self.days_data[x]
			self.update_weather(today, day)
			cycles = get_cycles(x)
			self.update_schedule(cycles, day)
	
	def get_day(self):
		return self.days_data[self.selected_day]

	def set_start_temperature(self, temperature):
		day = self.days_data[self.selected_day]
		day.start_temperature = temperature
		self.update_inside_temperature(day)
	
	def check_dates(self):
		print("CHECKING DATES")
		today = date.today().strftime('%Y-%m-%d')
		for day in range(7):
			if self.days_data[day].last_updated < int(cTime.time()) - 43200: # 12 hrs
				
				self.update_weather(today, self.days_data[day])
				self.update_inside_temperature(day)

	def update_schedule(self, cycles, day=None):
		print("UPDATING SCHEDULE FOR: ", self.selected_day)
		if day is None:
			day = self.days_data[self.selected_day]

		day.g_schedule = []
		day.sim_schedule = []

		for cycle in cycles:
			# generate list for graphing the schedule
			day.g_schedule.append((int(datetime(2020,1,1,cycle.h,cycle.m,0).timestamp() * 1000.0), cycle.t))
			hr = cycle.h + (cycle.m / 60)
			day.sim_schedule.append((hr, cycle.t))

		# This is so the canvasjs shows the graph all the way to the end
		day.g_schedule.append((int(datetime(2020,1,1,23,59,59).timestamp() * 1000.0), 60.0))

		self.update_inside_temperature(day)

	def update_weather(self, _date, day=None):
		print("UPDATING WEATHER FOR: ", self.selected_day)
		if day is None:
			day = self.days_data[self.selected_day]

		outside_t, uv = getWeatherData(_date)

		day.outside_temperatures = outside_t
		day.uv_indices = uv
		day.last_updated = int(cTime.time())
		day.g_outside_temperatures = []

		for hr in range(0,24):
			# generate list for graphing the outside temperature
			day.g_outside_temperatures.append(((int(datetime(2020,1,1,hr,0,0).timestamp() * 1000.0), outside_t[hr])))


	def update_inside_temperature(self, day=None):
		print("UPDATING INSIDE TEMPERATURES FOR: ", self.selected_day)
		if day is None:
			day = self.days_data[self.selected_day]

		day.g_inside_temperatures = []

		sim_inside_t, day.runtime = calulateModel(day.start_temperature, day.sim_schedule, day.outside_temperatures, day.uv_indices)

		for inside_t, hr in sim_inside_t:
			h = int(hr)
			m = int((hr - h)*60)

			# generate list for graphing the inside temperature
			day.g_inside_temperatures.append((int(datetime(2020,1,1,h,m,0).timestamp() * 1000.0), inside_t))


class DayData():
	def __init__(self):
		self.days_date = date.today().strftime('%Y-%m-%d')
		self.last_updated = 0
		self.outside_temperatures = []
		self.uv_indices = []
		self.sim_schedule = []
		self.g_schedule = []
		self.g_outside_temperatures = []
		self.g_inside_temperatures = []
		self.runtime = -1
		self.start_temperature = 70.0