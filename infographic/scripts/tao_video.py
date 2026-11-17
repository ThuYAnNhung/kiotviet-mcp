"""Ghép 4 ảnh mạng xã hội (ảnh 2–5) thành video trình chiếu dọc 9:16 cho TikTok, YouTube Shorts, Reels.

Cách dùng:
    python3 tao_video.py <ten>_2-mxh-bia.jpg <ten>_3-...jpg <ten>_4-...jpg <ten>_5-...jpg \
        --out <ten>_6-video-trinh-chieu.mp4 [--giay 4] [--chuyen 0.5]

Mỗi ảnh hiện --giay giây, chuyển cảnh mờ --chuyen giây, 1080 x 1920, 30 khung/giây, H.264.
Không chèn nhạc: lúc đăng chọn nhạc miễn phí bản quyền trong thư viện của từng nền tảng
(tránh bị chặn vì nhạc dính bản quyền). Cần ffmpeg.
"""
import argparse
import shutil
import subprocess
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument("anh", nargs="+")
    p.add_argument("--out", required=True)
    p.add_argument("--giay", type=float, default=4.0)
    p.add_argument("--chuyen", type=float, default=0.5)
    a = p.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("LỖI: chưa có ffmpeg.")
    n = len(a.anh)
    if n < 2:
        sys.exit("LỖI: cần ít nhất 2 ảnh.")

    vao, loc = [], []
    for i, f in enumerate(a.anh):
        vao += ["-loop", "1", "-t", str(a.giay + a.chuyen), "-i", f]
        loc.append(f"[{i}]scale=1080:1920,setsar=1,fps=30[v{i}]")
    truoc = "v0"
    for i in range(1, n):
        sau = "out" if i == n - 1 else f"x{i}"
        them = ",format=yuv420p" if i == n - 1 else ""
        loc.append(f"[{truoc}][v{i}]xfade=transition=fade:duration={a.chuyen}:offset={a.giay * i}{them}[{sau}]")
        truoc = sau
    lenh = ["ffmpeg", "-y", "-loglevel", "error", *vao, "-filter_complex", ";".join(loc), "-map", "[out]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart", a.out]
    try:
        subprocess.run(lenh, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"LỖI: ffmpeg không ghép được video ({e}).")
    tong = a.giay * n + a.chuyen
    print(f"OK: {a.out} — 1080x1920, khoảng {tong:.1f} giây, chưa có nhạc.")


if __name__ == "__main__":
    main()
