"""
Processing Window - Cửa sổ xử lý ảnh chung
"""
import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from matplotlib.widgets import Slider
import config


class ProcessingWindow:
    """Cửa sổ xử lý ảnh với matplotlib"""
    
    def __init__(self, original_image, original_image_size, dimension_number):
        self.original_image = original_image
        self.original_image_size = original_image_size
        self.dimension_number = dimension_number
        
        self.root = tk.Toplevel()
        self.root.geometry(config.PROCESSING_WINDOW_SIZE)
        self.root.configure(background='white')
        self.root.title(config.PROCESSING_WINDOW_TITLE)
        
        self.fig = None
        self.canvas = None
        self.ax1 = None
        self.ax2 = None
        
    def create_figure(self, figsize=(13, 7)):
        """Tạo figure matplotlib"""
        self.fig = plt.Figure(figsize=figsize)
        self.canvas = FigureCanvasTkAgg(self.fig, self.root)
        self.canvas.get_tk_widget().place(x=200, y=0)
        
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)
        
        # Cấu hình axes
        self.ax2.set_xlabel("Value", labelpad=15, fontsize=12, color="#333533")
        self.ax2.set_ylabel("Frequency", labelpad=15, fontsize=12, color="#333533")
        self.ax2.set_facecolor("#2E2E2E")
        self.ax1.set_title("Original Image", fontsize=12, color="#333533")
        self.ax2.set_title("Histogram", fontsize=12, color="#333533")
        
        # Toolbar
        toolbar_frame = tk.Frame(master=self.root)
        toolbar_frame.place(x=1000, y=650)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        
        def on_key_press(event):
            print("you pressed {}".format(event.key))
            key_press_handler(event, self.canvas, toolbar)
        
        self.canvas.mpl_connect("key_press_event", on_key_press)
        self.fig.subplots_adjust(bottom=0.25)
        
    def get_image_band(self, band_index):
        """Lấy một band từ ảnh"""
        if len(self.original_image_size) > 2:
            return self.original_image[:, :, band_index - 1]
        return self.original_image
    
    def plot_histogram(self, image, label="Histogram", color="gold"):
        """Vẽ histogram"""
        hist = cv2.calcHist([image], [0], None, [256], [0, 256])
        self.ax2.plot(range(256), hist.ravel(), color=color, label=label)
        self.ax2.legend(loc='best')
        self.fig.canvas.draw_idle()
    
    def save_image(self, image, default_name="filtered_image"):
        """Lưu ảnh"""
        f = filedialog.asksaveasfile(
            filetypes=(("jpeg files", "*.jpg"), ("png files", "*.png"), ("all files", "*.*"))
        )
        if f is None:
            return
        filename = f.name
        cv2.imwrite(str(filename) + '.jpg', image)
        f.close()
    
    def create_band_selector(self, callback):
        """Tạo combobox chọn band"""
        if len(self.original_image_size) > 2:
            dimension_number_int = list(range(1, self.original_image.shape[2] + 1))
            ttk.Label(self.root, text="Choose a band:").pack(anchor='w')
            number1 = tk.StringVar()
            number_chosen = ttk.Combobox(self.root, width=12, textvariable=number1)
            number_chosen['values'] = dimension_number_int
            number_chosen.pack(anchor='w')
            number_chosen.current(0)
            return number_chosen
        return None
    
    def mainloop(self):
        """Chạy mainloop"""
        self.root.mainloop()

