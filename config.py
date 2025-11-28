"""
Cấu hình chung cho ứng dụng xử lý ảnh
"""
import os

# Đường dẫn thư mục
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# Tạo thư mục nếu chưa tồn tại
os.makedirs(RESOURCES_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Cấu hình giao diện
WINDOW_TITLE = "VNU-UET - Group 16 - Image Processing Programme"
WINDOW_SIZE = "1920x1080"
WINDOW_BG = "white"

# Menu colors
MENU_COLORS = {
    'fg': 'blue',
    'bg': 'thistle4',
    'activeforeground': 'red2',
    'activeborderwidth': 4,
    'font': ('Franklin Gothic Demi Cond', 11)
}

# File paths
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
TITLE_IMAGE_PATH = os.path.join(BASE_DIR, "Title.jpg")

# Image processing window settings
PROCESSING_WINDOW_SIZE = "1800x900"
PROCESSING_WINDOW_TITLE = "VNU - UET - GROUP 16 - NGUYEN KHAC KIEN, BUI DUC ANH, TRAN HOANG HUAN"

