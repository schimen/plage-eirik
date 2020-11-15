import os
import html5lib
import asyncio
import aiohttp
import aiofiles
from aiofiles.os import remove
from bs4 import BeautifulSoup
from json import loads
from time import time
from PIL import Image

def resize_gif(path, size=(240,240)):
    #analyse image:
    im = Image.open(path)
    results = {'size': im.size, 'mode': 'full',}
    try:
        while True:
            if im.tile:
                tile = im.tile[0]
                update_region = tile[1]
                update_region_dimensions = update_region[2:]
                if update_region_dimensions != im.size:
                    results['mode'] = 'partial'
                    break
            im.seek(im.tell() + 1)

    except EOFError:
        pass

    #extract and resize frames:
    mode = results['mode']
    im.seek(0)

    i = 0
    p = im.getpalette()
    last_frame = im.convert('RGBA')

    all_frames = []

    try:
        while True:
            if not im.getpalette():
                im.putpalette(p)

            new_frame = Image.new('RGBA', im.size)

            if mode == 'partial':
                new_frame.paste(last_frame)

            new_frame.paste(im, (0, 0), im.convert('RGBA'))

            new_frame.thumbnail(size, Image.ANTIALIAS)
            all_frames.append(new_frame)

            i += 1
            last_frame = new_frame
            im.seek(im.tell() + 1)

    except EOFError:
        pass

    if len(all_frames) == 1:
        print("Warning: only 1 frame found")
        all_frames[0].save(path, optimize=True)
    else:
        try:
            all_frames[0].save(path, optimize=True, save_all=True, append_images=all_frames[1:], loop=1000)
        except ValueError:
            print(f'could not save {path}, unknown file extension')

def transform_images(path=os.path.join(os.getcwd(),'images'), size=(240,240)):
    print('transforming images')
    start = time()
    n_images = len(os.listdir(path))
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        im = Image.open(file_path)
        size=(240,240)
        if file.lower().endswith('.gif'):
            resize_gif(file_path, size=size)

        else:
            out = im.resize(size)
            out.save(file_path)

    end = time()
    print(f'finished transforming {n_images} images in {end-start} seconds')

async def purge_folder(path=os.path.join(os.getcwd(),'images')):
    start = time()
    remove_tasks = []
    n_files = len(os.listdir(path))
    for file in os.listdir(path):
        try:
            asyncio.create_task(remove(os.path.join(path, file)))
        except PermissionError:
            print(f'{file} was not deleted')

    await asyncio.gather(*remove_tasks)
    end = time()
    print(f'purged {n_files} files in {path} in {end-start} seconds')

def is_image(filename, accepted_endings=('.gif','.jpg','.png')):
    """
    checks the ending of the filename and returns true
    if the filename is equal to one of the specified file endings
    """
    for ending in accepted_endings:
        if filename.lower().endswith(ending):
            return True

    return False

async def get_soup(url, parser='html5lib'):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.read()

    return BeautifulSoup(text.decode('utf-8'), parser)

async def get_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.read()

    return loads(text.decode('utf-8'))

async def get_image(url, path=os.getcwd(), name=None):
    if name == None:
        name = url.split('/')[-1]

    forbidden_symbols = '/\:*?"<>|'
    name = ''.join([char for char in name if char not in forbidden_symbols])
    image_path = os.path.join(path, name)
    if is_image(name):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(image_path, mode='wb')
                    await f.write(await resp.read())
                    await f.close()

    else:
        print(f'{name} not an image')

async def scrape_4chan(channel, n_images=10,
                       save_folder=os.path.join(os.getcwd(),'images')):
    url = f'https://boards.4channel.org/{channel}/'
    print(f'scraping 4chan: {url}')
    start = time()
    soup = await get_soup(url)
    image_urls = []
    for i, element in enumerate(soup.find_all('div', class_='thread')[1:]):
        file_divs = element.find_all('div', class_='file')
        for j, file_div in enumerate(file_divs):
            filetext_div = file_div.find('div', class_='fileText')
            try:
                image_url = 'https:' + filetext_div.find('a')['href']
                image_urls.append(image_url)

            except AttributeError:
                print(f'no image here')
                continue

    tasks = []
    for url in image_urls[:n_images]:
        task = asyncio.create_task(get_image(url, path=save_folder))
        tasks.append(task)

    n_files = len(tasks)
    await asyncio.gather(*tasks)
    end = time()
    print('Scraped 4chan:')
    print(f'saved {n_files} files in {save_folder}.\nTook {end-start} seconds')

async def scrape_deviantart(search, minimum_size=(240,240), n_images=10,
                            save_folder=os.path.join(os.getcwd(),'images')):
    order = 'popular-24-hours'
    type = 'deviations'
    base_url = 'https://backend.deviantart.com/rss.xml'
    query_url = f'?type={type}&q=order%3A{order}+{search}'
    rss_url = base_url + query_url
    print(f'scraping deviantart: {rss_url}')
    start = time()
    soup = await get_soup(rss_url)
    items = soup.find_all('item')
    if len(items) > n_images:
        items = items[:n_images]

    tasks = []
    for item in items:
        content = item.find('media:content')
        file_url = content['url']
        author = item.find('media:credit').text
        title = item.find('title').text
        name = f'{author}-{title}'
        accepted_endings = ('.jpg', '.png', '.gif')
        for ending in accepted_endings:
            if ending in file_url:
                name += ending
                break

        task = asyncio.create_task(get_image(file_url,
                                             path=save_folder, name=name))
        tasks.append(task)

    n_files = len(tasks)
    await asyncio.gather(*tasks)
    end = time()
    print('Scraped deviantart:')
    print(f'saved {n_files} files in {save_folder}.\nTook {end-start} seconds')

async def scrape_giphy(search, minimum_size=(240,240), n_images=10,
                       save_folder=os.path.join(os.getcwd(),'images')):
    sort = 'recent'
    url = f'https://giphy.com/search/{search}?sort={sort}'
    print(f'scraping giphy: {url}')
    start = time()
    soup = await get_soup(url)
    longest_script = max(soup.find_all('script'), key = lambda x: len(x.text))
    longest_script = longest_script.text
    start_json, end_json = (0, 1)
    for i, symbol in enumerate(longest_script):
        if symbol == '[':
            start_json = i
            break

    longest_script_reversed = longest_script[::-1]
    for i, symbol in enumerate(longest_script_reversed):
        if symbol == ']':
            end_json = len(longest_script) - i
            break
    json_text = longest_script[start_json:end_json]
    data = loads(json_text)
    if n_images < len(data):
        data = data[:n_images]

    tasks = []
    for gif_data in data:
        name = gif_data['title']
        if gif_data['type'] != 'gif':
            print(f'{name} not a gif')
            continue
        name += '.gif'
        file_url = gif_data['images']['original']['url']
        task = asyncio.create_task(get_image(file_url, path=save_folder,
                                             name=name))
        tasks.append(task)

    n_files = len(tasks)
    await asyncio.gather(*tasks)
    end = time()
    print('Scraped giphy:')
    print(f'saved {n_files} files in {save_folder}.\nTook {end-start} seconds')
