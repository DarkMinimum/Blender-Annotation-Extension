import re
import os

import cv2
import numpy as np
from PIL import Image

N = 80
img_path = '%s/generated/img/IMG_%d.jpg' % (os.environ['SAMPLE_ROOT'], N)
points_path = '%s/generated/gt/GT_%d.txt' % (os.environ['SAMPLE_ROOT'], N)
output_path = 'tmp/res/result_' + str(N) + '_%d.jpg'


def annotate():
    img_raw = Image.open(img_path).convert('RGB')
    img_to_draw = cv2.cvtColor(np.array(img_raw), cv2.COLOR_RGB2BGR)

    with open(points_path, 'r') as file:
        file_content = file.read().strip()
        try:
            matches = re.findall(r'\((\d+), (\d+)\)', file_content)
            pairs = [(int(x), int(y)) for x, y in matches]

            # Ensure the parsed data is a list of tuples
            if isinstance(pairs, list) and all(isinstance(item, tuple) for item in pairs):
                print("Parsed data:", pairs)

            # Iterate over each row in the CSV
            print('heads to be printed ' + str(len(pairs)))
            for row in pairs:
                img_to_draw = cv2.circle(img_to_draw, (int(row[0]), int(row[1])), 2, (0, 255, 0), -1)
        finally:
            print("finally")

    cv2.imwrite((output_path % len(pairs)), img_to_draw)


if __name__ == '__main__':
    annotate()
