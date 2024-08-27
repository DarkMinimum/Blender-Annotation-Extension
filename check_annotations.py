import ast
import csv

import cv2
import numpy as np
from PIL import Image

img_path = 'tmp/IMG_72.jpg'
points_path = 'tmp/example.txt'
output_path = 'tmp/res_IMG_72.jpg'


def annotate():
    img_raw = Image.open(img_path).convert('RGB')
    img_to_draw = cv2.cvtColor(np.array(img_raw), cv2.COLOR_RGB2BGR)

    with open(points_path, 'r') as file:
        file_content = file.read().strip()
        try:
            parsed_data = ast.literal_eval(file_content)

            # Ensure the parsed data is a list of tuples
            if isinstance(parsed_data, list) and all(isinstance(item, tuple) for item in parsed_data):
                print("Parsed data:", parsed_data)

            # Iterate over each row in the CSV
            for row in parsed_data:
                img_to_draw = cv2.circle(img_to_draw, (int(row[0]), int(row[1])), 2, (0, 0, 255), -1)
        finally:
            print("finally")

    cv2.imwrite((output_path), img_to_draw)


if __name__ == '__main__':
    annotate()
