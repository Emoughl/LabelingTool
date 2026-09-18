# LabelingTool

Project gồm 2 phần chính:
- Tool thu thập ảnh giao thông
- Tool gán nhãn cho ảnh

## 1) Yêu cầu
- Python 3.10+
- Internet để tải ảnh
- Trên macOS có thể cần cài Tkinter nếu app gán nhãn báo thiếu GUI

## 2) Cài đặt môi trường

### Windows
```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Nếu thiếu Tkinter trên macOS
```bash
brew install python-tk
```

### Hoặc chạy script tự động
```bash
chmod +x install.sh
./install.sh
```

## 3) Tool lấy ảnh

```bash
source .venv/bin/activate
python traffic_collector.py
```

- Tự động tải ảnh từ camera giao thông
- Lưu ảnh theo ngày vào thư mục `images/`
- Lưu metadata vào `metadata.csv`

## 4) Tool gán nhãn

```bash
source .venv/bin/activate
python traffic_label_tool.py
```

- Đọc ảnh trong thư mục `images/YYYY-MM-DD/`
- Cho phép chọn ảnh và gán nhãn
- Lưu kết quả vào thư mục `output/` theo từng ngày

## 5) Cấu trúc thư mục mong đợi
```text
LabelingTool/
├── traffic_collector.py
├── traffic_label_tool.py
├── requirements.txt
├── README.md
├── metadata.csv
├── images/
│   └── YYYY-MM-DD/
├── output/
│   └── labels(YYYY-MM-DD).csv
└── .venv/
```

## 6) File dependency
`requirements.txt`:
```txt
requests>=2.31.0
Pillow>=10.0.0
urllib3>=2.5.0,<3.0.0
```

## 7) Lưu ý quan trọng
- Luôn chạy trong virtual environment, không nên cài trực tiếp vào hệ thống
- Nếu lỗi `externally-managed-environment` trên macOS/Linux, hãy dùng `.venv`
- Nếu tool gán nhãn không mở cửa sổ GUI, hãy kiểm tra lại việc cài Tkinter
- Nếu muốn thu ảnh mới thì phải chạy `traffic_collector.py` trước

## 8) Kiểm tra nhanh
```bash
python -c "import requests, PIL, urllib3; print('ok')"
```

Nếu in ra `ok`, môi trường đã sẵn sàng.

