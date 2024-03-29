import json
import socket
import logging
from logging import Handler

MSG_TEMPORARY = bytes('1', 'utf-8')
MSG_SCHED_UPDATE = bytes('2', 'utf-8')
MSG_NODE_RED = bytes('3', 'utf-8')
MSG_FLASK = bytes('4', 'utf-8')
MSG_SERVER_UP = bytes('5', 'utf-8')

class ConnectionManager():
	def __init__(self, config_file_path: str, log_handler: Handler, log_level: int | str) -> None:
		self.logger = logging.getLogger(type(self).__name__)
		self.logger.addHandler(log_handler)
		self.logger.setLevel(log_level)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.thermostat_ip_addr = None
		self.thermostat_found = False
		with open(config_file_path, 'r') as config_file:
			config_obj = json.loads(config_file.read())
			self.thermostat_hb_port = config_obj.get('thermostat-hb-por', 2391)
			self.thermostat_port = config_obj.get('thermostat-listen-port', 2390)
			self.thermostat_hostname = config_obj.get('thermostat-hostname', 'arduino-88fc')
		self.logger.info(f'Thermostat hostname is set to: {self.thermostat_hostname}')
		if self.find_thermostat():
			self.logger.info('Notifying thermostat that this server has started')
			self.sock.sendto(MSG_SERVER_UP, (self.thermostat_ip_addr, self.thermostat_port))

	def find_thermostat(self) -> bool:
		if self.thermostat_found:
			return True
		try:
			self.thermostat_ip_addr = socket.gethostbyname(self.thermostat_hostname)
			self.thermostat_found = True
			self.logger.info(f'Thermostat IP address is: {self.thermostat_ip_addr}')
		except:
			self.logger.error(f'Failed to find the thermostat by hostname: {self.thermostat_hostname}')
			self.thermostat_found = False
		
		return self.thermostat_found

	def heartbeat(self) -> None:
		if self.find_thermostat():
			self.logger.debug('healthy')
			self.sock.sendto(MSG_FLASK, (self.thermostat_ip_addr, self.thermostat_hb_port))

	def updatedTemporary(self) -> None:
		if self.find_thermostat():
			self.logger.info('Notifying thermostat of temporarily set temperature')
			self.sock.sendto(MSG_TEMPORARY, (self.thermostat_ip_addr, self.thermostat_port))
		
	def updatedSchedule(self) -> None:
		if self.find_thermostat():
			self.logger.info('Notifying thermostat of schedule change')
			self.sock.sendto(MSG_SCHED_UPDATE, (self.thermostat_ip_addr, self.thermostat_port))