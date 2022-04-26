# Enxor-Smart-Thermostat
### By: Matthew Crump
---
## Contents
1. [Overview](#overview)
2. [Heating-Model](#heating-model)
3. [Cpp-Model](#cpp-model)
4. [API](#api)
5. [Configuration](#configuration)

---
## Overview
At my duplex, I used to have a simple thermostat that used a mercery switch. I wanted to improve this by making a smart thermostat that could have a different schedule for each day of the week. As a college student at the time of creation, my schedule varied day by day. Another feature I wanted was to have the termostat automatically turn down after I had been away for a certain amount of time. The feature that is most unique to this project is the ability to predict/estimate how long the furnace might run for, given local weather data and the set schedule. This gives the user feedback as to whether the set schedule is efficient or not. All the data captured by the termostat is saved to an Influx DB running on a Raspberry Pi 4 through a Node-Red interface.

---
## Heating Model
To provide the user with feedback on the schedule they have chosen for a given day, I created a model that will simulate how the thermostat might respond. The simulation takes in local weather data, the schedule for the day, and the starting temperature and calculates how long the furnace might run for. After tunning the model, I was able to achive estimates that were within 5 to 20 minutes of the actual runtime for that day. Typical days in the winter can have runtimes of over 3 hours.
Below is a screenshot of the simulated runtime.
![Prediction Graph](docs/images/prediction_graph.png)
Below is a screenshot of the actual recorded data.
![Prediction Graph](docs/images/history_graph.png)
A comprehensive explaination of the math can be found [here](docs/Heating-Model.ipynb). GitHub markdown does not allow for rendering of LaTex math equtions. Using a Jupyter notebook overcomes this problem. This also frees up this readme as the extensive explaination can be found there.

---
## Cpp Model
The Python implementation can be quite slow, around 100 ms per simulation. I've created a C++ version of the model using the Python Boost library. The C++ version runs about 10 times faster. This aids in server startup as all 7 days are simulated in one go and serving the clients when dates change.
### Using the C++ model for simulation
* To use the the C++ model a value of ```true``` must be set for ```use-cpp-sim``` in the JSON config file.
* You may need to install the following libaries:
  * libboost-all-dev
  * python3.8-dev (change to what version you have)
* Run the provided make file to build the ```.so``` file that will be used by the web server.

---
## API

---
## Configuration
