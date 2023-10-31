import scaler
import cv2
import numpy as np
from typing import List, Tuple

class Cropper:
    """
    A class to crop an image using mouse events. The user can select a rectangle on the
    image and the image will be cropped to that rectangle. The user can also reset the
    rectangle if they make a mistake. The cropped image can be retrieved using the
    get_cropped_image() method.

    Once the cropped area is selected, the user can press 'c' to crop the image and
    close the window with 'q'. Pressing 'r' will reset the cropping rectangle.

    Attributes:
    -----------
    roi : List[Tuple[int, int]]
        A list of two tuples representing the top-left and bottom-right corners of the cropping rectangle.
    scaler : Scaler
        The Scaler object used to scale the image down before cropping.
    initial_img : numpy.ndarray
        The original image before scaling and cropping.
    scaled_img : numpy.ndarray
        The original image before cropping.
    crop_img : numpy.ndarray
        The image being displayed with the cropping rectangle drawn on it.
    cropped_img : numpy.ndarray
        The cropped image.

    Methods:
    --------
    __init__(self, image: np.ndarray) -> None
        Initializes the Cropper object with an image.
    shape_selection_handler(self, event: int, x: int, y: int, flags: int, param: int) -> None
        A callback function for mouse events. This function is called when the user clicks
        or drags on the image.
        Parameters:
        -----------
        event : int
            The mouse event.
        x : int
            The x-coordinate of the mouse event.
        y : int
            The y-coordinate of the mouse event.
        flags : int
            The flags for the mouse event.
        param : int
            The param for the mouse event.
    crop_image(self) -> None
        Displays the image and waits for the user to select a cropping rectangle. The user
        can press 'r' to reset the rectangle and 'c' to crop the image.
    get_initial_image(self) -> np.ndarray
        Returns the original image before scaling and cropping.
    get_cropped_image(self) -> np.ndarray
        Returns the cropped image.
    get_crop_image(self) -> np.ndarray
        Returns the image being displayed with the cropping rectangle drawn on it.
    get_roi(self) -> List[Tuple[int, int]]
        Returns the cropping rectangle.
    """
    roi: List[Tuple[int, int]] = []
    scaler = None
    initial_img: np.ndarray = None
    scaled_img: np.ndarray = None
    crop_img: np.ndarray = None
    cropped_img: np.ndarray = None

    def __init__(self, image: np.ndarray) -> None:
        """
        Initializes the Cropper object with an image.

        Parameters:
        -----------
        image : numpy.ndarray
            The image to be cropped.
        """
        self.roi = []
        self.initial_img = image.copy()
        self.scaler = scaler.Scaler(self.initial_img)
        self.scaler.scale_image()
        self.scaled_img = self.scaler.get_scaled_image()
        self.crop_img = self.scaled_img.copy()
        self.cropped_img = self.scaled_img.copy()

    def shape_selection_handler(self, event: int, x: int, y: int, flags: int, param: int) -> None:
        """
        A callback function for mouse events. This function is called when the user clicks
        or drags on the image.

        Parameters:
        -----------
        event : int
            The mouse event.
        x : int
            The x-coordinate of the mouse event.
        y : int
            The y-coordinate of the mouse event.
        flags : int
            The flags for the mouse event.
        param : int
            The param for the mouse event.
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            self.roi = [(x, y)]
        elif event == cv2.EVENT_LBUTTONUP:
            self.roi.append((x, y))
            cv2.rectangle(self.crop_img, self.roi[0], self.roi[1], (0, 255, 0), 2)
            cv2.imshow("Image", self.crop_img)

    def crop_image(self) -> None:
        """
        Displays the image and waits for the user to select a cropping rectangle. The user
        can press 'r' to reset the rectangle and 'c' to crop the image.
        """
        cv2.namedWindow("Crop Image")
        cv2.setMouseCallback("Crop Image", self.shape_selection_handler)
        while True:
            cv2.imshow("Crop Image", self.crop_img)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("r"):
                self.crop_img = self.scaled_img.copy()
                self.roi = []
            elif key == ord("c"):
                break
        self.roi = self.scaler.descale_roi(self.roi)
        self.cropped_img = crop_image_from_roi(self.initial_img, self.roi)
        cv2.destroyAllWindows()

    def get_initial_image(self) -> np.ndarray:
        """
        Returns the original image before scaling and cropping.
        """
        return self.scaled_img
    
    def get_cropped_image(self) -> np.ndarray:
        """
        Returns the cropped image.
        """
        return self.cropped_img
    
    def get_crop_image(self) -> np.ndarray:
        """
        Returns the image being displayed with the cropping rectangle drawn on it.
        """
        return self.crop_img
    
    def get_roi(self) -> List[Tuple[int, int]]:
        """
        Returns the cropping rectangle.
        """
        return self.roi


def crop_image_from_roi(image: np.ndarray, roi: List[Tuple[int, int]]) -> np.ndarray:
    '''
    If there are two reference points, then crop the region of interest
    from the image and display it. Take care of the case where the user
    drags from bottom right to top left instead of top left to bottom right.
    Also take care of the case where the user drags outside the image.
    '''
    if len(roi) == 2:
        x1, y1 = roi[0]
        x2, y2 = roi[1]
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        x_max = min(x_max, image.shape[1])
        y_max = min(y_max, image.shape[0])
        x_min = max(x_min, 0)
        y_min = max(y_min, 0)
        roi = image[y_min:y_max, x_min:x_max]
        return roi