import csv
import os
from os.path  import basename
import requests

# download single image with file name
def download_file(file_url : str = None, download_path : str = None):
    if not file_url:
        return None
    
    file_path = ''
    if download_path:
        if not os.path.exists(f'./results/{download_path}'):
            os.makedirs(f'./results/{download_path}')
        file_path = f'./results/{download_path}/{basename(file_url)}'
        
    else:
        file_path = f'./results/{basename(file_url)}'
        
    with open(file_path, 'wb') as f:
        f.write(requests.get(file_url).content)
    
    return None

# main function that loops overs posts urls in posts-data.csv
def download_images():
    print('Starting images download...')
    source_file = "./posts-data.csv"
    if not os.path.isfile(source_file):
        print('Source file "posts-data.csv" does not exists')
        return
    
    file_data = []
    header = None
    with open(source_file, encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file, ['name','url', 'content', 'date', 'slug', 'featured_image', 'description', 'categories', 'tags'])
        header = next(csv_reader)
        for row in csv_reader:
            file_data.append(row)

    if not file_data:
        print('Sources file returned empty data')
        return
    
    for row in file_data:
        url = row['featured_image']
        if not url:
            continue
        
        print(f"Downloading: {url}")
        download_file(url, 'images')


# run program
download_images()