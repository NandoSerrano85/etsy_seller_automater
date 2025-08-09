import os, cv2, numpy as np
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = str(pow(2,40))
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"

def crop_transparent(image_path='', image=None):
    # Read the image with OpenCV
    if image is None:
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    else:
        img = image
    
    # Ensure the image has an alpha channel
    if img.shape[2] != 4:
        print("Image doesn't have an alpha channel")
        return None
    
    # Split the image into color channels and alpha channel
    bgr = img[:,:,:3]
    alpha = img[:,:,3]
    
    # Get the bounding box of non-transparent pixels
    rows = np.any(alpha != 0, axis=1)
    cols = np.any(alpha != 0, axis=0)
    ymin, ymax = np.where(rows)[0][[0, -1]]
    xmin, xmax = np.where(cols)[0][[0, -1]]
    
    # Crop the image
    cropped = img[ymin:ymax+1, xmin:xmax+1]
    
    # Save the cropped image
    return cropped