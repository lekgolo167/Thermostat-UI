import json
import requests
import time
import datetime

def get_weather_data(today):
    f = open("key.txt", 'r')
    apiKey = f.readline().rstrip()
    lat = f.readline().rstrip()
    lon = f.readline().rstrip()

    todayInSec = datetime.datetime.strptime(today, "%Y-%m-%d").timestamp()
    print("SECONDS: " + str(todayInSec))
    URL = 'https://api.darksky.net/forecast/'+ apiKey + '/' + lat + ',' + lon + ',' + str(int(todayInSec))

    r = requests.get(url=URL)

    data = json.loads(r.text)
    hourlyData = data['hourly']['data']

    dailyTemperatures = []
    dailyUVindex = []
    for hourData in hourlyData:
        dailyTemperatures.append(hourData['temperature'])
        dailyUVindex.append(hourData['uvIndex'])

    return dailyTemperatures, dailyUVindex
