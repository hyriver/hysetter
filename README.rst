HySetter: Hyroclimate Data Subsetter based on HyRiver
=====================================================

.. image:: https://img.shields.io/pypi/v/hysetter.svg
    :target: https://pypi.python.org/pypi/hysetter
    :alt: PyPi

.. image:: https://img.shields.io/conda/vn/conda-forge/hysetter.svg
    :target: https://anaconda.org/conda-forge/hysetter
    :alt: Conda Version

.. image:: https://codecov.io/gh/hyriver/hysetter/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/hyriver/hysetter
    :alt: CodeCov

.. image:: https://img.shields.io/pypi/pyversions/hysetter.svg
    :target: https://pypi.python.org/pypi/hysetter
    :alt: Python Versions

.. image:: https://static.pepy.tech/badge/hysetter
    :target: https://pepy.tech/project/hysetter
    :alt: Downloads

|

.. image:: https://img.shields.io/badge/security-bandit-green.svg
    :target: https://github.com/PyCQA/bandit
    :alt: Security Status

.. image:: https://www.codefactor.io/repository/github/hyriver/hysetter/badge
   :target: https://www.codefactor.io/repository/github/hyriver/hysetter
   :alt: CodeFactor

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Ruff

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
    :target: https://github.com/pre-commit/pre-commit
    :alt: pre-commit

|

Features
--------

HySetter is an open-source Python package, built on HyRiver software stack, that provides a
command-line interface (CLI) for subsetting hydroclimate data from the following data sources
over conterminous United States (CONUS):

- **Area Of Interest**: From any `HUC <https://www.usgs.gov/national-hydrography/watershed-boundary-dataset>`__
  level, `GAGES-II basins <https://pubs.usgs.gov/publication/70046617>`__,
  `NHDPlusV2 <https://www.nhdplus.com/NHDPlus/NHDPlusV2_home.php>`__ catchments and their
  attributes (`StreamCat <https://www.epa.gov/national-aquatic-resource-surveys/streamcat-dataset>`__
  and `NLDI <https://labs.waterdata.usgs.gov/docs/nldi/about-nldi/index.html>`__),
  or a user-defined GeoDataFrame
- **Drainage Network**: From NHDPlusV2
- **Forcing**: From `Daymet <https://daymet.ornl.gov/>`__,
  `GridMET <https://www.climatologylab.org/gridmet.html>`__,
  or `NLDAS2 <https://ldas.gsfc.nasa.gov/nldas/v2/forcing>`__
- **Streamflow**: From `NWIS <https://nwis.waterdata.usgs.gov/nwis>`__
- **Soil**: From `gNATSGO <https://planetarycomputer.microsoft.com/dataset/gnatsgo-rasters>`__,
  or `SoilGrids <https://www.isric.org/explore/soilgrids>`__
- **Topography**: From `3DEP <https://www.usgs.gov/3d-elevation-program>`__
- **Dam**: From `NID <https://nid.sec.usace.army.mil>`__
- **Land Use/Land Cover, Canopy, Imperviousness, and Urban Descriptor**:
  From `MRLC <https://www.mrlc.gov/>`__

Citation
--------
If you use any of HyRiver packages in your research, we appreciate citations:

.. code-block:: bibtex

    @article{Chegini_2021,
        author = {Chegini, Taher and Li, Hong-Yi and Leung, L. Ruby},
        doi = {10.21105/joss.03175},
        journal = {Journal of Open Source Software},
        month = {10},
        number = {66},
        pages = {1--3},
        title = {{HyRiver: Hydroclimate Data Retriever}},
        volume = {6},
        year = {2021}
    }

Installation
------------
You can install ``hysetter`` using ``pip``:

.. code-block:: console

    $ pip install hysetter

Alternatively, ``hysetter`` can be installed from the ``conda-forge`` repository
using `micromamba <https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html/>`__:

.. code-block:: console

    $ micromamba install -c conda-forge hysetter


Quick start
-----------

Once HySetter is installed, you can use the CLI to subset hydroclimate data via a
configuration file. The configuration file is a YAML file that specifies the data
source, the area of interest (AOI), and the output directory. You can find an example
configuration file in the
`config_demo.yml <https://github.com/hyriver/hysetter/blob/main/config_demo.yml>`__.

.. image:: https://raw.githubusercontent.com/hyriver/hysetter/main/hs_help.svg
    :align: center

.. image:: https://asciinema.org/a/660577.svg
    :target: https://asciinema.org/a/660577?autoplay=1
    :align: center

Contributing
------------
Contributions are appreciated and very welcomed. Please read
`CONTRIBUTING.rst <https://github.com/hyriver/hysetter/blob/main/CONTRIBUTING.rst>`__
for instructions.


Acknowledgements
----------------
This work is supported by Consortium of Universities for the Advancement of Hydrologic
Science, Inc. (`CUAHSI <https://www.cuahsi.org/>`__) through the Hydroinformatics Innovation
Fellowship program.
