"""
File operations - Mở và lưu file ảnh
"""
from tkinter import filedialog
from PIL import Image
import numpy as np


def open_image_file(initialdir="/", title="Select file"):
    """
    Mở file ảnh và trả về đường dẫn, ảnh dạng array, và kích thước
    
    Returns:
        tuple: (filepath, image_array, image_size, dimension_number)
    """
    filepath = filedialog.askopenfilename(
        initialdir=initialdir,
        title=title,
        filetypes=(
            ("jpeg files", "*.jpg"),
            ("png files", "*.png"),
            ("tif files", "*.TIF"),
            ("all files", "*.*")
        )
    )
    
    if not filepath:
        return None, None, None, None
    
    image = Image.open(filepath)
    image_array = np.array(image)
    image_size = np.shape(image_array)
    
    # Tạo danh sách dimension number
    if len(image_size) > 2:
        dimension_number = [("Band ", i + 1) for i in range(image_array.shape[2])]
    else:
        dimension_number = [("Band", 1)]
    
    return filepath, image_array, image_size, dimension_number


def save_image_file(image_array, default_filename="output.png"):
    """
    Lưu ảnh dạng array ra file
    
    Args:
        image_array: numpy array của ảnh
        default_filename: tên file mặc định
    
    Returns:
        str: đường dẫn file đã lưu, None nếu hủy
    """
    filepath = filedialog.asksaveasfilename(
        defaultextension=".png",
        initialfile=default_filename,
        filetypes=(
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg"),
            ("TIFF files", "*.tif"),
            ("All files", "*.*")
        )
    )
    
    if not filepath:
        return None
    
    image = Image.fromarray(image_array)
    image.save(filepath)
    return filepath

