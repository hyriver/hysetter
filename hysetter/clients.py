"""Module for interacting with various web services."""
from __future__ import annotations

import numpy as np
import itertools
from pathlib import Path
from typing import Any, Literal, overload, Union, TYPE_CHECKING, cast
import hashlib
from typing import Any, Mapping, Sequence, Union

from multidict import MultiDict
from url_normalize import url_normalize
from yarl import URL
import pyproj
import shapely
import pygeoutils as geoutils
from pathlib import Path
from typing import Sequence, Any, Generator, cast, Literal, Mapping, overload
import os
import httpx
import joblib
from httpx._types import CertTypes
import hishel

from .exceptions import InputTypeError


if TYPE_CHECKING:
    CRSTYPE = Union[int, str, pyproj.CRS]

BOX_ORD = "(west, south, east, north)"

RequestParams = Union[Mapping[Any, Any], Sequence[Any], str, None]
StrOrURL = Union[str, URL]

__all__ = ["create_request_key"]


def _normalize_url_params(url: StrOrURL, params: RequestParams = None) -> URL:
    """Normalize any combination of request parameter formats that aiohttp accepts."""
    if isinstance(url, str):
        url = URL(url)

    # Handle `params` argument, and combine with URL query string if it exists
    if params:
        norm_params = MultiDict(url.query)
        norm_params.extend(url.with_query(params).query)
        url = url.with_query(norm_params)

    # Apply additional normalization and convert back to URL object
    return URL(str(url_normalize(str(url))))


def _encode_dict(data: Any) -> bytes:
    if not data:
        return b""
    if isinstance(data, bytes):
        return data
    elif not isinstance(data, Mapping):
        return str(data).encode()
    item_pairs = [f"{k}={v}" for k, v in sorted((data or {}).items())]
    return "&".join(item_pairs).encode()


def create_request_key(
    method: str,
    url: StrOrURL,
    params: RequestParams = None,
    data: Mapping[str, Any] | None = None,
    json: Mapping[str, Any] | None = None,
) -> str:
    """Create a unique cache key based on request details.
    
    This module is based on the ``aiohttp-client-cache`` package, which is
    licensed under the MIT license. See the ``LICENSE`` file for more details.
    """
    # Normalize and filter all relevant pieces of request data
    norm_url = _normalize_url_params(url, params)

    # Create a hash based on the normalized and filtered request
    return hashlib.sha256(
        method.upper().encode() + str(norm_url).encode() + _encode_dict(data) + _encode_dict(json)
    ).hexdigest()


MAX_CONN = 10
CHUNK_SIZE = 100 * 1024 * 1024  # 100 MB
EXPIRE_AFTER = 60 * 60 * 24 * 7  # 1 week


def httpx_client(
    ssl: bool = True,
    cert: CertTypes | None = None,
    timeout: int = 60,
    cached: bool = False,
) -> httpx.Client:
    """Create a new httpx client.
    
    Parameters
    ----------
    ssl : bool, optional
        Whether to use SSL verification, defaults to ``True``.
    cert : str or tuple, optional
        Path to a certificate file or a tuple of (cert, key) files, defaults
        to ``None``.
    timeout : int, optional
        Timeout in seconds, defaults to 60.
    cached : bool, optional
        Whether to use a cached client, defaults to ``False``.

    Returns
    -------
    httpx.Client
        A new httpx client.
    """
    transport = httpx.HTTPTransport(
        retries=3,
        verify=ssl,
        cert=cert,
    )
    if cached:
        storage = hishel.FileStorage(ttl=EXPIRE_AFTER)
        controller = hishel.Controller(
                cacheable_methods=["GET", "POST"],
                cacheable_status_codes=[200],
                allow_stale=True,
                always_revalidate=True,
        )
        transport = hishel.CacheTransport(transport=transport, storage=storage, controller=controller)
    return httpx.Client(transport=transport, follow_redirects=True, timeout=timeout)


def httpx_async_client(
    ssl: bool = True,
    cert: CertTypes | None = None,
    timeout: int = 60,
    cached: bool = False,
) -> httpx.AsyncClient:
    """Create a new async httpx client.
    
    Parameters
    ----------
    ssl : bool, optional
        Whether to use SSL verification, defaults to ``True``.
    cert : str or tuple, optional
        Path to a certificate file or a tuple of (cert, key) files, defaults
        to ``None``.
    timeout : int, optional
        Timeout in seconds, defaults to 60.
    cached : bool, optional
        Whether to use a cached client, defaults to ``False``.

    Returns
    -------
    httpx.AsyncClient
        A new async httpx client.
    """
    transport = httpx.AsyncHTTPTransport(
        retries=3,
        verify=ssl,
        cert=cert,
    )
    if cached:
        storage = hishel.AsyncFileStorage(ttl=EXPIRE_AFTER)
        controller = hishel.Controller(
                cacheable_methods=["GET", "POST"],
                cacheable_status_codes=[200],
                allow_stale=True,
                always_revalidate=True,
        )
        transport = hishel.AsyncCacheTransport(transport=transport, storage=storage, controller=controller)
    return httpx.AsyncClient(transport=transport, follow_redirects=True, timeout=timeout)


def _prepare_requests_args(
    urls: list[str] | str,
    kwds: list[dict[str, dict[Any, Any]]] | dict[str, dict[Any, Any]] | None,
    method: str,
    fnames: str | Path | Sequence[str | Path] | None,
    root_dir: str | Path | None,
    file_prefix: str,
    file_extention: str,
) -> tuple[
    tuple[str, ...], tuple[dict[str, None | dict[Any, Any]], ...], Generator[Path, None, None]
]:
    """Get url and kwds for streaming download."""
    url_list = (urls,) if isinstance(urls, str) else tuple(urls)

    if kwds is None:
        if method == "GET":
            kwd_list = ({"params": None},) * len(url_list)
        else:
            kwd_list = ({"data": None},) * len(url_list)
    else:
        kwd_list = (kwds,) if isinstance(kwds, dict) else tuple(kwds)
    key_list = set(itertools.chain.from_iterable(k.keys() for k in kwd_list))
    valid_keys = ("params", "data", "json", "headers")
    if any(k not in valid_keys for k in key_list):
        raise InputValueError("kwds", valid_keys)

    if len(url_list) != len(kwd_list):
        raise InputTypeError("urls/kwds", "list of same length")

    f_ext = file_extention.replace(".", "")
    f_ext = f".{f_ext}" if f_ext else ""

    if fnames is None:
        if root_dir is None:
            root_dir = Path(os.getenv("HYSETTER_CACHE_DIR", str(Path(".cache"))))
        else:
            root_dir = Path(root_dir)
        root_dir.mkdir(exist_ok=True, parents=True)
        files = (
            Path(root_dir, f"{file_prefix}{create_request_key(method, u, **p)}{f_ext}")
            for u, p in zip(url_list, kwd_list)
        )
    else:
        f_list = (fnames,) if isinstance(fnames, (str, Path)) else tuple(fnames)
        if len(url_list) != len(f_list):
            raise InputTypeError("urls/fnames", "lists of same length")
        files = (Path(f) for f in f_list)
    url_list = cast("tuple[str, ...]", url_list)
    kwd_list = cast("tuple[dict[str, None | dict[Any, Any]], ...]", kwd_list)
    return url_list, kwd_list, files


def _download(
    client: httpx.Client,
    kwds: Mapping[str, Any],
    fname: Path,
    chunk_size: int,
) -> Path:
    """Download a single file."""
    with client.stream(**kwds) as resp:
        fsize = int(resp.headers.get("Content-Length", -1))
        if not fname.exists() or fname.stat().st_size != fsize:
            fname.parent.mkdir(exist_ok=True, parents=True)
            with fname.open("wb") as f:
                f.writelines(resp.iter_bytes(chunk_size))
    return fname


@overload
def streaming_download(
    urls: str,
    kwds: dict[str, dict[Any, Any]] | None = ...,
    fnames: Sequence[str | Path] | None = ...,
    root_dir: str | Path | None = ...,
    file_prefix: str = ...,
    file_extention: str = ...,
    method: Literal["GET", "POST"] = ...,
    ssl: bool = ...,
    cert: CertTypes | None = ...,
    chunk_size: int = ...,
    n_jobs: int = ...,
) -> Path: ...


@overload
def streaming_download(
    urls: list[str],
    kwds: list[dict[str, dict[Any, Any]]] | None = ...,
    fnames: Sequence[str | Path] | None = ...,
    root_dir: str | Path | None = ...,
    file_prefix: str = ...,
    file_extention: str = ...,
    method: Literal["GET", "POST"] = ...,
    ssl: bool = ...,
    cert: CertTypes | None = ...,
    chunk_size: int = ...,
    n_jobs: int = ...,
) -> list[Path]: ...


def streaming_download(
    urls: list[str] | str,
    kwds: list[dict[str, dict[Any, Any]]] | dict[str, dict[Any, Any]] | None = None,
    fnames: str | Path | Sequence[str | Path] | None = None,
    root_dir: str | Path | None = None,
    file_prefix: str = "",
    file_extention: str = "",
    method: Literal["GET", "POST"] = "GET",
    ssl: bool = True,
    cert: CertTypes | None = None,
    chunk_size: int = CHUNK_SIZE,
    n_jobs: int = MAX_CONN,
) -> Path | list[Path]:
    """Download and store files in parallel from a list of URLs/Keywords.

    Notes
    -----
    This function runs asynchronously in parallel using ``n_jobs`` threads.

    Parameters
    ----------
    urls : tuple or list
        A list of URLs to download.
    kwds : tuple or list, optional
        A list of keywords associated with each URL, e.g.,
        ({"params": ..., "headers": ...}, ...). Defaults to ``None``.
    fnames : tuple or list, optional
        A list of filenames associated with each URL, e.g.,
        ("file1.zip", ...). Defaults to ``None``. If not provided,
        random unique filenames will be generated based on
        URL and keyword pairs.
    root_dir : str or Path, optional
        Root directory to store the files, defaults to ``None`` which
        uses HyRiver's cache directory. Note that you should either
        provide ``root_dir`` or ``fnames``. If both are provided,
        ``root_dir`` will be ignored.
    file_prefix : str, optional
        Prefix to add to filenames when storing the files, defaults
        to ``None``, i.e., no prefix. This argument will be only be
        used if ``fnames`` is not passed.
    file_extention : str, optional
        Extension to use for storing the files, defaults to ``None``,
        i.e., no extension if ``fnames`` is not provided otherwise. This
        argument will be only be used if ``fnames`` is not passed.
    method : {"GET", "POST"}, optional
        HTTP method to use, i.e, ``GET`` or ``POST``, by default "GET".
    ssl : bool, optional
        Whether to use SSL verification, defaults to ``True``.
    cert : str or tuple, optional
        Path to a certificate file or a tuple of (cert, key) files, defaults
        to ``None``.
    chunk_size : int, optional
        Chunk size to use when downloading, defaults to 100 * 1024 * 1024
        i.e., 100 MB.
    n_jobs: int, optional
        The maximum number of concurrent downloads, defaults to 10.

    Returns
    -------
    list
        A list of ``pathlib.Path`` objects associated with URLs in the
        same order.
    """
    method_ = method.upper()
    valid_methods = ("GET", "POST")
    if method_ not in valid_methods:
        raise InputValueError("method", valid_methods)

    url_list, kwd_list, files = _prepare_requests_args(
        urls, kwds, method_, fnames, root_dir, file_prefix, file_extention
    )

    client = httpx_client(ssl=ssl, cert=cert)
    n_jobs = min(n_jobs, len(url_list))
    fpaths = joblib.Parallel(n_jobs=n_jobs, prefer="threads")(
        joblib.delayed(_download)(client, {"method": method_, "url": u, **k}, f, chunk_size)
        for u, k, f in zip(url_list, kwd_list, files)
    )
    fpaths = cast("list[Path]", fpaths)
    client.close()
    if isinstance(urls, str):
        return fpaths[0]
    return fpaths


def check_bbox(bbox: tuple[float, float, float, float]) -> None:
    """Check if an input inbox is a tuple of length 4."""
    try:
        _ = shapely.box(*bbox)
    except (TypeError, AttributeError, ValueError) as ex:
        raise InputTypeError("bbox", "tuple", BOX_ORD) from ex


def bbox_decompose(
    bbox: tuple[float, float, float, float],
    resolution: float,
    box_crs: CRSTYPE = 4326,
    max_px: int = 8000000,
) -> list[tuple[tuple[float, float, float, float], str, int, int]]:
    r"""Split the bounding box vertically for WMS requests.

    Parameters
    ----------
    bbox : tuple
        A bounding box; (west, south, east, north)
    resolution : float
        The target resolution for a WMS request in meters.
    box_crs : str, int, or pyproj.CRS, optional
        The spatial reference of the input bbox, default to ``epsg:4326``.
    max_px : int, optional
        The maximum allowable number of pixels (width x height) for a WMS requests,
        defaults to 8 million based on some trial-and-error.

    Returns
    -------
    list of tuples
        Each tuple includes the following elements:

        * Tuple of px_tot 4 that represents a bounding box (west, south, east, north) of a cell,
        * A label that represents cell ID starting from bottom-left to top-right, for example a
          2x2 decomposition has the following labels::

          |---------|---------|
          |         |         |
          |   0_1   |   1_1   |
          |         |         |
          |---------|---------|
          |         |         |
          |   0_0   |   1_0   |
          |         |         |
          |---------|---------|

        * Raster width of a cell,
        * Raster height of a cell.

    """
    check_bbox(bbox)

    geod = pyproj.Geod(ellps="GRS80")

    west, south, east, north = bbox

    xmin, ymin, xmax, ymax = geoutils.geometry_reproject(bbox, box_crs, 4326)

    x_dist = geod.geometry_length(shapely.LineString([(xmin, ymin), (xmax, ymin)]))
    y_dist = geod.geometry_length(shapely.LineString([(xmin, ymin), (xmin, ymax)]))
    width = int(np.ceil(x_dist / resolution))
    height = int(np.ceil(y_dist / resolution))

    if width * height <= max_px:
        bboxs = [(bbox, "0_0", width, height)]

    n_px = int(np.sqrt(max_px))

    def _split_directional(low: float, high: float, px_tot: int) -> tuple[list[int], list[float]]:
        npt = [n_px for _ in range(int(px_tot / n_px))] + [px_tot % n_px]
        xd = abs(high - low)
        dx = [xd * n / sum(npt) for n in npt]
        xs = [low + d for d in itertools.accumulate(dx)]
        xs.insert(0, low)
        return npt, xs

    nw, xs = _split_directional(west, east, width)
    nh, ys = _split_directional(south, north, height)

    bboxs = []
    for j, h in enumerate(nh):
        for i, w in enumerate(nw):
            bx_crs = (xs[i], ys[j], xs[i + 1], ys[j + 1])
            bboxs.append((bx_crs, f"{i}_{j}", w, h))
    return bboxs


def wms_getmap(
    url: str,
    layers: list[str] | str,
    bbox: tuple[float, float, float, float],
    resolution: float,
    box_crs: CRSTYPE = 4326,
    always_xy: bool = False,
    max_px: int = 8000000,
    kwargs: dict[str, Any] | None = None,
    tiff_dir: str | Path = Path("cache"),
    wms_crs: CRSTYPE = 4326,
    wms_version: Literal["1.1.1", "1.3.0"] = "1.3.0",
    wms_outformat: str = "image/geotiff",
    ssl: bool = True,
) -> dict[str, bytes] | list[Path]:
    """Get data from a WMS service within a geometry or bounding box.

    Parameters
    ----------
    layers : list of str
        A list of WMS layers to be requested.
    bbox : tuple
        A bounding box for getting the data.
    resolution : float
        The output resolution in meters. The width and height of output are computed in pixel
        based on the geometry bounds and the given resolution.
    box_crs : str, int, or pyproj.CRS, optional
        The spatial reference system of the input bbox, defaults to
        ``epsg:4326``.
    always_xy : bool, optional
        Whether to always use xy axis order, defaults to False. Some services change the axis
        order from xy to yx, following the latest WFS version specifications but some don't.
        If the returned value does not have any geometry, it indicates that most probably the
        axis order does not match. You can set this to True in that case.
    max_px : int, optional
        The maximum allowable number of pixels (width x height) for a WMS requests,
        defaults to 8 million based on some trial-and-error.
    kwargs: dict, optional
        Optional additional keywords passed as payload, defaults to None.
        For example, ``{"styles": "default"}``.
    tiff_dir : str or pathlib.Path, optional
        Path to store the downloaded tiff files, defaults to "./cache".
    wms_crs : str, int, or pyproj.CRS, optional
        The spatial reference system of the WMS service, defaults to ``epsg:4326``.
    wms_version : {"1.1.1", "1.3.0"}, optional
        The WMS version, defaults to "1.3.0". The other option is "1.1.1".
    wms_outformat : str, optional
        The output format of the WMS request, defaults to "image/geotiff".
    ssl : bool, optional
        Whether to use SSL, defaults to True.

    Returns
    -------
    list of pathlib.Path
        A list of pathlib.Path objects to the saved files.
    """
    if isinstance(layers, (str, int)):
        layers = [str(layers)]
    else:
        layers = [str(lyr) for lyr in layers]
    check_bbox(bbox)
    wms_crs = pyproj.CRS(wms_crs)
    _bbox = geoutils.geometry_reproject(bbox, box_crs, wms_crs)
    bounds = bbox_decompose(_bbox, resolution, wms_crs, max_px)

    payload = {
        "version": wms_version,
        "format": wms_outformat,
        "request": "GetMap",
    }

    if kwargs is not None and not isinstance(kwargs, dict):
        raise InputTypeError("kwargs", "dict or None")

    if isinstance(kwargs, dict):
        payload.update(kwargs)

    if wms_version == "1.1.1":
        payload["srs"] = wms_crs.to_string().lower()
    else:
        payload["crs"] = wms_crs.to_string().lower()

    is_geographic = wms_crs.is_geographic
    def _get_payloads(
        args: tuple[str, tuple[tuple[float, float, float, float], str, int, int]],
    ) -> tuple[str, dict[str, str]]:
        lyr, bnds = args
        _bbox, counter, _width, _height = bnds

        if wms_version != "1.1.1" and is_geographic and not always_xy:
            _bbox = (_bbox[1], _bbox[0], _bbox[3], _bbox[2])
        _payload = payload.copy()
        _payload["bbox"] = ",".join(str(round(c, 6)) for c in _bbox)
        _payload["width"] = str(_width)
        _payload["height"] = str(_height)
        _payload["layers"] = lyr
        return f"{lyr}_dd_{counter}", _payload

    _lyr_payloads = (_get_payloads(i) for i in itertools.product(layers, bounds))
    layers, payloads = zip(*_lyr_payloads)
    # layers = cast("tuple[str]", layers)
    # payloads = cast("tuple[dict[str, str]]", payloads)

    tiff_dir = Path(tiff_dir)
    tiff_dir.mkdir(parents=True, exist_ok=True)
    return utils.streaming_download(
        [url] * len(payloads),
        [{"params": p} for p in payloads],
        root_dir=tiff_dir,
        file_extention="tiff",
        n_jobs=4,
        ssl=ssl,
    )