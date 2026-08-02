import os
import csv
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

IMAGE_DIR = "images"
OUTPUT_DIR = "output"

CLASSES = [
    (0, "Rất thông thoáng", "Hầu như không có xe, chạy tốc độ cao, khoảng cách xe rất lớn"),
    (1, "Thông thoáng",     "Có xe nhưng thưa, không phải giảm tốc"),
    (2, "Trung bình",       "Lượng xe vừa phải, bắt đầu đông nhưng vẫn di chuyển liên tục"),
    (3, "Đông",             "Xe nhiều, di chuyển chậm, khoảng cách giữa xe nhỏ"),
    (4, "Kẹt xe",           "Xe nối đuôi kín đường hoặc gần như đứng yên"),
]

TIME_OF_DAY_OPTIONS = ["Buổi sáng", "Buổi tối"]

CLASS_NAME_EN = {
    0: "Free_Flow",
    1: "Light_Traffic",
    2: "Moderate_Traffic",
    3: "Heavy_Traffic",
    4: "Traffic_Jam",
}

RAIN_NOTE_EN = "Rain"

TIME_OF_DAY_EN = {
    "Buổi sáng": "Morning",
    "Buổi tối": "Evening",
}

GRID_COLS = 5
GRID_ROWS = 4
THUMB_SIZE = (160, 120)

IMAGES_PER_PAGE = GRID_COLS * GRID_ROWS

CSV_HEADER = ["filename", "label_id", "label_name", "note", "filepath"]


def get_date_folders():
    if not os.path.isdir(IMAGE_DIR):
        return []
    return sorted(
        d for d in os.listdir(IMAGE_DIR)
        if os.path.isdir(os.path.join(IMAGE_DIR, d))
    )


def output_csv_path(date_str):
    return os.path.join(OUTPUT_DIR, f"labels({date_str}).csv")


def load_labeled_filenames(date_str):
    labeled = set()
    csv_path = output_csv_path(date_str)
    if os.path.exists(csv_path):
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row:
                    labeled.add(row[0])
    return labeled

class DateSelector:
    def __init__(self, root, on_select):
        self.root = root
        self.on_select = on_select

        root.title("Chọn tập dữ liệu theo ngày")
        root.geometry("560x600")

        tk.Label(
            root, text="Chọn ngày dữ liệu để gán nhãn",
            font=("Arial", 14, "bold")
        ).pack(pady=15)

        container = tk.Frame(root)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        dates = get_date_folders()

        if not dates:
            tk.Label(
                container,
                text=f"Không tìm thấy thư mục ngày nào trong '{IMAGE_DIR}'.\n"
                     f"Hãy đảm bảo ảnh được lưu dạng {IMAGE_DIR}/YYYY-MM-DD/*.jpg",
                fg="#a00", wraplength=480, justify="left"
            ).pack(pady=20)
            return

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for d in dates:
            folder = os.path.join(IMAGE_DIR, d)
            images = [
                f for f in os.listdir(folder)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            total = len(images)
            labeled = load_labeled_filenames(d)
            labeled_count = sum(1 for f in images if f in labeled)

            text = f"{d}    ({labeled_count}/{total} đã gán nhãn)"
            btn = tk.Button(
                scroll_frame, text=text, font=("Arial", 11), height=2,
                anchor="w", padx=15,
                command=lambda dd=d: self.on_select(dd)
            )
            btn.pack(fill="x", pady=3)

class LabelTool:
    def __init__(self, root, date_str, on_back):
        self.root = root
        self.date_str = date_str
        self.on_back = on_back

        self.image_dir = os.path.join(IMAGE_DIR, date_str)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.output_csv = output_csv_path(date_str)

        self.root.title(f"Traffic Image Labeling Tool - {date_str}")
        self.root.minsize(700, 500)
        self.root.geometry("1100x820")

        if not os.path.exists(self.output_csv):
            with open(self.output_csv, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(CSV_HEADER)

        self.labeled = load_labeled_filenames(date_str)

        all_files = sorted(
            f for f in os.listdir(self.image_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        )
        self.remaining = [f for f in all_files if f not in self.labeled]
        self.total = len(all_files)
        self.total_pages = 1
        self.page_number = 1
        self.cursor = 0
        self.next_cursor = 0
        self.cursor_history = []

        self.selected = set()
        self.thumbs = {}
        self.frames = {}
        self.focus_idx = None
        self.page_files = []
        self.history = []
        self.note_rain = False
        self.note_time = None

        top_bar = tk.Frame(root)
        top_bar.pack(fill="x", padx=10, pady=(8, 0))

        back_btn = tk.Button(top_bar, text="<< Chọn ngày khác", command=self.go_back)
        back_btn.pack(side="left")

        tk.Label(
            top_bar, text=f"Ngày: {date_str}",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=15)

        self.status_label = tk.Label(root, text="", font=("Arial", 11), wraplength=1000, justify="left")
        self.status_label.pack(pady=5, fill="x", padx=10)

        legend_text = "  |  ".join(
            f"[{lid}] {name}: {criteria}" for lid, name, criteria in CLASSES
        )
        self.legend_label = tk.Label(
            root, text=legend_text, font=("Arial", 9), fg="#555",
            wraplength=1000, justify="left"
        )
        self.legend_label.pack(pady=(0, 8), padx=10, fill="x")

        self.note_frame = tk.Frame(root)
        self.note_frame.pack(pady=(0, 8), padx=10, fill="x")

        tk.Label(self.note_frame, text="Ghi chú áp dụng:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 10))

        NOTE_CHIP_DEFAULT_BG = "#e8e8e8"
        NOTE_CHIP_ACTIVE_BG = "#4da3ff"
        self._note_chip_default_bg = NOTE_CHIP_DEFAULT_BG
        self._note_chip_active_bg = NOTE_CHIP_ACTIVE_BG

        def make_chip(text, on_click):
            chip = tk.Label(
                self.note_frame, text=text, font=("Arial", 9),
                padx=12, pady=6, relief="raised", borderwidth=1,
                bg=NOTE_CHIP_DEFAULT_BG, cursor="hand2"
            )
            chip.pack(side="left", padx=4)
            chip.bind("<Button-1>", lambda e: on_click())
            return chip

        self.rain_btn = make_chip("Đang mưa", self.toggle_rain)

        self.time_buttons = {}
        for label in TIME_OF_DAY_OPTIONS:
            self.time_buttons[label] = make_chip(label, lambda l=label: self.set_time_of_day(l))

        clear_note_btn = make_chip("Xoá ghi chú", self.clear_notes)

        self.refresh_note_buttons()

        self.grid_frame = tk.Frame(root)
        self.grid_frame.pack(expand=True)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10, fill="x", padx=10)

        self.root.bind("<Configure>", self.on_resize)

        self.build_buttons()
        self.load_page()

    def toggle_rain(self):
        self.note_rain = not self.note_rain
        self.refresh_note_buttons()

    def set_time_of_day(self, label):
        self.note_time = None if self.note_time == label else label
        self.refresh_note_buttons()

    def clear_notes(self):
        self.note_rain = False
        self.note_time = None
        self.refresh_note_buttons()

    def refresh_note_buttons(self):
        default_bg = self._note_chip_default_bg
        active_bg = self._note_chip_active_bg
        self.rain_btn.config(bg=active_bg if self.note_rain else default_bg)
        for label, btn in self.time_buttons.items():
            btn.config(bg=active_bg if self.note_time == label else default_bg)

    def current_note_text(self):
        """Ghi chú dùng để LƯU vào CSV - luôn ở dạng tiếng Anh."""
        parts = []
        if self.note_rain:
            parts.append(RAIN_NOTE_EN)
        if self.note_time:
            parts.append(TIME_OF_DAY_EN[self.note_time])
        return ", ".join(parts)

    def go_back(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.on_back()

    def build_buttons(self):
        self.class_buttons = []
        for lid, name, _criteria in CLASSES:
            self.button_frame.columnconfigure(lid, weight=1)
            btn = tk.Button(
                self.button_frame, text=f"[{lid}] {name}",
                height=2, bg="#dfe9f5",
                font=("Arial", 10), wraplength=140,
                command=lambda l=lid, n=name: self.assign_label(l, n)
            )
            btn.grid(row=0, column=lid, padx=4, pady=4, sticky="ew")
            self.class_buttons.append(btn)
            self.root.bind(str(lid), lambda e, l=lid, n=name: self.assign_label(l, n))

        nav_frame = tk.Frame(self.button_frame)
        nav_frame.grid(row=1, column=0, columnspan=len(CLASSES), pady=(8, 0), sticky="ew")
        for i in range(4):
            nav_frame.columnconfigure(i, weight=1)

        prev_btn = tk.Button(
            nav_frame, text="<- Trang trước", height=2,
            command=self.go_prev_page
        )
        prev_btn.grid(row=0, column=0, padx=4, sticky="ew")
        self.prev_btn = prev_btn

        undo_btn = tk.Button(
            nav_frame, text="Hoàn tác (Command+Z)", height=2, bg="#fff3cd",
            command=self.undo_last
        )
        undo_btn.grid(row=0, column=1, padx=4, sticky="ew")

        clear_btn = tk.Button(
            nav_frame, text="Bỏ chọn tất cả", height=2,
            command=self.clear_selection
        )
        clear_btn.grid(row=0, column=2, padx=4, sticky="ew")

        next_btn = tk.Button(
            nav_frame, text="Trang sau ->", height=2, bg="#f5dfdf",
            command=self.go_next_page
        )
        next_btn.grid(row=0, column=3, padx=4, sticky="ew")
        self.next_btn = next_btn

        self.root.bind("<Left>", lambda e: self.move_focus(-1))
        self.root.bind("<Right>", lambda e: self.move_focus(1))
        self.root.bind("<Up>", lambda e: self.move_focus(-GRID_COLS))
        self.root.bind("<Down>", lambda e: self.move_focus(GRID_COLS))
        self.root.bind("<Return>", lambda e: self.go_next_page())
        self.root.bind("<Control-z>", lambda e: self.undo_last())
        self.root.bind("<Command-z>", lambda e: self.undo_last())

    def on_resize(self, event):
        if event.widget != self.root:
            return
        width = event.width
        self.status_label.config(wraplength=width - 20)
        self.legend_label.config(wraplength=width - 20)
        per_btn = max(80, width // max(1, len(CLASSES)) - 20)
        for btn in self.class_buttons:
            btn.config(wraplength=per_btn)

    def load_page(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.selected.clear()
        self.thumbs.clear()
        self.frames.clear()
        self.focus_idx = None

        self.page_files = []
        idx = self.cursor
        n = len(self.remaining)
        while idx < n and len(self.page_files) < IMAGES_PER_PAGE:
            fname = self.remaining[idx]
            if fname not in self.labeled:
                self.page_files.append(fname)
            idx += 1
        self.next_cursor = idx

        done = len(self.labeled)
        unlabeled_count = self.total - done
        self.total_pages = max(1, -(-unlabeled_count // IMAGES_PER_PAGE))

        is_last_page = self.next_cursor >= len(self.remaining)
        if is_last_page:
            self.page_number = self.total_pages
        elif self.page_number > self.total_pages:
            self.page_number = self.total_pages

        self.status_label.config(
            text=f"Ngày: {self.date_str}  |  Trang {self.page_number}/{self.total_pages}  |  "
                 f"Đã gán: {done}/{self.total}"
        )

        self.next_btn.config(state=("disabled" if is_last_page else "normal"))
        self.prev_btn.config(state=("disabled" if not self.cursor_history else "normal"))

        if not self.page_files:
            if done >= self.total:
                messagebox.showinfo("Hoàn tất", "Không còn ảnh nào để gán nhãn trong ngày này.")
            return

        for idx, fname in enumerate(self.page_files):
            path = os.path.join(self.image_dir, fname)
            try:
                img = Image.open(path)
                img.thumbnail(THUMB_SIZE)
                tk_img = ImageTk.PhotoImage(img)
            except Exception:
                continue
            self.thumbs[idx] = tk_img

            r, c = divmod(idx, GRID_COLS)
            frame = tk.Frame(self.grid_frame, bd=2, relief="flat", bg="white")
            frame.grid(row=r, column=c, padx=4, pady=4)
            self.frames[idx] = frame

            lbl = tk.Label(frame, image=tk_img, bd=0)
            lbl.pack()
            lbl.bind("<Button-1>", lambda e, i=idx, f=frame: self.toggle_select(i, f))
            frame.bind("<Button-1>", lambda e, i=idx, f=frame: self.toggle_select(i, f))

    def toggle_select(self, idx, frame):
        self.focus_idx = idx
        if idx in self.selected:
            self.selected.remove(idx)
            frame.config(bg="white", relief="flat")
        else:
            self.selected.add(idx)
            frame.config(bg="black", relief="solid", borderwidth=2)

    def move_focus(self, delta):
        if not self.page_files:
            return
        if self.focus_idx is None:
            new_idx = 0
        else:
            new_idx = max(0, min(len(self.page_files) - 1, self.focus_idx + delta))

        self.selected = {new_idx}
        self.focus_idx = new_idx
        for idx, frame in self.frames.items():
            if idx == new_idx:
                frame.config(bg="black", relief="solid")
            else:
                frame.config(bg="white", relief="flat")

    def clear_selection(self):
        for widget in self.grid_frame.winfo_children():
            widget.config(bg="white", relief="flat")
        self.selected.clear()

    def assign_label(self, label_id, label_name):
        if not self.selected:
            messagebox.showwarning("Chưa chọn ảnh", "Hãy click chọn ít nhất 1 ảnh trước.")
            return

        note = self.current_note_text()
        label_name_en = CLASS_NAME_EN.get(label_id, label_name)
        batch = []
        with open(self.output_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for idx in self.selected:
                fname = self.page_files[idx]
                filepath = os.path.join(self.image_dir, fname)
                writer.writerow([fname, label_id, label_name_en, note, filepath])
                self.labeled.add(fname)
                batch.append(fname)

        self.history.append(batch)
        self.load_page()

    def undo_last(self):
        if not self.history:
            messagebox.showinfo("Hoàn tác", "Không còn thao tác nào để hoàn tác.")
            return

        batch = self.history.pop()
        batch_set = set(batch)
        self.labeled -= batch_set

        with open(self.output_csv, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            rows = [row for row in reader if row and row[0] not in batch_set]

        with open(self.output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(header)
            writer.writerows(rows)

        first_fname = batch[0]
        if first_fname in self.remaining:
            idx_in_remaining = self.remaining.index(first_fname)
            self.cursor = min(self.cursor, idx_in_remaining)

        self.load_page()

    def go_next_page(self):
        if self.next_cursor >= len(self.remaining):
            return
        self.cursor_history.append(self.cursor)
        self.cursor = self.next_cursor
        self.page_number += 1
        self.load_page()

    def go_prev_page(self):
        if self.cursor_history:
            self.cursor = self.cursor_history.pop()
            self.page_number -= 1
            self.load_page()
        else:
            messagebox.showinfo("Trang trước", "Đây đã là vị trí đầu tiên.")

# MAIN
def start_app():
    root = tk.Tk()

    def show_selector():
        for widget in root.winfo_children():
            widget.destroy()
        root.unbind("<Configure>")
        root.unbind("<Left>")
        root.unbind("<Right>")
        root.unbind("<Up>")
        root.unbind("<Down>")
        root.unbind("<Return>")
        root.unbind("<Control-z>")
        root.unbind("<Command-z>")
        for lid, _, _ in CLASSES:
            root.unbind(str(lid))
        DateSelector(root, on_select=open_label_tool)

    def open_label_tool(date_str):
        for widget in root.winfo_children():
            widget.destroy()
        LabelTool(root, date_str, on_back=show_selector)

    show_selector()
    root.mainloop()


if __name__ == "__main__":
    if not os.path.isdir(IMAGE_DIR):
        print(f"Không tìm thấy thư mục ảnh: {IMAGE_DIR}")
        print("Sửa biến IMAGE_DIR trong file này rồi chạy lại.")
    else:
        start_app()