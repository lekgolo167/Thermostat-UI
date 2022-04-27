from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, String, Float, DateTime

db = SQLAlchemy()
ma = Marshmallow()

db_cli = Blueprint('db_cli', __name__, cli_group='db')

@db_cli.cli.command('create')
def db_create():
    db.create_all()
    print('Database created!')

@db_cli.cli.command('drop')
def db_drop():
    db.drop_all()
    print('Database dropped')

@db_cli.cli.command('seed')
def db_seed():
    
    for day in range(0, 8):
        cycle = Cycle(d=day,h=0, m=0,t=60.0)
        db.session.add(cycle)

    dayIDs = DayIDs(sun=1,mon=1,tue=1,wed=1,thu=1,fri=1,sat=1)
    db.session.add(dayIDs)

    db.session.commit()
    print('Database seeded!')

class CyclesSchema(ma.Schema):
    class Meta:
        fields = ('id','h','m','t')

class DayIDsSchema(ma.Schema):
    class Meta:
        fields = ('sun','mon','tue','wed','thu','fri','sat')

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
