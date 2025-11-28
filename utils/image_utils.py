"""
Image utilities - Các hàm tiện ích xử lý ảnh
"""
import numpy as np
from PIL import Image


def convert_to_array(image):
    """
    Chuyển đổi PIL Image sang numpy array
    
    Args:
        image: PIL Image hoặc numpy array
    
    Returns:
        numpy array
    """
    if isinstance(image, Image.Image):
        return np.array(image)
    return image


def get_image_dimensions(image_array):
    """
    Lấy kích thước của ảnh
    
    Args:
        image_array: numpy array của ảnh
    
    Returns:
        tuple: kích thước ảnh
    """
    return np.shape(image_array)


def get_image_band(image_array, band_index):
    """
    Lấy một band cụ thể từ ảnh đa kênh
    
    Args:
        image_array: numpy array của ảnh
        band_index: chỉ số band (bắt đầu từ 0)
    
    Returns:
        numpy array: band đã chọn
    """
    if len(image_array.shape) > 2:
        return image_array[:, :, band_index]
    return image_array


def is_rgb_image(image_array):
    """
    Kiểm tra xem ảnh có phải RGB không
    
    Args:
        image_array: numpy array của ảnh
    
    Returns:
        bool: True nếu là RGB (3 channels)
    """
    return len(image_array.shape) == 3 and image_array.shape[2] == 3

