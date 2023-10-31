import cv2
import numpy as np

class Webcam:
    """
    A class used to represent a webcam.

    Attributes
    ----------
    cap : cv2.VideoCapture
        The VideoCapture object used to capture video from the webcam.

    Methods
    -------
    __init__(self)
        Initializes the Webcam object.

    open(self)
        Opens the webcam.

    close(self)
        Closes the webcam.

    get_frame(self)
        Returns a frame from the webcam.

    __del__(self)
        Destructor that closes the webcam.

    """

    cap = None
    
    def __init__(self) -> None:
        """
        Initializes the Webcam object.
        """
        pass

    def __del__(self) -> None:
        """
        Closes the webcam.
        """
        self.close()

    def open(self) -> bool:
        """
        Opens the webcam.

        Returns
        -------
        bool
            True if the webcam was opened successfully, False otherwise.
        """
        self.cap = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            return False
        return True

    def close(self) -> None:
        """
        Closes the webcam.
        """
        self.cap.release()

    def get_frame(self) -> np.ndarray:
        """
        Returns a frame from the webcam.

        Returns
        -------
        numpy.ndarray
            A frame from the webcam.
        """
        _, frame = self.cap.read()
        return frame
    