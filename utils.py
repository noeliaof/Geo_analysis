import zipfile
import os
import os
import glob
import pyproj
import rasterio
from rasterio.mask import mask
from shapely.ops import transform
from rasterio.io import MemoryFile
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