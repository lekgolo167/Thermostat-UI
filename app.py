from flask import Flask, render_template, url_for, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, String, Float, DateTime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedule.db'

db = SQLAlchemy(app)
ma = Marshmallow(app)

DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
selDay = 0

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
    
    for day in range(0, 7):
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

@app.route('/', methods=['POST', 'GET'])
def index():
    global selDay
    if request.method == 'POST':
        updateDayIDs(selDay)
        h = int(request.form['hour'])
        m = int(request.form['min'])
        t = float(request.form['temperature'])
        new_cycle = Cycle(d=selDay,h=h,m=m,t=t)
        print(new_cycle)
        try:
            db.session.add(new_cycle)
            db.session.commit()
            return redirect('/')
        except:
            return 'Could not add cycle to database'
        
    else:
        try:
            selDay = int(request.args.get('selector'))
        except:
            pass
        cycles = Cycle.query.filter_by(d=selDay).all()
        cycles = sort(cycles)
        cycles.append(Cycle(d=selDay,h=23,m=59,t=60.0))
        return render_template("index.html", cycles=cycles, days=DAYS, selDay=selDay)

@app.route('/getCycles/<int:day>', methods=['GET'])
def getCycles(day):
    cycles = Cycle.query.filter_by(d=day).all()
    return jsonify(cycles_schema.dump(cycles))


@app.route('/getDayIDs', methods=['GET'])
def getDayIDs():
    dayIDs = DayIDs.query.one()
    return jsonify(dayIDs_schema.dump(dayIDs))


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    cycle = Cycle.query.get_or_404(id)

    if request.method == 'POST':
        cycle.h = request.form['hour']
        cycle.m = request.form['min']
        cycle.t = request.form['temperature']

        try:
            updateDayIDs(cycle.d)
            db.session.commit()
            return redirect('/')
        except:
            return 'Faile to update cycle'
    else:
        return render_template("update.html", cycle=cycle)


@app.route('/delete/<int:id>')
def delete(id):
    cycle = Cycle.query.get_or_404(id)

    try:
        updateDayIDs(cycle.d)
        db.session.delete(cycle)
        db.session.commit()
        return redirect('/')
    except:
        return 'Could not delete cycle'


def sort(cycles):
    cycles.sort(key=lambda x: time(hour=x.h,minute=x.m))

    return cycles

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


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')