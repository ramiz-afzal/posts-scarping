import cloudscraper
from bs4 import BeautifulSoup as soup
import os
import time
import csv
import urllib.parse
import json

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
    if 'single-post' not in body_css_classes:
        return False
    
    # Get article element for post categories and tag css classes
    tags        = []
    categories  = []
    article     = web_soup.select_one('main.content article.post')
    if article:
        article_css_classes = article.get('class', [])
        if article_css_classes:
            for css_class in article_css_classes:
                if 'category-' in css_class:
                    category = to_title_case(css_class)
                    if category:
                        categories.append(category)
                    pass
                elif 'tag-' in css_class:
                    tag = to_title_case(css_class)
                    if tag:
                        tags.append(tag)


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
    slug = slug.replace('.html', '')
    
    # post date
    post_date = ''
    dateModified = body_content.find('meta', attrs={"itemprop": "dateModified"})
    if dateModified:
        post_date = dateModified.get('content', '')

    # Remove unnecessary elements from the data
    mainEntityOfPage = body_content.find('meta', attrs={"itemprop": "mainEntityOfPage"})
    if mainEntityOfPage:
        mainEntityOfPage.decompose()
        
    social_panels = body_content.find_all('div', attrs={"class": "swp_social_panel"})
    if social_panels:
        for panel in social_panels:
            panel.decompose()

    comment_box = body_content.find('div', attrs={"id": "wpdevar_comment_1"})
    if comment_box:
        comment_box.decompose()

    related_posts = body_content.find('div', attrs={"id": "crp_related"})
    if related_posts:
        related_posts.decompose()

    scripts = body_content.find_all('script')
    if scripts:
        for script in scripts:
            script.decompose()

    styles = body_content.find_all('style')
    if styles:
        for style in styles:
            style.decompose()

    publisher = body_content.find('div', attrs={"itemprop": "publisher"})
    if publisher:
        publisher.decompose()
        
    # replace images html
    image_links = []
    page_links = body_content.find_all('a')
    if page_links:
        for link in page_links:
            href = link.get('href', '')
            if 'https://www.lawofficeofdanharris.com/wp-content/' in href:
                image_links.append(link)
        
    if image_links:
        for link_img in image_links:
            noscript = link_img.find('noscript')
            if not noscript:
                continue
            
            img_element = noscript.find('img')
            if not img_element:
                continue
            
            img_src = link_img.get('href', '')
            css_classes = " ".join(img_element.get('class', []))
            html = soup(f'<img src="{img_src}" class="{css_classes}">', 'html5lib')
            link_img.clear()
            link_img.append(html.img)

    # create a safe post_name
    post_name = "".join([c for c in web_soup.title.string if c.isalpha() or c.isdigit() or c == ' ']).rstrip()

    # post content
    content = "".join([x.prettify(formatter='html') for x in body_content.find_all(recursive=False)])

    # create data object
    url_data = {}
    url_data.update({'name': post_name})
    url_data.update({'url': url})
    url_data.update({'content': content})
    url_data.update({'date': post_date})
    url_data.update({'slug': slug})
    url_data.update({'description': seo_description})
    url_data.update({'categories': json.dumps(categories)})
    url_data.update({'tags': json.dumps(tags)})

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

        print(f'Scrapping: {url}')
        url_data = get_url_data(url)
        if not url_data:
            continue

        scrapped_data.append(url_data)

    if len(scrapped_data) == 0:
        print('None of the provided URLs returned proper data')
        return

    output_file_name = f"./results/{time.time()}-posts-data.csv"
    with open(output_file_name, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, ['name','url', 'content', 'date', 'slug', 'description', 'categories', 'tags'])
        dict_writer.writeheader()
        dict_writer.writerows(scrapped_data)
    
    print('Data scrapped successfully')
    return


# convert kebab string to title * slug dict
def to_title_case(string: str = None):
    if not string:
        return None
    
    parts = string.split('-')
    parts.pop(0)
    x_slug  = '-'.join(parts)
    x_title = x_slug.replace('-', ' ').title()
    return {"slug": x_slug, "title": x_title}
    

# run program
scrap_data()