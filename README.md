# HySetter: Hydroclimate Data Subsetter based on HyRiver

[![PyPi](https://img.shields.io/pypi/v/hysetter.svg)](https://pypi.python.org/pypi/hysetter)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/hysetter.svg)](https://anaconda.org/conda-forge/hysetter)
[![CodeCov](https://codecov.io/gh/hyriver/hysetter/branch/main/graph/badge.svg)](https://codecov.io/gh/hyriver/hysetter)
[![Python Versions](https://img.shields.io/pypi/pyversions/hysetter.svg)](https://pypi.python.org/pypi/hysetter)
[![Downloads](https://static.pepy.tech/badge/hysetter)](https://pepy.tech/project/hysetter)

[![Security Status](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![CodeFactor](https://www.codefactor.io/repository/github/hyriver/hysetter/badge)](https://www.codefactor.io/repository/github/hyriver/hysetter)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/hyriver/hysetter/HEAD?labpath=docs%2Fexamples)

## Features

HySetter is an open-source Python package, built on HyRiver software stack, that
provides a command-line interface (CLI) and Python API for subsetting hydroclimate data
from the following data sources over the conterminous United States (CONUS):

- **Area Of Interest**: From any
    [HUC](https://www.usgs.gov/national-hydrography/watershed-boundary-dataset) level,
    [GAGES-II basins](https://pubs.usgs.gov/publication/70046617),
    [NHDPlusV2](https://www.nhdplus.com/NHDPlus/NHDPlusV2_home.php) catchments and their
    attributes
    ([StreamCat](https://www.epa.gov/national-aquatic-resource-surveys/streamcat-dataset)
    and [NLDI](https://labs.waterdata.usgs.gov/docs/nldi/about-nldi/index.html)), or a
    user-defined GeoDataFrame
- **Drainage Network**: From NHDPlusV2
- **Forcing**: From [Daymet](https://daymet.ornl.gov/),
    [GridMET](https://www.climatologylab.org/gridmet.html), or
    [NLDAS2](https://ldas.gsfc.nasa.gov/nldas/v2/forcing)
- **Streamflow**: From [NWIS](https://nwis.waterdata.usgs.gov/nwis)
- **Soil**: From
    [gNATSGO](https://planetarycomputer.microsoft.com/dataset/gnatsgo-rasters), or
    [SoilGrids](https://www.isric.org/explore/soilgrids)
- **Topography**: From [3DEP](https://www.usgs.gov/3d-elevation-program)
- **Dam**: From [NID](https://nid.sec.usace.army.mil)
- **Land Use/Land Cover, Canopy, Imperviousness, and Urban Descriptor**: From
    [MRLC](https://www.mrlc.gov/)

Try HySetter in your browser by clicking on the Binder badge above. You can refer to the
[documentation](https://hysetter.readthedocs.io/latest/examples/) for more examples and
details.

## Installation

You can install `hysetter` using `pip`:

```console
pip install hysetter
```

Alternatively, `hysetter` can be installed from the `conda-forge` repository using
[micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html/),
`conda`, or `mamba`:

```console
micromamba install -c conda-forge hysetter
```

You can use `conda` or `mamba` instead of `micromamba` if you prefer, but `micromamba`
is recommended for its efficiency and ease of use.

For just installing HySetter's CLI, you can first install Pixi by following the its
[installation instructions](https://pixi.sh/latest/installation/) for your platform.
Then, you can install HySetter using the following command:

```console
pixi global install hysetter
```

## Quick start

Once HySetter is installed, you can use its CLI or Python API to subset hydroclimate
data via a configuration file. The configuration file is a YAML file that specifies the
data source, the area of interest (AOI), and the output directory. You can find an
example configuration file in the
[config_demo.yml](https://github.com/hyriver/hysetter/blob/main/config_demo.yml).

![image](https://raw.githubusercontent.com/hyriver/hysetter/main/hs_help.svg)

[![image](https://asciinema.org/a/660577.svg)](https://asciinema.org/a/660577?autoplay=1)

## Contributing

Contributions are appreciated and very welcomed. Please read
[CONTRIBUTING.rst](https://github.com/hyriver/hysetter/blob/main/CONTRIBUTING.rst) for
instructions.

## Acknowledgements

This work is supported by the Consortium of Universities for the Advancement of
Hydrologic Science, Inc. ([CUAHSI](https://www.cuahsi.org/)) through the
Hydroinformatics Innovation Fellowship program.
