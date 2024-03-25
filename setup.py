#!/usr/bin/env python3

from setuptools import setup

setup(
    name='energy_offshore',
    version='0.2.0',
    description='Destination Earth ClimateDT app to calculate future conditions for offshore wind power in ice-covered seas.',
    author='Jonni Lehtiranta,
    author_email='jonni.lehtiranta@fmi.fi',
    url='https://earth.bsc.es/gitlab/digital-twins/de_340/energy_offshore',
    python_requires='>=3.9',
    packages=['energy_offshore'],
    install_requires=[
        'numpy',
        'scipy',
        'xarray',
        'pandas',
        'datetime',
        'dask',
        'netcdf4',
    ],
)


