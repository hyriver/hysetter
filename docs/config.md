# Configuration File

This page describes the settings available in the configuration file for HySetter. The
configuration file should be in YAML format. You can download an example configuration
file [here](https://raw.githubusercontent.com/hyriver/hysetter/main/config_demo.yml).

## Project (`project`)

The `project` section is required and contains basic information about your project.

- `name` (required): The name of your project. Data will be stored in `data_dir/name`.
- `data_dir` (required): The directory where data will be stored.

Example:

```yaml
project:
  name: example_1
  data_dir: data
```

## Area of Interest (`aoi`)

The `aoi` section is required and defines the area of interest for your project. You
should specify only one of the following options:

- `huc_ids`: A list of Hydrologic Unit Code (HUC) IDs. It can be a mix of different HUC
    levels.
- `nhdv2_ids`: A list of NHDPlusV2 catchment IDs (`featureid`).
- `gagesii_basins`: A list of GAGES-II basin IDs.
- `mainstem_main`: NHDPlusV2 catchments belonging to the main flowlines upstream of the
    provided mainstem ID.
- `mainstem_tributaries`: NHDPlusV2 catchments belonging to the tributaries upstream of
    the provided mainstem ID.
- `geometry_file`: Path to a file containing geometry data. Can be parquet, feather, or
    any format that `geopandas.read_file` accepts.

Additional AOI options:

- `nhdv2_flowlines` (optional): Boolean. If `true`, retrieve the NHDPlusV2 flowlines
    within the AOI.
- `streamcat_attrs` (optional): A list of valid StreamCat attributes to get for
    flowlines within the AOI.
- `nldi_attrs` (optional): A list of valid NLDI attributes to get for flowlines within
    the AOI.

Example:

```yaml
aoi:
  gagesii_basins: ['01031500', '01031450']
  nhdv2_flowlines: true
  streamcat_attrs: [fert, bfi]
```

## Forcing Data (`forcing`)

The `forcing` section is optional and defines settings for retrieving forcing data.

- `source`: The data source. Options are `daymet`, `gridmet`, or `nldas2`.
- `start_date`: The start date for the data retrieval (YYYY-MM-DD format).
- `end_date`: The end date for the data retrieval (YYYY-MM-DD format).
- `variables`: A list of variables to retrieve. Valid variable names depend on the
    chosen source.

Example:

```yaml
forcing:
  source: daymet
  start_date: 2000-01-01
  end_date: 2000-01-02
  variables: [prcp, tmin]
```

## Topography (`topo`)

The `topo` section is optional and defines settings for topographic data retrieval and
processing.

- `resolution_m`: The desired resolution in meters. Use `10`, `30`, or `60` for faster
    retrieval from 3DEP's static files.
- `derived_variables`: A list of derived variables to compute. Options are `slope`,
    `aspect`, and `curvature`.

Example:

```yaml
topo:
  resolution_m: 10
  derived_variables: [slope, aspect, curvature]
```

## Soil Data (`soil`)

The `soil` section is optional and defines settings for soil data retrieval.

- `source`: The data source. Options are `soilgrids` or `gnatsgo`.
- `variables`: A list of variables to retrieve. Valid options depend on the chosen
    source.

Example:

```yaml
soil:
  source: soilgrids
  variables: [bdod_5, cec_5]
```

## National Land Cover Database (`nlcd`)

The `nlcd` section is optional and defines settings for retrieving NLCD data.

- `cover`: A list of years for land cover data.
- `impervious`: A list of years for impervious surface data.
- `canopy`: A list of years for canopy data.
- `descriptor`: A list of years for descriptor data.

Valid years:

- Cover, Impervious, Descriptor: 2021, 2019, 2016, 2013, 2011, 2008, 2006, 2004, 2001
- Canopy: Any year between 2011–2022 (inclusive)

Example:

```yaml
nlcd:
  cover: [2016]
  impervious: [2016]
  canopy: [2016]
  descriptor: [2016]
```

## National Inventory of Dams (`nid`)

The `nid` section is optional and defines settings for retrieving NID data.

- `within_aoi`: Boolean. If `true`, only return dams within the defined AOIs. If `false`
    or omitted, store the full NID database.

Example:

```yaml
nid:
  within_aoi: true
```

## Streamflow Data (`streamflow`)

The `streamflow` section is optional and defines settings for retrieving streamflow
data.

- `start_date`: The start date for data retrieval (YYYY-MM-DD format).
- `end_date`: The end date for data retrieval (YYYY-MM-DD format).
- `frequency`: The data frequency. Options are `daily` or `instantaneous`.
- `within_aoi`: Boolean. If `true`, get streamflow for all stations within the AOIs.
- `use_col`: A column name from the AOIs GeoDataFrame to use as the station IDs to query
    NWIS for streamflow. When provided, `within_aoi` is ignored.

Example:

```yaml
streamflow:
  start_date: 2000-01-01
  end_date: 2000-01-02
  frequency: daily
  use_col: gage_id
```

This configuration file allows you to customize various aspects of data retrieval and
processing for your project. Adjust the settings as needed to suit your specific
requirements.

## Remote Raster Data (`remote_raster`)

The `remote_raster` section is optional and defines settings for retrieving remote
raster data. Any number of name/URL pairs can be specified. The URL should point to a
raster file or a VRT file that references multiple raster files. The data will be
downloaded and stored in the `data_dir` directory. Note that the name will be sanitized
(strip, lower, replace space with `_`) since it is used as filenames (e.g.,
`data_dir/twi/twi_geom_1.tif`). Similar to other gridded data, there are two additional
options that can be specified:

- `crop`: Boolean. Whether to crop the data to the geometry of the AOI. Default is
    `true`.
- `geometry_buffer`: Buffer distance in meters to add to the geometry of the AOI before
    requesting the data. Default is `0`.

Example:

```yaml
remote_raster:
  twi:
    https://lynker-spatial.s3-us-west-2.amazonaws.com/gridded-resources/twi.vrt
  fdr:
    https://lynker-spatial.s3-us-west-2.amazonaws.com/gridded-resources/fdr.vrt
  crop: true
  geometry_buffer: 0
```
