import json
from datetime import time
from database import db, Cycle, DayIDs

class CyclesController():
	def __init__(self, config_file_path) -> None:

		with open(config_file_path, 'r') as config_file:
			config_obj = json.loads(config_file.read())
			self.min_t = config_obj.get('min-settable-temperature', 55)
			self.max_t = config_obj.get('max-settable-temperature', 90)
			self.mid_t = self.min_t + ((self.max_t - self.min_t)//2)

	
	def get_min_mid_max(self):
		return self.min_t, self.mid_t, self.max_t
	
	def get_day_ids(self):
		return DayIDs.query.one()

	def get_cycles(self, day):
		cycles = Cycle.query.filter_by(d=day).all()
		cycles.sort(key=lambda x: time(hour=x.h,minute=x.m))
		return cycles

	def _update_day_ids(self, day):
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

	def update_cycles(self, id, t, h, m):
		cycle = Cycle.query.get_or_404(id)

		cycle.h = h
		cycle.m = m
		cycle.t = t

		try:
			self._update_day_ids(cycle.d)
			db.session.commit()
			return '{}'
		except:
			return 'Failed to update cycle'

	def delete_cycle(self, id):
		cycle = Cycle.query.get_or_404(id)

		try:
			self._update_day_ids(cycle.d)
			db.session.delete(cycle)
			db.session.commit()
			return '{}'
		except:
			return 'Could not delete cycle'

	def new_cycle(self, day, t, h, m):
		new_cycle = Cycle(d=day,h=h,m=m,t=t)
		print(new_cycle)
		try:
			db.session.add(new_cycle)
			db.session.commit()
			return '{}'
		except:
			return 'Could not add cycle to database'

	def copy_day_to(self, from_day, this_day):
		cycles = Cycle.query.filter_by(d=this_day).all()
		# remove all cycles for that day
		for cycle in cycles:
			db.session.delete(cycle)
		
		cycles = Cycle.query.filter_by(d=from_day.selected_day).all()
		# copy all cycles for that day
		for cycle in cycles:
			copied_cycle = Cycle(d=this_day,h=cycle.h,m=cycle.m,t=cycle.t)
			db.session.add(copied_cycle)

		# save and update
		db.session.commit()
