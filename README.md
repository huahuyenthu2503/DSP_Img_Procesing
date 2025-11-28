# DSP Image Processing Application

Ứng dụng xử lý ảnh được refactor với cấu trúc module rõ ràng.

## Cấu trúc thư mục

```
DSP_Img_Procesing/
├── main.py                 # Entry point chính
├── config.py               # Cấu hình chung
├── README.md               # File này
│
├── ui/                     # Giao diện người dùng
│   ├── __init__.py
│   ├── main_window.py      # Cửa sổ chính
│   └── processing_window.py # Cửa sổ xử lý ảnh
│
├── image_processing/       # Xử lý ảnh
│   ├── __init__.py
│   ├── edge_detection.py   # (Sẽ được tạo)
│   ├── thresholding.py     # (Sẽ được tạo)
│   └── filters.py          # (Sẽ được tạo)
│
├── image_editing/          # Chỉnh sửa ảnh
│   └── Image_Editing.py    # Đã có sẵn
│
└── utils/                  # Tiện ích chung
    ├── __init__.py
    ├── file_operations.py  # Mở, lưu file
    └── image_utils.py      # Chuyển đổi, resize ảnh
```

## Cách chạy

```bash
python main.py
```

## Lưu ý

- Thư mục gốc "Source Code" được giữ nguyên để tránh mất dữ liệu
- Các hàm xử lý ảnh hiện tại vẫn gọi từ App.py gốc để đảm bảo tương thích
- Có thể dần dần refactor các hàm vào các module tương ứng

## Dependencies

- tkinter
- PIL (Pillow)
- numpy
- opencv-python (cv2)
- matplotlib
- scikit-image
- scipy

