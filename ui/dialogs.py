"""
Dialogs - Các dialog chung
"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


def show_image_viewer(image_array, title="Image Viewer"):
    """
    Hiển thị cửa sổ xem ảnh
    
    Args:
        image_array: numpy array của ảnh
        title: tiêu đề cửa sổ
    """
    root = tk.Toplevel()
    root.geometry('600x600')
    root.title(title)
    
    def resize_image(event):
        new_width = event.width
        new_height = event.height
        image = copy_of_image.resize((new_width, new_height))
        photo = ImageTk.PhotoImage(image)
        label.config(image=photo)
        label.image = photo  # avoid garbage collection
    
    from PIL import Image
    image = Image.fromarray(image_array)
    copy_of_image = image.copy()
    photo = ImageTk.PhotoImage(image)
    label = ttk.Label(root, image=photo)
    label.bind('<Configure>', resize_image)
    label.pack(fill=tk.BOTH, expand='YES')
    
    root.mainloop()

