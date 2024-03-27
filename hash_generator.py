from io import BytesIO
from typing import Optional

from PIL import Image


def _expand_to_range(numbers):
    min_num = min(numbers)
    max_num = max(numbers)
    new_numbers = []
    for num in numbers:
        try:
            new_num = round(((num - min_num) / (max_num - min_num)) * 255)
        except Exception as e:
            print(e)
            new_num = round(num)
        new_numbers.append(new_num)
    return new_numbers


def process_image(file_to_process: Optional[bytes] = None, filename: Optional[str] = '') -> Optional[str]:
    if file_to_process:
        image = Image.open(BytesIO(file_to_process))
        image = image.convert("L")

        image_v = image.resize((31, 31), Image.LANCZOS)
        pixels = list(image_v.getdata())
        vertical_avg_pixels = [sum(pixels[i::31]) / 31 for i in range(31)]

        image_h = image.resize((17, 17), Image.LANCZOS)
        pixels = list(image_h.getdata())
        horizontal_avg_pixels = [sum(pixels[i * 17:(i + 1) * 17]) / 17 for i in range(17)]

        vertical_hex_values = "".join(hex(pixel)[2:].zfill(2) for pixel in _expand_to_range(vertical_avg_pixels))
        horizontal_hex_values = "".join(hex(pixel)[2:].zfill(2) for pixel in _expand_to_range(horizontal_avg_pixels))

        hash_value = vertical_hex_values + horizontal_hex_values

        print(f'{filename}: {hash_value}')
        return hash_value
