import os
import re
from time import sleep
from typing import Optional

import requests

from constants import OUT_FOLDER, SAVED_POST_LINKS_FILE, IMAGE_HASHES_FILE
from hash_generator import process_image


def is_error_page(response: requests.Response) -> bool:
    result = bool(re.search(r'<title>Ошибка \| ВКонтакте</title>', response.text))
    return result


def is_deleted_page(response: requests.Response) -> bool:
    result = bool(re.search(r'<title>Запись удалена \| ВКонтакте</title>', response.text))
    return result


def gen_links(start_pos: int, count: int = 10):
    post_mask = 'https://vk.com/wall-136259311_{post_id}'
    while start_pos >= count:
        result = [post_mask.format(post_id=str(x)) for x in range(start_pos, start_pos - count, -1)]
        start_pos -= count
        yield result
    yield [post_mask.format(post_id=str(x)) for x in range(start_pos, 0, -1)]


def get_saved_links() -> list[str]:
    path = os.path.join(OUT_FOLDER, SAVED_POST_LINKS_FILE)
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            saved_links = f.read()
            saved_links = saved_links.split('\n')
            saved_links = list(filter(lambda x: x, saved_links))
        return saved_links
    return []


def save_links_to_file(links_to_save: list[str]) -> bool:
    print(f'Saving delta to file. Links to save: {len(links_to_save)}')
    path = os.path.join(OUT_FOLDER, SAVED_POST_LINKS_FILE)
    if links_to_save:
        with open(path, 'a', encoding='utf-8') as f:
            f.write('\n'.join(links_to_save))
            f.write('\n')
    return True


def get_post_links(
        start_post_id: int,
        timeout: float = 1.0,
        previous_saved_links: Optional[list[str]] = None,
        save_to_file_delta: int = 10
) -> list[str]:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/123.0.0.0 '
                             'Safari/537.36'}

    start_post = start_post_id
    saved_links = previous_saved_links or []

    try:
        link_generator = gen_links(start_post, count=save_to_file_delta)
        for current_links in link_generator:
            save_delta = []
            for link in current_links:
                print(f'Link is: {link}')
                if link in saved_links:
                    print('Link already saved!')
                    continue
                x = requests.get(link, headers=headers)
                print(f'GET {link} - {x.status_code}')
                if x.status_code == 200 and len(x.history) == 0 and not is_error_page(x) and not is_deleted_page(x):
                    save_delta.append(link)
                    print(f'Add {link} to save_delta')
                if timeout:
                    sleep(timeout)
            save_links_to_file(save_delta)
    except StopIteration as e:
        print('All links were parsed')

    return saved_links


def get_image_links_from_page(link: str) -> list[dict[str, str]]:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/123.0.0.0 '
                             'Safari/537.36'}
    x = requests.get(link, headers=headers)
    images = re.findall(r'<img class="PhotoPrimaryAttachment__imageElement" src="(.*?)"', x.text)
    if not images:
        images = re.findall(r'<img class="MediaGrid__imageElement" src="(.*?)"', x.text)
    images = [{
        'link': image_link.replace('amp;', ''),
        'filename': re.search(r'/([a-zA-Z0-9_\-]+\.\w+)\?', image_link).group(1)
    } for image_link in images]
    return images


def save_image_hash_to_file(image_link: str, image_hash: str) -> bool:
    path = os.path.join(OUT_FOLDER, IMAGE_HASHES_FILE)
    with open(path, 'a', encoding='utf-8') as file:
        file.write(f'{image_hash}:{image_link}')
        file.write('\n')
    return True


def main():
    previous_saved_links = get_saved_links()
    start_post_id = int(previous_saved_links[-1].split('_')[-1]) - 1 if previous_saved_links else 327956
    links = get_post_links(start_post_id, timeout=0, previous_saved_links=previous_saved_links)

    image_links = []
    for link in links:
        image_links.extend(get_image_links_from_page(link))

    for item in image_links:
        file_data = requests.get(item['link']).content
        file_hash = process_image(file_to_process=file_data, filename=item['filename'])
        save_image_hash_to_file(item['link'], file_hash)


if __name__ == '__main__':
    main()
