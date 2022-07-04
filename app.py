
from asyncio.log import logger
import atexit
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify, request, redirect
import time as cTime
import json
import logging

from urllib3 import Retry

from database import db, ma, db_cli, CyclesSchema, DayIDsSchema
from modules.cyclesController import CyclesController
from modules.connectionManager import ConnectionManager
from modules.simulationDayController import SimulationDayController

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
LOG_LEVEL = logging.INFO
with open('config.json', 'r') as config_file:
    config_obj = json.loads(config_file.read())
    DEBUG_ENABLED = config_obj.get('debug-enabled', False)
    TIME_ZONE = config_obj.get('time-zone-from-gmt', 0) * 3600 # convert to seconds
    if DEBUG_ENABLED:
        LOG_LEVEL = logging.DEBUG
    else:
        LOG_LEVEL = logging.INFO

log_handler = RotatingFileHandler(filename='app.log', mode='a', maxBytes=5*1024*1024, backupCount=2)
log_format = logging.Formatter('%(asctime)s %(levelname)s %(name)s-> %(message)s')
log_handler.setFormatter(log_format)
app_log = logging.getLogger('App')
app_log.setLevel(LOG_LEVEL)
app_log.addHandler(log_handler)
thermostat_log = logging.getLogger('Thermostat')
thermostat_log.setLevel(LOG_LEVEL)
thermostat_log.addHandler(log_handler)

cycles_controller = CyclesController('config.json', log_handler, LOG_LEVEL)
simulation_controller = SimulationDayController('config.json', log_handler, LOG_LEVEL)
connection_manager = ConnectionManager('config.json', log_handler, LOG_LEVEL)

def startup():
    app_log.info('Server starting up.....')
    simulation_controller.check_dates()
    simulation_controller.init(cycles_controller.get_cycles)

@app.route('/', methods=['GET'])
def index():
    
    simulation_controller.check_dates()
    sel_day = simulation_controller.selected_day
    sim_params = simulation_controller.heating_model.get_values()
    cycles = cycles_controller.get_cycles(sel_day)

    day = simulation_controller.get_day()
    min_t, mid_t, max_t = cycles_controller.get_min_mid_max()

    return render_template('index.jinja', cycles=cycles, days=DAYS, selDay=sel_day, min_t=min_t, mid_t=mid_t, max_t=max_t,
                            runtime=day.runtime, today=day.days_date, startTemp=day.start_temperature, sim_params=sim_params)

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    connection_manager.heartbeat()
    return 'healthy'

@app.route('/plot', methods=['GET'])
def plot():
    day = simulation_controller.get_day()
    return jsonify({'schedule': day.g_schedule, 'outside': day.g_outside_temperatures, 'inside': day.g_inside_temperatures})

@app.route('/getForecast', methods=['GET'])
def getForecast():
    app_log.info('Fetching weather forecast')
    return simulation_controller._get_weather_forecast()

@app.route('/getCycles/<int:day>', methods=['GET'])
def getCycles(day):
    app_log.info(f'Fetching cycles for day: {day}')
    cycles = cycles_controller.get_cycles(day)
    return jsonify(cycles=cycles_schema.dump(cycles))

@app.route('/setDay/<int:day>', methods=['GET'])
def setDay(day):
    if day >= 0 and day <= 7:
        simulation_controller.selected_day = day
        return '{}', 200
    else:
        app_log.error(f'Invalid day set: {day}')
        return jsonify(message='Invalid day!'), 400

@app.route('/getDayIDs', methods=['GET'])
def getDayIDs():
    app_log.info('Fetching day IDs')
    dayIDs = cycles_controller.get_day_ids()

    return jsonify(dayIDs_schema.dump(dayIDs))

@app.route('/getEpoch', methods=['GET'])
def getEpoch():
    timezone = TIME_ZONE
    is_dst = cTime.localtime().tm_isdst
    if is_dst == 1:
        timezone -= 3600 # make it minus one hour for daylight savings\
    epoch = int(cTime.time()-timezone)
    app_log.info(f'Fetching epoch: {epoch}')
    return jsonify(epoch=epoch)

@app.route('/getTemporary', methods=['GET'])
def getTemporary():
    app_log.info('Fetching temporary temperature')
    tmp = simulation_controller.temporary_temperature
    simulation_controller.temporary_temperature = 0.0

    return jsonify(temporary=tmp)

@app.route('/setTemporaryTemp/<int:tmp>', methods=['GET'])
def setTemporaryTemp(tmp):
    if cycles_controller.validate_range(tmp):
        simulation_controller.temporary_temperature = float(tmp)
        connection_manager.updatedTemporary()
        return jsonify(message='Thermostat temperature has been set!'), 202
    else:
        app_log.warning(f'Invalid temperature: {tmp}')
        return jsonify(message='Invalid temperature range!'), 400

@app.route('/newCycle/<int:t>/<int:h>/<int:m>', methods=['POST', 'GET'])
def newCycle(t, h, m):
    sel_day = simulation_controller.selected_day
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
            cycles_controller.copy_day_to(simulation_controller.selected_day, day)
            update_simulation(day)

    return redirect('/')

@app.route('/setDate', methods=['POST'])
def setDate():
    date_picked = request.form['datePicker']
    app_log.debug(f'Set date to: {date_picked}')
    simulation_controller.update_weather(date_picked)
    simulation_controller.update_inside_temperature()
    
    return redirect('/')

@app.route('/startTemp', methods=['POST'])
def setStartTemp():
    startTemp = float(request.form['startTempPicker'])
    simulation_controller.set_start_temperature(startTemp)
    
    return redirect('/')

@app.route('/simParams', methods=['POST'])
def simParams():
    simulation_controller.heating_model.set_values(request.form)
    update_simulation()
    return redirect('/')

@app.route('/log', methods=['POST'])
def log_it():
    try:
        level = logging.getLevelName(request.form['level'].upper())
        msg = request.form['msg']
        if type(level) is int:
            thermostat_log.log(level=level, msg=msg)
            return '', 200
        else:
            return 'Unknown log level.', 400
    except Exception as e:
        return str(e), 400

def update_simulation(day=None):
    if day is None:
        day = simulation_controller.selected_day
    cycles = cycles_controller.get_cycles(day)
    simulation_controller.update_schedule(cycles, simulation_controller.days_data[day])

def server_shutdown():
    app_log.info('Server is shutting down...')

if __name__ == "__main__":
    atexit.register(server_shutdown)
    app.before_first_request(startup)
    try:
        app.run(debug=DEBUG_ENABLED, host='0.0.0.0')
    except Exception as e:
        app_log.error(e)
        app_log.exception('An exception has occurred. Server shutting down...')