import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                             QSlider, QLineEdit, QRadioButton, QTableWidget,
                             QTableWidgetItem, QHBoxLayout, QGraphicsView, QGraphicsScene,
                             QSizePolicy, QGridLayout)

from PyQt5.QtGui import QPixmap, QPainter, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QObject

from webcam import Webcam
from connect4 import Connect4
import cv2
import numpy as np

class Connect4Worker(QObject):
    '''
    Worker thread for the Connect4 object
    '''

    # Signals
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    update = pyqtSignal(object)

    webcam = None
    connect4 = None

    radius = 45
    radius_delta = 5

    # Constructor
    def __init__(self, radius=45, radius_delta=5):
        super().__init__()

        self.radius = radius
        self.radius_delta = radius_delta

        self.webcam = Webcam()
        opened = self.webcam.open()
        if not opened:
            print('Error opening webcam')
            return

        self.connect4 = Connect4(self.radius, self.radius_delta)

    # Destructor
    def __del__(self):
        self.webcam.close()

    # Run the worker thread
    @pyqtSlot()
    def run(self):
        while True:
            self.detect()
            QApplication.processEvents()
            QThread.msleep(60)

    # Detect the circles in the webcam frame
    def detect(self):
        frame = self.webcam.get_frame()
        try:
            self.connect4.from_image(frame)
            detected_circles = self.connect4.draw_circles()
            detected_circle_colors = self.connect4.draw_circle_colors()
            detected_color = self.connect4.draw_board_state()
            board = self.connect4.get_board()
            self.update.emit((frame, detected_circles, detected_circle_colors, detected_color, board, None))
        except ValueError as e:
            self.error.emit(e.args)
            self.update.emit((frame, frame, frame, frame, None, e.args))

    def update_radius(self, radius):
        self.radius = radius
        self.connect4.set_radius(radius)

    def update_radius_delta(self, radius_delta):
        self.radius_delta = radius_delta
        self.connect4.set_radius_delta(radius_delta)

class Connect4UI(QWidget):
    # UI Elements
    radius_label = None
    radius_slider = None
    radius_text = None
    radius_delta_label = None
    radius_delta_slider = None
    radius_delta_text = None
    webcam_radio = None
    detected_circles_radio = None
    detected_colors_radio = None
    grid_radio = None
    error_log = None
    game_grid_layout = None
    webcam_frame = None
    webcam_scene = None

    # Saved frames from the webcam
    frame = None
    detected_circles = None
    detected_circle_colors = None
    detected_color = None

    # Saved board state
    board = None

    # Constructor
    def __init__(self):
        super().__init__()

        # Initialize the board state. This is rendered in the UI.
        self.board = np.full((6, 7), 'O')

        # Initialize the UI
        self.initUI()

        # Create a new thread to run the Connect4 object
        self.thread = QThread()
        self.worker = Connect4Worker()
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.update.connect(lambda args: self.handle_webcam_update(*args))

        # Update the radius and radius delta values in the worker thread
        self.radius_slider.valueChanged.connect(self.worker.update_radius)
        self.radius_delta_slider.valueChanged.connect(self.worker.update_radius_delta)

        # Trigger am update to the radius and radius delta values
        self.radius_slider.valueChanged.emit(self.radius_slider.value())
        self.radius_delta_slider.valueChanged.emit(self.radius_delta_slider.value())

        # Start the thread
        self.thread.start()

    # Destructor
    def __del__(self):
        self.webcam.close()

    # Initialize the UI
    def initUI(self):
        top_layout = QHBoxLayout()

        # Options Panel
        options_layout = QVBoxLayout()
        options_layout.addStretch(0)
        options_layout.setSpacing(10)

        # Add large "Options" label
        options_label = QLabel('Options')
        options_label.setStyleSheet('font-size: 20px; font-weight: bold;')
        options_layout.addWidget(options_label)

        # Add "Variables" label
        variables_label = QLabel('Variables')
        variables_label.setStyleSheet('font-weight: bold;')
        options_layout.addWidget(variables_label)

        # Radius Setting. Slider and text box should be on the same line
        radius_layout = QHBoxLayout()
        radius_layout.setSpacing(10)
        self.radius_label = QLabel('Radius:')
        self.radius_slider = QSlider(Qt.Horizontal)
        self.radius_slider.setRange(1, 100)  # Adjust range as needed
        self.radius_slider.setValue(35)  # Adjust initial value as needed
        self.radius_slider.setTickPosition(QSlider.TicksBelow)
        self.radius_slider.setTickInterval(10)
        self.radius_slider.setSingleStep(1)
        self.radius_slider.setFixedWidth(150)
        self.radius_text = QLineEdit()
        self.radius_text.setFixedWidth(50)
        self.radius_text.setText(str(self.radius_slider.value()))
        radius_layout.addWidget(self.radius_slider)
        radius_layout.addWidget(self.radius_text)
        options_layout.addWidget(self.radius_label)
        options_layout.addLayout(radius_layout)

        # Radius Delta Setting
        radius_delta_layout = QHBoxLayout()
        radius_delta_layout.setSpacing(10)
        self.radius_delta_label = QLabel('Radius Delta:')
        self.radius_delta_slider = QSlider(Qt.Horizontal)
        self.radius_delta_slider.setRange(1, 20)  # Adjust range as needed
        self.radius_delta_slider.setValue(5)  # Adjust initial value as needed
        self.radius_delta_slider.setTickPosition(QSlider.TicksBelow)
        self.radius_delta_slider.setTickInterval(5)
        self.radius_delta_slider.setSingleStep(1)
        self.radius_delta_slider.setFixedWidth(150)
        self.radius_delta_text = QLineEdit()
        self.radius_delta_text.setFixedWidth(50)
        self.radius_delta_text.setText(str(self.radius_delta_slider.value()))
        radius_delta_layout.addWidget(self.radius_delta_slider)
        radius_delta_layout.addWidget(self.radius_delta_text)
        options_layout.addWidget(self.radius_delta_label)
        options_layout.addLayout(radius_delta_layout)

        # Add event handlers to the slider and text box
        self.radius_slider.valueChanged.connect(lambda: self.slider_changed(self.radius_slider, self.radius_text))
        self.radius_text.textChanged.connect(lambda: self.text_changed(self.radius_text, self.radius_slider))
        self.radius_delta_slider.valueChanged.connect(lambda: self.slider_changed(self.radius_delta_slider, self.radius_delta_text))
        self.radius_delta_text.textChanged.connect(lambda: self.text_changed(self.radius_delta_text, self.radius_delta_slider))

        # Radio buttons label
        radio_buttons_label = QLabel('Display:')
        radio_buttons_label.setStyleSheet('font-weight: bold;')
        options_layout.addWidget(radio_buttons_label)

        # Radio Buttons
        self.webcam_radio = QRadioButton('Webcam')
        self.webcam_radio.setChecked(True)  # Set the default option
        self.detected_circles_radio = QRadioButton('Detected Circles')
        self.detected_colors_radio = QRadioButton('Detected Colors')
        self.grid_radio = QRadioButton('Grid')
        options_layout.addWidget(self.webcam_radio)
        options_layout.addWidget(self.detected_circles_radio)
        options_layout.addWidget(self.detected_colors_radio)
        options_layout.addWidget(self.grid_radio)

        # Add a stretchable space to push the "Error Log" label to the bottom
        options_layout.addStretch(1)

        # Add large "Error Log" label
        error_log_label = QLabel('Error Log')
        error_log_label.setStyleSheet('font-size: 20px; font-weight: bold;')
        options_layout.addWidget(error_log_label)

        # Error Log
        self.error_log = QTableWidget()
        self.error_log.setColumnCount(1)
        self.error_log.horizontalHeader().setVisible(False)
        self.error_log.verticalHeader().setVisible(False)
        self.error_log.setEditTriggers(QTableWidget.NoEditTriggers)
        self.error_log.setSelectionMode(QTableWidget.NoSelection)
        self.error_log.setFocusPolicy(Qt.NoFocus)
        self.error_log.setShowGrid(False)
        self.error_log.setAlternatingRowColors(True)
        self.error_log.setRowCount(0)
        self.error_log.setFixedHeight(150)
        self.error_log.setFixedWidth(200)
        # Set font size
        font = self.error_log.font()
        font.setPointSize(8)
        self.error_log.setFont(font)
        options_layout.addWidget(self.error_log)

        # Add a stretchable space to push the "Game State" label to the bottom
        options_layout.addStretch(1)

        # Add large "Game State" label
        game_state_label = QLabel('Game State')
        game_state_label.setStyleSheet('font-size: 20px; font-weight: bold;')
        options_layout.addWidget(game_state_label)

        # Game Grid
        self.game_grid_layout = QGridLayout()
        self.game_grid_layout.setSpacing(0)  # No spacing between items
        self.update_game_grid(self.board)

        options_layout.addLayout(self.game_grid_layout, 0)
        top_layout.addLayout(options_layout)

        # Webcam Frame
        self.webcam_frame = QGraphicsView()
        self.webcam_scene = QGraphicsScene()
        self.webcam_frame.setScene(self.webcam_scene)

        # Remove the scroll bars
        self.webcam_frame.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.webcam_frame.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        top_layout.addWidget(self.webcam_frame)

        # Fix the size of Options widgets
        self.radius_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.radius_slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.radius_text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.radius_delta_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.radius_delta_slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.radius_delta_text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.webcam_radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.detected_circles_radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.detected_colors_radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.grid_radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Maintain 1:1 aspect ratio for the webcam frame
        # self.webcam_frame.setAspectMode(Qt.KeepAspectRatio)
        self.webcam_frame.setRenderHint(QPainter.SmoothPixmapTransform)

        # Initial size of the window
        window_width = 1300
        window_height = 800
        self.resize(window_width, window_height)  # Adjust these values as needed to ensure a comfortable fit
        self.setMinimumSize(window_width, window_height)
        
        self.setLayout(top_layout)
        self.setWindowTitle('Connect4 Detection UI')
        self.show()

    def slider_changed(self, slider, text):
        text.setText(str(slider.value()))

    def text_changed(self, text, slider):
        value = text.text()
        if value.isdigit() \
        and int(value) >= slider.minimum() \
        and int(value) <= slider.maximum():
            slider.setValue(int(value))

    def get_radius(self):
        return self.radius_slider.value()
    
    def get_radius_delta(self):
        return self.radius_delta_slider.value()
    
    def get_display_option(self):
        if self.webcam_radio.isChecked():
            return "webcam"
        elif self.detected_circles_radio.isChecked():
            return "detected_circles"
        elif self.detected_colors_radio.isChecked():
            return "detected_colors"
        elif self.grid_radio.isChecked():
            return "grid"
        else:
            return None
        
    def handle_webcam_update(self, webcam, detected_circles, detected_circle_colors, detected_color, board, error):
        display_option = self.get_display_option()
        if error is not None:
            # We can still display the webcam frame even if there is an error.
            self.frame = webcam

            # We still want to display the webcam updates if it is an image
            # which looks close to a webcam raw.
            if display_option == "webcam" \
            or display_option == "detected_circles" \
            or display_option == "detected_colors":
                self.update_webcam_frame(webcam)

            if self.detected_circles is None:
                self.detected_circles = detected_circles
            if self.detected_circle_colors is None:
                self.detected_circle_colors = detected_circle_colors
            if self.detected_color is None:
                self.detected_color = detected_color
            
            # Add the error to the error log
            self.error_log.insertRow(0)
            self.error_log.setItem(0, 0, QTableWidgetItem(error[0]))
            self.error_log.resizeColumnsToContents()
            return

        # We have a valid update from the worker thread so update the UI
        # and save the images for later use in case of an error.
        self.board = board
        self.frame = webcam
        self.detected_circles = detected_circles
        self.detected_circle_colors = detected_circle_colors
        self.detected_color = detected_color

        # Pick the image to display based on the radio button selection
        
        image = webcam
        if display_option == "detected_circles":
            image = detected_circles
        elif display_option == "detected_colors":
            image = detected_circle_colors
        elif display_option == "grid":
            image = detected_color

        # Update the UI elements
        self.update_webcam_frame(image)
        self.update_game_grid(board)

        # Check for a winner and use TTS to announce the winner
        winner = Connect4.check_winner(board)
        if winner is not None:
            if winner == "R":
                text = "Red wins!"
            elif winner == "Y":
                text = "Yellow wins!"
            else:
                text = "It's a draw!"
            
            # Add the winner to the error log
            self.error_log.insertRow(0)
            self.error_log.setItem(0, 0, QTableWidgetItem(text))
            self.error_log.resizeColumnsToContents()

            self.tts_announce_winner(winner)

    # Announce the winner using text-to-speech coqui-tts
    def tts_announce_winner(self, winner):       
        # Create a new thread to run the Connect4 object
        self.tts_thread = QThread()
        self.tts_worker = TTSThread(winner)
        self.tts_worker.moveToThread(self.tts_thread)

        # Connect signals
        self.tts_thread.started.connect(self.tts_worker.run)
        self.tts_worker.finished.connect(self.tts_thread.quit)
        self.tts_worker.finished.connect(self.tts_worker.deleteLater)
        self.tts_thread.finished.connect(self.tts_thread.deleteLater)

        # Start the thread
        self.tts_thread.start()

    def update_webcam_frame(self, image):
        width = self.webcam_frame.width()
        height = self.webcam_frame.height()
        image = cv2.resize(image, (width, height))
        bytes_per_line = 3 * width
        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.webcam_scene.clear()
        self.webcam_scene.addPixmap(QPixmap(q_img))

    def update_game_grid(self, board):
        game_state = board.reshape(6, 7)
        
        for i, row in enumerate(game_state):
            for j, cell in enumerate(row):
                label = QLabel(self)
                label_size = 30
                label.setFixedSize(label_size, label_size)
                
                if cell == "R":
                    label.setStyleSheet("background-color: red; border: 1px solid black;")
                elif cell == "Y":
                    label.setStyleSheet("background-color: yellow; border: 1px solid black;")
                else:
                    label.setStyleSheet("background-color: white; border: 1px solid black;")

                # Clear the previous widget at this position otherwise we will
                # have multiple widgets at the same position and the UI will
                # slow down significantly.
                item = self.game_grid_layout.itemAtPosition(i, j)
                if item is not None:
                    item.widget().deleteLater()

                self.game_grid_layout.addWidget(label, i, j)

class TTSThread(QObject):
    # Signals
    finished = pyqtSignal()
    error = pyqtSignal(tuple)

    winner = None

    # Constructor
    def __init__(self, winner):
        super().__init__()

        self.winner = winner

    # Destructor
    def __del__(self):
        pass

    # Run the worker thread. This is where the text-to-speech happens.
    @pyqtSlot()
    def run(self):


        # Just ring the bell for now
        print('\a')

        self.finished.emit()            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Connect4UI()
    sys.exit(app.exec_())
