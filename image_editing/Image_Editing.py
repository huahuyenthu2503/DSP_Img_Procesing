import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import cv2
import numpy as np
import os
from datetime import datetime
import copy


class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Editing App")
        self.root.geometry("1500x700")  # Tăng chiều ngang để hai khung ảnh bằng nhau
        self.root.minsize(1200, 550)  # Kích thước tối thiểu
        self.root.resizable(True, True)  # Cho phép thu nhỏ/phóng to
        
        # Màu sắc hài hòa - bảng màu hiện đại
        self.colors = {
            'bg_main': '#2C3E50',      # Xanh đậm
            'bg_panel': '#34495E',     # Xanh xám
            'bg_button': '#3498DB',    # Xanh dương
            'bg_button_hover': '#2980B9',
            'bg_secondary': '#95A5A6', # Xám nhạt
            'text_light': '#ECF0F1',   # Trắng nhạt
            'text_dark': '#2C3E50',    # Xanh đậm
            'accent': '#E74C3C',       # Đỏ nhạt
            'success': '#27AE60',      # Xanh lá
            'warning': '#F39C12'       # Cam
        }
        
        self.root.configure(bg=self.colors['bg_main'])

        self.image = None
        self.edited_image = None
        self.undo_stack = []
        self.webcam_capture = None
        self.webcam_active = False
        self.webcam_cap = None
        self.captured_images_list = []
        self.original_canvas_state = None  # Lưu trạng thái canvas gốc
        self.current_filter = "Không"
        self.view_zoom = 1.0
        self.filter_values_defaults = {
            "Viền": 1.0,
            "Làm Mờ": 2.0,
            "Đen Trắng": 1.0,
            "Chi Tiết": 1.0,
            "Tăng Cạnh": 1.0,
            "Làm Mịn": 1.0,
            "Làm Nổi": 1.0,
        }
        self.filter_values = self.filter_values_defaults.copy()
        self.adjustments = {}
        self.suspend_slider_commands = False
        self.current_operation = None
        
        # Tạo folder lưu ảnh
        self.webcam_folder = "captured_images"
        self.saved_images_folder = "saved_images"
        if not os.path.exists(self.webcam_folder):
            os.makedirs(self.webcam_folder)
        if not os.path.exists(self.saved_images_folder):
            os.makedirs(self.saved_images_folder)
        
        # Panel bên trái - Công cụ với scrollbar
        tools_container = tk.Frame(root, bg=self.colors['bg_main'])
        tools_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        tools_container.config(width=350)
        
        # Tạo Canvas và Scrollbar cho phần công cụ
        self.canvas_tools = tk.Canvas(tools_container, bg=self.colors['bg_panel'], highlightthickness=0)
        self.scrollbar_tools = tk.Scrollbar(tools_container, orient="vertical", command=self.canvas_tools.yview)
        self.tools_panel = tk.Frame(self.canvas_tools, bg=self.colors['bg_panel'], relief=tk.RAISED, bd=2)
        
        # Cấu hình scrollbar
        self.scrollbar_tools.pack(side="right", fill="y")
        self.canvas_tools.pack(side="left", fill="both", expand=True)
        self.canvas_tools.configure(yscrollcommand=self.scrollbar_tools.set)
        
        # Tạo window trong canvas
        self.canvas_window = self.canvas_tools.create_window((0, 0), window=self.tools_panel, anchor="nw")
        
        # Cập nhật scroll region khi panel thay đổi kích thước
        def configure_scroll_region(event=None):
            self.canvas_tools.configure(scrollregion=self.canvas_tools.bbox("all"))
            # Đảm bảo canvas window có chiều rộng bằng canvas
            canvas_width = self.canvas_tools.winfo_width()
            if canvas_width > 1:
                self.canvas_tools.itemconfig(self.canvas_window, width=canvas_width)
        
        def on_canvas_configure(event):
            canvas_width = event.width
            self.canvas_tools.itemconfig(self.canvas_window, width=canvas_width)
        
        self.tools_panel.bind("<Configure>", configure_scroll_region)
        self.canvas_tools.bind("<Configure>", on_canvas_configure)
        
        # Cho phép cuộn bằng chuột (hỗ trợ cả Windows và Linux)
        def on_mousewheel(event):
            # Windows và MacOS
            if event.delta:
                self.canvas_tools.yview_scroll(int(-1*(event.delta/120)), "units")
            # Linux
            elif event.num == 4:
                self.canvas_tools.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas_tools.yview_scroll(1, "units")
        
        # Bind cho Windows/MacOS
        self.canvas_tools.bind_all("<MouseWheel>", on_mousewheel)
        # Bind cho Linux
        self.canvas_tools.bind_all("<Button-4>", on_mousewheel)
        self.canvas_tools.bind_all("<Button-5>", on_mousewheel)
        
        # Bind khi focus vào canvas
        def on_enter(event):
            self.canvas_tools.focus_set()
        
        self.canvas_tools.bind("<Enter>", on_enter)
        
        # Panel bên phải - Hiển thị ảnh (sử dụng pack với fill để responsive)
        self.image_panel = tk.Frame(root, bg=self.colors['bg_main'])
        self.image_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bind resize event để cập nhật ảnh khi thay đổi kích thước
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Tiêu đề
        title = tk.Label(self.tools_panel, text="CÔNG CỤ CHỈNH SỬA", 
                        font=("Arial", 16, "bold"), 
                        bg=self.colors['bg_panel'], 
                        fg=self.colors['text_light'])
        title.pack(pady=15)
        
        # Phần mở ảnh và Webcam
        file_frame = tk.LabelFrame(self.tools_panel, text="Mở Ảnh", 
                                   font=("Arial", 11, "bold"),
                                   bg=self.colors['bg_panel'], 
                                   fg=self.colors['text_light'],
                                   padx=10, pady=10)
        file_frame.pack(fill=tk.X, padx=15, pady=10)
        
        btn_style = {'font': ("Arial", 10), 'relief': tk.RAISED, 'bd': 2, 
                    'cursor': 'hand2', 'padx': 10, 'pady': 5}
        
        tk.Button(file_frame, text="Mở File", 
                 bg=self.colors['bg_button'], fg='white',
                 command=self.open_image, **btn_style).pack(fill=tk.X, pady=5)
        
        tk.Button(file_frame, text="Mở Webcam", 
                 bg=self.colors['success'], fg='white',
                 command=self.open_webcam, **btn_style).pack(fill=tk.X, pady=5)
        
        # Nút AI
        tk.Button(file_frame, text=" Tự Động Sửa Ảnh", 
                 bg=self.colors['accent'], fg='white',
                 command=self.ai_auto_edit, **btn_style).pack(fill=tk.X, pady=5)
        
        # Phần chỉnh sửa cơ bản
        basic_frame = tk.LabelFrame(self.tools_panel, text="Chỉnh Sửa Cơ Bản", 
                                    font=("Arial", 11, "bold"),
                                    bg=self.colors['bg_panel'], 
                                    fg=self.colors['text_light'],
                                    padx=10, pady=10)
        basic_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Sliders cho các điều chỉnh
        self.brightness_slider = self.add_slider(basic_frame, "Độ Sáng", 0, 2, 1, self.adjust_brightness)
        self.color_slider = self.add_slider(basic_frame, "Màu Sắc", 0, 2, 1, self.adjust_color)
        self.contrast_slider = self.add_slider(basic_frame, "Độ Tương Phản", 0, 2, 1, self.adjust_contrast)
        self.sharpen_slider = self.add_slider(basic_frame, "Độ Sắc Nét", 0, 2, 1, self.adjust_sharpen)
        self.blur_slider = self.add_slider(basic_frame, "Làm Mờ", 0, 5, 0, self.apply_blur)
        
        # Phần xoay ảnh với slider
        rotate_frame = tk.LabelFrame(self.tools_panel, text="Xoay Ảnh", 
                                     font=("Arial", 11, "bold"),
                                     bg=self.colors['bg_panel'], 
                                     fg=self.colors['text_light'],
                                     padx=10, pady=10)
        rotate_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.rotation_slider = self.add_slider(rotate_frame, "Góc Xoay (°)", -180, 180, 0, self.rotate_image_slider)
        
        # Nút lật ảnh
        flip_frame = tk.Frame(rotate_frame, bg=self.colors['bg_panel'])
        flip_frame.pack(fill=tk.X, pady=5)
        tk.Button(flip_frame, text="Lật Ngang", bg=self.colors['bg_secondary'], fg='white',
                 command=self.flip_horizontal, **btn_style).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        tk.Button(flip_frame, text="Lật Dọc", bg=self.colors['bg_secondary'], fg='white',
                 command=self.flip_vertical, **btn_style).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        transform_frame = tk.LabelFrame(self.tools_panel, text="Cắt & Kích Thước", 
                                        font=("Arial", 11, "bold"),
                                        bg=self.colors['bg_panel'], 
                                        fg=self.colors['text_light'],
                                        padx=10, pady=10)
        transform_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Button(transform_frame, text="Cắt Ảnh", bg=self.colors['bg_secondary'], fg='white',
                 command=self.crop_image, **btn_style).pack(fill=tk.X, pady=3)
        tk.Button(transform_frame, text="Bỏ Cắt", bg=self.colors['bg_secondary'], fg='white',
                 command=self.clear_crop_adjustment, **btn_style).pack(fill=tk.X, pady=3)
        
        zoom_label = tk.Label(transform_frame, text="Thu phóng (%)",
                              bg=self.colors['bg_panel'],
                              fg=self.colors['text_light'],
                              font=("Arial", 10, "bold"))
        zoom_label.pack(pady=(8, 2))
        self.zoom_slider = tk.Scale(transform_frame, from_=50, to=200, resolution=1,
                                    orient="horizontal",
                                    bg=self.colors['bg_panel'],
                                    fg=self.colors['text_light'],
                                    highlightthickness=0,
                                    troughcolor=self.colors['bg_main'],
                                    activebackground=self.colors['bg_button'],
                                    command=self.adjust_zoom,
                                    length=220)
        self.zoom_slider.set(100)
        self.zoom_slider.pack(fill=tk.X)
        
        # Phần bộ lọc
        filter_frame = tk.LabelFrame(self.tools_panel, text="Bộ Lọc", 
                                     font=("Arial", 11, "bold"),
                                     bg=self.colors['bg_panel'], 
                                     fg=self.colors['text_light'],
                                     padx=10, pady=10)
        filter_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.filter_combo = ttk.Combobox(filter_frame, 
                                        values=["Không", "Đen Trắng", "Làm Mờ", "Viền", "Chi Tiết", "Tăng Cạnh", "Làm Mịn", "Làm Nổi"],
                                        state="readonly", width=25)
        self.filter_combo.set("Không")
        self.filter_combo.pack(pady=5)
        self.filter_combo.bind("<<ComboboxSelected>>", self.on_filter_change)
        
        # Slider riêng cho từng bộ lọc - Tăng phạm vi để hiệu ứng rõ hơn
        # Slider cho Viền (Contour)
        self.contour_slider, self.contour_slider_frame = self.add_slider_with_frame(
            filter_frame, "Viền (Đậm/Nhẹ)", 0.1, 5.0, 1.0, self.on_contour_change)
        
        # Slider cho Làm Mờ (Blur)
        self.blur_filter_slider, self.blur_filter_slider_frame = self.add_slider_with_frame(
            filter_frame, "Làm Mờ (Đậm/Nhẹ)", 0.5, 15.0, 2.0, self.on_blur_filter_change)
        
        # Slider cho Đen Trắng
        self.bw_slider, self.bw_slider_frame = self.add_slider_with_frame(
            filter_frame, "Đen Trắng (Đậm/Nhẹ)", 0.1, 1.0, 1.0, self.on_bw_change)
        
        # Slider cho Chi Tiết
        self.detail_slider, self.detail_slider_frame = self.add_slider_with_frame(
            filter_frame, "Chi Tiết (Đậm/Nhẹ)", 0.1, 5.0, 1.0, self.on_detail_change)
        
        # Slider cho Tăng Cạnh
        self.edge_slider, self.edge_slider_frame = self.add_slider_with_frame(
            filter_frame, "Tăng Cạnh (Đậm/Nhẹ)", 0.1, 5.0, 1.0, self.on_edge_change)
        
        # Slider cho Làm Mịn
        self.smooth_slider, self.smooth_slider_frame = self.add_slider_with_frame(
            filter_frame, "Làm Mịn (Đậm/Nhẹ)", 0.1, 5.0, 1.0, self.on_smooth_change)
        
        # Slider cho Làm Nổi
        self.emboss_slider, self.emboss_slider_frame = self.add_slider_with_frame(
            filter_frame, "Làm Nổi (Đậm/Nhẹ)", 0.1, 5.0, 1.0, self.on_emboss_change)
        
        # Ẩn các slider ban đầu, chỉ hiện khi chọn bộ lọc tương ứng
        self.hide_filter_sliders()
        
        # Phần thao tác
        action_frame = tk.LabelFrame(self.tools_panel, text="Thao Tác", 
                                     font=("Arial", 11, "bold"),
                                     bg=self.colors['bg_panel'], 
                                     fg=self.colors['text_light'],
                                     padx=10, pady=10)
        action_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Button(action_frame, text="Lưu Ảnh", 
                 bg=self.colors['success'], fg='white',
                 command=self.save_image, **btn_style).pack(fill=tk.X, pady=3)
        
        tk.Button(action_frame, text="Lưu Nhanh", 
                 bg=self.colors['bg_button'], fg='white',
                 command=self.quick_save_image, **btn_style).pack(fill=tk.X, pady=3)
        tk.Button(action_frame, text="Hoàn Tác", 
                 bg=self.colors['warning'], fg='white',
                 command=self.undo_last_change, **btn_style).pack(fill=tk.X, pady=3)
        tk.Button(action_frame, text="Đặt Lại", 
                 bg=self.colors['bg_secondary'], fg='white',
                 command=self.reset_image, **btn_style).pack(fill=tk.X, pady=3)
        tk.Button(action_frame, text="Thoát", 
                 bg=self.colors['accent'], fg='white',
                 command=root.quit, **btn_style).pack(fill=tk.X, pady=3)
        
        # Canvas cho ảnh gốc và đã chỉnh sửa
        self.img_display_frame = tk.Frame(self.image_panel, bg=self.colors['bg_main'])
        self.img_display_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Ảnh gốc
        self.original_frame = tk.Frame(self.img_display_frame, bg=self.colors['bg_panel'], relief=tk.RAISED, bd=2)
        self.original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(self.original_frame, text="Ảnh Gốc", 
                font=("Arial", 14, "bold"), 
                bg=self.colors['bg_panel'], 
                fg=self.colors['text_light']).pack(pady=10)
        
        self.original_canvas = tk.Canvas(self.original_frame, 
                                        bg='#1A1A1A', highlightthickness=0)
        self.original_canvas.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        # Ảnh đã chỉnh sửa
        self.edited_frame = tk.Frame(self.img_display_frame, bg=self.colors['bg_panel'], relief=tk.RAISED, bd=2)
        self.edited_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(self.edited_frame, text="Ảnh Đã Chỉnh Sửa", 
                font=("Arial", 14, "bold"), 
                bg=self.colors['bg_panel'], 
                fg=self.colors['text_light']).pack(pady=10)
        
        # Container cho canvas và gallery
        self.edited_container = tk.Frame(self.edited_frame, bg=self.colors['bg_panel'])
        self.edited_container.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        self.edited_canvas = tk.Canvas(self.edited_container, 
                                      bg='#1A1A1A', highlightthickness=0)
        self.edited_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Gallery cho ảnh đã chụp (sẽ hiện khi ở chế độ webcam)
        gallery_frame = tk.Frame(self.edited_frame, bg=self.colors['bg_panel'], height=120)
        gallery_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(gallery_frame, text="Ảnh Đã Chụp", 
                font=("Arial", 10, "bold"), 
                bg=self.colors['bg_panel'], 
                fg=self.colors['text_light']).pack()
        
        # Canvas và scrollbar cho gallery
        gallery_canvas_frame = tk.Frame(gallery_frame, bg=self.colors['bg_panel'])
        gallery_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.gallery_canvas = tk.Canvas(gallery_canvas_frame, bg=self.colors['bg_main'], 
                                       height=100, highlightthickness=0)
        gallery_scrollbar = tk.Scrollbar(gallery_canvas_frame, orient="horizontal", 
                                        command=self.gallery_canvas.xview)
        self.gallery_canvas.configure(xscrollcommand=gallery_scrollbar.set)
        
        self.gallery_inner = tk.Frame(self.gallery_canvas, bg=self.colors['bg_main'])
        self.gallery_canvas.create_window((0, 0), window=self.gallery_inner, anchor="nw")
        
        gallery_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.gallery_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Ẩn gallery ban đầu
        gallery_frame.pack_forget()
        self.gallery_frame = gallery_frame
        
        # Tạo khung webcam lớn (sẽ hiện khi mở webcam)
        self.webcam_frame = tk.Frame(self.img_display_frame, bg=self.colors['bg_panel'], relief=tk.RAISED, bd=2)
        tk.Label(self.webcam_frame, text="📷 Webcam", 
                font=("Arial", 16, "bold"), 
                bg=self.colors['bg_panel'], 
                fg=self.colors['text_light']).pack(pady=10)
        
        # Container chính chia làm 2 bên
        self.webcam_main_container = tk.Frame(self.webcam_frame, bg=self.colors['bg_panel'])
        # Sẽ pack sau khi tạo xong các thành phần
        
        # Bên trái: Canvas webcam
        self.webcam_left_frame = tk.Frame(self.webcam_main_container, bg=self.colors['bg_panel'])
        
        # Bên phải: Gallery, scrollbar, và các nút
        self.webcam_right_frame = tk.Frame(self.webcam_main_container, bg=self.colors['bg_panel'])
        
        # Gallery cho ảnh đã chụp trong webcam frame (hiển thị dọc)
        self.webcam_gallery_frame = tk.Frame(self.webcam_right_frame, bg=self.colors['bg_panel'])
        
        # Canvas và scrollbar cho gallery webcam (scrollbar dọc) - sát nhau, sát bên phải, không có padding
        webcam_gallery_canvas_frame = tk.Frame(self.webcam_gallery_frame, bg=self.colors['bg_panel'])
        webcam_gallery_canvas_frame.pack(fill=tk.BOTH, expand=True, pady=0, padx=(0, 0))
        
        self.webcam_gallery_canvas = tk.Canvas(webcam_gallery_canvas_frame, bg=self.colors['bg_main'], 
                                       highlightthickness=0)
        webcam_gallery_scrollbar = tk.Scrollbar(webcam_gallery_canvas_frame, orient="vertical", 
                                        command=self.webcam_gallery_canvas.yview,
                                        width=15)  # Đảm bảo scrollbar có độ rộng đủ để kéo
        self.webcam_gallery_canvas.configure(yscrollcommand=webcam_gallery_scrollbar.set)
        self.webcam_gallery_scrollbar = webcam_gallery_scrollbar  # Lưu reference
        
        self.webcam_gallery_inner = tk.Frame(self.webcam_gallery_canvas, bg=self.colors['bg_main'])
        # Tạo window với anchor nw nhưng sẽ căn phải nội dung bên trong
        self.webcam_gallery_window = self.webcam_gallery_canvas.create_window((0, 0), window=self.webcam_gallery_inner, anchor="nw")
        
        # Cấu hình để scrollbar hoạt động đúng (scrollbar dọc) và căn phải nội dung
        def configure_webcam_gallery_scroll(event=None):
            # Cập nhật scroll region dựa trên nội dung thực tế
            self.webcam_gallery_canvas.update_idletasks()
            bbox = self.webcam_gallery_canvas.bbox("all")
            if bbox:
                # Mở rộng scroll region để bao gồm tất cả nội dung (theo chiều dọc)
                self.webcam_gallery_canvas.configure(scrollregion=(0, 0, bbox[2], bbox[3]))
            # Căn phải window khi canvas resize
            canvas_width = self.webcam_gallery_canvas.winfo_width()
            if canvas_width > 1:
                inner_width = self.webcam_gallery_inner.winfo_reqwidth()
                if inner_width < canvas_width:
                    # Căn phải bằng cách đặt x position
                    x_pos = canvas_width - inner_width
                    self.webcam_gallery_canvas.coords(self.webcam_gallery_window, x_pos, 0)
        
        self.webcam_gallery_inner.bind("<Configure>", configure_webcam_gallery_scroll)
        # Cũng bind cho canvas để cập nhật khi canvas resize
        self.webcam_gallery_canvas.bind("<Configure>", configure_webcam_gallery_scroll)
        
        # Cho phép scroll bằng mouse wheel khi hover vào canvas (scroll dọc)
        def on_canvas_scroll(event):
            # Chỉ scroll khi hover vào canvas hoặc inner frame
            widget = event.widget
            if widget == self.webcam_gallery_canvas or widget == self.webcam_gallery_inner or str(widget).endswith('webcam_gallery_inner'):
                if event.delta:
                    # Windows/MacOS
                    self.webcam_gallery_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                elif event.num == 4:
                    # Linux
                    self.webcam_gallery_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.webcam_gallery_canvas.yview_scroll(1, "units")
        
        # Bind cho canvas và inner frame
        def bind_scroll_to_widget(widget):
            widget.bind("<MouseWheel>", on_canvas_scroll)
            widget.bind("<Button-4>", on_canvas_scroll)
            widget.bind("<Button-5>", on_canvas_scroll)
        
        bind_scroll_to_widget(self.webcam_gallery_canvas)
        bind_scroll_to_widget(self.webcam_gallery_inner)
        
        # Đảm bảo scrollbar luôn hiển thị và có thể kéo được (scrollbar dọc)
        # Pack scrollbar trước, sau đó pack canvas (scrollbar sát bên phải)
        webcam_gallery_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 0))
        self.webcam_gallery_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 0))
        
        # Ẩn gallery webcam ban đầu
        self.webcam_gallery_frame.pack_forget()
        
        # Canvas webcam lớn - bên trái (giảm padding để mở rộng)
        self.webcam_canvas = tk.Canvas(self.webcam_left_frame, 
                                      bg='#1A1A1A', highlightthickness=0)
        self.webcam_canvas.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Container cho nút điều khiển webcam (nhỏ hơn) - bên phải
        self.webcam_control_container = tk.Frame(self.webcam_right_frame, bg=self.colors['bg_panel'])
        # Sẽ pack sau gallery
        
        # Ẩn webcam frame ban đầu
        self.webcam_frame.pack_forget()

        # Đồng bộ trạng thái chỉnh sửa ban đầu
        self.reset_adjustments()
    
    # ========== CÁC HÀM BỘ LỌC TỐI ƯU SỬ DỤNG OPENCV VÀ NUMPY ==========
    
    def apply_filter_contour_optimized(self, img_array, intensity):
        """Bộ lọc viền tối ưu sử dụng OpenCV"""
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Sử dụng Canny edge detection với threshold động
        low_threshold = max(1, int(50 * (1 / intensity)))
        high_threshold = max(2, int(150 * (1 / intensity)))
        edges = cv2.Canny(gray, low_threshold, high_threshold)
        
        # Chuyển đổi edges thành RGB
        if len(img_array.shape) == 3:
            edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        else:
            edges_rgb = edges
        
        # Blend với ảnh gốc
        blend_ratio = min(1.0, intensity / 3.0)
        result = cv2.addWeighted(img_array, 1 - blend_ratio, edges_rgb, blend_ratio, 0)
        return result
    
    def apply_filter_blur_optimized(self, img_array, intensity):
        """Bộ lọc làm mờ tối ưu sử dụng OpenCV GaussianBlur"""
        kernel_size = int(intensity * 2) * 2 + 1  # Đảm bảo số lẻ
        kernel_size = max(3, min(kernel_size, 31))  # Giới hạn từ 3 đến 31
        return cv2.GaussianBlur(img_array, (kernel_size, kernel_size), 0)
    
    def apply_filter_bw_optimized(self, img_array, intensity):
        """Bộ lọc đen trắng tối ưu"""
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            gray_rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        else:
            gray_rgb = img_array
        
        # Blend với ảnh gốc
        result = cv2.addWeighted(img_array, 1 - intensity, gray_rgb, intensity, 0)
        return result
    
    def apply_filter_detail_optimized(self, img_array, intensity):
        """Bộ lọc chi tiết tối ưu sử dụng Unsharp Masking"""
        # Chuyển sang grayscale để tính toán
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Tạo unsharp mask với sigma động
        sigma = max(0.5, intensity * 1.5)
        kernel_size = int(sigma * 4) * 2 + 1  # Đảm bảo số lẻ
        kernel_size = max(3, min(kernel_size, 21))  # Giới hạn từ 3 đến 21
        blurred = cv2.GaussianBlur(gray, (kernel_size, kernel_size), sigma)
        
        # Unsharp masking
        unsharp_mask = cv2.addWeighted(gray, 1.0 + intensity * 0.5, blurred, -intensity * 0.5, 0)
        unsharp_mask = np.clip(unsharp_mask, 0, 255).astype(np.uint8)
        
        # Áp dụng cho từng kênh màu
        if len(img_array.shape) == 3:
            result = img_array.copy().astype(np.float32)
            gray_float = gray.astype(np.float32) + 1e-5  # Tránh chia cho 0
            unsharp_float = unsharp_mask.astype(np.float32)
            enhancement = unsharp_float / gray_float
            
            for i in range(3):
                channel = img_array[:, :, i].astype(np.float32)
                result[:, :, i] = np.clip(channel * enhancement, 0, 255)
            return result.astype(np.uint8)
        else:
            return unsharp_mask
    
    def apply_filter_edge_enhance_optimized(self, img_array, intensity):
        """Bộ lọc tăng cạnh tối ưu sử dụng Laplacian"""
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Laplacian edge detection
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian = np.absolute(laplacian)
        laplacian = np.uint8(np.clip(laplacian, 0, 255))
        
        # Chuyển sang RGB
        if len(img_array.shape) == 3:
            laplacian_rgb = cv2.cvtColor(laplacian, cv2.COLOR_GRAY2RGB)
        else:
            laplacian_rgb = laplacian
        
        # Blend với ảnh gốc
        blend_ratio = min(1.0, intensity / 3.0)
        result = cv2.addWeighted(img_array, 1.0, laplacian_rgb, blend_ratio, 0)
        return result
    
    def apply_filter_smooth_optimized(self, img_array, intensity):
        """Bộ lọc làm mịn tối ưu sử dụng Bilateral Filter"""
        if len(img_array.shape) == 3:
            d = int(intensity * 5)  # Diameter
            d = max(1, min(d, 15))  # Giới hạn từ 1 đến 15
            return cv2.bilateralFilter(img_array, d, 80, 80)
        else:
            return cv2.GaussianBlur(img_array, (5, 5), intensity)
    
    def apply_filter_emboss_optimized(self, img_array, intensity):
        """Bộ lọc làm nổi tối ưu sử dụng Sobel operator - chỉ dùng Sobel x và Sobel y"""
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Tính toán Sobel gradients theo cả hai hướng với ksize=5
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)  # Sobel x
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)  # Sobel y
        
        # Kết hợp gradients và chuyển về uint8
        sobel_combined = np.sqrt(sobel_x**2 + sobel_y**2)
        sobel_normalized = np.clip(sobel_combined, 0, 255).astype(np.uint8)
        
        # Chuyển sang RGB
        if len(img_array.shape) == 3:
            embossed_rgb = cv2.cvtColor(sobel_normalized, cv2.COLOR_GRAY2RGB)
        else:
            embossed_rgb = sobel_normalized
        
        # Blend với ảnh gốc theo intensity
        blend_ratio = min(1.0, intensity / 3.0)
        result = cv2.addWeighted(img_array, 1 - blend_ratio, embossed_rgb, blend_ratio, 0)
        return result
    
    def apply_filter_to_frame(self, frame_rgb):
        """Áp dụng bộ lọc hiện tại lên frame webcam"""
        intensity_lookup = lambda key, default=1.0: self.filter_values.get(key, default)

        if self.current_filter == "Không":
            return frame_rgb
        elif self.current_filter == "Viền":
            return self.apply_filter_contour_optimized(frame_rgb, intensity_lookup("Viền"))
        elif self.current_filter == "Làm Mờ":
            return self.apply_filter_blur_optimized(frame_rgb, intensity_lookup("Làm Mờ", 2.0))
        elif self.current_filter == "Đen Trắng":
            return self.apply_filter_bw_optimized(frame_rgb, intensity_lookup("Đen Trắng"))
        elif self.current_filter == "Chi Tiết":
            return self.apply_filter_detail_optimized(frame_rgb, intensity_lookup("Chi Tiết"))
        elif self.current_filter == "Tăng Cạnh":
            return self.apply_filter_edge_enhance_optimized(frame_rgb, intensity_lookup("Tăng Cạnh"))
        elif self.current_filter == "Làm Mịn":
            return self.apply_filter_smooth_optimized(frame_rgb, intensity_lookup("Làm Mịn"))
        elif self.current_filter == "Làm Nổi":
            return self.apply_filter_emboss_optimized(frame_rgb, intensity_lookup("Làm Nổi"))
        else:
            return frame_rgb
    
    def add_slider(self, parent, label, from_val, to_val, default, command):
        frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        frame.pack(fill=tk.X, pady=5)
        
        tk.Label(frame, text=label, bg=self.colors['bg_panel'], 
                fg=self.colors['text_light'], 
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        slider = tk.Scale(frame, from_=from_val, to=to_val, 
                         resolution=1 if label == "Góc Xoay (°)" else 0.1,
                         orient="horizontal", 
                         bg=self.colors['bg_panel'],
                         fg=self.colors['text_light'],
                         highlightthickness=0,
                         troughcolor=self.colors['bg_main'],
                         activebackground=self.colors['bg_button'],
                         command=command,
                         length=200)
        slider.set(default)
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        slider.bind("<ButtonRelease-1>", self.commit_current_operation)
        
        return slider

    def add_slider_with_frame(self, parent, label, from_val, to_val, default, command):
        """Thêm slider và trả về cả slider và frame"""
        frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        frame.pack(fill=tk.X, pady=5)
        
        tk.Label(frame, text=label, bg=self.colors['bg_panel'], 
                fg=self.colors['text_light'], 
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        slider = tk.Scale(frame, from_=from_val, to=to_val, 
                         resolution=0.1,
                         orient="horizontal", 
                         bg=self.colors['bg_panel'],
                         fg=self.colors['text_light'],
                         highlightthickness=0,
                         troughcolor=self.colors['bg_main'],
                         activebackground=self.colors['bg_button'],
                         command=command,
                         length=200)
        slider.set(default)
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        slider.bind("<ButtonRelease-1>", self.commit_current_operation)
        
        return slider, frame


    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")])
        if file_path:
            try:
                self.image = Image.open(file_path)
                self.undo_stack = []
                self.reset_adjustments()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở ảnh: {str(e)}")
    
    def open_webcam(self):
        """Mở webcam và hiển thị trong khung lớn duy nhất thay thế cả hai canvas"""
        if self.webcam_active:
            messagebox.showinfo("Thông báo", "Webcam đã được mở!")
            return
        
        
        self.webcam_cap = cv2.VideoCapture(0)
        
        if not self.webcam_cap.isOpened():
            messagebox.showerror("Lỗi", "Không thể mở webcam!")
            return
        
        # Lưu trạng thái canvas hiện tại
        self.original_canvas_state = (self.image, self.edited_image) if self.image else None
        
        # Đánh dấu webcam đang hoạt động
        self.webcam_active = True
        
        # Ẩn hai frame ảnh gốc và chỉnh sửa
        self.original_frame.pack_forget()
        self.edited_frame.pack_forget()
        
        # Hiện khung webcam lớn - chiếm toàn bộ không gian
        self.webcam_frame.pack(fill=tk.BOTH, expand=True)
        
        # Xóa các nút cũ nếu có
        for widget in self.webcam_control_container.winfo_children():
            widget.destroy()
        
        # Sắp xếp layout: bên trái và bên phải (frame trái to ra, frame phải nhỏ lại)
        self.webcam_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 1), pady=10)
        self.webcam_right_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=(1, 0), pady=10)
        # Giới hạn chiều rộng bên phải (giảm xuống để frame trái to ra hơn nữa)
        self.webcam_right_frame.config(width=200)
        self.webcam_right_frame.pack_propagate(False)
        # Pack container chính
        self.webcam_main_container.pack(fill=tk.BOTH, expand=True)
        
        # Hiện gallery webcam - bên phải (hiển thị dọc, sát bên phải, không có padding)
        self.webcam_gallery_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 2), padx=(0, 0), anchor=tk.E)
        self.load_captured_images_webcam()
        
        # Tạo nút điều khiển webcam (nhỏ hơn) - bên phải, dưới gallery, sát bên phải
        capture_btn = tk.Button(self.webcam_control_container, text="  Chụp Ảnh  ", 
                               bg=self.colors['success'], fg='white',
                               font=("Arial", 9),
                               command=self.capture_photo,
                               padx=5, pady=5)
        capture_btn.pack(side=tk.RIGHT, padx=(7, 3))
        
        # Nút đóng (nhỏ hơn) - sát bên phải
        close_btn = tk.Button(self.webcam_control_container, text="  Thoát Webcam   ", 
                             bg=self.colors['accent'], fg='white',
                             font=("Arial", 9),
                             command=self.close_webcam,
                             padx=5, pady=5)
        close_btn.pack(side=tk.RIGHT, padx=(3, 0))
        
        # Pack container nút điều khiển - bên phải, dưới gallery, sát bên phải
        self.webcam_control_container.pack(fill=tk.X, pady=2, padx=(0, 0), anchor=tk.E)
        
        # Bắt đầu cập nhật frame
        self.update_webcam_frame()
    
    def update_webcam_frame(self):
        """Cập nhật frame webcam trên canvas lớn duy nhất - phóng to gấp đôi"""
        if not self.webcam_active or self.webcam_cap is None:
            return
        
        ret, frame = self.webcam_cap.read()
        if ret:
            # Chuyển BGR sang RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Lưu frame hiện tại
            self.webcam_capture = frame_rgb.copy()
            
            # Áp dụng bộ lọc nếu có
            frame_display = self.apply_filter_to_frame(frame_rgb.copy())
            
            # Chuyển sang PIL Image
            frame_pil = Image.fromarray(frame_display)
            
            # Cập nhật canvas webcam
            self.webcam_canvas.update_idletasks()
            canvas_width = self.webcam_canvas.winfo_width()
            canvas_height = self.webcam_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Phóng to gấp đôi - scale để fill toàn bộ canvas
                scaled_frame = self.scale_image_to_canvas_fill(frame_pil, self.webcam_canvas)
                frame_tk = ImageTk.PhotoImage(scaled_frame)
                
                self.webcam_canvas.delete("all")
                # Vẽ ảnh từ góc trên bên trái để fill toàn bộ canvas
                self.webcam_canvas.create_image(0, 0, image=frame_tk, anchor=tk.NW)
                self.webcam_canvas.image = frame_tk  # Giữ reference
            
            # Lên lịch cập nhật tiếp theo
            self.root.after(30, self.update_webcam_frame)
        else:
            messagebox.showerror("Lỗi", "Không thể đọc từ webcam!")
            self.close_webcam()
    
    def capture_photo(self):
        """Chụp ảnh từ webcam và lưu vào folder (lưu cả ảnh gốc và ảnh đã áp dụng bộ lọc)"""
        if self.webcam_capture is not None and self.webcam_active:
            # Tạo tên file với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Lưu ảnh gốc
            filename_original = f"{self.webcam_folder}/capture_original_{timestamp}.jpg"
            image_pil_original = Image.fromarray(self.webcam_capture)
            image_pil_original.save(filename_original)
            
            # Lưu ảnh đã áp dụng bộ lọc (nếu có)
            if self.current_filter != "Không":
                frame_filtered = self.apply_filter_to_frame(self.webcam_capture.copy())
                filename_filtered = f"{self.webcam_folder}/capture_filtered_{timestamp}.jpg"
                image_pil_filtered = Image.fromarray(frame_filtered)
                image_pil_filtered.save(filename_filtered)
                self.captured_images_list.append(filename_filtered)
            else:
                self.captured_images_list.append(filename_original)
            
            # Cập nhật gallery (cả gallery thường và gallery webcam nếu đang mở)
            self.load_captured_images()
            if self.webcam_active:
                self.load_captured_images_webcam()
            
            messagebox.showinfo("Thành công", f"Ảnh đã được chụp và lưu!")
        else:
            messagebox.showwarning("Cảnh báo", "Không có ảnh để chụp!")
    
    def load_captured_images(self):
        """Tải và hiển thị các ảnh đã chụp trong gallery (cho edited_frame)"""
        # Xóa các widget cũ trong gallery
        for widget in self.gallery_inner.winfo_children():
            widget.destroy()
        
        # Khởi tạo danh sách nếu chưa có
        if not hasattr(self, 'captured_images_list'):
            self.captured_images_list = []
        
        # Tải danh sách ảnh từ folder
        if os.path.exists(self.webcam_folder):
            image_files = sorted([f for f in os.listdir(self.webcam_folder) 
                                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))],
                                key=lambda x: os.path.getmtime(os.path.join(self.webcam_folder, x)),
                                reverse=True)
            
            self.captured_images_list = [os.path.join(self.webcam_folder, f) for f in image_files]
        
        # Hiển thị các ảnh trong gallery (tối đa 10 ảnh gần nhất)
        for img_path in self.captured_images_list[:10]:
            try:
                img = Image.open(img_path)
                img.thumbnail((80, 80))
                img_tk = ImageTk.PhotoImage(img)
                
                # Tạo button với ảnh
                btn = tk.Button(self.gallery_inner, image=img_tk, 
                              command=lambda path=img_path: self.load_captured_image(path),
                              bg=self.colors['bg_main'], relief=tk.RAISED, bd=2)
                btn.image = img_tk  # Giữ reference
                btn.pack(side=tk.LEFT, padx=5)
            except Exception as e:
                continue
        
        # Cập nhật scroll region
        self.gallery_inner.update_idletasks()
        self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))
    
    def load_captured_images_webcam(self):
        """Tải và hiển thị các ảnh đã chụp trong gallery webcam"""
        # Xóa các widget cũ trong gallery webcam
        for widget in self.webcam_gallery_inner.winfo_children():
            widget.destroy()
        
        # Khởi tạo danh sách nếu chưa có
        if not hasattr(self, 'captured_images_list'):
            self.captured_images_list = []
        
        # Tải danh sách ảnh từ folder
        if os.path.exists(self.webcam_folder):
            image_files = sorted([f for f in os.listdir(self.webcam_folder) 
                                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))],
                                key=lambda x: os.path.getmtime(os.path.join(self.webcam_folder, x)),
                                reverse=True)
            
            self.captured_images_list = [os.path.join(self.webcam_folder, f) for f in image_files]
        
        # Hiển thị các ảnh trong gallery webcam (tất cả ảnh, không giới hạn) - hiển thị dọc, to nhất có thể
        for img_path in self.captured_images_list:
            try:
                img = Image.open(img_path)
                # Tăng kích thước thumbnail (110x110 để phù hợp với frame nhỏ hơn)
                img.thumbnail((197, 197))
                img_tk = ImageTk.PhotoImage(img)
                
                # Tạo button với ảnh (pack dọc, sát bên phải giống nút chụp ảnh)
                btn = tk.Button(self.webcam_gallery_inner, image=img_tk, 
                              command=lambda path=img_path: self.load_captured_image(path),
                              bg=self.colors['bg_main'], relief=tk.FLAT, bd=0)
                btn.image = img_tk  # Giữ reference
                # Pack với anchor E để căn phải, và fill X để chiếm toàn bộ chiều rộng nhưng căn phải
                btn.pack(side=tk.TOP, pady=0, anchor=tk.E, fill=tk.X)
            except Exception as e:
                continue
        
        # Cập nhật scroll region - QUAN TRỌNG: phải cập nhật sau khi thêm tất cả ảnh (scroll dọc)
        # Đợi một chút để đảm bảo tất cả widget đã được render
        self.webcam_gallery_inner.update_idletasks()
        self.webcam_gallery_canvas.update_idletasks()
        
        # Lấy kích thước thực tế của inner frame
        inner_height = self.webcam_gallery_inner.winfo_reqheight()
        canvas_height = self.webcam_gallery_canvas.winfo_height()
        
        # Cập nhật scroll region dựa trên bbox của tất cả nội dung (theo chiều dọc)
        bbox = self.webcam_gallery_canvas.bbox("all")
        if bbox:
            # Sử dụng height thực tế của inner frame hoặc bbox, lấy giá trị lớn hơn
            scroll_height = max(inner_height, bbox[3]) if inner_height > 0 else bbox[3]
            # Mở rộng scroll region để bao gồm tất cả nội dung (theo chiều dọc)
            self.webcam_gallery_canvas.configure(scrollregion=(0, 0, bbox[2], scroll_height))
        else:
            # Nếu không có nội dung, set scroll region dựa trên inner height
            if inner_height > 0:
                self.webcam_gallery_canvas.configure(scrollregion=(0, 0, 110, inner_height))
            else:
                self.webcam_gallery_canvas.configure(scrollregion=(0, 0, 1, 1))
        
        # Force update scrollbar và reset về đầu (scroll dọc)
        self.webcam_gallery_canvas.yview_moveto(0)
        # Đảm bảo scrollbar được cập nhật
        self.webcam_gallery_scrollbar.update()
        
        # Căn phải các ảnh sau khi load xong
        self.webcam_gallery_canvas.update_idletasks()
        canvas_width = self.webcam_gallery_canvas.winfo_width()
        if canvas_width > 1:
            inner_width = self.webcam_gallery_inner.winfo_reqwidth()
            if inner_width < canvas_width:
                # Căn phải bằng cách đặt x position
                x_pos = canvas_width - inner_width
                self.webcam_gallery_canvas.coords(self.webcam_gallery_window, x_pos, 0)
    
    def load_captured_image(self, image_path):
        """Tải ảnh đã chụp vào editor"""
        try:
            # Tải ảnh mới trước
            new_image = Image.open(image_path)
            
            # Thoát webcam mode (sẽ không khôi phục trạng thái cũ)
            self.webcam_active = False
            if self.webcam_cap is not None:
                self.webcam_cap.release()
                self.webcam_cap = None
            
            # Ẩn khung webcam lớn
            self.webcam_frame.pack_forget()
            
            # Ẩn gallery
            self.gallery_frame.pack_forget()
            
            # Hiện lại hai frame ảnh gốc và chỉnh sửa
            self.original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
            self.edited_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
            
            # Đặt ảnh mới
            self.image = new_image
            self.undo_stack = []
            self.original_canvas_state = None
            self.reset_adjustments()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải ảnh: {str(e)}")
    
    def close_webcam(self):
        """Đóng webcam và khôi phục trạng thái ban đầu"""
        if not self.webcam_active:
            return
        
        self.webcam_active = False
        
        # Giải phóng webcam
        if self.webcam_cap is not None:
            self.webcam_cap.release()
            self.webcam_cap = None
        
        # Ẩn khung webcam lớn và gallery webcam
        self.webcam_frame.pack_forget()
        self.webcam_gallery_frame.pack_forget()
        
        # Ẩn gallery thường
        self.gallery_frame.pack_forget()
        
        # Hiện lại hai frame ảnh gốc và chỉnh sửa
        self.original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        self.edited_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        # Khôi phục trạng thái canvas ban đầu
        if self.original_canvas_state:
            self.image, self.edited_image = self.original_canvas_state
            self.update_images()
        else:
            # Nếu không có ảnh ban đầu, xóa cả hai canvas
            self.original_canvas.delete("all")
            self.edited_canvas.delete("all")
        
        self.webcam_capture = None
        self.current_operation = None

    def save_image(self):
        """Lưu ảnh với dialog chọn folder và tên file"""
        if self.edited_image:
            # Chọn folder để lưu
            folder_path = filedialog.askdirectory(title="Chọn thư mục để lưu ảnh")
            if folder_path:
                # Tạo dialog để nhập tên file
                save_window = tk.Toplevel(self.root)
                save_window.title("Lưu Ảnh")
                save_window.geometry("150x150")
                save_window.configure(bg=self.colors['bg_panel'])
                save_window.transient(self.root)
                save_window.grab_set()
                
                # Center window
                save_window.update_idletasks()
                x = (save_window.winfo_screenwidth() // 2) - (save_window.winfo_width() // 2)
                y = (save_window.winfo_screenheight() // 2) - (save_window.winfo_height() // 2)
                save_window.geometry(f"+{x}+{y}")
                
                tk.Label(save_window, text="Tên file:", 
                        bg=self.colors['bg_panel'], 
                        fg=self.colors['text_light'],
                        font=("Arial", 10)).pack(pady=10)
                
                name_entry = tk.Entry(save_window, width=30, font=("Arial", 10))
                name_entry.pack(pady=5)
                name_entry.insert(0, f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                name_entry.select_range(0, tk.END)
                name_entry.focus()
                
                format_var = tk.StringVar(value="png")
                format_frame = tk.Frame(save_window, bg=self.colors['bg_panel'])
                format_frame.pack(pady=5)
                tk.Radiobutton(format_frame, text="PNG", variable=format_var, value="png",
                              bg=self.colors['bg_panel'], fg=self.colors['text_light'],
                              selectcolor=self.colors['bg_main']).pack(side=tk.LEFT, padx=10)
                tk.Radiobutton(format_frame, text="JPEG", variable=format_var, value="jpg",
                              bg=self.colors['bg_panel'], fg=self.colors['text_light'],
                              selectcolor=self.colors['bg_main']).pack(side=tk.LEFT, padx=10)
                
                def do_save():
                    filename = name_entry.get().strip()
                    if not filename:
                        messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên file!")
                        return
                    
                    file_format = format_var.get()
                    file_path = os.path.join(folder_path, f"{filename}.{file_format}")
                    
                    try:
                        self.edited_image.save(file_path)
                        messagebox.showinfo("Thành công", f"Ảnh đã được lưu thành công!\n{file_path}")
                        save_window.destroy()
                    except Exception as e:
                        messagebox.showerror("Lỗi", f"Không thể lưu ảnh: {str(e)}")
                
                btn_frame = tk.Frame(save_window, bg=self.colors['bg_panel'])
                btn_frame.pack(pady=10)
                tk.Button(btn_frame, text="Lưu", bg=self.colors['success'], fg='white',
                         command=do_save, padx=20, pady=5).pack(side=tk.LEFT, padx=5)
                tk.Button(btn_frame, text="Hủy", bg=self.colors['accent'], fg='white',
                         command=save_window.destroy, padx=20, pady=5).pack(side=tk.LEFT, padx=5)
                
                # Enter để lưu
                name_entry.bind("<Return>", lambda e: do_save())
        else:
            messagebox.showwarning("Cảnh báo", "Không có ảnh để lưu!")
    
    def quick_save_image(self):
        """Lưu ảnh nhanh vào folder saved_images"""
        if self.edited_image:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.saved_images_folder}/edited_{timestamp}.png"
                self.edited_image.save(filename)
                messagebox.showinfo("Thành công", f"Ảnh đã được lưu nhanh vào:\n{filename}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu ảnh: {str(e)}")
        else:
            messagebox.showwarning("Cảnh báo", "Không có ảnh để lưu!")

    def reset_image(self):
        if self.image:
            self.undo_stack = []
            self.reset_adjustments()

    def crop_image(self):
        if not self.edited_image:
            messagebox.showwarning("Cảnh báo", "Vui lòng mở ảnh trước!")
            return

        crop_window = tk.Toplevel(self.root)
        crop_window.title("Cắt Ảnh")
        crop_window.configure(bg=self.colors['bg_panel'])
        crop_window.resizable(False, False)

        preview_image = self.edited_image.copy()
        max_w, max_h = 900, 600
        preview_image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        preview_w, preview_h = preview_image.size
        preview_photo = ImageTk.PhotoImage(preview_image)

        instruction = tk.Label(crop_window,
                               text="Kéo chuột để chọn vùng cần cắt. Nhấn Áp dụng để xác nhận.",
                               bg=self.colors['bg_panel'],
                               fg=self.colors['text_light'],
                               font=("Arial", 10))
        instruction.pack(pady=5)

        canvas = tk.Canvas(crop_window, width=preview_w, height=preview_h,
                           bg="#000000", highlightthickness=0, cursor="tcross")
        canvas.pack(padx=10, pady=10)
        canvas.create_image(0, 0, image=preview_photo, anchor=tk.NW)
        canvas.image = preview_photo

        selection = {'start': None, 'rect': None, 'coords': None}

        def clamp_point(x, y):
            return max(0, min(x, preview_w - 1)), max(0, min(y, preview_h - 1))

        def on_press(event):
            x, y = clamp_point(event.x, event.y)
            selection['start'] = (x, y)
            if selection['rect']:
                canvas.delete(selection['rect'])
            selection['rect'] = canvas.create_rectangle(x, y, x, y, outline=self.colors['accent'], width=2)
            selection['coords'] = None

        def on_drag(event):
            if selection['start'] and selection['rect']:
                x, y = clamp_point(event.x, event.y)
                canvas.coords(selection['rect'], selection['start'][0], selection['start'][1], x, y)

        def on_release(event):
            if selection['start'] and selection['rect']:
                x, y = clamp_point(event.x, event.y)
                canvas.coords(selection['rect'], selection['start'][0], selection['start'][1], x, y)
                x0, y0, x1, y1 = canvas.coords(selection['rect'])
                if abs(x1 - x0) >= 5 and abs(y1 - y0) >= 5:
                    selection['coords'] = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)

        # Hiển thị vùng cắt hiện tại nếu có
        existing_crop = self.adjustments.get('crop_box')
        if existing_crop:
            l, t, r, b = existing_crop
            canvas_rect = (l * preview_w, t * preview_h, r * preview_w, b * preview_h)
            selection['rect'] = canvas.create_rectangle(*canvas_rect, outline=self.colors['accent'], width=2)
            selection['coords'] = canvas_rect

        def apply_crop_selection():
            coords = selection.get('coords')
            if not coords:
                messagebox.showwarning("Thông báo", "Vui lòng chọn vùng cần cắt.")
                return
            left, top, right, bottom = coords
            if right - left < 5 or bottom - top < 5:
                messagebox.showwarning("Thông báo", "Vùng cắt quá nhỏ.")
                return
            left_norm = left / preview_w
            top_norm = top / preview_h
            right_norm = right / preview_w
            bottom_norm = bottom / preview_h
            self.save_state_for_undo()
            self.adjustments['crop_box'] = (left_norm, top_norm, right_norm, bottom_norm)
            self.reapply_adjustments()
            self.current_operation = None
            crop_window.destroy()

        def remove_crop():
            self.clear_crop_adjustment()
            crop_window.destroy()

        btn_frame = tk.Frame(crop_window, bg=self.colors['bg_panel'])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Áp dụng", bg=self.colors['success'], fg='white',
                  command=apply_crop_selection, padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Bỏ vùng cắt", bg=self.colors['bg_secondary'], fg='white',
                  command=remove_crop, padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Hủy", bg=self.colors['accent'], fg='white',
                  command=crop_window.destroy, padx=15, pady=5).pack(side=tk.LEFT, padx=5)

    def clear_crop_adjustment(self):
        if not self.image:
            return
        if not self.adjustments.get('crop_box'):
            messagebox.showinfo("Thông báo", "Không có vùng cắt nào để bỏ.")
            return
        self.save_state_for_undo()
        self.adjustments['crop_box'] = None
        self.reapply_adjustments()
        self.current_operation = None

    def resize_image(self):
        if not self.edited_image:
            messagebox.showwarning("Cảnh báo", "Vui lòng mở ảnh trước!")
            return

        resize_window = tk.Toplevel(self.root)
        resize_window.title("Đổi Kích Thước Ảnh")
        resize_window.configure(bg=self.colors['bg_panel'])
        resize_window.resizable(False, False)

        img_width, img_height = self.edited_image.size

        width_var = tk.StringVar(value=str(img_width))
        height_var = tk.StringVar(value=str(img_height))
        keep_aspect = tk.BooleanVar(value=True)

        frame_w = tk.Frame(resize_window, bg=self.colors['bg_panel'])
        frame_w.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frame_w, text="Chiều rộng (px)", bg=self.colors['bg_panel'], fg=self.colors['text_light'],
                 font=("Arial", 10)).pack(side=tk.LEFT)
        width_entry = tk.Entry(frame_w, textvariable=width_var, width=10)
        width_entry.pack(side=tk.RIGHT, padx=5)

        frame_h = tk.Frame(resize_window, bg=self.colors['bg_panel'])
        frame_h.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frame_h, text="Chiều cao (px)", bg=self.colors['bg_panel'], fg=self.colors['text_light'],
                 font=("Arial", 10)).pack(side=tk.LEFT)
        height_entry = tk.Entry(frame_h, textvariable=height_var, width=10)
        height_entry.pack(side=tk.RIGHT, padx=5)

        tk.Checkbutton(resize_window, text="Giữ tỷ lệ",
                       variable=keep_aspect,
                       bg=self.colors['bg_panel'],
                       fg=self.colors['text_light'],
                       selectcolor=self.colors['bg_main']).pack(pady=5)

        def apply_resize():
            try:
                new_width = int(width_var.get())
                new_height = int(height_var.get())
            except ValueError:
                messagebox.showerror("Lỗi", "Vui lòng nhập số hợp lệ!")
                return

            if new_width <= 0 or new_height <= 0:
                messagebox.showerror("Lỗi", "Kích thước phải lớn hơn 0!")
                return

            if keep_aspect.get():
                aspect = img_height / img_width
                new_height_calc = max(1, int(new_width * aspect))
                new_height = new_height_calc
                height_var.set(str(new_height))

            self.save_state_for_undo()
            resized = self.edited_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.image = resized.copy()
            self.reset_adjustments()
            resize_window.destroy()

        btn_frame = tk.Frame(resize_window, bg=self.colors['bg_panel'])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Áp dụng", bg=self.colors['success'], fg='white',
                  command=apply_resize, padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Hủy", bg=self.colors['accent'], fg='white',
                  command=resize_window.destroy, padx=15, pady=5).pack(side=tk.LEFT, padx=5)

    def reset_adjustments(self):
        """Đặt lại tất cả tham số chỉnh sửa về mặc định và đồng bộ UI."""
        self.adjustments = {
            'brightness': 1.0,
            'color': 1.0,
            'contrast': 1.0,
            'sharpen': 1.0,
            'blur': 0.0,
            'rotation': 0.0,
            'flip_horizontal': False,
            'flip_vertical': False,
            'filter': "Không",
            'crop_box': None,
        }
        self.filter_values = self.filter_values_defaults.copy()
        self.current_filter = "Không"

        if hasattr(self, 'brightness_slider'):
            self.suspend_slider_commands = True
            self.brightness_slider.set(self.adjustments['brightness'])
            self.color_slider.set(self.adjustments['color'])
            self.contrast_slider.set(self.adjustments['contrast'])
            self.sharpen_slider.set(self.adjustments['sharpen'])
            self.blur_slider.set(self.adjustments['blur'])
            self.rotation_slider.set(self.adjustments['rotation'])
            self.contour_slider.set(self.filter_values["Viền"])
            self.blur_filter_slider.set(self.filter_values["Làm Mờ"])
            self.bw_slider.set(self.filter_values["Đen Trắng"])
            self.detail_slider.set(self.filter_values["Chi Tiết"])
            self.edge_slider.set(self.filter_values["Tăng Cạnh"])
            self.smooth_slider.set(self.filter_values["Làm Mịn"])
            self.emboss_slider.set(self.filter_values["Làm Nổi"])
            self.filter_combo.set("Không")
            self.hide_filter_sliders()
            if hasattr(self, 'zoom_slider'):
                self.zoom_slider.set(100)
            self.suspend_slider_commands = False

        if self.image:
            self.reapply_adjustments()
        else:
            self.edited_image = None
            self.update_images()
        self.current_operation = None
        self.view_zoom = 1.0

    def start_operation(self, operation_name):
        """Lưu trạng thái để hoàn tác, chỉ thực hiện một lần cho mỗi thao tác."""
        if self.suspend_slider_commands:
            return
        if self.current_operation != operation_name:
            self.save_state_for_undo()
            self.current_operation = operation_name

    def commit_current_operation(self, event=None):
        """Kết thúc thao tác sau khi thả slider hoặc hoàn thành hành động."""
        self.current_operation = None

    def sync_sliders_with_adjustments(self):
        """Đưa slider về đúng trạng thái theo adjustments."""
        self.suspend_slider_commands = True
        self.brightness_slider.set(self.adjustments['brightness'])
        self.color_slider.set(self.adjustments['color'])
        self.contrast_slider.set(self.adjustments['contrast'])
        self.sharpen_slider.set(self.adjustments['sharpen'])
        self.blur_slider.set(self.adjustments['blur'])
        self.rotation_slider.set(self.adjustments['rotation'])
        self.filter_combo.set(self.adjustments['filter'])
        self.contour_slider.set(self.filter_values["Viền"])
        self.blur_filter_slider.set(self.filter_values["Làm Mờ"])
        self.bw_slider.set(self.filter_values["Đen Trắng"])
        self.detail_slider.set(self.filter_values["Chi Tiết"])
        self.edge_slider.set(self.filter_values["Tăng Cạnh"])
        self.smooth_slider.set(self.filter_values["Làm Mịn"])
        self.emboss_slider.set(self.filter_values["Làm Nổi"])
        self.current_filter = self.adjustments.get('filter', "Không")
        self.update_filter_slider_visibility()
        if hasattr(self, 'zoom_slider'):
            self.zoom_slider.set(100)
        self.view_zoom = 1.0
        self.suspend_slider_commands = False

    def reapply_adjustments(self):
        """Áp dụng lại toàn bộ chỉnh sửa từ ảnh gốc để đảm bảo mượt mà."""
        if not self.image:
            return

        result = self.image.copy()
        adj = self.adjustments

        if adj['brightness'] != 1.0:
            result = ImageEnhance.Brightness(result).enhance(adj['brightness'])
        if adj['color'] != 1.0:
            result = ImageEnhance.Color(result).enhance(adj['color'])
        if adj['contrast'] != 1.0:
            result = ImageEnhance.Contrast(result).enhance(adj['contrast'])
        if adj['sharpen'] != 1.0:
            result = ImageEnhance.Sharpness(result).enhance(adj['sharpen'])
        if adj['blur'] > 0:
            result = result.filter(ImageFilter.GaussianBlur(radius=adj['blur']))

        filter_name = adj['filter']
        self.current_filter = filter_name
        if filter_name != "Không":
            filter_intensity = self.filter_values.get(filter_name, 1.0)
            img_array = np.array(result)
            if filter_name == "Làm Mờ":
                filtered_array = self.apply_filter_blur_optimized(img_array, filter_intensity)
            elif filter_name == "Viền":
                filtered_array = self.apply_filter_contour_optimized(img_array, filter_intensity)
            elif filter_name == "Chi Tiết":
                filtered_array = self.apply_filter_detail_optimized(img_array, filter_intensity)
            elif filter_name == "Tăng Cạnh":
                filtered_array = self.apply_filter_edge_enhance_optimized(img_array, filter_intensity)
            elif filter_name == "Đen Trắng":
                filtered_array = self.apply_filter_bw_optimized(img_array, filter_intensity)
            elif filter_name == "Làm Mịn":
                filtered_array = self.apply_filter_smooth_optimized(img_array, filter_intensity)
            elif filter_name == "Làm Nổi":
                filtered_array = self.apply_filter_emboss_optimized(img_array, filter_intensity)
            else:
                filtered_array = img_array
            result = Image.fromarray(filtered_array)

        if adj['rotation'] != 0.0:
            result = result.rotate(-adj['rotation'], expand=True, fillcolor='white')

        if adj['flip_horizontal']:
            result = result.transpose(Image.FLIP_LEFT_RIGHT)
        if adj['flip_vertical']:
            result = result.transpose(Image.FLIP_TOP_BOTTOM)

        crop_box = adj.get('crop_box')
        if crop_box:
            left_norm, top_norm, right_norm, bottom_norm = crop_box
            left = max(0, min(int(result.width * left_norm), result.width - 1))
            top = max(0, min(int(result.height * top_norm), result.height - 1))
            right = max(left + 1, min(int(result.width * right_norm), result.width))
            bottom = max(top + 1, min(int(result.height * bottom_norm), result.height))
            if right - left >= 2 and bottom - top >= 2:
                result = result.crop((left, top, right, bottom))

        self.edited_image = result
        self.update_images()

    def scale_image_to_canvas(self, image, canvas):
        """Scale ảnh để vừa với canvas, giữ tỷ lệ"""
        canvas.update_idletasks()  # Đảm bảo canvas đã được render
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width, canvas_height = 480, 360
        
        # Tính toán kích thước để vừa với canvas, giữ tỷ lệ
        img_width, img_height = image.size
        scale_w = (canvas_width - 20) / img_width
        scale_h = (canvas_height - 20) / img_height
        scale = min(scale_w, scale_h)  # Chọn scale nhỏ hơn để ảnh vừa hoàn toàn
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return scaled_image
    
    def scale_image_to_canvas_fill(self, image, canvas):
        """Scale ảnh để fill toàn bộ canvas, có thể crop để phóng to"""
        canvas.update_idletasks()  # Đảm bảo canvas đã được render
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width, canvas_height = 480, 360
        
        # Tính toán kích thước để fill toàn bộ canvas
        img_width, img_height = image.size
        scale_w = canvas_width / img_width
        scale_h = canvas_height / img_height
        scale = max(scale_w, scale_h)  # Chọn scale lớn hơn để fill toàn bộ
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize ảnh
        scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop ảnh để vừa với canvas (center crop)
        left = (new_width - canvas_width) // 2
        top = (new_height - canvas_height) // 2
        right = left + canvas_width
        bottom = top + canvas_height
        
        cropped_image = scaled_image.crop((left, top, right, bottom))
        return cropped_image

    def on_window_resize(self, event=None):
        """Cập nhật ảnh khi cửa sổ thay đổi kích thước"""
        # Chỉ cập nhật khi resize cửa sổ chính, không phải các widget con
        if event and event.widget == self.root:
            if self.image:
                # Delay một chút để canvas có thời gian resize
                self.root.after(100, self.update_images)

    def update_images(self):
        """Cập nhật hiển thị ảnh trên canvas"""
        # Không cập nhật nếu đang ở chế độ webcam
        if self.webcam_active:
            return
        
        if self.image:
            try:
                # Ảnh gốc
                self.original_canvas.update_idletasks()
                scaled_original = self.scale_image_to_canvas(self.image, self.original_canvas)
                original_image_tk = ImageTk.PhotoImage(scaled_original)
                self.original_canvas.delete("all")
                canvas_width = self.original_canvas.winfo_width()
                canvas_height = self.original_canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    x = canvas_width // 2
                    y = canvas_height // 2
                    self.original_canvas.create_image(x, y, image=original_image_tk, anchor=tk.CENTER)
                self.original_canvas.image = original_image_tk  # Giữ reference
                
                # Ảnh đã chỉnh sửa
                self.edited_canvas.update_idletasks()
                scaled_edited = self.scale_image_to_canvas(self.edited_image, self.edited_canvas)
                if self.view_zoom != 1.0 and scaled_edited is not None:
                    zoom_w = max(1, int(scaled_edited.width * self.view_zoom))
                    zoom_h = max(1, int(scaled_edited.height * self.view_zoom))
                    scaled_edited = scaled_edited.resize((zoom_w, zoom_h), Image.Resampling.LANCZOS)
                edited_image_tk = ImageTk.PhotoImage(scaled_edited)
                self.edited_canvas.delete("all")
                canvas_width = self.edited_canvas.winfo_width()
                canvas_height = self.edited_canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    x = canvas_width // 2
                    y = canvas_height // 2
                    self.edited_canvas.create_image(x, y, image=edited_image_tk, anchor=tk.CENTER)
                self.edited_canvas.image = edited_image_tk  # Giữ reference
            except Exception as e:
                # Xử lý lỗi một cách im lặng để tránh crash
                pass
    
    def adjust_brightness(self, value=None):
        if not self.image or self.suspend_slider_commands:
            return
        self.start_operation("brightness")
        new_value = float(value) if value is not None else float(self.brightness_slider.get())
        self.adjustments['brightness'] = new_value
        self.reapply_adjustments()

    def adjust_color(self, value=None):
        if not self.image or self.suspend_slider_commands:
            return
        self.start_operation("color")
        new_value = float(value) if value is not None else float(self.color_slider.get())
        self.adjustments['color'] = new_value
        self.reapply_adjustments()

    def adjust_contrast(self, value=None):
        if not self.image or self.suspend_slider_commands:
            return
        self.start_operation("contrast")
        new_value = float(value) if value is not None else float(self.contrast_slider.get())
        self.adjustments['contrast'] = new_value
        self.reapply_adjustments()

    def adjust_sharpen(self, value=None):
        if not self.image or self.suspend_slider_commands:
            return
        self.start_operation("sharpen")
        new_value = float(value) if value is not None else float(self.sharpen_slider.get())
        self.adjustments['sharpen'] = new_value
        self.reapply_adjustments()

    def apply_blur(self, value=None):
        if not self.image or self.suspend_slider_commands:
            return
        self.start_operation("blur_basic")
        new_value = float(value) if value is not None else float(self.blur_slider.get())
        self.adjustments['blur'] = new_value
        self.reapply_adjustments()

    def rotate_image_slider(self, value=None):
        if not self.image or self.suspend_slider_commands:
            return
        self.start_operation("rotation")
        new_value = float(value) if value is not None else float(self.rotation_slider.get())
        self.adjustments['rotation'] = new_value
        self.reapply_adjustments()

    def adjust_zoom(self, value=None):
        if self.suspend_slider_commands:
            return
        if value is None and hasattr(self, 'zoom_slider'):
            value = self.zoom_slider.get()
        try:
            percent = float(value)
        except (TypeError, ValueError):
            percent = 100.0
        self.view_zoom = max(0.1, percent / 100.0)
        self.update_images()

    def flip_horizontal(self):
        if not self.image:
            return
            self.save_state_for_undo()
        current = self.adjustments.get('flip_horizontal', False)
        self.adjustments['flip_horizontal'] = not current
        self.reapply_adjustments()
        self.current_operation = None
    
    def flip_vertical(self):
        if not self.image:
            return
            self.save_state_for_undo()
        current = self.adjustments.get('flip_vertical', False)
        self.adjustments['flip_vertical'] = not current
        self.reapply_adjustments()
        self.current_operation = None

    def hide_filter_sliders(self):
        """Ẩn tất cả slider bộ lọc"""
        self.contour_slider_frame.pack_forget()
        self.blur_filter_slider_frame.pack_forget()
        self.bw_slider_frame.pack_forget()
        self.detail_slider_frame.pack_forget()
        self.edge_slider_frame.pack_forget()
        self.smooth_slider_frame.pack_forget()
        self.emboss_slider_frame.pack_forget()
    
    def show_filter_slider(self, slider_frame):
        """Hiện slider bộ lọc cụ thể"""
        self.hide_filter_sliders()
        slider_frame.pack(fill=tk.X, pady=5)
    
    def update_filter_slider_visibility(self):
        """Hiển thị đúng slider dựa trên bộ lọc đang chọn"""
        if self.current_filter == "Viền":
            self.show_filter_slider(self.contour_slider_frame)
        elif self.current_filter == "Làm Mờ":
            self.show_filter_slider(self.blur_filter_slider_frame)
        elif self.current_filter == "Đen Trắng":
            self.show_filter_slider(self.bw_slider_frame)
        elif self.current_filter == "Chi Tiết":
            self.show_filter_slider(self.detail_slider_frame)
        elif self.current_filter == "Tăng Cạnh":
            self.show_filter_slider(self.edge_slider_frame)
        elif self.current_filter == "Làm Mịn":
            self.show_filter_slider(self.smooth_slider_frame)
        elif self.current_filter == "Làm Nổi":
            self.show_filter_slider(self.emboss_slider_frame)
        else:
            self.hide_filter_sliders()
        
    def on_filter_change(self, event=None):
        """Khi thay đổi bộ lọc"""
        if self.suspend_slider_commands:
            return

        self.current_filter = self.filter_combo.get()
        self.adjustments['filter'] = self.current_filter
        self.update_filter_slider_visibility()

        if not self.image:
            return

        self.save_state_for_undo()
        self.reapply_adjustments()
        self.current_operation = None
    
    def on_contour_change(self, value=None):
        """Khi thay đổi slider viền"""
        new_value = float(value) if value is not None else float(self.contour_slider.get())
        self.filter_values["Viền"] = new_value
        if (self.current_filter != "Viền" or self.webcam_active or
                self.suspend_slider_commands or not self.image):
            return
        self.start_operation("filter_Viền")
        self.reapply_adjustments()
    
    def on_blur_filter_change(self, value=None):
        """Khi thay đổi slider làm mờ"""
        new_value = float(value) if value is not None else float(self.blur_filter_slider.get())
        self.filter_values["Làm Mờ"] = new_value
        if (self.current_filter != "Làm Mờ" or self.webcam_active or
                self.suspend_slider_commands or not self.image):
            return
        self.start_operation("filter_Làm Mờ")
        self.reapply_adjustments()
    
    def on_bw_change(self, value=None):
        """Khi thay đổi slider đen trắng"""
        new_value = float(value) if value is not None else float(self.bw_slider.get())
        self.filter_values["Đen Trắng"] = new_value
        if (self.current_filter != "Đen Trắng" or self.webcam_active or
                self.suspend_slider_commands or not self.image):
            return
        self.start_operation("filter_Đen Trắng")
        self.reapply_adjustments()
    
    def on_detail_change(self, value=None):
        """Khi thay đổi slider chi tiết"""
        new_value = float(value) if value is not None else float(self.detail_slider.get())
        self.filter_values["Chi Tiết"] = new_value
        if (self.current_filter != "Chi Tiết" or self.webcam_active or
                self.suspend_slider_commands or not self.image):
            return
        self.start_operation("filter_Chi Tiết")
        self.reapply_adjustments()
    
    def on_edge_change(self, value=None):
        """Khi thay đổi slider tăng cạnh"""
        new_value = float(value) if value is not None else float(self.edge_slider.get())
        self.filter_values["Tăng Cạnh"] = new_value
        if (self.current_filter != "Tăng Cạnh" or self.webcam_active or
                self.suspend_slider_commands or not self.image):
            return
        self.start_operation("filter_Tăng Cạnh")
        self.reapply_adjustments()
    
    def on_smooth_change(self, value=None):
        """Khi thay đổi slider làm mịn"""
        new_value = float(value) if value is not None else float(self.smooth_slider.get())
        self.filter_values["Làm Mịn"] = new_value
        if (self.current_filter != "Làm Mịn" or self.webcam_active or
                self.suspend_slider_commands or not self.image):
            return
        self.start_operation("filter_Làm Mịn")
        self.reapply_adjustments()
    
    def on_emboss_change(self, value=None):
        """Khi thay đổi slider làm nổi"""
        new_value = float(value) if value is not None else float(self.emboss_slider.get())
        self.filter_values["Làm Nổi"] = new_value
        if (self.current_filter != "Làm Nổi" or self.webcam_active or
                self.suspend_slider_commands or not self.image):
            return
        self.start_operation("filter_Làm Nổi")
        self.reapply_adjustments()
    
    def ai_auto_edit(self):
        """Tự động chỉnh sửa ảnh bằng AI - áp dụng nhiều cải tiến tự động thông minh"""
        if self.image:
            self.save_state_for_undo()
            
            # Chuyển sang numpy array để xử lý
            img_array = np.array(self.image)
            original_img = self.image.copy()
            
            # 1. Tự động điều chỉnh độ sáng và độ tương phản (Auto Levels)
            img_array = img_array.astype(np.float32)
            
            # Tính toán histogram để tự động điều chỉnh
            if len(img_array.shape) == 3:
                # Ảnh màu - xử lý từng kênh
                for i in range(3):
                    channel = img_array[:, :, i]
                    # Auto contrast với percentile
                    p2, p98 = np.percentile(channel, (2, 98))
                    if p98 > p2:
                        channel = np.clip((channel - p2) / (p98 - p2) * 255, 0, 255)
                        img_array[:, :, i] = channel
            else:
                # Ảnh grayscale
                p2, p98 = np.percentile(img_array, (2, 98))
                if p98 > p2:
                    img_array = np.clip((img_array - p2) / (p98 - p2) * 255, 0, 255)
            
            img_array = img_array.astype(np.uint8)
            
            # Chuyển lại sang PIL Image
            self.edited_image = Image.fromarray(img_array)
            
            # 2. Tự động cân bằng màu sắc (Color Balance)
            # Tính toán độ lệch màu và điều chỉnh
            enhancer = ImageEnhance.Color(self.edited_image)
            # Tự động tăng độ bão hòa nhẹ nếu ảnh có vẻ nhạt màu
            self.edited_image = enhancer.enhance(1.15)
            
            # 3. Tăng độ sắc nét thông minh (Smart Sharpening)
            enhancer = ImageEnhance.Sharpness(self.edited_image)
            self.edited_image = enhancer.enhance(1.25)
            
            # 4. Tự động điều chỉnh độ tương phản (Auto Contrast)
            enhancer = ImageEnhance.Contrast(self.edited_image)
            self.edited_image = enhancer.enhance(1.12)
            
            # 5. Tự động điều chỉnh độ sáng (Auto Brightness)
            # Tính toán độ sáng trung bình
            gray = self.edited_image.convert('L')
            brightness = np.array(gray).mean() / 255.0
            
            # Nếu ảnh quá tối (< 0.4) hoặc quá sáng (> 0.7), điều chỉnh
            if brightness < 0.4:
                enhancer = ImageEnhance.Brightness(self.edited_image)
                self.edited_image = enhancer.enhance(1.2)
            elif brightness > 0.7:
                enhancer = ImageEnhance.Brightness(self.edited_image)
                self.edited_image = enhancer.enhance(0.9)
            
            # 6. Giảm nhiễu nhẹ (Noise Reduction)
            # Áp dụng làm mịn nhẹ để giảm nhiễu
            temp_img = self.edited_image.filter(ImageFilter.SMOOTH_MORE)
            self.edited_image = Image.blend(self.edited_image, temp_img, 0.2)
            
            # 7. Tăng cường chi tiết (Detail Enhancement)
            detail_enhanced = self.edited_image.filter(ImageFilter.DETAIL)
            self.edited_image = Image.blend(self.edited_image, detail_enhanced, 0.15)
            
            self.update_images()
            messagebox.showinfo("Hoàn thành", 
                              " AI đã tự động chỉnh sửa ảnh của bạn!\n\n"
                              "Đã áp dụng:\n"
                              "• Tự động cân bằng độ sáng và tương phản\n"
                              "• Tăng cường màu sắc\n"
                              "• Làm sắc nét thông minh\n"
                              "• Giảm nhiễu\n"
                              "• Tăng cường chi tiết")
        else:
            messagebox.showwarning("Cảnh báo", "Vui lòng mở ảnh trước!")

    def save_state_for_undo(self):
        if self.edited_image:
            state = {
                'edited_image': self.edited_image.copy(),
                'base_image': self.image.copy() if self.image else None,
                'adjustments': copy.deepcopy(self.adjustments),
                'filter_values': copy.deepcopy(self.filter_values),
            }
            self.undo_stack.append(state)
            if len(self.undo_stack) > 20:
                self.undo_stack.pop(0)


    def undo_last_change(self):
        if self.undo_stack:
            state = self.undo_stack.pop()
            if state.get('base_image') is not None:
                self.image = state['base_image']
            self.adjustments = state.get('adjustments', self.adjustments)
            self.filter_values = state.get('filter_values', self.filter_values_defaults.copy())
            self.edited_image = state.get('edited_image', self.edited_image)
            self.sync_sliders_with_adjustments()
            self.update_images()
            self.current_operation = None
        else:
            messagebox.showinfo("Thông tin", "Không có thao tác nào để hoàn tác!")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()
