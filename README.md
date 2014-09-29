urban-lu-model
============

This piece of code is a computer model for simulating historical and future land use. The model takes one or more land use images and will output a "prediction" of land-use, for each user-defined time-step (e.g. a year). The model came to life after I wrote a thesis on this topic: http://www.itc.nl/library/papers_2008/msc/gem/lahti.pdf 

The model is based on a combination of Cellular Automata and Agent-based modelling.

## How does the model work?

Each land-use corresponds to an integer in the raster.

1. For each time-step, a matrix is created representing the suitability for a certain land-use type (each land use type is represented by a unique integer in the array, e.g. "forest" could be number 3).
The suitability matrix is calculated based on the distance to surrounding land uses (up to 8 pixels radius). Land-use types can be attracting or repelling for one-another. For instance, an industrial area is repelling residential land-use, thus decreasing the suitability for residential land-use (up to a certain distance). This attraction or repulsion must be defined by the user as a graph, for all interacting land-uses. The suitability raster can also include non-dynamical data, e.g. zoning and slope – but must be create by the user, using e.g. zoning data and a Digital Elevation Model (DEM).

2. For each time-step, a macro-model will calculate the demand for land-use (e.g. the demand for housing). For each pixel, the most suitable land-use will be assigned until the demand has been satisfied for that time-step. When all land-uses have been assigned, the time-step is complete.


## Are human systems predictable?

Due to the unpredictability of human systems, a stochastic effect is added at each time-step. This means, the model will give a different output each time it runs. So how can this be called a prediction then??? Well, if you run the model a hundred times (using something called a Monte Carlo algorithm) you can then calculate the average of the outputs. This will show the estimated probability of a particular land use at a particular location.

Also, the stochasticity can in fact lead to clusters of similar outputs – where e.g. 40% of the "predictions" are similar whereas the rest take a different path (a completely different output). This is analogous to the "Butterfly effect", where one small change in the past can have big consequences in the future.

## Calibration

The model can be calibrated using historical land use data. The model will then run many times, each time the land use interaction graphs will be slightly tweeked. At each output (where ever land use data exists), the model will evaluate the prediction using a sort of Fuzzy Kappa image algorithm. If the prediction was better then previous ones, the new interaction graphs (parameters) will be kept. See the output folder for an example output of such a calibration (running over night).

## Issues

It was a while since I developed this model and it could need some work before running smoothly.

## Contact

Let me know if you have any ideas, suggestions or thoughts in general. My email is johanlahti (at) gmail.com .