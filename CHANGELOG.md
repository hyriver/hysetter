# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2024-09-13

Starting from this release, HySetter has a [website](https://hysetter.readthedocs.io)!

### Added

- Add two options for getting streamflow data, allowing to use a column from the
  AOI's GeoDataFrame as USGS station IDs.
- Add a new example notebook to demonstrate using HySetter for hydrological modeling.
- Add two new AOI sources: `mainstem_main` and `mainstem_tributaries`.
  The `mainstem_main` source gets the catchments of the main flowlines belonging
  to the given mainstem ID, whereas the `mainstem_tributaries` source gets the
  catchments of the tributaries of the main flowlines belonging to the given mainstem ID.

### Changed

- Add the `exceptions` module to the high-level API.
- Switch to using the `src` layout instead of the `flat` layout
  for the package structure. This is to make the package more
  maintainable and to avoid any potential conflicts with other
  packages.
- Add artifact attestations to the release workflow.

## [0.1.1] - 2024-09-1

### Added

- Add support for getting StreamCat and NLDI catchment-level attributes.
  Target attributes can passed through `streamcat_attrs` and `nldi_attrs`
  fields in the config file. Check out the
  demo config [file](https://github.com/hyriver/hysetter/blob/main/config_demo.yml)
  for more details.

### Changed

- Add a new method to the `Config` class called `get_data` to get the
  data efficiently by lazy loading functions and their dependencies.
- Refactored the CLI to use the new `get_data` method.

## [0.1.0] - 2024-05-20

- Initial release.
