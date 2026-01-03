import cv2
import numpy as np

# Constants for consistent visuals
WIDTH = 800
HEIGHT = 600
FPS = 30
BG_COLOR = (255, 255, 255) # White
STICKMAN_COLOR = (0, 0, 0) # Black

def create_canvas(width=WIDTH, height=HEIGHT, color=BG_COLOR):
    """Creates a blank canvas."""
    # OpenCV uses BGR
    img = np.zeros((height, width, 3), np.uint8)
    img[:] = color
    return img

def inverted_y(y, height=HEIGHT):
    """
    Optional helper to flip Y if the LLM struggles with top-left origin.
    However, the system prompt explicitly tells the LLM to handle it, 
    so this might just be for specific calculations.
    """
    return height - y
