"""
Main entry point cho ứng dụng xử lý ảnh
"""
import tkinter as tk
from image_editing.Image_Editing import ImageEditorApp

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()

