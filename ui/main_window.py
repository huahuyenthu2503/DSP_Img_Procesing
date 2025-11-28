"""
Main Window - Cửa sổ chính của ứng dụng
"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import subprocess
import os
import sys
import config


class MainWindow:
    """Cửa sổ chính của ứng dụng"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry(config.WINDOW_SIZE)
        self.root.configure(bg=config.WINDOW_BG)
        self.root.title(config.WINDOW_TITLE)
        
        # Đặt icon
        try:
            if os.path.exists(config.LOGO_PATH):
                img = ImageTk.PhotoImage(file=config.LOGO_PATH)
                self.root.tk.call('wm', 'iconphoto', self.root._w, img)
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        # Biến toàn cục để lưu ảnh
        self.original_image = None
        self.original_image_size = None
        self.dimension_number = None
        
        self.setup_ui()
        self.setup_menu()
    
    def setup_ui(self):
        """Thiết lập giao diện chính"""
        # Hàm resize ảnh
        def resize_image(event):
            new_width = event.width
            new_height = event.height
            image = copy_of_image.resize((new_width, new_height))
            photo = ImageTk.PhotoImage(image)
            label.config(image=photo)
            label.image = photo  # avoid garbage collection
        
        # Mở ảnh title
        try:
            if os.path.exists(config.TITLE_IMAGE_PATH):
                image = Image.open(config.TITLE_IMAGE_PATH)
                copy_of_image = image.copy()
                photo = ImageTk.PhotoImage(image)
                label = ttk.Label(self.root, image=photo)
                label.bind('<Configure>', resize_image)
                label.pack(fill=tk.BOTH, expand='YES')
        except Exception as e:
            print(f"Could not load title image: {e}")
            # Tạo label mặc định nếu không có ảnh
            label = tk.Label(self.root, text="Image Processing Application", 
                           font=("Arial", 24), bg=config.WINDOW_BG)
            label.pack(fill=tk.BOTH, expand='YES')
    
    def setup_menu(self):
        """Thiết lập menu"""
        menubar = tk.Menu(self.root)
        
        # Menu File
        filemenu = tk.Menu(menubar, tearoff=0, **config.MENU_COLORS)
        filemenu.add_command(label="New", command=self.open_file)
        filemenu.add_command(label="Open", command=self.open_file)
        filemenu.add_command(label="Save", command=self.open_file)
        filemenu.add_command(label="Save as...", command=self.open_file)
        filemenu.add_command(label="Close", command=self.open_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        
        # Menu Image Editing
        image_editing_menu = tk.Menu(menubar, tearoff=0)
        image_editing_menu.add_command(label="Open Image Editor", command=self.open_image_editor)
        menubar.add_cascade(label="Image Editing", menu=image_editing_menu)
        
        # Menu Segmentation
        segmenu = tk.Menu(menubar, tearoff=0, **config.MENU_COLORS)
        
        # Edge Detection submenu
        edge_menu = tk.Menu(menubar, tearoff=0, **config.MENU_COLORS)
        segmenu.add_cascade(label="Edge Detection", menu=edge_menu)
        edge_menu.add_command(label="Robertz", command=self.robertz)
        edge_menu.add_command(label="Prewitt", command=self.prewitt)
        edge_menu.add_command(label="Sobel", command=self.sobel)
        edge_menu.add_command(label="Canny", command=self.canny)
        
        # Thresholding submenu
        threshold_menu = tk.Menu(menubar, tearoff=0, **config.MENU_COLORS)
        segmenu.add_cascade(label="Tresholding", menu=threshold_menu)
        threshold_menu.add_command(label="Simple Tresholding", command=self.thresholding)
        threshold_menu.add_command(label="Adaptive Tresholding", command=self.adaptive_thresholding)
        threshold_menu.add_command(label="Otsu's Thresholding", command=self.otsu_thresholding)
        
        menubar.add_cascade(label="Segmentation", menu=segmenu)
        
        self.root.config(menu=menubar)
    
    def open_file(self):
        """Mở file ảnh"""
        from utils.file_operations import open_image_file
        
        filepath, image_array, image_size, dimension_number = open_image_file()
        if filepath:
            self.original_image = image_array
            self.original_image_size = image_size
            self.dimension_number = dimension_number
            # Hiển thị thông tin ảnh
            self.show_image_info(image_size)
    
    def show_image_info(self, image_size):
        """Hiển thị thông tin ảnh"""
        a1 = str(image_size)
        # Tạo label hiển thị dimensions
        info_label = tk.Label(self.root, text=f'Dimensions: {a1}', 
                            bg=config.WINDOW_BG, font=("Arial", 10))
        info_label.place(x=0, y=0)
    
    def open_image_editor(self):
        """Mở trình chỉnh sửa ảnh"""
        image_editing_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "image_editing", 
            "Image_Editing.py"
        )
        if os.path.exists(image_editing_path):
            subprocess.run(["python", image_editing_path])
        else:
            print(f"Image editing file not found: {image_editing_path}")
    
    def robertz(self):
        """Gọi hàm Robertz từ App.py gốc"""
        self._call_original_function("Robertz")
    
    def prewitt(self):
        """Gọi hàm Prewitt từ App.py gốc"""
        self._call_original_function("Prewitt")
    
    def sobel(self):
        """Gọi hàm Sobel từ App.py gốc"""
        self._call_original_function("Sobel")
    
    def canny(self):
        """Gọi hàm Canny từ App.py gốc"""
        self._call_original_function("Canny")
    
    def thresholding(self):
        """Gọi hàm Tresholding từ App.py gốc"""
        self._call_original_function("Tresholding")
    
    def adaptive_thresholding(self):
        """Gọi hàm AT từ App.py gốc"""
        self._call_original_function("AT")
    
    def otsu_thresholding(self):
        """Gọi hàm OT từ App.py gốc"""
        self._call_original_function("OT")
    
    def _call_original_function(self, func_name):
        """Gọi hàm từ App.py gốc (tạm thời để đảm bảo tương thích)"""
        # Import App.py từ thư mục gốc
        # Đường dẫn tương đối từ thư mục hiện tại
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        original_app_path = os.path.join(
            base_dir,
            "Source Code-20251126T054017Z-1-001",
            "Source Code",
            "App.py"
        )
        
        if os.path.exists(original_app_path):
            # Thêm path vào sys.path
            app_dir = os.path.dirname(original_app_path)
            if app_dir not in sys.path:
                sys.path.insert(0, app_dir)
            try:
                # Import App module
                import importlib.util
                spec = importlib.util.spec_from_file_location("App", original_app_path)
                App = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(App)
                
                func = getattr(App, func_name, None)
                if func:
                    # Set global variables
                    App.Original_Image = self.original_image
                    App.Original_image_Size = self.original_image_size
                    App.Dimension_Number = self.dimension_number
                    App.root1 = self.root
                    func()
                else:
                    print(f"Function {func_name} not found in App.py")
            except Exception as e:
                print(f"Error calling {func_name}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Original App.py not found at: {original_app_path}")
            print("Please ensure the original App.py is accessible")
            print(f"Current base directory: {base_dir}")
    
    def mainloop(self):
        """Chạy ứng dụng"""
        self.root.mainloop()

