import cloudscraper
from bs4 import BeautifulSoup as soup
import os
import time
import csv
import urllib.parse

def get_url_data(url: str = None):
    # sanity check
    if not url:
        return False

    # make HTTP request
    scraper = cloudscraper.create_scraper()
    website = scraper.get(url)

    if website.status_code != 200:
        print(f"Invalid status code: {website.status_code}\n")
        return False
    
    # initialize BeautifulSoup
    web_soup = soup(website.text, 'html5lib')

    # Check if body has "post" class so we can confirm we are on a post
    body = web_soup.find('body')
    if not body:
        return False

    body_css_classes = body.get('class', [])
    if 'post' not in body_css_classes:
        return False

    # Get post text content
    body_content = web_soup.find('div', attrs={"class": "entry-content"})
    if not body_content:
        return False
    
    # SEO Description
    seo_description = ''
    meta_description = web_soup.find('meta', attrs={"name": "description"})
    if meta_description:
        seo_description = meta_description['content']
    
    # post slug
    slug = ''
    parsed_URL = urllib.parse.urlparse(url)
    if "/" in parsed_URL.path:
        slug = parsed_URL.path.split('/')[-1]
    else:
        slug = parsed_URL.path

    # Remove unnecessary elements from the data
    dateModified = body_content.find('meta', attrs={"itemprop": "dateModified"})
    if dateModified:
        dateModified.decompose()

    mainEntityOfPost = body_content.find('meta', attrs={"itemprop": "mainEntityOfPost"})
    if mainEntityOfPost:
        mainEntityOfPost.decompose()

    gform = body_content.find('div', attrs={"class": "gform_wrapper"})
    if gform:
        gform.decompose()

    iframes = body_content.find_all('iframe')
    if iframes:
        for iframe in iframes:
            iframe.decompose()

    scripts = body_content.find_all('script')
    if scripts:
        for script in scripts:
            script.decompose()

    swp = body_content.find('div', attrs={"class": "swp-hidden-panel-wrap"})
    if swp:
        swp.decompose()

    publisher = body_content.find('div', attrs={"itemprop": "publisher"})
    if publisher:
        publisher.decompose()

    # create a safe post_name
    post_name = "".join([c for c in web_soup.title.string if c.isalpha() or c.isdigit() or c == ' ']).rstrip()

    # post content
    content = "".join([x.prettify(formatter='html') for x in body_content.find_all(recursive=False)])

    # create data object
    url_data = {}
    url_data.update({'name': post_name})
    url_data.update({'url': url})
    url_data.update({'content': content})
    url_data.update({'slug': slug})
    url_data.update({'description': seo_description})

    return url_data


# main function that loops overs posts urls in posts.xml
def scrap_data():
    print('Data scrapping started...')
    source_file = "./posts.xml"
    if not os.path.isfile(source_file):
        print('Source file "posts.xml" does not exists')
        return
    
    file_data = None
    with open(source_file, 'r') as file:
        file_data = file.read()

    if not file_data:
        print('Sources file returned empty data')
        return
    
    web_soup = soup(file_data, features='lxml')
    link_elements = web_soup.find_all('loc')
    if not link_elements or len(link_elements) == 0:
        print('No url elements available in source file')
        return
    
    scrapped_data = []
    for link in link_elements:
        url = link.text
        if not url:
            continue

        url_data = get_url_data(url)
        if not url_data:
            continue

        scrapped_data.append(url_data)

    if len(scrapped_data) == 0:
        print('None of the provided URLs returned proper data')
        return

    output_file_name = f"./results/{time.time()}-posts-data.csv"
    with open(output_file_name, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, ['name','url', 'content', 'slug', 'description'])
        dict_writer.writeheader()
        dict_writer.writerows(scrapped_data)
    
    print('Data scrapped successfully')
    return

# run program
scrap_data()