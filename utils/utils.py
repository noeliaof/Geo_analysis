import zipfile
import os
import os
import glob
import pyproj
import rasterio
from rasterio.mask import mask
from shapely.ops import transform
from rasterio.io import MemoryFile
import numpy as np
import geopandas as gpd
from scipy.interpolate import RectBivariateSpline
# to unzip 

def unzip(s_conf):
    # -- Unzips all files in data directory. -- #
    cwd = os.getcwd()
    os.chdir(s_conf['data_dir'])

    files = os.listdir()
    zip_files = [file for file in files if '.zip' in file]  # Find all .zip files.
    safe_files = [file for file in files if '.SAFE' in file]  # Find all .SAFe files.

    files_to_unzip = [file for file in zip_files if not
                      [file.split('.')[0] in safe_file for safe_file in safe_files]]  # Find .zip files not unzipped.

    # Unzip files.
    for file_to_unzip in files_to_unzip:
        to_unzip = zipfile.ZipFile(file_to_unzip, 'r')
        to_unzip.extractall()
        to_unzip.close()
        # remove zip files
        os.remove(file_to_unzip)
    os.chdir(cwd)

# Credits to: https://medium.com/analytics-vidhya/two-ways-of-extracting-points-of-interest-from-sentinel-2a-data-baa124b1ed92

def reproject(polygons, proj_from, proj_to):
    proj_from = pyproj.Proj(proj_from)
    proj_to = pyproj.Proj(proj_to)
    
    projection = pyproj.Transformer.from_proj(proj_from, proj_to)
    return [transform(projection.transform, p) for p in polygons]


def crop_memory_tiff_file(mem_file, polygons, crop):
    polygons = reproject(polygons, "EPSG:4326", mem_file.crs)
    result_image, result_transform = mask(mem_file, polygons, crop=crop)
    
    profile = mem_file.profile
    profile.update(width=result_image.shape[1], 
                   height=result_image.shape[2], 
                   transform=result_transform)

    result_f = MemoryFile().open(**profile)
    result_f.write(result_image)
    
    return result_f

def extrapolate(arr, target_dim):
    x = np.array(range(arr.shape[0]))
    y = np.array(range(arr.shape[1]))
    z = arr
    xx = np.linspace(x.min(), x.max(), target_dim[0])
    yy = np.linspace(y.min(), y.max(), target_dim[1])

    new_kernel = RectBivariateSpline(x, y, z, kx=2, ky=2)
    result = new_kernel(xx, yy)

    return result


def get_bounds_of_AoI(obj_aoi, src_crs):
    
    aoi = gpd.read_file(obj_aoi)
    
    bounds = aoi.total_bounds
    
    offset = 1/60  #2000m in degree

    # WGS84 coordinates
    minx, miny = bounds[0]-offset, bounds[1]-offset
    maxx, maxy = bounds[2]+offset, bounds[3]+offset

    bbox = box(minx, miny, maxx, maxy)
    
    print(bbox)

    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs="EPSG:4326")

    #picking up the coordinate system of the image:
    #crs=src.crs.to_epsg()
    geo = geo.to_crs(crs=src_crs) #src.crs.to_epsg())

    coords = getFeatures(geo)
    
    return coords

def clip_raster_with_bounds(in_tif, out_tif, coords):

    #load the mosaided file
    data = rasterio.open(in_tif)

    out_img, out_transform = rasterio.mask.mask(dataset=data, shapes=coords, crop=True)

    # Copy the metadata
    out_meta = data.meta.copy()

    # Parse EPSG code
    epsg_code = int(data.crs['init'][5:])

    out_meta.update({"driver": "GTiff",
            "height": out_img.shape[1],
            "width": out_img.shape[2],
            "transform": out_transform,
            "crs": epsg_code} #pycrs.parse.from_epsg_code(epsg_code).to_proj4()}
            )

    with rasterio.open(out_tif, "w", **out_meta) as dest:
        dest.write(out_img)

    print('save file',out_tif)


def get_src_crs(prototype_tif):
    
    with rasterio.open(prototype_tif, 'r') as test:
        src_crs = test.crs.to_epsg()
        
    return src_crs

def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]



def get_bounds_of_AoI(obj_aoi, offset):
    
    aoi = gpd.read_file(obj_aoi)
    
    bounds = aoi.total_bounds
    #offset = 1/60  #200m in degree
    # Extend the bounding box by 200 m
    minx, miny = bounds[0]-offset, bounds[1]-offset
    maxx, maxy = bounds[2]+offset, bounds[3]+offset

    bbox = box(minx, miny, maxx, maxy)
    
    print(bbox)

    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs="EPSG:4326")

    
    return geo 