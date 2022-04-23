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

---
## Heating-Model
Wanted to be able to simulate how long the furnace would run for.
### Background

Newton's law of cooling states that the rate of change of the inside temperature is proportional to the difference between the outside temperature $T(t)$ and the inside temperature $x(t)$. That is, $x'(t)=k[T(t)-x(t)]$. The constant of proportionality k is called the heat transfer constant and is dependent on the amount of insulation in the walls. To describe the values that can be assigned to k, consider the simplified case where the outside temperature is constant with $T(t) = T$. Then, under the substitution $y(t)=x(t)-T$, Newton's law of cooling becomes $y'(t)=-ky(t)$. The solution to this differential equation is the exponential decay equations $y(t)=y_0e^{(-kt)}$. The half-life for such an eaution is $t_{1/2}=(ln2)/k$; that is $t_{1/2}$ is the amount of time it takes for the difference $y(t)=x(t)-T$ in temperatures to reduce to half of its original value. Typical values of $t_{1/2}$ range from 1 for an uninsulated room to 6 for a well-instulated room. Thus $0.115 \approx \frac{ln2}{6} \le k \le \frac{ln2}{1} \approx 0.694$ and k is inversely proportional to the amount of insulation in the walls. For our investigation we will use $k=0.46,0.35$, and $0.28$ to indicate minimal, average, and above-average insulation, respectively. These values correspond approximately to $t_{1/2}=1.5,2.0$, and $2.5$ hourse, respectively.
To avoid overcomplicating our model, we will ignore heat loss through the floor of the house. When the furnace is on, it adds heat to the living area at a constant rate $f$ (BTU/hr). if $c$ (degree/hr) is the heat capacity of the air in the living area (the mass of air times the specific heat of air), then if it were not for heat conduction through the walls and ceiling, the temperature of the air in the living area would rise at the constant rate $fc$. Furnaces are generally rated from 60,000 to 100,000 BTU/hr, and the heat capacity of air in a living space is typically in the range of $0.2-0.3\degree F$ per thousand BTU. In our investigation, we will use $f=80,000$ BTU/hr and $c=0.24\degree F$ per thousand BTU, yielding $fc=20\degree F$ per hour. Thus the rate at which the furnace changes the air temperature in the living area can be described by a step function
$ H(t)=\begin{cases} 
          20\degree F & \text{when the furnace is on} \\
          0\degree F & \text{when the furnace is off}
       \end{cases}$
### Setting up the problem
Let $x_1(t)$ denote the temperature in the living area at time $t$, and $x_2(t)$ denote the temperature in the attic. $H(t)$ denotes the rate at which the furnace raises the living area temperature;; $T(t)$ is the outdoor temperature; and $k_1$, $k_2$, and $k_3$ are the heat transfer constants associated with the house's sides, ceiling, and roof, respecively.
The living area temperature $x_1(t)$ is affected by the furnace, the outside temperature, and the attic temperature, while the attic temperature $x_2(t)$ is affected by the living area and outdoor temperatures. So by Newton's law of cooling, the rates which the living area and attic temperatures change over time are given by
$x'_1(t)=k_1[T(t)-x_1(t)] + k_2[x_2(t)-x_1(t)] + H(t)$
$x'_2(t)=k_2[x_1(t)-x_2(t)]+k_3[T(t)-x_2(t)]$
### Simplified case
We will initially assume that the sides of the house contain average insulation $(k_1=0.35)$, the ceiling contains minimal insulation $(k_2=0.46)$, and the roof contains above-average insulation $(k_3=0.28)$. With $T(t)=35$ and $H(t)=20$, we observe in Figure 2. that the temperature in the house reaches $68\degree$ after approximately 5.5 hours.
### A more realistic case
In reality, when the house temperature exceeds some threshold, a thermostat turns off the furnace. We can add a thermostat that turns off the furnace at $68\degree$ by modifying $H(t)$ as follows:
$ H(t)=\begin{cases} 
          20 & \text{if } x_1(t) \lt 68 \\
          0 & \text{if } x_1(t) \ge 68
       \end{cases}$
To simulate outdoor temperatur fluctuations, we will set
$T(t)=-17.5sin(\frac{\pi}{12}(t+3))+47$
We get the reulsts displayed in Figure 3, which shows that agter approximately 7 hours, the thermostat maintains the house temperature at approximately $68\degree$ while the attic temperatrue fluctuates with the outside temperature.

---
# If using C++ function for simulation
  * build the simulation.so file by running make
  * you may need to install 
    * libboost-all-dev
	* python3.6-dev
  * or just run the Python version in model.py but it is 4-5x times slower