"""Dựng video dọc 9:16 (1080 x 1920) ~35 giây cho TikTok, YouTube Shorts, Reels từ mẫu mau_video.html.

Cách dùng:
    python3 tao_video.py video.html --out <ten>_6-video.mp4 [--giay-mo 7] [--giay-cong-dung 13]
                         [--giay-doi-tuong 7] [--giay-ket 8]

Kịch bản (anh chốt 17/11/2026):
    MỞ BÀI   logo + tên sản phẩm + slogan chữ to, ảnh sản phẩm phóng to dần (7 giây)
    THÂN BÀI công dụng hiện lần lượt từng ý (13 giây), rồi dùng cho con gì + đường dùng (7 giây)
    KẾT BÀI  mời nhắn tin cho trang, Follow, Like + dòng chính hãng (8 giây)
Các cảnh nối nhau bằng chuyển cảnh mờ 0,5 giây. Không chèn nhạc: lúc đăng chọn nhạc miễn phí
bản quyền trong thư viện của từng nền tảng (tránh bị chặn vì nhạc dính bản quyền).

Cách làm: mở HTML bằng Chromium, chụp từng cảnh ở 2160 x 3840 (2x) cho chữ nét, rồi ghép bằng ffmpeg
(H.264, 30 khung/giây, preset veryfast). Cần playwright + ffmpeg.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

CHUYEN = 0.5  # giây chuyển cảnh mờ


def chup_canh(html, thu_muc):
    """Chụp các khung cảnh, trả về danh sách (đường dẫn png, loại cảnh)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("LỖI: thiếu playwright. Chạy: pip install playwright --break-system-packages && playwright install chromium")
    url = "file://" + os.path.abspath(html)
    ds = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=2)

        def chup(ten, hash_):
            pg.goto(url + "#" + hash_)
            pg.reload()  # chạy lại script đọc #canh
            pg.wait_for_load_state("networkidle")
            pg.evaluate("document.fonts.ready")
            hong = pg.evaluate("() => [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'))")
            if hong:
                sys.exit(f"LỖI: ảnh không tải được: {hong}")
            f = os.path.join(thu_muc, ten + ".png")
            pg.screenshot(path=f)
            return f

        ds.append((chup("mo", "canh=mo"), "mo"))
        so_y = pg.evaluate("() => document.querySelectorAll('#cd li').length")
        if so_y == 0:
            sys.exit("LỖI: cảnh công dụng chưa có ý nào.")
        for k in range(1, so_y + 1):
            ds.append((chup(f"cd{k}", f"canh=cd&hien={k}"), "cd"))
        ds.append((chup("dt", "canh=dt"), "dt"))
        ds.append((chup("ket", "canh=ket"), "ket"))
        chu = pg.evaluate("() => document.documentElement.innerHTML")
        b.close()
    if "{{" in chu.split("<script")[0].split("-->", 1)[-1]:
        print("CẢNH BÁO: video còn chỗ {{...}} chưa điền nội dung.")
    if any(x in chu for x in ("0988", "370 387", "Tô Hiệu")):
        print("CẢNH BÁO: video đăng mạng xã hội không được có số điện thoại, địa chỉ — xoá khỏi HTML.")
    return ds


def main():
    p = argparse.ArgumentParser()
    p.add_argument("html")
    p.add_argument("--out", required=True)
    p.add_argument("--giay-mo", type=float, default=7)
    p.add_argument("--giay-cong-dung", type=float, default=13)
    p.add_argument("--giay-doi-tuong", type=float, default=7)
    p.add_argument("--giay-ket", type=float, default=8)
    a = p.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("LỖI: chưa có ffmpeg.")

    with tempfile.TemporaryDirectory() as tm:
        canh = chup_canh(a.html, tm)
        so_cd = sum(1 for _, l in canh if l == "cd")
        thoi_luong = {"mo": a.giay_mo, "cd": a.giay_cong_dung / so_cd, "dt": a.giay_doi_tuong, "ket": a.giay_ket}

        vao, loc = [], []
        for i, (f, loai) in enumerate(canh):
            d = thoi_luong[loai] + (CHUYEN if i < len(canh) - 1 else 0)
            vao += ["-loop", "1", "-framerate", "30", "-t", f"{d:.3f}", "-i", f]
            if loai == "mo":
                # phóng to dần 1,00 -> 1,05 về phía ảnh sản phẩm (hiệu ứng Ken Burns), giữ logo và tên ở trên; chụp gốc 2160 nên không vỡ
                n = int(round(d * 30))
                loc.append(f"[{i}]zoompan=z='1+0.05*on/{n}':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*0.35'"
                           f":d=1:s=1080x1920:fps=30,setsar=1[v{i}]")
            else:
                loc.append(f"[{i}]scale=1080:1920:flags=lanczos,setsar=1,fps=30[v{i}]")
        truoc, moc = "v0", 0.0
        for i in range(1, len(canh)):
            moc += thoi_luong[canh[i - 1][1]]
            sau = "out" if i == len(canh) - 1 else f"x{i}"
            them = ",format=yuv420p" if i == len(canh) - 1 else ""
            loc.append(f"[{truoc}][v{i}]xfade=transition=fade:duration={CHUYEN}:offset={moc:.3f}{them}[{sau}]")
            truoc = sau
        lenh = ["ffmpeg", "-y", "-loglevel", "error", *vao, "-filter_complex", ";".join(loc), "-map", "[out]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-movflags", "+faststart", a.out]
        try:
            subprocess.run(lenh, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(f"LỖI: ffmpeg không ghép được video ({e}).")
    tong = sum(thoi_luong[l] for _, l in canh)
    print(f"OK: {a.out} — 1080x1920, khoảng {tong:.0f} giây, {len(canh)} khung cảnh, chưa có nhạc.")


if __name__ == "__main__":
    main()
