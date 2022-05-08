#include <iostream>
#include <boost/python.hpp>
#include <deque>

using namespace boost::python;

double delta_time = 0.01;
double BTU = 25.0;
double thresh_L = 2.0;
double thresh_H = 2.0;
double runtime = 0.0;

double get_target_temp(double time_hr, list schedule) {
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

double H(double inside_t, double target, bool* furnace_on) {
	if (inside_t < (target - thresh_L) || (*furnace_on && inside_t < (target + thresh_H))) {
		runtime += delta_time;
		*furnace_on = true;
		return BTU;
	}
	*furnace_on = false;
	return 0.0;
}

tuple simulate(double start_temperature, list sched, list weather_t, list uv_index, dict vals) {
	// time of day in hours
	double time_hr = 0.0;
	// if the furnace is on
	bool furnace_on = false;
	
	BTU = extract<double>(vals.get("btu"));
	delta_time = extract<double>(vals.get("delta-time"));
	thresh_H = extract<double>(vals.get("thresh-upper"));
	thresh_L = extract<double>(vals.get("thresh-lower"));
	int sample_avg_size = extract<int>(vals.get("sample-avg"));
	int rolling_avg_size = extract<int>(vals.get("rolling-avg-size"));

	// insulation
	double k1 = extract<double>(vals.get("k1")); // wall
	double k2 = extract<double>(vals.get("k2")); // cieling
	double k3 = extract<double>(vals.get("k3")); // roof
	double f1 = extract<double>(vals.get("f1")); // uv walls
	double f2 = extract<double>(vals.get("f2")); // uv roof
	runtime = 0.0;

	// starting temperatures
	double inside_t = start_temperature;
	double attic_t = start_temperature - 4.0;

	// change in temperature
	double delta_t1, delta_t2;

	// used for heat capacity calculations
	std::deque<double> heat_retension(rolling_avg_size);
	std::deque<double> sample_arr(sample_avg_size);
	double accum = (inside_t - 2.0)*rolling_avg_size;
	double sample_avg = (inside_t)*sample_avg_size;
	std::fill_n(heat_retension.begin(), rolling_avg_size, inside_t-2.0);
	std::fill_n(sample_arr.begin(), sample_avg_size, inside_t);

	// data to return
	runtime = 0.0;
	list data;
	while(time_hr < 24.0) {
		// extract variables
		int hour_index = int(time_hr);
		double outside_t = extract<double>(weather_t[hour_index]);
		double uv = extract<double>(uv_index[hour_index]);

		data.append(make_tuple(inside_t, time_hr));

		// heat_retension update rolling average
		double old = heat_retension.front();
		heat_retension.push_back(inside_t);
		accum = accum - old + inside_t;
		heat_retension.pop_front();

		old = sample_arr.front();
		sample_arr.push_back(inside_t);
		sample_avg = sample_avg - old + inside_t;
		sample_arr.pop_front();
		

		double c = (accum/rolling_avg_size) - inside_t;
		double inside_avg = sample_avg / sample_avg_size;
		double target = get_target_temp(time_hr, sched);
		double h = H(inside_avg, target, &furnace_on);
		//std::cout << inside_avg << std::endl;

		// calculate change in temperature
		delta_t1 = k1 * (outside_t - inside_t) + k2 * (attic_t-inside_t) + h + uv * f1 + c;
		delta_t2 = k2 * (inside_t - attic_t) + k3 * (outside_t - attic_t) + uv * f2;

		// scale the change in temperature
		delta_t1 *= delta_time;
		delta_t2 *= delta_time;

		// add the change in temperature
		inside_t += delta_t1;
		attic_t += delta_t2;

		// increment time
		time_hr += delta_time;
	}

	return make_tuple(data, runtime);
}

BOOST_PYTHON_MODULE(simulation)
{
		def("simulate", simulate);
}
