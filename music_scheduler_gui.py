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
import sounddevice as sd
import soundfile as sf
import numpy as np


class MusicSchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Scheduler - Hẹn Giờ Phát Nhạc")
        self.root.geometry("700x700")  # Increased size to fit all elements
        self.root.resizable(True, True)  # Allow resizing

        self.music_folder = ""
        self.scheduled_times = []
        self.is_running = False
        self.last_played = {}
        self.scheduler = BackgroundScheduler()
        self.audio_devices = []
        self.selected_device = None
        self.current_volume = 0.7  # Default volume 70%
        self.is_paused = False
        self.playback_stream = None

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

        # Initialize mixer and get audio devices
        mixer.init()
        self.detect_audio_devices()

        self.setup_ui()
        self.load_config()

    def detect_audio_devices(self):
        """Phát hiện các thiết bị âm thanh"""
        try:
            devices = sd.query_devices()
            self.device_info = []
            self.audio_devices = []

            # Get output devices only
            for idx, device in enumerate(devices):
                if device['max_output_channels'] > 0:  # Output device
                    device_name = f"{device['name']}"
                    self.audio_devices.append(device_name)
                    self.device_info.append({
                        'index': idx,
                        'name': device_name,
                        'channels': device['max_output_channels']
                    })

            # If no devices found, add default
            if not self.audio_devices:
                self.audio_devices = ["Default Audio Output"]
                self.device_info = [{'index': None, 'name': 'Default Audio Output', 'channels': 2}]
        except Exception as e:
            print(f"Error detecting audio devices: {e}")
            self.audio_devices = ["Default Audio Output"]
            self.device_info = [{'index': None, 'name': 'Default Audio Output', 'channels': 2}]

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
        main = tk.Frame(self.root, padx=20, pady=15, bg=self.colors['light'])
        main.pack(fill=tk.BOTH, expand=True)

        # Folder selection with modern style
        folder_frame = ttk.LabelFrame(main, text="📁 Folder Nhạc", padding=10)
        folder_frame.pack(fill=tk.X, pady=(0, 10))

        self.folder_label = ttk.Label(folder_frame, text="Chưa chọn folder",
                                      foreground="gray", font=("Segoe UI", 9))
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_btn = ttk.Button(folder_frame, text="Chọn Folder",
                               command=self.browse_folder)
        browse_btn.pack(side=tk.RIGHT)

        # Audio Output Selection
        audio_frame = ttk.LabelFrame(main, text="🔊 Thiết Bị Âm Thanh", padding=10)
        audio_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(audio_frame, text="Output:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 10))

        self.audio_var = tk.StringVar(value="Default Audio Output")
        # Create custom combobox style with dark text
        combo_style = ttk.Style()
        combo_style.map('TCombobox', fieldbackground=[('readonly', 'white')])
        combo_style.map('TCombobox', foreground=[('readonly', 'black')])

        self.audio_dropdown = ttk.Combobox(audio_frame,
                                          textvariable=self.audio_var,
                                          values=self.audio_devices,
                                          state="readonly",
                                          font=("Segoe UI", 9),
                                          width=30)
        self.audio_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Playback Controls
        controls_frame = ttk.LabelFrame(main, text="🎛️ Điều Khiển Phát Nhạc", padding=10)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Volume control
        vol_frame = ttk.Frame(controls_frame)
        vol_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(vol_frame, text="🔊 Volume:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 10))
        self.volume_var = tk.DoubleVar(value=70)
        self.volume_slider = ttk.Scale(vol_frame, from_=0, to=100,
                                      variable=self.volume_var,
                                      orient=tk.HORIZONTAL,
                                      command=self.on_volume_change)
        self.volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.volume_label = ttk.Label(vol_frame, text="70%", font=("Segoe UI", 9), width=4)
        self.volume_label.pack(side=tk.LEFT)

        # Playback buttons
        btn_controls = ttk.Frame(controls_frame)
        btn_controls.pack(fill=tk.X)

        self.pause_btn = ttk.Button(btn_controls, text="⏸️ Pause",
                                    command=self.toggle_pause, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = ttk.Button(btn_controls, text="⏹️ Stop",
                                   command=self.stop_song, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        # Schedule times with improved layout
        schedule_frame = ttk.LabelFrame(main, text="⏰ Lịch Phát Nhạc", padding=10)
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
        status_frame = ttk.LabelFrame(main, text="📊 Trạng Thái", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_label = tk.Label(status_frame, text="⏹️ Đang dừng",
                                     font=("Segoe UI", 10, "bold"),
                                     fg=self.colors['danger'],
                                     bg="white",
                                     relief=tk.SOLID,
                                     borderwidth=1,
                                     padx=8, pady=6)
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
                    # Get selected device index
                    selected_device_name = self.audio_var.get()
                    device_index = None
                    for dev_info in self.device_info:
                        if dev_info['name'] == selected_device_name:
                            device_index = dev_info['index']
                            break

                    # Load audio file
                    data, samplerate = sf.read(str(song))

                    # Apply volume
                    data = data * self.current_volume

                    # Enable playback controls
                    self.root.after(0, lambda: self.pause_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.stop_btn.config(state=tk.NORMAL))

                    # Play using sounddevice on selected device
                    sd.play(data, samplerate, device=device_index)
                    sd.wait()  # Wait until sound finishes

                    # Disable playback controls
                    self.root.after(0, lambda: self.pause_btn.config(state=tk.DISABLED))
                    self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

                    # Mark as played
                    self.last_played[scheduled_time] = today

                    # Update UI
                    if self.is_running:
                        self.root.after(0, lambda: self.status_label.config(
                            text="✅ Đã phát xong - Chờ lịch tiếp theo",
                            fg=self.colors['primary']))
                except Exception as e:
                    print(f"Lỗi phát nhạc: {e}")
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"❌ Lỗi phát nhạc: {str(e)[:30]}...",
                        fg=self.colors['danger']))

            threading.Thread(target=play_thread, daemon=True).start()

    def on_volume_change(self, value):
        """Callback when volume slider changes"""
        volume_percent = int(float(value))
        self.current_volume = volume_percent / 100.0
        self.volume_label.config(text=f"{volume_percent}%")

    def toggle_pause(self):
        """Pause/Resume playback"""
        if sd.get_stream().active:
            if self.is_paused:
                # Resume
                self.is_paused = False
                self.pause_btn.config(text="⏸️ Pause")
            else:
                # Pause
                self.is_paused = True
                self.pause_btn.config(text="▶️ Resume")
                sd.stop()

    def stop_song(self):
        """Stop current song"""
        sd.stop()
        self.pause_btn.config(state=tk.DISABLED, text="⏸️ Pause")
        self.stop_btn.config(state=tk.DISABLED)
        self.is_paused = False
        self.status_label.config(
            text="⏹️ Đã dừng phát nhạc",
            fg=self.colors['warning'])

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
