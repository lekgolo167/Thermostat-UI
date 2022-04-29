
from flask import Flask, render_template, jsonify, request, redirect
import time as cTime
import json

from database import db, ma, db_cli, CyclesSchema, DayIDsSchema
from modules.cyclesController import CyclesController
from modules.connectionManager import ConnectionManager
from modules.cachedController import ChachedDaysController
from modules.weather import get_weather_forecast

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedule.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
ma.init_app(app)
cycles_schema = CyclesSchema(many=True)
dayIDs_schema = DayIDsSchema()
app.register_blueprint(db_cli, cli_group='db')

DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', "Try"]

DEBUG_ENABLED = False
TIME_ZONE = 0
with open('config.json', 'r') as config_file:
    config_obj = json.loads(config_file.read())
    DEBUG_ENABLED = config_obj.get('debug-enabled', False)
    TIME_ZONE = config_obj.get('time-zone-gmt', 0) * 3600 # convert to seconds

cycles_controller = CyclesController('config.json')
days_controller = ChachedDaysController('config.json', DEBUG_ENABLED)
connection_manager = ConnectionManager('config.json')

@app.route('/', methods=['GET'])
def index():
    
    days_controller.check_dates()
    days_controller.init(cycles_controller.get_cycles)
    sel_day = days_controller.selected_day
    
    cycles = cycles_controller.get_cycles(sel_day)

    day = days_controller.get_day()
    min_t, mid_t, max_t = cycles_controller.get_min_mid_max()

    return render_template("index.jinja", cycles=cycles, days=DAYS, selDay=sel_day, min_t=min_t, mid_t=mid_t, max_t=max_t,
                            runtime=day.runtime, today=day.days_date, startTemp=day.start_temperature)

@app.route('/simParams')
def simParams():
    print('reloading simulation parameters')
    days_controller.update_sim_params()
    return '{}'

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    connection_manager.heartbeat()
    return 'healthy'

@app.route('/plot', methods=['GET'])
def plot():
    day = days_controller.get_day()
    return jsonify({'schedule': day.g_schedule, 'outside': day.g_outside_temperatures, 'inside': day.g_inside_temperatures})

@app.route('/getForecast', methods=['GET'])
def getForecast():
    forecast = get_weather_forecast(days_controller.apiKey, days_controller.lat, days_controller.lon)
    return forecast

@app.route('/getCycles/<int:day>', methods=['GET'])
def getCycles(day):

    cycles = cycles_controller.get_cycles(day)
    return jsonify(cycles=cycles_schema.dump(cycles))

@app.route('/setDay/<int:day>', methods=['GET'])
def setDay(day):
    if day >= 0 and day <= 7:
        days_controller.selected_day = day
        return '{}', 200
    else:
        return jsonify(message='Invalid day!'), 400

@app.route('/getDayIDs', methods=['GET'])
def getDayIDs():

    dayIDs = cycles_controller.get_day_ids()

    return jsonify(dayIDs_schema.dump(dayIDs))

@app.route('/getEpoch', methods=['GET'])
def getEpoch():
    timezone = TIME_ZONE
    is_dst = cTime.localtime().tm_isdst
    if is_dst == 1:
        timezone -= 3600 # make it minus one hour for daylight savings

    return jsonify(epoch=int(cTime.time()-timezone))

@app.route('/getTemporary', methods=['GET'])
def getTemporary():

    tmp = days_controller.temporary_temperature
    days_controller.temporary_temperature = 0.0

    return jsonify(temporary=tmp)

@app.route('/setTemporaryTemp/<int:tmp>', methods=['GET'])
def setTemporaryTemp(tmp):
    if cycles_controller.validate_range(tmp):
        days_controller.temporary_temperature = float(tmp)
        connection_manager.updatedTemporary()
        return jsonify(message='Thermostat temperature has been set!'), 202
    else:
        return jsonify(message='Invalid temperature range!'), 400

@app.route('/newCycle/<int:t>/<int:h>/<int:m>', methods=['POST', 'GET'])
def newCycle(t, h, m):
    sel_day = days_controller.selected_day
    valid, msg, status_code = cycles_controller.new_cycle(sel_day, t, h, m)
    if valid:
        connection_manager.updatedSchedule()
        update_simulation()
    
    return jsonify(message=msg), status_code

@app.route('/update/<int:_id>/<int:t>/<int:h>/<int:m>', methods=['GET', 'POST'])
def update(_id, t, h, m):
    valid, msg, status_code = cycles_controller.update_cycles(_id, t, h, m)
    if valid:
        connection_manager.updatedSchedule()
        update_simulation()
    
    return jsonify(message=msg), status_code


@app.route('/delete/<int:id>')
def delete(id):
    valid, msg, status_code = cycles_controller.delete_cycle(id)
    if valid:
        connection_manager.updatedSchedule()
        update_simulation()
    
    return jsonify(message=msg), status_code

@app.route('/copyDayTo', methods=['POST'])
def copyDayTo():
    for day in range(len(DAYS)):
        checked = request.form.get(DAYS[day])
        if checked:
            cycles_controller.copy_day_to(days_controller.selected_day, day)
            update_simulation(day)

    return '{}'

@app.route('/setDate', methods=['POST'])
def setDate():
    date_picked = request.form['datePicker']
    days_controller.update_weather(date_picked)
    days_controller.update_inside_temperature()
    
    return redirect('/')

@app.route('/startTemp', methods=['POST'])
def setStartTemp():
    startTemp = float(request.form['startTempPicker'])
    days_controller.set_start_temperature(startTemp)
    
    return redirect('/')

def update_simulation(day=None):
    if day is None:
        day = days_controller.selected_day
    cycles = cycles_controller.get_cycles(day)
    days_controller.update_schedule(cycles, days_controller.days_data[day])

if __name__ == "__main__":
    app.run(debug=DEBUG_ENABLED, host='0.0.0.0')
