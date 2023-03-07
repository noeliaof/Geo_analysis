import zipfile
# to unzip 

def unzip(sentinelsat_options):
    # -- Unzips all files in data directory. -- #
    cwd = os.getcwd()
    os.chdir(sentinelsat_options['data_dir'])

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