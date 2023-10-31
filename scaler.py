import numpy as np
import cv2

class Scaler:
    """
    A class to scale an image down to a smaller size. This is useful for processing large images
    that would take a long time to process at full size. The image is scaled down while maintaining
    its aspect ratio.

    Attributes:
    -----------
    img : numpy.ndarray
        The original image before scaling.
    scaled_img : numpy.ndarray
        The scaled image.
    scale_limit : int
        The maximum size of the image after scaling. If the image is already smaller than this size,
        it will not be scaled.
    scale_percent : float
        The percentage by which the image is scaled down.

    Methods:
    --------
    __init__(self, image: np.ndarray, scale_limit: int = 1000) -> None
        Initializes the Scaler object with an image and a scale limit.

    scale_image(self) -> None
        Scales the image down to the specified scale limit.

    get_scaled_image(self) -> np.ndarray
        Returns the scaled image.

    get_scale_limit(self) -> int
        Returns the scale limit.

    get_scale_percent(self) -> float
        Returns the scale percentage.

    descale_roi(self, roi: np.ndarray) -> np.ndarray
        If the image was scaled down for cropping, this function scales the roi back up to the
        original size of the image.

    """

    img: np.ndarray = None
    scaled_img: np.ndarray = None
    scale_limit: int = 1000
    scale_percent: float = 1

    def __init__(self, image: np.ndarray, scale_limit: int = 1000) -> None:
        """
        Initializes the Scaler object with an image and a scale limit.

        Parameters:
        -----------
        image : numpy.ndarray
            The image to be scaled down.
        scale_limit : int, optional
            The maximum size of the image after scaling. If the image is already smaller than this size,
            it will not be scaled. Default is 1000.
        """
        self.img = image.copy()
        self.scale_limit = scale_limit
        if self.img.shape[0] > self.scale_limit or self.img.shape[1] > self.scale_limit:
            if self.img.shape[0] > self.img.shape[1]:
                self.scale_percent = self.scale_limit / self.img.shape[0]
            else:
                self.scale_percent = self.scale_limit / self.img.shape[1]
            self.scale_image()

    def scale_image(self) -> None:
        """
        Scales the image down to the specified scale limit.
        """
        width =  int(self.img.shape[1] * self.scale_percent)
        height = int(self.img.shape[0] * self.scale_percent)
        dim = (width, height)
        self.scaled_img = cv2.resize(self.img, dim, interpolation = cv2.INTER_AREA)

    def get_scaled_image(self) -> np.ndarray:
        """
        Returns the scaled image.

        Returns:
        --------
        numpy.ndarray
            The scaled image.
        """
        return self.scaled_img
    
    def get_scale_limit(self) -> int:
        """
        Returns the scale limit.

        Returns:
        --------
        int
            The maximum size of the image after scaling.
        """
        return self.scale_limit
    
    def get_scale_percent(self) -> float:
        """
        Returns the scale percentage.

        Returns:
        --------
        float
            The percentage by which the image is scaled down.
        """
        return self.scale_percent
    
    def descale_roi(self, roi: np.ndarray) -> np.ndarray:
        """
        If the image was scaled down for cropping, this function scales the roi back up to the
        original size of the image.

        Parameters:
        -----------
        roi : list of tuples
            The region of interest to be descaled. Each tuple contains the (x, y) coordinates of a point.

        Returns:
        --------
        list of tuples
            The descaled region of interest. Each tuple contains the (x, y) coordinates of a point.
        """
        if self.img.shape[0] > self.scale_limit or self.img.shape[1] > self.scale_limit:
            roi = [(int(t[0]/self.scale_percent),
                    int(t[1]/self.scale_percent))
                    for t in roi]
        return roi
