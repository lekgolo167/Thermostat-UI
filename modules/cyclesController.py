import json
from datetime import time
from database import db, Cycle, DayIDs

class CyclesController():

	_MSG_INVALID_RANGE = 'Invalid temperature!'
	_MSG_INVALID_TIME = 'Invalid hours or minutes!'
	_MSG_CYCLE_EXISTS = 'Cycle already exists!'
	_MSG_FAILED_DELETE = 'Failed to delete cycle!'
	_MSG_FAILED_UPDATE = 'Failed to update cycle!'
	_MSG_FAILED_CREATE = 'Failed to create cycle!'
	_MSG_UPDATED_CYCLE = 'Cycle updated!'
	_MSG_DELETED_CYCLE = 'Cycle deleted!'
	_MSG_CREATED_CYCLE = 'Cycle created!'
	_MSG_UNEDITABLE = 'The time of the first cycle is not editable! Only the tempereature can be alterted.'
	_MSG_ID_NOT_FOUND = 'A cycle with ID: {} was not found!'

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

	def validate_range(self, temperature):
		return temperature >= self.min_t and temperature <= self.max_t

	def _validate_time(self, h, m):
		return h >= 0 and h <= 23 and m >= 0 and m <= 59

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
		if not self.validate_range(t):
			return False, CyclesController._MSG_INVALID_RANGE, 400
		if not self._validate_time(h, m):
			return False, CyclesController._MSG_INVALID_TIME, 400
			
		try:
			cycle = Cycle.query.get(id)
			if cycle is None:
				return False, CyclesController._MSG_ID_NOT_FOUND.format(id), 404
			if cycle.h == 0 and cycle.m == 0:
				if not (h == 0 and m == 0):
					return False, CyclesController._MSG_UNEDITABLE, 400
			cycle.h = h
			cycle.m = m
			cycle.t = t
			self._update_day_ids(cycle.d)
			db.session.commit()
			return True, CyclesController._MSG_UPDATED_CYCLE, 200
		except:
			return False, CyclesController._MSG_FAILED_UPDATE, 500

	def delete_cycle(self, id):
		try:
			cycle = Cycle.query.get(id)
			if cycle is None:
				return False, CyclesController._MSG_ID_NOT_FOUND.format(id), 404
			if cycle.h == 0 and cycle.m == 0:
				return False, CyclesController._MSG_UNEDITABLE, 400

			db.session.delete(cycle)
			self._update_day_ids(cycle.d)
			db.session.commit()
			return True, CyclesController._MSG_DELETED_CYCLE, 200
		except:
			return False, CyclesController._MSG_FAILED_DELETE, 500

	def new_cycle(self, day, t, h, m):
		if not self.validate_range(t):
			return False, CyclesController._MSG_INVALID_RANGE, 400
		if not self._validate_time(h, m):
			return False, CyclesController._MSG_INVALID_TIME, 400
		new_cycle = Cycle(d=day,h=h,m=m,t=t)
		if new_cycle.h == 0 and new_cycle.m == 0:
				return False, CyclesController._MSG_UNEDITABLE, 400
		try:
			db.session.add(new_cycle)
			db.session.commit()
			return True, CyclesController._MSG_CREATED_CYCLE, 200
		except:
			return False, CyclesController._MSG_FAILED_CREATE, 500

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
