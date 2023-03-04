from PIL import Image
import numpy as np
import regex as re
from pathlib import Path
import os
import multiprocessing
dataDir = 'dataset/'

# Get image size and (approximately) the number unique colors in it:
i = 0
def get_img_properties(img_path):
    # Load the image and convert to a NumPy array
    # image = cv2.imread(img_path, cv2.COLOR_BGR2RGB)
    image = Image.open(img_path)
    global i
    if i % 1000 == 0:
        print(image.size)
    i += 1
    image_np = np.array(image)
    # Round each color value to the nearest integer
    rounded_image_np = np.round(image_np).astype(int)
    # Reshape the array to a 2D array of pixels
    pixel_values = rounded_image_np.reshape((-1, 3))
    # Get the unique colors
    unique_colors = np.unique(pixel_values, axis=0)
    # Get their number
    num_unique_colors = len(unique_colors)
    return image.size, num_unique_colors

def getImgsPropsDf(classes_paths=None):
    if classes_paths is None:
        classes_paths = [class_path.absolute() for class_path in Path(dataDir).iterdir() if re.match("^\d+\. ", class_path.name)]
    df = None
    for class_path in classes_paths:
        # get the image names
        imgs = [img.name for img in class_path.iterdir()]
        img_paths = [os.path.join(os.path.normpath(class_path.as_posix()), img) for img in imgs]
        # Get image properties
        PROCESSES = 8
        with multiprocessing.Pool(PROCESSES) as pool:
            results = [pool.apply_async(get_img_properties, (p,)) for p in img_paths]
            results = [res.get() for res in results]
        widths, heights = zip(*results[0])
        aspect_ratios = [round(w / h, 2) for w, h in results[0]]
        areas = [w * h for w, h in results[0]]


if __name__ == "__main__":
    
    datasetPaths = [dp for dp in Path(dataDir).iterdir() if re.match("^\d+\. ", dp.name)]
    imgPropertiesDf = getImgsPropsDf(datasetPaths[1:]) 
