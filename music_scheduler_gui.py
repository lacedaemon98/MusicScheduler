#!/usr/bin/env python3
"""
Music Scheduler - Phần mềm hẹn giờ phát nhạc
Có thể build thành .exe cho Windows
"""

import os
import random
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pygame import mixer
import json


class MusicSchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Scheduler - Hẹn Giờ Phát Nhạc")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        self.music_folder = ""
        self.scheduled_times = []
        self.is_running = False
        self.last_played = {}

        mixer.init()

        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """Thiết lập giao diện"""
        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=60)
        header.pack(fill=tk.X)

        title = tk.Label(header, text="🎵 Music Scheduler",
                        font=("Arial", 18, "bold"),
                        bg="#2c3e50", fg="white")
        title.pack(pady=15)

        # Main container
        main = tk.Frame(self.root, padx=20, pady=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Folder selection
        folder_frame = tk.LabelFrame(main, text="📁 Folder Nhạc",
                                     font=("Arial", 10, "bold"), padx=10, pady=10)
        folder_frame.pack(fill=tk.X, pady=(0, 15))

        self.folder_label = tk.Label(folder_frame, text="Chưa chọn folder",
                                     fg="gray", anchor="w")
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = tk.Button(folder_frame, text="Chọn Folder",
                              command=self.browse_folder, bg="#3498db",
                              fg="white", cursor="hand2")
        browse_btn.pack(side=tk.RIGHT)

        # Schedule times
        schedule_frame = tk.LabelFrame(main, text="⏰ Lịch Phát Nhạc",
                                       font=("Arial", 10, "bold"), padx=10, pady=10)
        schedule_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Add time controls
        add_frame = tk.Frame(schedule_frame)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(add_frame, text="Giờ:").pack(side=tk.LEFT, padx=(0, 5))
        self.hour_var = tk.StringVar(value="12")
        hour_spin = ttk.Spinbox(add_frame, from_=0, to=23, width=5,
                                textvariable=self.hour_var, format="%02.0f")
        hour_spin.pack(side=tk.LEFT, padx=(0, 5))

        tk.Label(add_frame, text="Phút:").pack(side=tk.LEFT, padx=(0, 5))
        self.minute_var = tk.StringVar(value="00")
        minute_spin = ttk.Spinbox(add_frame, from_=0, to=59, width=5,
                                  textvariable=self.minute_var, format="%02.0f")
        minute_spin.pack(side=tk.LEFT, padx=(0, 10))

        add_btn = tk.Button(add_frame, text="➕ Thêm",
                           command=self.add_schedule, bg="#27ae60",
                           fg="white", cursor="hand2")
        add_btn.pack(side=tk.LEFT)

        # Schedule list
        list_frame = tk.Frame(schedule_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.schedule_listbox = tk.Listbox(list_frame, height=6,
                                          yscrollcommand=scrollbar.set,
                                          font=("Courier", 11))
        self.schedule_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.schedule_listbox.yview)

        remove_btn = tk.Button(schedule_frame, text="🗑️ Xóa Mục Đã Chọn",
                              command=self.remove_schedule, bg="#e74c3c",
                              fg="white", cursor="hand2")
        remove_btn.pack(pady=(5, 0))

        # Status
        status_frame = tk.LabelFrame(main, text="📊 Trạng Thái",
                                     font=("Arial", 10, "bold"), padx=10, pady=10)
        status_frame.pack(fill=tk.X, pady=(0, 15))

        self.status_label = tk.Label(status_frame, text="⏹️ Đang dừng",
                                     font=("Arial", 10), fg="red")
        self.status_label.pack()

        # Control buttons
        btn_frame = tk.Frame(main)
        btn_frame.pack(fill=tk.X)

        self.start_btn = tk.Button(btn_frame, text="▶️ Bắt Đầu",
                                   command=self.start_scheduler,
                                   bg="#27ae60", fg="white",
                                   font=("Arial", 12, "bold"),
                                   cursor="hand2", height=2)
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.stop_btn = tk.Button(btn_frame, text="⏹️ Dừng",
                                  command=self.stop_scheduler,
                                  bg="#e74c3c", fg="white",
                                  font=("Arial", 12, "bold"),
                                  cursor="hand2", height=2, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True)

    def browse_folder(self):
        """Chọn folder nhạc"""
        folder = filedialog.askdirectory(title="Chọn folder chứa nhạc")
        if folder:
            self.music_folder = folder
            self.folder_label.config(text=folder, fg="black")
            self.save_config()

    def add_schedule(self):
        """Thêm lịch phát nhạc"""
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            time_str = f"{hour:02d}:{minute:02d}"

            if time_str not in self.scheduled_times:
                self.scheduled_times.append(time_str)
                self.scheduled_times.sort()
                self.update_schedule_list()
                self.save_config()
            else:
                messagebox.showwarning("Cảnh báo", "Giờ này đã có trong lịch!")
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập giờ và phút hợp lệ!")

    def remove_schedule(self):
        """Xóa lịch đã chọn"""
        selection = self.schedule_listbox.curselection()
        if selection:
            idx = selection[0]
            del self.scheduled_times[idx]
            self.update_schedule_list()
            self.save_config()

    def update_schedule_list(self):
        """Cập nhật danh sách lịch"""
        self.schedule_listbox.delete(0, tk.END)
        for time_str in self.scheduled_times:
            self.schedule_listbox.insert(tk.END, f"  🕐 {time_str}")

    def get_random_song(self):
        """Lấy bài hát ngẫu nhiên"""
        if not self.music_folder or not os.path.exists(self.music_folder):
            return None

        extensions = ['.mp3', '.wav', '.ogg', '.flac']
        songs = []

        for ext in extensions:
            songs.extend(Path(self.music_folder).glob(f'*{ext}'))

        return random.choice(songs) if songs else None

    def play_song(self, song_path):
        """Phát nhạc"""
        try:
            mixer.music.load(str(song_path))
            mixer.music.play()

            # Đợi cho đến khi phát xong
            while mixer.music.get_busy():
                time.sleep(0.5)
                if not self.is_running:
                    mixer.music.stop()
                    break
        except Exception as e:
            print(f"Lỗi phát nhạc: {e}")

    def scheduler_loop(self):
        """Vòng lặp kiểm tra lịch"""
        while self.is_running:
            now = datetime.now()
            current_time = now.strftime('%H:%M')

            if current_time in self.scheduled_times:
                if current_time not in self.last_played or \
                   self.last_played[current_time] != now.strftime('%Y-%m-%d'):

                    song = self.get_random_song()
                    if song:
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"🎵 Đang phát: {song.name}", fg="green"))

                        self.play_song(song)

                        self.last_played[current_time] = now.strftime('%Y-%m-%d')

                        if self.is_running:
                            self.root.after(0, lambda: self.status_label.config(
                                text="✅ Đã phát xong - Chờ lịch tiếp theo", fg="blue"))

            time.sleep(5)  # Kiểm tra mỗi 5 giây để không bỏ lỡ

    def start_scheduler(self):
        """Bắt đầu scheduler"""
        if not self.music_folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn folder nhạc!")
            return

        if not self.scheduled_times:
            messagebox.showerror("Lỗi", "Vui lòng thêm ít nhất một lịch phát nhạc!")
            return

        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="▶️ Đang chạy - Chờ đến giờ phát nhạc...", fg="green")

        # Chạy scheduler trong thread riêng
        thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        thread.start()

    def stop_scheduler(self):
        """Dừng scheduler"""
        self.is_running = False
        mixer.music.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏹️ Đã dừng", fg="red")

    def save_config(self):
        """Lưu cấu hình"""
        config = {
            'music_folder': self.music_folder,
            'scheduled_times': self.scheduled_times
        }
        try:
            with open('music_scheduler_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except:
            pass

    def load_config(self):
        """Tải cấu hình"""
        try:
            if os.path.exists('music_scheduler_config.json'):
                with open('music_scheduler_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.music_folder = config.get('music_folder', '')
                    self.scheduled_times = config.get('scheduled_times', [])

                    if self.music_folder:
                        self.folder_label.config(text=self.music_folder, fg="black")
                    self.update_schedule_list()
        except:
            pass


def main():
    root = tk.Tk()
    app = MusicSchedulerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
