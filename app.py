from flask import Flask, render_template, url_for, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, String, Float, DateTime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedule.db'

db = SQLAlchemy(app)
ma = Marshmallow(app)
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
        print(cycle)

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

@app.route('/', methods=['POST', 'GET'])
def index():
    global selDay
    if request.method == 'POST':
        d = int(request.form['day'])
        h = int(request.form['hour'])
        m = int(request.form['min'])
        t = float(request.form['temperature'])
        new_cycle = Cycle(d=d,h=h,m=m,t=t)
        print(new_cycle)
        try:
            db.session.add(new_cycle)
            db.session.commit()
            return redirect('/')
        except:
            return 'Could not add task to database'
        
    else:
        try:
            z = int(request.args.get('selector'))
            print('we did it' +str(z))
            selDay = z
        except:
            print("FAILED")
        print('\n\n selday {}'.format(selDay))
        cycles = Cycle.query.filter_by(d=selDay).all()
        print(cycles)
        return render_template("index.html", cycles=cycles)

@app.route('/day', methods=['GET'])
def day():
    global selDay
    print('-------------------------------------\n\n')
    selDay = int(request.args.get('selector'))
    print(selDay)
    return redirect('/')


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Cycle.query.get_or_404(id)

    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'Faile to update task'
    else:
        return render_template("update.html", task=task)


@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Cycle.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'Could not delete task'

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')