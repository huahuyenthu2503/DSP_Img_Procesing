import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import cv2
import numpy as np
import os
from datetime import datetime


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
        self.current_filter = "Không"
        self.filter_intensity = 1.0
        # Slider riêng cho từng bộ lọc
        self.contour_slider_value = 1.0
        self.blur_slider_value = 2.0
        self.bw_slider_value = 1.0
        self.detail_slider_value = 1.0
        self.edge_slider_value = 1.0
        self.smooth_slider_value = 1.0
        self.emboss_slider_value = 1.0
        
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
        
        tk.Button(file_frame, text="📁 Mở File", 
                 bg=self.colors['bg_button'], fg='white',
                 command=self.open_image, **btn_style).pack(fill=tk.X, pady=5)
        
        tk.Button(file_frame, text="📷 Mở Webcam", 
                 bg=self.colors['success'], fg='white',
                 command=self.open_webcam, **btn_style).pack(fill=tk.X, pady=5)
        
        # Nút AI
        tk.Button(file_frame, text="🤖 AI Tự Động Sửa Ảnh", 
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
        
        # Slider riêng cho từng bộ lọc
        # Slider cho Viền (Contour)
        self.contour_slider, self.contour_slider_frame = self.add_slider_with_frame(
            filter_frame, "Viền (Đậm/Nhẹ)", 0.1, 3.0, 1.0, self.on_contour_change)
        
        # Slider cho Làm Mờ (Blur)
        self.blur_filter_slider, self.blur_filter_slider_frame = self.add_slider_with_frame(
            filter_frame, "Làm Mờ (Đậm/Nhẹ)", 0.5, 10.0, 2.0, self.on_blur_filter_change)
        
        # Slider cho Đen Trắng
        self.bw_slider, self.bw_slider_frame = self.add_slider_with_frame(
            filter_frame, "Đen Trắng (Đậm/Nhẹ)", 0.1, 1.0, 1.0, self.on_bw_change)
        
        # Slider cho Chi Tiết
        self.detail_slider, self.detail_slider_frame = self.add_slider_with_frame(
            filter_frame, "Chi Tiết (Đậm/Nhẹ)", 0.1, 3.0, 1.0, self.on_detail_change)
        
        # Slider cho Tăng Cạnh
        self.edge_slider, self.edge_slider_frame = self.add_slider_with_frame(
            filter_frame, "Tăng Cạnh (Đậm/Nhẹ)", 0.1, 3.0, 1.0, self.on_edge_change)
        
        # Slider cho Làm Mịn
        self.smooth_slider, self.smooth_slider_frame = self.add_slider_with_frame(
            filter_frame, "Làm Mịn (Đậm/Nhẹ)", 0.1, 3.0, 1.0, self.on_smooth_change)
        
        # Slider cho Làm Nổi
        self.emboss_slider, self.emboss_slider_frame = self.add_slider_with_frame(
            filter_frame, "Làm Nổi (Đậm/Nhẹ)", 0.1, 3.0, 1.0, self.on_emboss_change)
        
        # Ẩn các slider ban đầu, chỉ hiện khi chọn bộ lọc tương ứng
        self.hide_filter_sliders()
        
        # Phần thao tác
        action_frame = tk.LabelFrame(self.tools_panel, text="Thao Tác", 
                                     font=("Arial", 11, "bold"),
                                     bg=self.colors['bg_panel'], 
                                     fg=self.colors['text_light'],
                                     padx=10, pady=10)
        action_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Button(action_frame, text="💾 Lưu Ảnh", 
                 bg=self.colors['success'], fg='white',
                 command=self.save_image, **btn_style).pack(fill=tk.X, pady=3)
        
        tk.Button(action_frame, text="💾 Lưu Nhanh", 
                 bg=self.colors['bg_button'], fg='white',
                 command=self.quick_save_image, **btn_style).pack(fill=tk.X, pady=3)
        tk.Button(action_frame, text="↺ Hoàn Tác", 
                 bg=self.colors['warning'], fg='white',
                 command=self.undo_last_change, **btn_style).pack(fill=tk.X, pady=3)
        tk.Button(action_frame, text="🔄 Đặt Lại", 
                 bg=self.colors['bg_secondary'], fg='white',
                 command=self.reset_image, **btn_style).pack(fill=tk.X, pady=3)
        tk.Button(action_frame, text="❌ Thoát", 
                 bg=self.colors['accent'], fg='white',
                 command=root.quit, **btn_style).pack(fill=tk.X, pady=3)
        
        # Canvas cho ảnh gốc và đã chỉnh sửa
        img_display_frame = tk.Frame(self.image_panel, bg=self.colors['bg_main'])
        img_display_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Ảnh gốc
        original_frame = tk.Frame(img_display_frame, bg=self.colors['bg_panel'], relief=tk.RAISED, bd=2)
        original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(original_frame, text="Ảnh Gốc", 
                font=("Arial", 14, "bold"), 
                bg=self.colors['bg_panel'], 
                fg=self.colors['text_light']).pack(pady=10)
        
        self.original_canvas = tk.Canvas(original_frame, 
                                        bg='#1A1A1A', highlightthickness=0)
        self.original_canvas.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        # Ảnh đã chỉnh sửa
        edited_frame = tk.Frame(img_display_frame, bg=self.colors['bg_panel'], relief=tk.RAISED, bd=2)
        edited_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(edited_frame, text="Ảnh Đã Chỉnh Sửa", 
                font=("Arial", 14, "bold"), 
                bg=self.colors['bg_panel'], 
                fg=self.colors['text_light']).pack(pady=10)
        
        self.edited_canvas = tk.Canvas(edited_frame, 
                                      bg='#1A1A1A', highlightthickness=0)
        self.edited_canvas.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
    
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
        
        return slider, frame

    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")])
        if file_path:
            try:
                self.image = Image.open(file_path)
                self.edited_image = self.image.copy()
                self.undo_stack = []
                self.update_images()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở ảnh: {str(e)}")
    
    def open_webcam(self):
        """Mở webcam và chụp ảnh"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            messagebox.showerror("Lỗi", "Không thể mở webcam!")
            return
        
        # Tạo cửa sổ webcam
        webcam_window = tk.Toplevel(self.root)
        webcam_window.title("Webcam")
        webcam_window.geometry("640x520")
        webcam_window.configure(bg=self.colors['bg_main'])
        
        # Canvas để hiển thị webcam
        webcam_canvas = tk.Canvas(webcam_window, width=640, height=480, bg='black')
        webcam_canvas.pack(pady=10)
        
        # Nút chụp ảnh
        capture_btn = tk.Button(webcam_window, text="📸 Chụp Ảnh", 
                               bg=self.colors['success'], fg='white',
                               font=("Arial", 12, "bold"),
                               command=lambda: self.capture_photo(cap, webcam_window),
                               padx=20, pady=10)
        capture_btn.pack(pady=5)
        
        # Nút đóng
        close_btn = tk.Button(webcam_window, text="Đóng", 
                             bg=self.colors['accent'], fg='white',
                             command=lambda: self.close_webcam(cap, webcam_window),
                             padx=20, pady=5)
        close_btn.pack()
        
        def update_frame():
            ret, frame = cap.read()
            if ret:
                # Chuyển BGR sang RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_pil = Image.fromarray(frame_rgb)
                frame_pil.thumbnail((640, 480))
                
                frame_tk = ImageTk.PhotoImage(frame_pil)
                webcam_canvas.create_image(320, 240, image=frame_tk)
                webcam_canvas.image = frame_tk
                
                self.webcam_capture = frame_rgb
                webcam_window.after(30, update_frame)
            else:
                messagebox.showerror("Lỗi", "Không thể đọc từ webcam!")
                cap.release()
                webcam_window.destroy()
        
        update_frame()
    
    def capture_photo(self, cap, window):
        """Chụp ảnh từ webcam và lưu vào folder"""
        if self.webcam_capture is not None:
            # Tạo tên file với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.webcam_folder}/capture_{timestamp}.jpg"
            
            # Chuyển numpy array sang PIL Image và lưu
            image_pil = Image.fromarray(self.webcam_capture)
            image_pil.save(filename)
            
            # Mở ảnh vừa chụp trong editor
            self.image = image_pil
            self.edited_image = self.image.copy()
            self.undo_stack = []
            self.update_images()
            
            messagebox.showinfo("Thành công", f"Ảnh đã được lưu vào: {filename}")
            cap.release()
            window.destroy()
        else:
            messagebox.showwarning("Cảnh báo", "Không có ảnh để chụp!")
    
    def close_webcam(self, cap, window):
        cap.release()
        window.destroy()

    def save_image(self):
        """Lưu ảnh với dialog chọn folder và tên file"""
        if self.edited_image:
            # Chọn folder để lưu
            folder_path = filedialog.askdirectory(title="Chọn thư mục để lưu ảnh")
            if folder_path:
                # Tạo dialog để nhập tên file
                save_window = tk.Toplevel(self.root)
                save_window.title("Lưu Ảnh")
                save_window.geometry("400x150")
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
            self.edited_image = self.image.copy()
            self.undo_stack = []
            # Reset các slider về giá trị mặc định
            self.brightness_slider.set(1)
            self.color_slider.set(1)
            self.contrast_slider.set(1)
            self.sharpen_slider.set(1)
            self.blur_slider.set(0)
            self.rotation_slider.set(0)
            self.filter_combo.set("Không")
            self.current_filter = "Không"
            self.contour_slider.set(1.0)
            self.blur_filter_slider.set(2.0)
            self.bw_slider.set(1.0)
            self.detail_slider.set(1.0)
            self.edge_slider.set(1.0)
            self.smooth_slider.set(1.0)
            self.emboss_slider.set(1.0)
            self.hide_filter_sliders()
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

    def on_window_resize(self, event=None):
        """Cập nhật ảnh khi cửa sổ thay đổi kích thước"""
        # Chỉ cập nhật khi resize cửa sổ chính, không phải các widget con
        if event and event.widget == self.root:
            if self.image:
                # Delay một chút để canvas có thời gian resize
                self.root.after(100, self.update_images)

    def update_images(self):
        """Cập nhật hiển thị ảnh trên canvas"""
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
        if self.image:
            self.save_state_for_undo()
            enhancer = ImageEnhance.Brightness(self.image)
            self.edited_image = enhancer.enhance(self.brightness_slider.get())
            self.update_images()

    def adjust_color(self, value=None):
        if self.image:
            self.save_state_for_undo()
            enhancer = ImageEnhance.Color(self.image)
            self.edited_image = enhancer.enhance(self.color_slider.get())
            self.update_images()

    def adjust_contrast(self, value=None):
        if self.image:
            self.save_state_for_undo()
            enhancer = ImageEnhance.Contrast(self.image)
            self.edited_image = enhancer.enhance(self.contrast_slider.get())
            self.update_images()

    def adjust_sharpen(self, value=None):
        if self.image:
            self.save_state_for_undo()
            enhancer = ImageEnhance.Sharpness(self.image)
            self.edited_image = enhancer.enhance(self.sharpen_slider.get())
            self.update_images()

    def apply_blur(self, value=None):
        if self.image:
            self.save_state_for_undo()
            blur_radius = self.blur_slider.get()
            if blur_radius > 0:
                self.edited_image = self.image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            else:
                self.edited_image = self.image.copy()
            self.update_images()

    def rotate_image_slider(self, value=None):
        if self.image:
            self.save_state_for_undo()
            angle = self.rotation_slider.get()
            self.edited_image = self.image.rotate(-angle, expand=True, fillcolor='white')
            self.update_images()

    def flip_horizontal(self):
        if self.image:
            self.save_state_for_undo()
            self.edited_image = self.image.transpose(Image.FLIP_LEFT_RIGHT)
            self.update_images()
    
    def flip_vertical(self):
        if self.image:
            self.save_state_for_undo()
            self.edited_image = self.image.transpose(Image.FLIP_TOP_BOTTOM)
            self.update_images()

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
    
    def on_filter_change(self, event=None):
        """Khi thay đổi bộ lọc"""
        self.current_filter = self.filter_combo.get()
        
        # Hiện/ẩn slider tương ứng
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
        
        self.apply_filter_with_intensity()
    
    def on_contour_change(self, value=None):
        """Khi thay đổi slider viền"""
        if self.current_filter == "Viền":
            self.contour_slider_value = self.contour_slider.get()
            self.apply_filter_with_intensity()
    
    def on_blur_filter_change(self, value=None):
        """Khi thay đổi slider làm mờ"""
        if self.current_filter == "Làm Mờ":
            self.blur_slider_value = self.blur_filter_slider.get()
            self.apply_filter_with_intensity()
    
    def on_bw_change(self, value=None):
        """Khi thay đổi slider đen trắng"""
        if self.current_filter == "Đen Trắng":
            self.bw_slider_value = self.bw_slider.get()
            self.apply_filter_with_intensity()
    
    def on_detail_change(self, value=None):
        """Khi thay đổi slider chi tiết"""
        if self.current_filter == "Chi Tiết":
            self.detail_slider_value = self.detail_slider.get()
            self.apply_filter_with_intensity()
    
    def on_edge_change(self, value=None):
        """Khi thay đổi slider tăng cạnh"""
        if self.current_filter == "Tăng Cạnh":
            self.edge_slider_value = self.edge_slider.get()
            self.apply_filter_with_intensity()
    
    def on_smooth_change(self, value=None):
        """Khi thay đổi slider làm mịn"""
        if self.current_filter == "Làm Mịn":
            self.smooth_slider_value = self.smooth_slider.get()
            self.apply_filter_with_intensity()
    
    def on_emboss_change(self, value=None):
        """Khi thay đổi slider làm nổi"""
        if self.current_filter == "Làm Nổi":
            self.emboss_slider_value = self.emboss_slider.get()
            self.apply_filter_with_intensity()
    
    def apply_filter_with_intensity(self, value=None):
        """Áp dụng bộ lọc với cường độ điều chỉnh được"""
        if self.image:
            self.save_state_for_undo()
            filter_name = self.current_filter
            
            if filter_name == "Không":
                self.edited_image = self.image.copy()
            elif filter_name == "Làm Mờ":
                # Sử dụng slider riêng cho làm mờ
                radius = max(0.5, self.blur_slider_value)
                self.edited_image = self.image.filter(ImageFilter.GaussianBlur(radius=radius))
            elif filter_name == "Viền":
                # Sử dụng slider riêng cho viền
                intensity = self.contour_slider_value
                if intensity > 1.0:
                    # Tăng cường độ bằng cách áp dụng nhiều lần và blend
                    temp_img = self.image.filter(ImageFilter.CONTOUR)
                    # Áp dụng nhiều lần để tăng độ đậm
                    num_applications = int(intensity)
                    for _ in range(num_applications - 1):
                        temp_img = temp_img.filter(ImageFilter.CONTOUR)
                    # Blend với ảnh gốc để điều chỉnh độ đậm/nhẹ
                    blend_factor = intensity - int(intensity)
                    if blend_factor > 0:
                        self.edited_image = Image.blend(self.image, temp_img, min(1.0, blend_factor + 0.5))
                    else:
                        self.edited_image = Image.blend(self.image, temp_img, 0.5)
                else:
                    # Giảm cường độ bằng cách blend với ảnh gốc
                    filtered = self.image.filter(ImageFilter.CONTOUR)
                    self.edited_image = Image.blend(self.image, filtered, intensity)
            elif filter_name == "Chi Tiết":
                # Sử dụng slider riêng cho chi tiết
                intensity = self.detail_slider_value
                filtered = self.image.filter(ImageFilter.DETAIL)
                if intensity != 1.0:
                    self.edited_image = Image.blend(self.image, filtered, min(1.0, intensity / 3.0))
                else:
                    self.edited_image = filtered
            elif filter_name == "Tăng Cạnh":
                # Sử dụng slider riêng cho tăng cạnh
                intensity = self.edge_slider_value
                filtered = self.image.filter(ImageFilter.EDGE_ENHANCE)
                if intensity != 1.0:
                    self.edited_image = Image.blend(self.image, filtered, min(1.0, intensity / 3.0))
                else:
                    self.edited_image = filtered
            elif filter_name == "Đen Trắng":
                # Sử dụng slider riêng cho đen trắng
                intensity = self.bw_slider_value
                bw_image = self.image.convert("L").convert("RGB")
                if intensity < 1.0:
                    # Blend giữa ảnh màu và đen trắng để điều chỉnh độ đậm/nhẹ
                    self.edited_image = Image.blend(self.image, bw_image, intensity)
                else:
                    self.edited_image = bw_image
            elif filter_name == "Làm Mịn":
                # Sử dụng slider riêng cho làm mịn
                intensity = self.smooth_slider_value
                filtered = self.image.filter(ImageFilter.SMOOTH)
                if intensity != 1.0:
                    self.edited_image = Image.blend(self.image, filtered, min(1.0, intensity / 3.0))
                else:
                    self.edited_image = filtered
            elif filter_name == "Làm Nổi":
                # Sử dụng slider riêng cho làm nổi
                intensity = self.emboss_slider_value
                filtered = self.image.filter(ImageFilter.EMBOSS)
                if intensity != 1.0:
                    self.edited_image = Image.blend(self.image, filtered, min(1.0, intensity / 3.0))
                else:
                    self.edited_image = filtered
            
            self.update_images()
    
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
                              "🤖 AI đã tự động chỉnh sửa ảnh của bạn!\n\n"
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
            self.undo_stack.append(self.edited_image.copy())
            # Giới hạn stack để tránh tốn bộ nhớ
            if len(self.undo_stack) > 20:
                self.undo_stack.pop(0)

    def undo_last_change(self):
        if self.undo_stack:
            self.edited_image = self.undo_stack.pop()
            self.update_images()
        else:
            messagebox.showinfo("Thông tin", "Không có thao tác nào để hoàn tác!")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()
