# energy_offshore

Products for offshore wind turbines


## Requirements

The Energy offshore use case depends on numpy, xarray, gsv and opa. Currently 
It is currently set up for Lumi as such:

    function load_environment_ENERGY_OFFSHORE() {
        module load LUMI/22.08
        module load partition/C
        module load PrgEnv-gnu
        module load GObject-Introspection/1.72.0-cpeGNU-22.08-cray-python3.9
        load_environment_gsv
    }

## Installation

The application does not need to be installed. The runscript will run the relevant python codes
from the energy_offshore repository.

## How to run



## Data request

For now, Energy offshore should request the following parameters, all through Opa and raw,
but the runs don't succeed.

- 2t (Temperature)
- 2d, tcwv (Humidity, water content)
- 10u, 10v, 100u, 100v (wind)
- ci, sithick (Sea ice concentration and thickness)
- sst, so, zos (Sea surface temperature, salinity and height)
- ocu, ocv (Sea surface current)

The attempts can be found in workflow's app-integrate-offshore branch in conf/applications/energy-offshore .


## Authors and acknowledgment

The Energy offshore application is developped in the Finnish Meteorological Institute.


## Project status

The project is in active development.
