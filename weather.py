import json
import requests
import time

def getWeatherData():
    f = open("key.txt", 'r')
    apiKey = f.readline().rstrip()
    lat = f.readline().rstrip()
    lon = f.readline().rstrip()

    todayInSec =  int(time.time())
    threeDayTemperatures = []
    threeDayUVindex = []
    timestamps = [str(todayInSec - 86400), str(todayInSec), str(todayInSec + 86400)]

    for i in range(0, 3):
        URL = 'https://api.darksky.net/forecast/'+ apiKey + '/' + lat + ',' + lon + ','
        URL += timestamps[i]

        r = requests.get(url=URL)

        data = json.loads(r.text)
        hourlyData = data['hourly']['data']

        dailyTemperatures = []
        dailyUVindex = []
        for hourData in hourlyData:
            dailyTemperatures.append(hourData['temperature'])
            dailyUVindex.append(hourData['uvIndex'])

        threeDayUVindex.append(dailyUVindex)
        threeDayTemperatures.append(dailyTemperatures)

    day1 = threeDayTemperatures[0]
    day2 = threeDayTemperatures[1]
    day3 = threeDayTemperatures[2]
    uv1 = threeDayUVindex[0]
    uv2 = threeDayUVindex[1]
    uv3 = threeDayUVindex[2]

    avgTemps = []
    avgUVs = []
    for i in range(0,len(day1)):
        avgT = (day1[i]+day2[i]+day3[i])/3
        avgUV = (uv1[i] + uv2[i] + uv3[i])/3
        avgTemps.append(avgT)
        avgUVs.append(avgUV)
        

    print(avgTemps)
    print(avgUVs)

    avgUVs.pop(0)
    avgUVs.append(0.0)

    return avgTemps, avgUVs
