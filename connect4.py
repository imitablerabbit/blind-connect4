import cv2
import numpy as np
from sklearn.cluster import KMeans

class Connect4:
    board = np.zeros((6, 7), dtype=int)

    piece_radius = 35
    radius_delta = 2

    img = None
    circles = None
    piece_colors = None

    red_low = np.array([50, 0, 0])
    red_high = np.array([255, 100, 100])
    yellow_low = np.array([50, 50, 0])
    yellow_high = np.array([255, 255, 100])

    def __init__(self, piece_radius=33, radius_delta=3) -> None:
        self.piece_radius = piece_radius
        self.radius_delta = radius_delta
        pass

    def from_image(self, img):
        self.img = img.copy()
        self.circles = self.detect_circles(self.img)
        board = []
        piece_colors = []
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        for _, (x, y, r) in enumerate(self.circles):
            x, y, r = int(x), int(y), int(r)
            pixel = img_rgb[y, x]
            int_pixel = (int(pixel[2]), int(pixel[1]), int(pixel[0]))
            if np.all((self.red_low <= pixel) & (pixel <= self.red_high)):
                piece_colors.append(int_pixel)
                board.append('R')
            elif np.all((self.yellow_low <= pixel) & (pixel <= self.yellow_high)):
                piece_colors.append(int_pixel)
                board.append('Y')
            else:
                piece_colors.append((255, 255, 255))
                board.append('O')

        if len(board) != 42:
            raise ValueError('Incorrect number of discs found!')
        
        self.board = np.array(board).reshape(6, 7)
        self.piece_colors = piece_colors
        return
    
    def circles_overlap(self, circle1, circle2):
        x1, y1, r1 = circle1
        x2, y2, r2 = circle2
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return distance < (r1 + r2)

    def remove_overlapping_circles(self, circles):
        non_overlapping_circles = []
        for circle in circles:
            overlap = False
            for other_circle in non_overlapping_circles:
                if self.circles_overlap(circle, other_circle):
                    overlap = True
                    if circle[2] < other_circle[2]:  # If current circle is smaller, replace the other_circle
                        non_overlapping_circles.remove(other_circle)
                        non_overlapping_circles.append(tuple(circle))
                    break
            if not overlap:
                non_overlapping_circles.append(tuple(circle))
        return non_overlapping_circles
    
    def detect_circles(self, img):
        # Convert the image to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Set minimum and maximum radius of the circles to detect
        min_radius = self.piece_radius - self.radius_delta
        max_radius = self.piece_radius + self.radius_delta
        average_radius = (min_radius + max_radius) / 2
        average_radius = int(average_radius)

        # Use Hough Transform to detect circles
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=average_radius*2, param1=200, param2=20,
                                minRadius=min_radius, maxRadius=max_radius)
        if circles is None:
            raise ValueError('No circles found!')
        if len(circles[0]) != 42:
            raise ValueError('Incorrect number of circles found!')

        # Convert circles to list of tuples and remove overlapping circles
        circles_list = [tuple(circle) for circle in circles[0]]
        non_overlapping_circles = self.remove_overlapping_circles(circles_list)
        circles = np.array([non_overlapping_circles])

        # Cluster the y-coordinates to determine distinct rows
        kmeans = KMeans(n_clusters=6, n_init=10)  # Assuming 6 rows in Connect 4
        y_coords = circles[0][:, 1].reshape(-1, 1)
        kmeans.fit(y_coords)

        # Get and sort the cluster centers
        sorted_centers = sorted([(center[0], idx) for idx, center in enumerate(kmeans.cluster_centers_)])

        # Create a mapping from original cluster label to sorted order
        label_map = {original_idx: sorted_idx for sorted_idx, (_, original_idx) in enumerate(sorted_centers)}

        # Use the label_map to get labels in sorted order
        labels = [label_map[label] for label in kmeans.labels_]

        # Sort by the new labels (rows) and then by x-coordinate within each row
        sorted_circles = [circle for _, circle in sorted(zip(labels, circles[0]), key=lambda c: (c[0], c[1][0]))]
        return sorted_circles

    def get_board(self):
        return self.board
    
    def set_radius(self, radius):
        self.piece_radius = radius
        
    def set_radius_delta(self, radius_delta):
        self.radius_delta = radius_delta

    def draw_circles(self):
        circles_img = self.img.copy()
        for idx, (x, y, r) in enumerate(self.circles):
            x, y, r = int(x), int(y), int(r)
            cv2.circle(circles_img, (x, y), r, (0, 255, 0), 2)  # draw the circle in green
            text = str(idx + 1)
            cv2.putText(circles_img, text, (x - 10, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        return circles_img
    
    def draw_circle_colors(self):
        circles_img = self.img.copy()
        for idx, (x, y, r) in enumerate(self.circles):
            x, y, r = int(x), int(y), int(r)
            cv2.circle(circles_img, (x, y), r, self.piece_colors[idx], -1)
        return circles_img

    def draw_board_state(self):
        board_img = np.ones((300, 350, 3), dtype=np.uint8) * 255  # Assuming 50x50 pixels per cell
        for idx, color in enumerate(self.piece_colors):
            row = idx // 7
            col = idx % 7
            if np.all(color == 0):
                continue
            cv2.rectangle(board_img, (col*50, row*50), ((col+1)*50, (row+1)*50), color, -1)
        return board_img
    
    @staticmethod
    def check_winner(board):
        patterns = ['RRRR', 'YYYY']
        # Check rows
        for row in board:
            for pattern in patterns:
                if pattern in ''.join(row):
                    return pattern[0]
        # Check columns
        for col in board.T:
            for pattern in patterns:
                if pattern in ''.join(col):
                    return pattern[0]
        # Check diagonals
        diagonals = [board.diagonal(i) for i in range(-3, 4)]
        antidiagonals = [np.fliplr(board).diagonal(i) for i in range(-3, 4)]
        for diagonal in diagonals + antidiagonals:
            for pattern in patterns:
                if pattern in ''.join(diagonal):
                    return pattern[0]
        return None