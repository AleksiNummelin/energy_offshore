# energy_offshore

This repository contains the scripts related to the Energy Offshore use case (WP10) of the Climate Adaptation
Digital Twin (Climate DT). All the work is being developed in the frame of the Destination Earth initiative.

## Description

Energy_Offshore is a Destination Earth ClimateDT app to calculate future conditions for offshore wind power
in ice-covered seas. It is a work in progress, aiming to provide useful information on current and future
conditions on the oceans from the perspective of offshore wind turbine operation, installation and maintenance.

It is being developed as a Python package in two parts: data retrieval and reduction, and data analysis and plotting.

## Version

Current version can be found at tag v0.3.0. The project is in active development.

## Roadmap

Projected developments in the future include eg.
- Using new Workflow for all data requests
- Icing prediction

## Requirements

The Energy offshore use case depends on numpy, xarray, gsv and opa. Currently 
It is currently set up on the Lumi supercomputer as such:

function load_environment_ENERGY_OFFSHORE() {
    set +xuve
    module use /project/project_465000454/devaraju/modules/LUMI/23.03/C

    # Load modules
    ml ecCodes/2.33.0-cpeCray-23.03
    ml fdb/5.11.94-cpeCray-23.03
    ml metkit/1.11.0-cpeCray-23.03
    ml eckit/1.25.0-cpeCray-23.03
    ml python-climatedt/3.11.7-cpeCray-23.03
    set -xuve
}

## Installation

The application does not need to be installed. The runscript will run the relevant python codes
from the energy_offshore repository.

## How to run

Currently the application can practically only be run from an autosubmit workflow. The application
expects to find surface data on the hard drive. All settings are passed to the application as
program parameters.

## Data request

Energy Offshore is requesting several parameters from several different levels of data. The
surface data is requested from the workflow using a request file, ocean data, 100 m data and
pressure level data is requested directly from within the application. This is done as the
workflow package only recently introduced the capability to request data from many levels.

Surface data:
- 2t (2 metre temperature, [K])
- 2d (2 metre dew point temperature, [K])
- 10u, 10v (10 metre wind velocity components, [m/s])
- tprate (total precipitation rate, [kg m**-2 s**.1])
- sp (surface air pressure, [Pa])

100 metre data:
- 100u, 100v (100 metre wind velocity components, [m/s])

Pressure level data for 1000 Pa level only:
- t (temperature, [K])
- q (specific humidity, [kg kg**-1])
- clwc (specific cloud liquid water content, [kg kg**-1])
- z (geopotential, [m**2 s**-2]

Ocean data:
- avg_sithick (daily average of sea ice thickness, [m])
- avg_siconc (daily average of sea ice concentration, [fraction])
- avg_siue (time-mean eastward sea ice velocity, [m/s])
- avg_sivn (time-mean northward sea ice velocity, [m/s])
- avg_tos (daily average sea surface temperature, [K])
- avg_sos (daily average sea surface practical salinity, [g kg**-1])
- avg_zos (daily average sea surface height, [m])


## Authors and acknowledgment

The Energy offshore application is developped in the Finnish Meteorological Institute
by Jonni Lehtiranta, Aleksi Nummelin and Andrew Twelves.

