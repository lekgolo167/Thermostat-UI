import time as cTime
import json
import requests
import logging
from logging import Handler
from datetime import datetime, timedelta, date

from database import Cycle
from modules.heatingModel import HeatingModel


class SimulationDayController():
	def __init__(self, config_file_path: str, log_handler: Handler, log_level: int | str) -> None:
		self.logger = logging.getLogger(type(self).__name__)
		self.logger.addHandler(log_handler)
		self.logger.setLevel(log_level)
		self.apiKey = None
		self.lat = None
		self.lon = None
		self.wind_speed_warning = None
		self.get_weather = None
		self.get_forecast = None
		self.last_forecast_update = datetime.today() - timedelta(days=1)
		self.heating_model = HeatingModel(config_file_path, log_handler, log_level)
		self.days_data = [DayData(d) for d in range(8)]
		self.selected_day = 1
		self.temporary_temperature = 0.0
		self.load_config(config_file_path)
		self.weather_icons_dict = {
			'none': -1,
			'01d': 0, # clear-day
			'01n': 1, # clear-night
			'02d': 2, # partly cloudy day/few clouds
			'02n': 3, # partly cloudy night/few clouds
			'03d': 4, # scattered clouds day
			'03n': 5, # scattered clouds night
			'04d': 6, # cloudy day
			'04n': 7, # cloudy night
			'09d': 8, # shower rain
			'09n': 8, # shower rain
			'10d': 9, # rain day
			'10n': 10, # rain night
			'11d': 11, # thuderstorm
			'11n': 11, # thuderstorm
			'13d': 12, # snow
			'13n': 12, # snow
			'50d': 13, # mist/fog day
			'50n': 14, # mist/fog night
			'sleet': 15,
			'wind': 16,
		}
		self.forecast_url = 'https://api.openweathermap.org/data/3.0/onecall?lat={0}&lon={1}&appid={2}&units=imperial&exclude=current,minutely'
	
	def init(self, get_cycles: callable) -> None:
		today = date.today().strftime('%Y-%m-%d')
		for x in range(0,8):
			day = self.days_data[x]
			day.start_temperature = 69.0
			self.update_weather(today, day)
			cycles = get_cycles(x)
			self.update_schedule(cycles, day)

	def load_config(self, config_file_path: str) -> None:
		self.logger.debug(f'Loading configuration from file: {config_file_path}')
		with open(config_file_path, 'r') as config_file:
			config_obj = json.loads(config_file.read())
			self.apiKey = config_obj.get('api-key', 'null')
			self.lat = str(config_obj.get('lat', 0.0))
			self.lon = str(config_obj.get('lon', 0.0))
			self.wind_speed_warning = float(config_obj.get('wind-advisory', 100.0))

			if config_obj.get('debug-enabled', False):
				self.get_weather = self._weather_data_from_file
				self.get_forecast = self._get_weather_forecast_from_file
			else:
				self.get_weather = self._weather_data_from_file #self._get_weather_data TODO rewrite this with Open Weather Map API
				self.get_forecast = self._get_weather_forecast

	def get_day(self) -> 'DayData':
		return self.days_data[self.selected_day]

	def set_start_temperature(self, temperature: float) -> None:
		day = self.days_data[self.selected_day]
		day.start_temperature = temperature
		self.update_inside_temperature(day)
		self.logger.debug(f'Setting simulation initial temperature to: {temperature} for day: {day}')
	
	def check_dates(self) -> None:
		today = date.today().strftime('%Y-%m-%d')
		for day in range(0,7):
			if self.days_data[day].last_updated < int(cTime.time()) - 43200: # 12 hrs
				self.logger.debug(f'Updating simulation day: {day} with date: {today}')
				self.update_weather(today, self.days_data[day])
				self.update_inside_temperature(self.days_data[day])

	def update_schedule(self, cycles: list['Cycle'], day: 'DayData'=None) -> None:
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

	def update_weather(self, _date: str, day: 'DayData'=None) -> None:
		if day is None:
			day = self.days_data[self.selected_day]

		outside_t = []
		uv =[]
		outside_t, uv = self.get_weather(_date)

		day.outside_temperatures = outside_t
		day.uv_indices = uv
		day.last_updated = int(cTime.time())
		day.g_outside_temperatures = []
		day.days_date = _date

		for hr in range(0,24):
			# generate list for graphing the outside temperature
			timestamp = str(hr).zfill(2) + ':00'
			day.g_outside_temperatures.append({'x': timestamp, 'y': outside_t[hr]})


	def update_inside_temperature(self, day: 'DayData'=None) -> None:
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

	def _get_weather_forecast_from_file(self) -> str:
		filename = f'archive/3-0-current.json'
		self.logger.debug(f'Loading weather forecast from file: {filename}')

		with open(filename, 'r') as infile:
			text = infile.read()
			data = json.loads(text)
			
			return self._format_weather_forecast(data), 200

	def _get_weather_forecast(self) -> str:
		last_request_date:timedelta = datetime.today() - self.last_forecast_update
		if last_request_date.seconds < 3600*12 and last_request_date.days == 0:
			return '{"message":"Only 1 call allowed every 12 hours!"}', 409
		self.last_forecast_update = datetime.today()
		r = requests.get(url=self.forecast_url.format(self.lat, self.lon, self.apiKey))
		if r.status_code >= 400:
			self.logger.error(f'Forecast API HTTP status code ({r.status_code})')
			return self._get_weather_forecast_from_file()
		data = json.loads(r.text)

		return self._format_weather_forecast(data), 200

	def _format_weather_forecast(self, forecast: dict[str, any]) -> str:
		hourly = []
		hour = 0
		for hourlyData in forecast['hourly']:
			icon = None
			try:
				if hourlyData['wind_speed'] > self.wind_speed_warning:
					icon = self.weather_icons_dict['wind']
				else:
					icon = self.weather_icons_dict[hourlyData['weather'][0]['icon']]
			except KeyError:
				self.logger.error(f'Hourly weather icon not found for hour: {hour}')
				icon = self.weather_icons_dict['none']

			temperature = int(hourlyData['temp'])
			hourly.append({'i':icon, 't':temperature})
			hour += 1
			if hour >= 25:
				break

		daily = []
		day = datetime.today().weekday()+1
		for fdaily in forecast['daily'][:4]:
			icon = None
			try:
				icon = self.weather_icons_dict[fdaily['weather'][0]['icon']]
			except KeyError:
				print(f'Daily weather icon not found for day: {day}')
				icon = self.weather_icons_dict['none']
			tHigh = int(fdaily['temp']['max'])
			tLow =  int(fdaily['temp']['min'])
			if day == 7:
				day = 0
			daily.append({'d':day,'i':icon, 'H':tHigh, 'L':tLow})
			day += 1
		
		parsed_dict = {'hourly': hourly, 'daily':daily}
		json_data = json.dumps(parsed_dict)

		return json_data

	def _format_weather_data(self, hourlyData: list[dict[str, any]]) -> tuple[list[float], list[float]]:

		dailyTemperatures = []
		dailyUVindex = []
		for hourData in hourlyData:
			dailyTemperatures.append(hourData['temperature'])
			dailyUVindex.append(hourData['uvIndex'])

		return dailyTemperatures, dailyUVindex

	def _get_weather_data(self, date_str: str) -> tuple[list[float], list[float]]:

		self.logger.debug(f'Fetching weather data for: {date_str}')

		todayInSec = datetime.strptime(date_str, "%Y-%m-%d").timestamp()
		URL = 'https://api.darksky.net/forecast/'+ self.apiKey + '/' + self.lat + ',' + self.lon + ',' + str(int(todayInSec)) + '?exclude=currently,minutely,daily,alerts,flags'

		r = requests.get(url=URL)

		data = json.loads(r.text)
		hourlyData = data['hourly']['data']

		return self._format_weather_data(hourlyData)

	def _weather_data_from_file(self, date_str: str) -> tuple[list[float], list[float]]:

		date = datetime.strptime(date_str, "%Y-%m-%d")
		day = 1
		if date.day >= 15:
			day = 15
		filename = f'archive/2022-{date.month}-{day}.json'
		self.logger.debug(f'Loading weather data from file: {filename}')

		with open(filename, 'r') as infile:
			text = infile.read()
			data = json.loads(text)
			hourlyData = data['hourly']['data']
			return self._format_weather_data(hourlyData)

class DayData():
	def __init__(self, d: int):
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
