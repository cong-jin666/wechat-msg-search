from PIL import Image
import numpy as np
from skimage.feature import hog

def rgb2gray(im):
    return im[:,:,0]*0.2989 + im[:,:,1]*0.587 + im[:,:,2]*0.114

def get_feat():
    image_path = 'jokerpoke.jpg'
    image = Image.open(image_path)  # Open the image file
    image = image.resize((256, 256))  # Resize the image
    image = np.array(image)  # Convert the image to a numpy array

    # Convert the image to grayscale
    gray = rgb2gray(image)

    # Extract HOG features
    fd = hog(gray, orientations=20, pixels_per_cell=(20, 20), cells_per_block=(2, 2), visualize=False, transform_sqrt=True, block_norm='L2-Hys')
    print(fd)

if __name__ == '__main__':
    get_feat()
