# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Fix a bug in the NWIS module where due to having ":" in filenames, Windows users were
    unable to download streamflow data. The bug was fixed by removing hours and minutes
    from the file name. [#7](https://github.com/hyriver/hysetter/issues/7)

### Added

- In the installation section, explain that `conda` and `mamba` can be used instead of
    `micromamba` for installing HySetter.
    [#6](https://github.com/hyriver/hysetter/issues/6)

### Changed

## [0.3.1] - 2025-05-24

### Fixed

- Fix a bug in CLI where passing `--overwrite` removed the root directory instead of the
    project directory. As a result, the root directory for the AOI file was removed
    causing the CLI to fail.

### Changed

- For forcing and streamflow data, include the start and end dates in the file name to
    avoid overwriting the files when the same data is requested for different dates.

## [0.3.0] - 2025-02-11

This release many new features and improvements and culmination of several months of
development. The most notable changes are listed below.

### Added

- Add support for subsetting remote raster datasets.
- Add support for POLARIS data which is a probabilistic remapping of SSURGO (POLARIS)
    soil properties at 30-m resolution over the CONUS.
- The `Config.file_paths` attribute now includes a `FileList` object for each requested
    data source. This allows for easy access to the file paths of the downloaded data.
    The indices of the list of files correspond to the geometries in the AOI
    GeoDataFrame.
- Add a new option called `crop` to all gridded data sources. This option allows to
    disable cropping of the data to the AOI. This is useful when the user wants to get
    the data for the bounding box of the AOI instead of the AOI itself, e.g., for
    topography data where the data at the edges of the AOI is needed.
- Add a new option called `geometry_buffer` to all gridded data sources. This option
    allows to buffer the geometry of the AOI by a given distance. This is useful when
    the user wants to get the data for a larger area than the AOI itself, e.g., for
    topography data where the data at the edges of the AOI is needed.
- Add a new option called `overwrite` to allow overwriting the existing data files.

### Changed

- A major refactoring of the code base to improve the performance by avoiding
    unnecessary web service calls and package imports.

## [0.2.0] - 2024-09-13

Starting from this release, HySetter has a [website](https://hysetter.readthedocs.io)!

### Added

- Add two options for getting streamflow data, allowing to use a column from the AOI's
    GeoDataFrame as USGS station IDs.
- Add a new example notebook to demonstrate using HySetter for hydrological modeling.
- Add two new AOI sources: `mainstem_main` and `mainstem_tributaries`. The
    `mainstem_main` source gets the catchments of the main flowlines belonging to the
    given mainstem ID, whereas the `mainstem_tributaries` source gets the catchments of
    the tributaries of the main flowlines belonging to the given mainstem ID.

### Changed

- Add the `exceptions` module to the high-level API.
- Switch to using the `src` layout instead of the `flat` layout for the package
    structure. This is to make the package more maintainable and to avoid any potential
    conflicts with other packages.
- Add artifact attestations to the release workflow.

## [0.1.1] - 2024-09-1

### Added

- Add support for getting StreamCat and NLDI catchment-level attributes. Target
    attributes can passed through `streamcat_attrs` and `nldi_attrs` fields in the
    config file. Check out the demo config
    [file](https://github.com/hyriver/hysetter/blob/main/config_demo.yml) for more
    details.

### Changed

- Add a new method to the `Config` class called `get_data` to get the data efficiently
    by lazy loading functions and their dependencies.
- Refactored the CLI to use the new `get_data` method.

## [0.1.0] - 2024-05-20

- Initial release.
