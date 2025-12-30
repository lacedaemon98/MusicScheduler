#!/usr/bin/env python3
"""
Music Scheduler - Phần mềm hẹn giờ phát nhạc
Có thể build thành .exe cho Windows
Version 2.0 - Improved with APScheduler and better UI
"""

import os
import random
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pygame import mixer
import json
from apscheduler.schedulers.background import BackgroundScheduler
from ttkthemes import ThemedStyle


class MusicSchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Scheduler - Hẹn Giờ Phát Nhạc")
        self.root.geometry("650x550")
        self.root.resizable(False, False)

        self.music_folder = ""
        self.scheduled_times = []
        self.is_running = False
        self.last_played = {}
        self.scheduler = BackgroundScheduler()

        # Apply modern theme
        self.style = ThemedStyle(root)
        self.style.set_theme("arc")  # Modern, clean theme

        # Custom colors
        self.colors = {
            'primary': '#3498db',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'dark': '#2c3e50',
            'light': '#ecf0f1',
            'warning': '#f39c12'
        }

        mixer.init()

        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """Thiết lập giao diện"""
        # Header with gradient effect
        header = tk.Frame(self.root, bg=self.colors['dark'], height=70)
        header.pack(fill=tk.X)

        title = tk.Label(header, text="🎵 Music Scheduler",
                        font=("Segoe UI", 20, "bold"),
                        bg=self.colors['dark'], fg="white")
        title.pack(pady=20)

        # Main container
        main = tk.Frame(self.root, padx=25, pady=20, bg=self.colors['light'])
        main.pack(fill=tk.BOTH, expand=True)

        # Folder selection with modern style
        folder_frame = ttk.LabelFrame(main, text="📁 Folder Nhạc", padding=15)
        folder_frame.pack(fill=tk.X, pady=(0, 15))

        self.folder_label = ttk.Label(folder_frame, text="Chưa chọn folder",
                                      foreground="gray", font=("Segoe UI", 9))
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_btn = ttk.Button(folder_frame, text="Chọn Folder",
                               command=self.browse_folder)
        browse_btn.pack(side=tk.RIGHT)

        # Schedule times with improved layout
        schedule_frame = ttk.LabelFrame(main, text="⏰ Lịch Phát Nhạc", padding=15)
        schedule_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Add time controls with better spacing
        add_frame = ttk.Frame(schedule_frame)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(add_frame, text="Giờ:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.hour_var = tk.StringVar(value="12")
        hour_spin = ttk.Spinbox(add_frame, from_=0, to=23, width=7,
                                textvariable=self.hour_var, format="%02.0f",
                                font=("Segoe UI", 10))
        hour_spin.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(add_frame, text="Phút:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.minute_var = tk.StringVar(value="00")
        minute_spin = ttk.Spinbox(add_frame, from_=0, to=59, width=7,
                                  textvariable=self.minute_var, format="%02.0f",
                                  font=("Segoe UI", 10))
        minute_spin.pack(side=tk.LEFT, padx=(0, 15))

        add_btn = ttk.Button(add_frame, text="➕ Thêm Lịch",
                            command=self.add_schedule)
        add_btn.pack(side=tk.LEFT)

        # Schedule list with better styling
        list_frame = ttk.Frame(schedule_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.schedule_listbox = tk.Listbox(list_frame, height=6,
                                          yscrollcommand=scrollbar.set,
                                          font=("Consolas", 11),
                                          selectmode=tk.SINGLE,
                                          relief=tk.FLAT,
                                          bg="white",
                                          highlightthickness=1,
                                          highlightcolor=self.colors['primary'])
        self.schedule_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.schedule_listbox.yview)

        remove_btn = ttk.Button(schedule_frame, text="🗑️ Xóa Mục Đã Chọn",
                               command=self.remove_schedule)
        remove_btn.pack()

        # Status with better visibility
        status_frame = ttk.LabelFrame(main, text="📊 Trạng Thái", padding=15)
        status_frame.pack(fill=tk.X, pady=(0, 15))

        self.status_label = tk.Label(status_frame, text="⏹️ Đang dừng",
                                     font=("Segoe UI", 11, "bold"),
                                     fg=self.colors['danger'],
                                     bg="white",
                                     relief=tk.SOLID,
                                     borderwidth=1,
                                     padx=10, pady=8)
        self.status_label.pack(fill=tk.X)

        # Control buttons with modern styling
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X)

        # Create custom button style
        style = ttk.Style()
        style.configure('Start.TButton', font=('Segoe UI', 11, 'bold'))
        style.configure('Stop.TButton', font=('Segoe UI', 11, 'bold'))

        self.start_btn = ttk.Button(btn_frame, text="▶️ Bắt Đầu",
                                    command=self.start_scheduler,
                                    style='Start.TButton')
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.stop_btn = ttk.Button(btn_frame, text="⏹️ Dừng",
                                   command=self.stop_scheduler,
                                   style='Stop.TButton',
                                   state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True)

    def browse_folder(self):
        """Chọn folder nhạc"""
        folder = filedialog.askdirectory(title="Chọn folder chứa nhạc")
        if folder:
            self.music_folder = folder
            self.folder_label.config(text=folder, foreground="black")
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

                # Update scheduler if running
                if self.is_running:
                    self.update_scheduler_jobs()
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

            # Update scheduler if running
            if self.is_running:
                self.update_scheduler_jobs()

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

    def play_song_job(self, scheduled_time):
        """Job để phát nhạc - được gọi bởi APScheduler"""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')

        # Kiểm tra xem đã phát trong ngày chưa
        if scheduled_time in self.last_played and self.last_played[scheduled_time] == today:
            return

        song = self.get_random_song()
        if song:
            # Update UI
            self.root.after(0, lambda: self.status_label.config(
                text=f"🎵 Đang phát: {song.name}",
                fg=self.colors['success']))

            # Play song in a separate thread to not block scheduler
            def play_thread():
                try:
                    mixer.music.load(str(song))
                    mixer.music.play()

                    # Wait until song finishes
                    while mixer.music.get_busy():
                        if not self.is_running:
                            mixer.music.stop()
                            break
                        threading.Event().wait(0.5)

                    # Mark as played
                    self.last_played[scheduled_time] = today

                    # Update UI
                    if self.is_running:
                        self.root.after(0, lambda: self.status_label.config(
                            text="✅ Đã phát xong - Chờ lịch tiếp theo",
                            fg=self.colors['primary']))
                except Exception as e:
                    print(f"Lỗi phát nhạc: {e}")

            threading.Thread(target=play_thread, daemon=True).start()

    def update_scheduler_jobs(self):
        """Cập nhật các jobs trong scheduler"""
        # Xóa tất cả jobs cũ
        self.scheduler.remove_all_jobs()

        # Thêm jobs mới
        for time_str in self.scheduled_times:
            hour, minute = map(int, time_str.split(':'))
            self.scheduler.add_job(
                func=lambda t=time_str: self.play_song_job(t),
                trigger='cron',
                hour=hour,
                minute=minute,
                id=f'play_{time_str}',
                replace_existing=True
            )

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
        self.status_label.config(
            text="▶️ Đang chạy - Chờ đến giờ phát nhạc...",
            fg=self.colors['success'])

        # Start APScheduler
        self.update_scheduler_jobs()
        if not self.scheduler.running:
            self.scheduler.start()

    def stop_scheduler(self):
        """Dừng scheduler"""
        self.is_running = False
        mixer.music.stop()

        # Stop scheduler
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.scheduler = BackgroundScheduler()  # Create new instance for next start

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏹️ Đã dừng", fg=self.colors['danger'])

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
                        self.folder_label.config(text=self.music_folder, foreground="black")
                    self.update_schedule_list()
        except:
            pass


def main():
    root = tk.Tk()
    app = MusicSchedulerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
