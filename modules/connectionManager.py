import json
import socket

MSG_TEMPORARY = bytes('1', 'utf-8')
MSG_SCHED_UPDATE = bytes('2', 'utf-8')
MSG_NODE_RED = bytes('3', 'utf-8')
MSG_FLASK = bytes('4', 'utf-8')
MSG_SERVER_UP = bytes('5', 'utf-8')

class ConnectionManager():
	def __init__(self, config_file_path) -> None:
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.thermostat_ip_addr = None
		with open(config_file_path, 'r') as config_file:
			config_obj = json.loads(config_file.read())
			self.thermostat_hb_port = config_obj.get('thermostat-hb-por', 2391)
			self.thermostat_port = config_obj.get('thermostat-listen-port', 2390)
			self.thermostat_hostname = config_obj.get('thermostat-hostname', 'arduino-88fc')
		try:
			self.thermostat_ip_addr = socket.gethostbyname(self.thermostat_hostname)
			self.sock.sendto(MSG_SERVER_UP, (self.thermostat_ip_addr, self.thermostat_port))
		except:
			pass

	def heartbeat(self) -> None:
		self.sock.sendto(MSG_FLASK, (self.thermostat_ip_addr, self.thermostat_hb_port))

	def updatedTemporary(self) -> None:
		self.sock.sendto(MSG_TEMPORARY, (self.thermostat_ip_addr, self.thermostat_port))
		
	def updatedSchedule(self) -> None:
		self.sock.sendto(MSG_SCHED_UPDATE, (self.thermostat_ip_addr, self.thermostat_port))