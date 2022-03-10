import json
import requests
import time
import datetime

weather_icons_dict = {
    'none': -1,
    'clear-day': 0,
    'clear-night': 1,
    'rain': 2,
    'snow': 3,
    'sleet': 4,
    'wind': 5,
    'fog': 6,
    'cloudy': 7,
    'partly-cloudy-day': 8,
    'partly-cloudy-night': 9,
    'thuderstorm': 10,
    'hail': 11
}

def get_weather_forecast(apiKey, lat, lon):

    URL = 'https://api.darksky.net/forecast/'+ apiKey + '/' + lat + ',' + lon + '?exclude=currently,minutely,alerts,flags'

    r = requests.get(url=URL)

    data = json.loads(r.text)

    parsed_dict = {}
    hourly = {}
    hour = 0
    for hourlyData in data['hourly']['data']:
        icon = None
        try:
            icon = weather_icons_dict[hourlyData['icon']]
        except KeyError:
            icon = weather_icons_dict['none']

        temperature = hourlyData['temperature']
        hourly[hour] = [icon, temperature]
        hour += 1
    
    daily = {}
    day = 0
    for forecast in data['daily']['data']:
        icon = None
        try:
            icon = weather_icons_dict[forecast['icon']]
        except KeyError:
            icon = weather_icons_dict['none']
        tHigh = forecast['temperatureHigh']
        tLow = forecast['temperatureLow']
        daily[day] = [icon, tHigh, tLow]
        day += 1
        if day == 3:
            break
    
    parsed_dict = {'hourly': hourly, 'daily':daily}
    json_data = json.dumps(parsed_dict)

    return json_data

def get_weather_data(today, apiKey, lat, lon):

    todayInSec = datetime.datetime.strptime(today, "%Y-%m-%d").timestamp()
    print("SECONDS: " + str(todayInSec))
    URL = 'https://api.darksky.net/forecast/'+ apiKey + '/' + lat + ',' + lon + ',' + str(int(todayInSec)) + '?exclude=currently,minutely,daily,alerts,flags'

    r = requests.get(url=URL)

    data = json.loads(r.text)
    hourlyData = data['hourly']['data']

    dailyTemperatures = []
    dailyUVindex = []
    for hourData in hourlyData:
        dailyTemperatures.append(hourData['temperature'])
        dailyUVindex.append(hourData['uvIndex'])

    return dailyTemperatures, dailyUVindex
