# HySetter: Hyroclimate Data Subsetter based on HyRiver

[![PyPi](https://img.shields.io/pypi/v/hysetter.svg)](https://pypi.python.org/pypi/hysetter)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/hysetter.svg)](https://anaconda.org/conda-forge/hysetter)
[![CodeCov](https://codecov.io/gh/hyriver/hysetter/branch/main/graph/badge.svg)](https://codecov.io/gh/hyriver/hysetter)
[![Python Versions](https://img.shields.io/pypi/pyversions/hysetter.svg)](https://pypi.python.org/pypi/hysetter)
[![Downloads](https://static.pepy.tech/badge/hysetter)](https://pepy.tech/project/hysetter)

[![Security Status](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![CodeFactor](https://www.codefactor.io/repository/github/hyriver/hysetter/badge)](https://www.codefactor.io/repository/github/hyriver/hysetter)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## Features

HySetter is an open-source Python package, built on HyRiver software
stack, that provides a command-line interface (CLI) for subsetting
hydroclimate data from the following data sources over conterminous
United States (CONUS):

- **Area Of Interest**: From any
    [HUC](https://www.usgs.gov/national-hydrography/watershed-boundary-dataset)
    level, [GAGES-II
    basins](https://pubs.usgs.gov/publication/70046617),
    [NHDPlusV2](https://www.nhdplus.com/NHDPlus/NHDPlusV2_home.php)
    catchments and their attributes
    ([StreamCat](https://www.epa.gov/national-aquatic-resource-surveys/streamcat-dataset)
    and
    [NLDI](https://labs.waterdata.usgs.gov/docs/nldi/about-nldi/index.html)),
    or a user-defined GeoDataFrame
- **Drainage Network**: From NHDPlusV2
- **Forcing**: From [Daymet](https://daymet.ornl.gov/),
    [GridMET](https://www.climatologylab.org/gridmet.html), or
    [NLDAS2](https://ldas.gsfc.nasa.gov/nldas/v2/forcing)
- **Streamflow**: From [NWIS](https://nwis.waterdata.usgs.gov/nwis)
- **Soil**: From
    [gNATSGO](https://planetarycomputer.microsoft.com/dataset/gnatsgo-rasters),
    or [SoilGrids](https://www.isric.org/explore/soilgrids)
- **Topography**: From
    [3DEP](https://www.usgs.gov/3d-elevation-program)
- **Dam**: From [NID](https://nid.sec.usace.army.mil)
- **Land Use/Land Cover, Canopy, Imperviousness, and Urban
    Descriptor**: From [MRLC](https://www.mrlc.gov/)

## Installation

You can install `hysetter` using `pip`:

``` console
pip install hysetter
```

Alternatively, `hysetter` can be installed from the `conda-forge`
repository using
[micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html/):

``` console
micromamba install -c conda-forge hysetter
```

## Quick start

Once HySetter is installed, you can use the CLI to subset hydroclimate
data via a configuration file. The configuration file is a YAML file
that specifies the data source, the area of interest (AOI), and the
output directory. You can find an example configuration file in the
[config_demo.yml](https://github.com/hyriver/hysetter/blob/main/config_demo.yml).

![image](https://raw.githubusercontent.com/hyriver/hysetter/main/hs_help.svg){.align-center}

[![image](https://asciinema.org/a/660577.svg){.align-center}](https://asciinema.org/a/660577?autoplay=1)

## Acknowledgements

This work is supported by Consortium of Universities for the Advancement
of Hydrologic Science, Inc. ([CUAHSI](https://www.cuahsi.org/)) through
the Hydroinformatics Innovation Fellowship program.