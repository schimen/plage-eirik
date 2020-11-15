from async_scraper_lib import scrape_4chan, scrape_deviantart, scrape_giphy, purge_folder, transform_images
import asyncio

async def main():
    tasks = []
    tasks.append(asyncio.create_task(purge_folder()))
    tasks.append(asyncio.create_task(scrape_4chan('wg',n_images=25)))
    tasks.append(asyncio.create_task(scrape_deviantart('electronics',n_images=25)))
    tasks.append(asyncio.create_task(scrape_giphy('arduino',n_images=25)))

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    transform_images()
