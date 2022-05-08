import time

from logging.handlers import RotatingFileHandler
from modules.heatingModel import HeatingModel
from modules.simulation_cpp import simulation
import sys

def test_benchmark():
	heatingModel = HeatingModel('./config.json', RotatingFileHandler(filename='/dev/null'), 'DEBUG')
	vals = heatingModel.get_values()
	starting_temperature = 68.0
	sched = [(0.0, 62.0), (12.0, 68.0), (18.5, 70.0), (22.0, 64.0)]
	temps = [31.32, 32.28, 29.47, 29.61, 30.68, 30.05, 29.57, 29.98, 29.09, 28.85, 31.42, 32.74, 34.01, 35.13, 36.39, 36.15, 36.64, 35.74, 33.59, 31.35, 28.75, 26.8, 27.05, 26.09]
	uv = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]

	print('Testing with these parameters:')
	print(vals)
	start = time.time()
	for _ in range(500):
		data, runtime_cpp = simulation.simulate(starting_temperature, sched, temps, uv, vals)
	cpp_time = time.time() - start
	print('CPP time: {:.3f}s'.format(cpp_time))

	start = time.time()
	for _ in range(500):
		data, runtime_py = heatingModel.simulate(starting_temperature, sched, temps, uv)
	py_time = time.time() - start
	print('Py time: {:.3f}s'.format(py_time))
	print('C++ is {:.1f}x times faster'.format(py_time/cpp_time))

	assert py_time > cpp_time
	assert runtime_py == runtime_cpp
