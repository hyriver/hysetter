"""Access to the WaterData service."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Sequence, Union, cast

import pygeoutils as geoutils
import warnings
from .exceptions import EmptyResponseError, InputTypeError, InputValueError, ZeroMatchedError

if TYPE_CHECKING:
    import geopandas as gpd
    import pyproj
    from shapely import MultiPoint, MultiPolygon, Point, Polygon, LineString

    CRSTYPE = Union[int, str, pyproj.CRS]
    GTYPE = Union[
        Polygon, MultiPolygon, MultiPoint, LineString, Point, "tuple[float, float, float, float]"
    ]
    NHD_LAYERS = Literal[
        "point",
        "point_event",
        "line_hr",
        "flow_direction",
        "flowline_mr",
        "flowline_hr_nonconus",
        "flowline_hr",
        "area_mr",
        "area_hr_nonconus",
        "area_hr",
        "waterbody_mr",
        "waterbody_hr_nonconus",
        "waterbody_hr",
    ]
    WD_LAYERS = Literal[
        "catchmentsp",
        "gagesii",
        "gagesii_basins",
        "huc08",
        "huc12",
        "nhdarea",
        "nhdflowline_network",
        "nhdflowline_nonnetwork",
        "nhdwaterbody",
        "wbd02",
        "wbd04",
        "wbd06",
        "wbd08",
        "wbd10",
        "wbd12",
    ]
    PREDICATES = Literal[
        "equals",
        "disjoint",
        "intersects",
        "touches",
        "crosses",
        "within",
        "contains",
        "overlaps",
        "relate",
        "beyond",
    ]


class WaterData:
    """Access to `WaterData <https://labs.waterdata.usgs.gov/geoserver>`__ service.

    Parameters
    ----------
    layer : str
        A valid layer from the WaterData service. Valid layers are:

        - ``catchmentsp``
        - ``gagesii``
        - ``gagesii_basins``
        - ``nhdarea``
        - ``nhdflowline_network``
        - ``nhdflowline_nonnetwork``
        - ``nhdwaterbody``
        - ``wbd02``
        - ``wbd04``
        - ``wbd06``
        - ``wbd08``
        - ``wbd10``
        - ``wbd12``

        Note that the layers' namespace for the WaterData service is
        ``wmadata`` and will be added to the given ``layer`` argument
        if it is not provided.
    crs : str, int, or pyproj.CRS, optional
        The target spatial reference system, defaults to ``epsg:4326``.
    validation : bool, optional
        Whether to validate the input data, defaults to ``True``.
    """

    def __init__(
        self,
        layer: WD_LAYERS,
        crs: CRSTYPE = 4326,
    ) -> None:
        self.base_url = "https://labs.waterdata.usgs.gov/geoserver/wmadata/ows"
        self.valid_layers = [
            "catchmentsp",
            "gagesii",
            "gagesii_basins",
            "huc08",
            "huc12",
            "nhdarea",
            "nhdflowline_network",
            "nhdflowline_nonnetwork",
            "nhdwaterbody",
            "wbd02",
            "wbd04",
            "wbd06",
            "wbd08",
            "wbd10",
            "wbd12",
        ]
        if layer not in self.valid_layers:
            raise InputValueError("layer", self.valid_layers)
        self.layer = layer if ":" in layer else f"wmadata:{layer}"
        if "wbd" in self.layer and "20201006" not in self.layer:
            self.layer = f"{self.layer}_20201006"
        self.crs = crs
        self.wfs = WFS(
            self.base_url,
            layer=self.layer,
            outformat="application/json",
            version="2.0.0",
            crs=4269,
            validation=False,
        )

    def _to_geodf(self, resp: list[dict[str, Any]]) -> gpd.GeoDataFrame:
        """Convert a response from WaterData to a GeoDataFrame.

        Parameters
        ----------
        resp : list of dicts
            A ``json`` response from a WaterData request.

        Returns
        -------
        geopandas.GeoDataFrame
            The requested features in a GeoDataFrames.
        """
        try:
            features = geoutils.json2geodf(resp, self.wfs.crs, self.crs)
        except EmptyResponseError as ex:
            raise ZeroMatchedError from ex

        if features.empty:
            raise ZeroMatchedError
        return features

    def bybox(
        self,
        bbox: tuple[float, float, float, float],
        box_crs: CRSTYPE = 4326,
        sort_attr: str | None = None,
    ) -> gpd.GeoDataFrame:
        """Get features within a bounding box.

        Parameters
        ----------
        bbox : tuple of floats
            A bounding box in the form of (minx, miny, maxx, maxy).
        box_crs : str, int, or pyproj.CRS, optional
            The spatial reference system of the bounding box, defaults to ``epsg:4326``.
        sort_attr : str, optional
            The column name in the database to sort request by, defaults
            to the first attribute in the schema that contains ``id`` in its name.

        Returns
        -------
        geopandas.GeoDataFrame
            The requested features in a GeoDataFrames.
        """
        resp = self.wfs.getfeature_bybox(
            bbox,
            box_crs,
            always_xy=True,
            sort_attr=sort_attr,
        )
        resp = cast("list[dict[str, Any]]", resp)
        return self._to_geodf(resp)

    def bygeom(
        self,
        geometry: Polygon | MultiPolygon,
        geo_crs: CRSTYPE = 4326,
        xy: bool = True,
        predicate: PREDICATES = "intersects",
        sort_attr: str | None = None,
    ) -> gpd.GeoDataFrame:
        """Get features within a geometry.

        Parameters
        ----------
        geometry : shapely.Polygon or shapely.MultiPolygon
            The input (multi)polygon to request the data.
        geo_crs : str, int, or pyproj.CRS, optional
            The CRS of the input geometry, default to epsg:4326.
        xy : bool, optional
            Whether axis order of the input geometry is xy or yx.
        predicate : str, optional
            The geometric prediacte to use for requesting the data, defaults to
            INTERSECTS. Valid predicates are:

            - ``equals``
            - ``disjoint``
            - ``intersects``
            - ``touches``
            - ``crosses``
            - ``within``
            - ``contains``
            - ``overlaps``
            - ``relate``
            - ``beyond``

        sort_attr : str, optional
            The column name in the database to sort request by, defaults
            to the first attribute in the schema that contains ``id`` in its name.

        Returns
        -------
        geopandas.GeoDataFrame
            The requested features in the given geometry.
        """
        resp = self.wfs.getfeature_bygeom(
            geometry, geo_crs, always_xy=not xy, predicate=predicate.upper(), sort_attr=sort_attr
        )
        resp = cast("list[dict[str, Any]]", resp)
        return self._to_geodf(resp)

    def bydistance(
        self,
        coords: tuple[float, float],
        distance: int,
        loc_crs: CRSTYPE = 4326,
        sort_attr: str | None = None,
    ) -> gpd.GeoDataFrame:
        """Get features within a radius (in meters) of a point.

        Parameters
        ----------
        coords : tuple of float
            The x, y coordinates of the point.
        distance : int
            The radius (in meters) to search within.
        loc_crs : str, int, or pyproj.CRS, optional
            The CRS of the input coordinates, default to ``epsg:4326``.
        sort_attr : str, optional
            The column name in the database to sort request by, defaults
            to the first attribute in the schema that contains ``id`` in its name.

        Returns
        -------
        geopandas.GeoDataFrame
            Requested features as a GeoDataFrame.
        """
        if not (isinstance(coords, tuple) and len(coords) == 2):
            raise InputTypeError("coods", "tuple of length 2", "(x, y)")

        x, y = geoutils.geometry_reproject([coords], loc_crs, self.wfs.crs)[0]
        geom_name = self.wfs.schema[self.layer].get("geometry_column", "the_geom")
        cql_filter = f"DWITHIN({geom_name},POINT({y:.6f} {x:.6f}),{distance},meters)"
        resp = self.wfs.getfeature_byfilter(
            cql_filter,
            "GET",
            sort_attr=sort_attr,
        )
        resp = cast("list[dict[str, Any]]", resp)
        return self._to_geodf(resp)

    def byid(
        self, featurename: str, featureids: Sequence[int | str] | int | str
    ) -> gpd.GeoDataFrame:
        """Get features based on IDs."""
        resp = self.wfs.getfeature_byid(
            featurename,
            featureids,
        )
        resp = cast("list[dict[str, Any]]", resp)
        features = self._to_geodf(resp)

        if isinstance(featureids, (str, int)):
            fids = [str(featureids)]
        else:
            fids = [str(f) for f in featureids]

        failed = set(fids).difference(set(features[featurename].astype(str)))

        if failed:
            msg = ". ".join(
                (
                    f"{len(failed)} of {len(fids)} requests failed.",
                    f"IDs of the failed requests are {list(failed)}",
                )
            )
            warnings.warn(msg, UserWarning, stacklevel=2)
        return features

    def byfilter(
        self,
        cql_filter: str,
        method: Literal["GET", "get", "POST", "post"] = "GET",
        sort_attr: str | None = None,
    ) -> gpd.GeoDataFrame:
        """Get features based on a CQL filter.

        Parameters
        ----------
        cql_filter : str
            The CQL filter to use for requesting the data.
        method : str, optional
            The HTTP method to use for requesting the data, defaults to GET.
            Allowed methods are GET and POST.
        sort_attr : str, optional
            The column name in the database to sort request by, defaults
            to the first attribute in the schema that contains ``id`` in its name.

        Returns
        -------
        geopandas.GeoDataFrame
            The requested features as a GeoDataFrames.
        """
        resp = self.wfs.getfeature_byfilter(
            cql_filter,
            method,
            sort_attr,
        )
        resp = cast("list[dict[str, Any]]", resp)
        return self._to_geodf(resp)

    def __repr__(self) -> str:
        """Print the services properties."""
        return "\n".join(
            (
                "Connected to the WaterData web service on GeoServer:",
                f"URL: {self.wfs.url}",
                f"Version: {self.wfs.version}",
                f"Layer: {self.layer}",
                f"Output Format: {self.wfs.outformat}",
                f"Output CRS: {self.crs}",
            )
        )