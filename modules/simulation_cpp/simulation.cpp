#include <iostream>
#include <boost/python.hpp>

using namespace boost::python;

const int N = 250;
const double delta_time = 0.01;
const double BTU = 25.0;
const double thresh_L = 2.0;
const double thresh_H = 2.0;
bool heat_on = false;
bool last_heating = false;
double runtime = 0.0;
double time_hr = 0.0;

double find_target_t(list schedule) {
	double target_t = 0.0;

	int n = len(schedule);

	for(int i=0; i < n; i++) {
		tuple t1 = extract<tuple>(schedule[i]);
		double _time = extract<double>(t1[0]);
		double set_temp = extract<double>(t1[1]);
		if (_time > time_hr) {
			break;
		}
		target_t = set_temp;
	}
	return target_t;
}

double H(double temp, list schedule) {
	double target_t = find_target_t(schedule);

	if (temp <= target_t - thresh_L) {
		runtime += delta_time;
		heat_on = true;
		return BTU;
	}
	else if (temp <= target_t + thresh_H && heat_on) {
		runtime += delta_time;
		return BTU;
	}
	else {
		heat_on = false;
		return 0.0;
	}
}

tuple simulate(double start_temperature, list sched, list weather_t, list uv_index) {
	// time of day in hours
	time_hr = 0.0;
	// if the furnace is on
	heat_on = false;
	last_heating = false;
	// insulation
	double k1 = 0.08; // wall
	double k2 = 0.18; // cieling
	double k3 = 0.03; // roof
	// starting temperatures
	double inside_t = start_temperature;
	double attic_t = start_temperature - 4.0;
	// change in temperature
	double delta_t1, delta_t2;
	// used for heat capacity calculations
	double heat_retension[N];
	int index = 0;
	double accum = (inside_t - 2.0)*N;
	std::fill_n(heat_retension, N, attic_t+2.0);
	// data to return
	bool save_every_other = true;
	runtime = 0.0;
	list data;

	while(time_hr < 23.99) {
		// extract variables
		int hour_index = int(time_hr);
		double outside_t = extract<double>(weather_t[hour_index]);
		double uv = extract<double>(uv_index[hour_index]);

		// not every data point needs to be graphed
		if (save_every_other) {
			data.append(make_tuple(inside_t, time_hr));
		}
		save_every_other = !save_every_other;

		// calculate change in temperature
		delta_t1 = k1 * (outside_t - inside_t) + k2 * (attic_t-inside_t) + H(inside_t, sched) + uv * 0.2;
		delta_t2 = k2 * (inside_t - attic_t) + k3 * (outside_t - attic_t) + uv * 0.9;

		// scale the change in temperature
		delta_t1 *= delta_time;
		delta_t2 *= delta_time;

		// heat_retension update rolling average
		if(index >= N) {
			index = 0;
		}
		double old = heat_retension[index];
		heat_retension[index++] = inside_t;
		accum = accum - old + inside_t;

		if(!heat_on) {
			double pen = (accum / N - inside_t) * delta_time;
			delta_t1 += pen*2.7;
		}

		// add the change in temperature plus heat from neighbors wall
		inside_t += delta_t1 + 0.0005*(72.0-inside_t);
		attic_t += delta_t2  + 0.0005*(69.0-attic_t);

		// if the heater just turned off, add a little time for it to shutdown
		if (!heat_on && last_heating) {
			runtime += 0.01;
		}

		// increment time
		time_hr += delta_time;
		last_heating = heat_on;
	}

	return make_tuple(data, runtime);
}

BOOST_PYTHON_MODULE(simulation)
{
		def("simulate", simulate);
}
