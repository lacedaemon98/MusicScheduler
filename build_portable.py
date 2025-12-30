"""
Script tạo phiên bản portable của Music Scheduler
Chạy script này sẽ tạo file ZIP có thể giải nén và chạy trên bất kỳ máy Windows nào
"""

import os
import shutil
import zipfile
from pathlib import Path
import PyInstaller.__main__

print("="*60)
print("🔨 BẮT ĐẦU BUILD MUSIC SCHEDULER - PORTABLE VERSION")
print("="*60)

# Bước 1: Build file .exe
print("\n[1/4] 📦 Đang build file .exe...")
PyInstaller.__main__.run([
    'music_scheduler_gui.py',
    '--name=MusicScheduler',
    '--onefile',
    '--windowed',
    '--clean',
])

# Bước 2: Tạo folder portable
print("\n[2/4] 📁 Đang tạo folder portable...")
portable_folder = Path("MusicScheduler_Portable")
if portable_folder.exists():
    shutil.rmtree(portable_folder)
portable_folder.mkdir()

# Bước 3: Copy file .exe và tạo file hướng dẫn
print("\n[3/4] 📋 Đang copy files...")

# Copy .exe
exe_source = Path("dist/MusicScheduler.exe")
if exe_source.exists():
    shutil.copy(exe_source, portable_folder / "MusicScheduler.exe")
else:
    print("❌ Lỗi: Không tìm thấy file .exe")
    exit(1)

# Tạo file hướng dẫn
readme_content = """╔═══════════════════════════════════════════════════════════╗
║          🎵 MUSIC SCHEDULER - HƯỚNG DẪN SỬ DỤNG           ║
╚═══════════════════════════════════════════════════════════╝

📖 CÁCH SỬ DỤNG:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Double-click file "MusicScheduler.exe" để chạy

2. Chọn folder chứa nhạc của bạn (MP3, WAV, OGG, FLAC)

3. Thêm giờ muốn phát nhạc:
   - Ví dụ: 12:00 (12 giờ trưa)
   - Ví dụ: 13:00 (1 giờ chiều)
   - Có thể thêm nhiều giờ

4. Nhấn nút "▶️ Bắt Đầu"

5. Phần mềm sẽ tự động:
   ✅ Chờ đến đúng giờ đã hẹn
   ✅ Phát NGẪU NHIÊN 1 bài nhạc
   ✅ Tự động dừng sau khi phát xong


⚙️ TÍNH NĂNG:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Không cần cài đặt - chạy trực tiếp
✓ Không cần cài Python hay thư viện gì cả
✓ Giao diện đơn giản, dễ sử dụng
✓ Tự động lưu cấu hình
✓ Hỗ trợ nhiều định dạng nhạc
✓ Có thể hẹn nhiều giờ khác nhau


💡 LƯU Ý:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Để phần mềm chạy liên tục, đừng tắt cửa sổ
• Có thể thu nhỏ cửa sổ xuống taskbar
• Mỗi lần hẹn giờ chỉ phát 1 bài, sau đó tự động dừng
• Phần mềm sẽ chọn bài NGẪU NHIÊN từ folder của bạn


📞 HỖ TRỢ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Nếu có vấn đề, hãy kiểm tra:
1. Folder nhạc có file nhạc chưa?
2. File nhạc có định dạng đúng không? (MP3, WAV, OGG, FLAC)
3. Đã thêm lịch phát nhạc chưa?


Version: 1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

with open(portable_folder / "📖 HƯỚNG DẪN.txt", "w", encoding="utf-8") as f:
    f.write(readme_content)

# Bước 4: Nén thành file ZIP
print("\n[4/4] 🗜️  Đang nén thành file ZIP...")
zip_filename = "MusicScheduler_Portable.zip"

if os.path.exists(zip_filename):
    os.remove(zip_filename)

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in portable_folder.rglob('*'):
        if file.is_file():
            arcname = file.relative_to(portable_folder.parent)
            zipf.write(file, arcname)

# Hoàn tất
print("\n" + "="*60)
print("✅ BUILD HOÀN TẤT!")
print("="*60)
print(f"\n📦 File ZIP: {zip_filename}")
print(f"📁 Dung lượng: {os.path.getsize(zip_filename) / 1024 / 1024:.1f} MB")
print("\n💡 Cách sử dụng:")
print("   1. Gửi file ZIP này cho ai cũng được")
print("   2. Giải nén ra")
print("   3. Chạy file MusicScheduler.exe")
print("   4. KHÔNG CẦN cài đặt gì thêm!")
print("\n" + "="*60)
