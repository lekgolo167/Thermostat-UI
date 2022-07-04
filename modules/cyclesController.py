import json
import logging
from datetime import time
from logging import Handler

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

	def __init__(self, config_file_path: str, log_handler: Handler, log_level: int | str) -> None:
		self.logger = logging.getLogger(type(self).__name__)
		self.logger.addHandler(log_handler)
		self.logger.setLevel(log_level)
		self.min_t = None
		self.max_t = None
		self.mid_t = None
		self.load_config(config_file_path)

	def load_config(self, config_file_path: str) -> None:
		self.logger.debug(f'Loading configuration from file: {config_file_path}')
		with open(config_file_path, 'r') as config_file:
			config_obj = json.loads(config_file.read())
			self.min_t = config_obj.get('min-settable-temperature', 55)
			self.max_t = config_obj.get('max-settable-temperature', 90)
			self.mid_t = self.min_t + ((self.max_t - self.min_t)//2)
		self.logger.info(f'Temperature bounds set to min:{self.min_t}, max:{self.max_t}')

	def get_min_mid_max(self) -> tuple[int, int, int]:
		return self.min_t, self.mid_t, self.max_t
	
	def get_day_ids(self) -> list:
		return DayIDs.query.one()

	def get_cycles(self, day: int) -> list['Cycle']:
		cycles = Cycle.query.filter_by(d=day).all()
		cycles.sort(key=lambda x: time(hour=x.h,minute=x.m))
		return cycles

	def validate_range(self, temperature: float) -> bool:
		if temperature >= self.min_t and temperature <= self.max_t:
			return True
		
		self.logger.warning(f'Rejecting cycle with temperature: {temperature}')
		return  False

	def _validate_time(self, h: int, m: int) -> bool:
		if h >= 0 and h <= 23 and m >= 0 and m <= 59:
			return True

		self.logger.warning(f'Rejecting cycle with time: {h}:{m}')
		return False

	def _update_day_ids(self, day: int) -> None:
		self.logger.info(f'Updating day ID for: {day}')
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

	def update_cycles(self, id: int, t: float, h: int, m: int) -> tuple[bool, str, int]:
		if not self.validate_range(t):
			return False, CyclesController._MSG_INVALID_RANGE, 400
		if not self._validate_time(h, m):
			return False, CyclesController._MSG_INVALID_TIME, 400
			
		try:
			cycle = Cycle.query.get(id)
			if cycle is None:
				msg = CyclesController._MSG_ID_NOT_FOUND.format(id)
				self.logger.warning(msg)
				return False, msg, 404
			if cycle.h == 0 and cycle.m == 0:
				if not (h == 0 and m == 0):
					self.logger.warning(f'{CyclesController._MSG_UNEDITABLE} ID:{id}')
					return False, CyclesController._MSG_UNEDITABLE, 400
			cycle.h = h
			cycle.m = m
			cycle.t = t
			self._update_day_ids(cycle.d)
			db.session.commit()
			self.logger.info(CyclesController._MSG_UPDATED_CYCLE)
			self.logger.debug(cycle)
			return True, CyclesController._MSG_UPDATED_CYCLE, 200
		except:
			self.logger.error(CyclesController._MSG_FAILED_UPDATE)
			return False, CyclesController._MSG_FAILED_UPDATE, 500

	def delete_cycle(self, id: int) -> tuple[bool, str, int]:
		try:
			cycle = Cycle.query.get(id)
			if cycle is None:
				msg = CyclesController._MSG_ID_NOT_FOUND.format(id)
				self.logger.warning(msg)
				return False, msg, 404
			if cycle.h == 0 and cycle.m == 0:
				self.logger.warning(f'{CyclesController._MSG_UNEDITABLE} ID:{id}')
				return False, CyclesController._MSG_UNEDITABLE, 400

			db.session.delete(cycle)
			self._update_day_ids(cycle.d)
			db.session.commit()
			self.logger.info(CyclesController._MSG_DELETED_CYCLE)
			self.logger.debug(cycle)
			return True, CyclesController._MSG_DELETED_CYCLE, 200
		except:
			self.logger.error(CyclesController._MSG_FAILED_DELETE)
			return False, CyclesController._MSG_FAILED_DELETE, 500

	def new_cycle(self, day: int, t: float, h: int, m: int) -> tuple[bool, str, int]:
		if not self.validate_range(t):
			return False, CyclesController._MSG_INVALID_RANGE, 400
		if not self._validate_time(h, m):
			return False, CyclesController._MSG_INVALID_TIME, 400
		new_cycle = Cycle(d=day,h=h,m=m,t=t)
		if new_cycle.h == 0 and new_cycle.m == 0:
			self.logger.warning(f'{CyclesController._MSG_UNEDITABLE} ID:{id}')
			return False, CyclesController._MSG_UNEDITABLE, 400
		try:
			db.session.add(new_cycle)
			db.session.commit()
			self.logger.info(CyclesController._MSG_CREATED_CYCLE)
			self.logger.debug(new_cycle)
			return True, CyclesController._MSG_CREATED_CYCLE, 200
		except:
			self.logger.error(CyclesController._MSG_FAILED_CREATE)
			return False, CyclesController._MSG_FAILED_CREATE, 500

	def copy_day_to(self, from_day: int, this_day: int) -> None:
		self.logger.debug(f'Copying day: {from_day} to day: {this_day}')
		cycles = Cycle.query.filter_by(d=this_day).all()
		# remove all cycles for that day
		for cycle in cycles:
			db.session.delete(cycle)
		
		cycles = Cycle.query.filter_by(d=from_day).all()
		# copy all cycles for that day
		for cycle in cycles:
			copied_cycle = Cycle(d=this_day,h=cycle.h,m=cycle.m,t=cycle.t)
			db.session.add(copied_cycle)

		# save and update
		db.session.commit()
