from webcam import Webcam
from connect4 import Connect4
import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

def main():
    # Create a new webcam object
    webcam = Webcam()
    opened = webcam.open()
    if not opened:
        print('Error opening webcam')
        return

    connect4 = Connect4()

    # Images to render on the screen
    frame = None
    detected_circles = None
    detected_circle_colors = None
    detected_color = None
    output = None
    
    while True:
        frame = webcam.get_frame()

        # First time through the loop, initialize the images
        if detected_circles is None:
            detected_circles = frame.copy()
            detected_circle_colors = frame.copy()
            detected_color = frame.copy()

        try :
            connect4.from_image(frame)
            detected_circles = connect4.draw_circles()
            detected_circle_colors = connect4.draw_circle_colors()
            detected_color = connect4.draw_board_state()
        
        except ValueError as e:
            print(e)

        # Reduce the size of the image to fit on the screen
        frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

        # Resize the detected circles image to be the same size as the original image
        detected_circles = cv2.resize(detected_circles, (frame.shape[1], frame.shape[0]))
        detected_circle_colors = cv2.resize(detected_circle_colors, (frame.shape[1], frame.shape[0]))
        detected_color = cv2.resize(detected_color, (frame.shape[1], frame.shape[0]))

        # Stack the images onto a single image
        top = np.hstack([frame, detected_circles])
        bottom = np.hstack([detected_circle_colors, detected_color])
        output = np.vstack([top, bottom])
        cv2.imshow('frame', output)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the capture
    webcam.close()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()


