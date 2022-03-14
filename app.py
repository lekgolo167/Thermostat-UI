from flask import Flask, render_template, url_for, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time, date
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, String, Float, DateTime
import time as cTime
import socket
import argparse

from modules.cachedController import ChachedDaysController
from modules.weather import get_weather_forecast

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedule.db'

db = SQLAlchemy(app)
ma = Marshmallow(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database created!')

@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped')

@app.cli.command('db_seed')
def db_seed():
    
    for day in range(0, 8):
        cycle = Cycle(d=day,h=0, m=0,t=60.0)
        db.session.add(cycle)

    dayIDs = DayIDs(sun=1,mon=1,tue=1,wed=1,thu=1,fri=1,sat=1)
    db.session.add(dayIDs)

    db.session.commit()
    print('Database seeded!')

class Cycle(db.Model):
    id = Column(Integer, primary_key=True)
    d = Column(Integer)
    h = Column(Integer)
    m = Column(Integer)
    t = Column(Float)

    def __repr__(self):
        return str(self.d) + ' -> h:' + str(self.h) + ':' + str(self.m) + ', @%.1fF°' % self.t

class DayIDs(db.Model):
    id = Column(Integer, primary_key=True)
    sun = Column(Integer)
    mon = Column(Integer)
    tue = Column(Integer)
    wed = Column(Integer)
    thu = Column(Integer)
    fri = Column(Integer)
    sat = Column(Integer)

    def __repr__(self):
        return "0:{},1:{},2:{},3:{},4:{},5{},6{}".format(self.sun,self.mon,self.tue,self.wed,self.thu,self.fri,self.sat)

class CyclesSchema(ma.Schema):
    class Meta:
        fields = ('id','h','m','t')

class DayIDsSchema(ma.Schema):
    class Meta:
        fields = ('sun','mon','tue','wed','thu','fri','sat')

cycles_schema = CyclesSchema(many=True)
dayIDs_schema = DayIDsSchema()

DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', "Try"]

def sort(cycles):
    cycles.sort(key=lambda x: time(hour=x.h,minute=x.m))

    return cycles

def get_cycles(day):

    return sort(Cycle.query.filter_by(d=day).all())

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind('', )
parser = argparse.ArgumentParser()
parser.add_argument('--debug', '-d', action='store_true', default=False,
						help='Enables debugging which loads weather data from file rather than the API')
argument = parser.parse_args()
DEBUG_ENABLED = bool(argument.debug)

days_controller = ChachedDaysController(get_cycles, DEBUG_ENABLED)


@app.route('/', methods=['GET'])
def index():
    
    days_controller.check_dates()
    sel_day = days_controller.selected_day
    
    cycles = Cycle.query.filter_by(d=sel_day).all()
    cycles = sort(cycles)

    day = days_controller.get_day()

    return render_template("index.jinja", cycles=cycles, days=DAYS, selDay=sel_day, sched=day.g_schedule,
                            furn=day.g_inside_temperatures , outside=day.g_outside_temperatures,
                            runtime=day.runtime, today=day.days_date, startTemp=day.start_temperature)


@app.route('/heartbeat', methods=['GET'])
def heartbeat():

    sock.sendto(bytes(str(4), 'utf-8'), ("192.168.0.202", 2391))
    return redirect('/')

@app.route('/getForecast', methods=['GET'])
def getForecast():
    forecast = get_weather_forecast(days_controller.apiKey, days_controller.lat, days_controller.lon)
    return forecast

@app.route('/getCycles/<int:day>', methods=['GET'])
def getCycles(day):

    cycles = sort(Cycle.query.filter_by(d=day).all())
    return jsonify(cycles=cycles_schema.dump(cycles))

@app.route('/setDay/<int:day>', methods=['GET'])
def setDay(day):

    days_controller.selected_day = day
    return redirect('/')

@app.route('/getDayIDs', methods=['GET'])
def getDayIDs():

    dayIDs = DayIDs.query.one()

    return jsonify(dayIDs_schema.dump(dayIDs))

@app.route('/getEpoch', methods=['GET'])
def getEpoch():
    timezone = 25200 # 7 hours from GMT
    is_dst = cTime.localtime().tm_isdst
    if is_dst == 1:
        timezone -= 3600 # make it 6 hours for when daylight savings

    return jsonify(epoch=int(cTime.time()-timezone))

@app.route('/getTemporary', methods=['GET'])
def getTemporary():

    tmp = days_controller.temporary_temperature
    days_controller.temporary_temperature = 0.0

    return jsonify(temporary=tmp)

@app.route('/setTemporaryTemp/<int:tmp>', methods=['GET'])
def setTemporaryTemp(tmp):
    
    days_controller.temporary_temperature = float(tmp)
    sock.sendto(bytes(str(1), 'utf-8'), ("192.168.0.202", 2390))
    return redirect('/')

@app.route('/newCycle/<int:t>/<int:h>/<int:m>', methods=['POST', 'GET'])
def newCycle(t, h, m):
    sel_day = days_controller.selected_day
    updateDayIDs(sel_day)

    new_cycle = Cycle(d=sel_day,h=h,m=m,t=t)
    print(new_cycle)
    try:
        db.session.add(new_cycle)
        db.session.commit()
        sock.sendto(bytes(str(2), 'utf-8'), ("192.168.0.202", 2390))
        update_simulation()
        return redirect('/')
    except:
        return 'Could not add cycle to database'

@app.route('/update/<int:_id>/<int:t>/<int:h>/<int:m>', methods=['GET', 'POST'])
def update(_id, t, h, m):
    cycle = Cycle.query.get_or_404(_id)

    cycle.h = h
    cycle.m = m
    cycle.t = t

    try:
        updateDayIDs(cycle.d)
        db.session.commit()
        sock.sendto(bytes(str(2), 'utf-8'), ("192.168.0.202", 2390))
        update_simulation()
        return redirect('/')
    except:
        return 'Faile to update cycle'


@app.route('/delete/<int:id>')
def delete(id):
    cycle = Cycle.query.get_or_404(id)

    try:
        updateDayIDs(cycle.d)
        db.session.delete(cycle)
        db.session.commit()
        sock.sendto(bytes(str(2), 'utf-8'), ("192.168.0.202", 2390))
        update_simulation()
        return redirect('/')
    except:
        return 'Could not delete cycle'

@app.route('/copyDayTo', methods=['POST'])
def copyDayTo():
    for day in range(len(DAYS)):
        checked = request.form.get(DAYS[day])
        if checked:

            cycles = Cycle.query.filter_by(d=day).all()
            # remove all cycles for that day
            for cycle in cycles:
                db.session.delete(cycle)
            
            cycles = Cycle.query.filter_by(d=days_controller.selected_day).all()
            # copy all cycles for that day
            for cycle in cycles:
                copied_cycle = Cycle(d=day,h=cycle.h,m=cycle.m,t=cycle.t)
                db.session.add(copied_cycle)

            # save and update
            db.session.commit()
            updateDayIDs(day)
            update_simulation(day)

    return redirect('/')

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

def updateDayIDs(day):
    dayIDs = DayIDs.query.one()

    if day == 0:
        dayIDs.sun += 1
    elif day == 1:
        dayIDs.mon += 1
    elif day == 2:
        dayIDs.tue += 1
    elif day == 3:
        dayIDs.wed += 1
    elif day == 4:
        dayIDs.thu += 1
    elif day == 5:
        dayIDs.fri += 1
    elif day == 6:
        dayIDs.sat += 1

    db.session.commit()

def update_simulation(day=None):
    if day is None:
        day = days_controller.selected_day
    cycles = sort(Cycle.query.filter_by(d=day).all())
    days_controller.update_schedule(cycles, days_controller.days_data[day])


if __name__ == "__main__":
    app.run(debug=DEBUG_ENABLED, host='0.0.0.0')
