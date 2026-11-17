"""Dựng video dọc 9:16 (1080 x 1920) 30 giây có GIỌNG ĐỌC tiếng Việt + PHỤ ĐỀ chạy liên tục.

Kịch bản (anh chốt 17/11/2026 lần 4):
    0–3 s    HOOK: câu hỏi về sản phẩm chữ to, giật nảy (vd. "Sát trùng nano bạc có thể làm được gì?")
    3–25 s   cứ 3 giây đổi cảnh: xịt thuốc, pha thuốc, đàn heo/gà/bò, con vật ốm mệt...;
             phụ đề + giọng đọc nói liên tục về thành phần, công dụng
    25–30 s  KẾT: mời nhắn tin cho An Nhung để được tư vấn, Follow, Like + dòng chính hãng/SĐK
             (không số điện thoại – anh giữ quy tắc 17/11)
Không chèn nhạc: lúc đăng chọn nhạc miễn phí bản quyền của nền tảng, để nhỏ dưới giọng đọc.

Cách dùng (trong thư mục làm việc đã chạy chuan_bi.py, có sp.png + nen_chim.png):
    python3 tao_video_30s.py kich_ban.json --out <ten>_6-video.mp4

kich_ban.json:
{
  "anh_san_pham": "sp.png", "nha_san_xuat": "CP ...", "sdk": "VA-300",
  "canh": [
    {"loai": "hook", "bd": 0, "kt": 3, "chu": "SÁT TRÙNG <span class=vang>NANO BẠC</span> LÀM ĐƯỢC GÌ?", "doc": "Sát trùng nano bạc có thể làm được gì?"},
    {"bd": 3, "kt": 6, "chu": "Nano Bạc + *Nano *Đồng", "doc": "...", "hinh": [{"ky": "🐖", "x": 100, "y": 200, "co": 260, "kieu": "chay"}],
     "clip": "clips/heo.mp4"},        # tuỳ chọn: video quay thật làm nền cảnh này
    ...
    {"loai": "ket", "bd": 25, "kt": 30, "moi": "Nhắn tin cho An Nhung để được tư vấn", "doc": "..."}
  ]
}
  - "chu": phụ đề hiện trên màn hình; từ có dấu * đứng trước được tô vàng.
  - "doc": câu giọng đọc (viết số bằng chữ, tên nước ngoài phiên âm: "Niu cát xơn").
  - "hinh": biểu tượng Noto Emoji (hoặc "SP" = ảnh sản phẩm); kieu: chay | bay | om | diet | xit | zoom.
  - "so" / "so_phu": thẻ số to (liều pha) giữa màn hình.

Giọng đọc: Piper vi_VN-vais1000-medium chạy bằng sherpa-onnx==1.13.8 (bản 2.x lỗi tiếng Việt), tự tải
từ GitHub về ~/.cache/annhung-tts. Có file giọng anh tự thu cho cảnh nào thì thêm "giong": "thu_am/canh3.wav".
Ra kèm <ten>.srt (phụ đề) để up lên YouTube/Facebook nếu cần.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

import numpy as np

FPS = 30
SR = 22050
GIONG = "vits-piper-vi_VN-vais1000-medium"
URL_GIONG = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{GIONG}.tar.bz2"


def tai_giong():
    goc = os.path.expanduser("~/.cache/annhung-tts")
    d = os.path.join(goc, GIONG)
    if not os.path.isdir(d):
        os.makedirs(goc, exist_ok=True)
        tep = os.path.join(goc, "g.tar.bz2")
        print("Đang tải giọng đọc tiếng Việt (~67 MB)...")
        urllib.request.urlretrieve(URL_GIONG, tep)
        with tarfile.open(tep) as t:
            t.extractall(goc)
        os.remove(tep)
    return d


def tao_tts():
    try:
        import sherpa_onnx
    except ImportError:
        sys.exit("LỖI: thiếu sherpa-onnx. Chạy: pip install sherpa-onnx==1.13.8 soundfile --break-system-packages")
    d = tai_giong()
    onnx = [f for f in os.listdir(d) if f.endswith(".onnx")][0]
    cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=os.path.join(d, onnx), tokens=os.path.join(d, "tokens.txt"),
                                                   data_dir=os.path.join(d, "espeak-ng-data")), num_threads=4))
    return sherpa_onnx.OfflineTts(cfg)


def doc(tts, cau, toc):
    a = tts.generate(cau, sid=0, speed=toc)
    s = np.array(a.samples, dtype="float32")
    if not len(s):
        sys.exit(f"LỖI: giọng đọc không tạo được câu '{cau}' (sherpa-onnx phải là bản 1.13.8).")
    if a.sample_rate != SR:
        from scipy.signal import resample_poly
        s = resample_poly(s, SR, a.sample_rate).astype("float32")
    return s


def doc_file(tep):
    import soundfile as sf
    s, sr = sf.read(tep, dtype="float32", always_2d=True)
    s = s.mean(axis=1)
    if sr != SR:
        from scipy.signal import resample_poly
        s = resample_poly(s, SR, sr).astype("float32")
    return s


def lam_giong(kb, toc_goc, thu_muc):
    """Tạo giọng từng cảnh, đặt đúng mốc thời gian; câu dài quá cảnh thì đọc nhanh dần (tối đa 1,35)."""
    tong = kb["canh"][-1]["kt"]
    bang = np.zeros(int(tong * SR) + SR, dtype="float32")
    tts = None
    for c in kb["canh"]:
        L = c["kt"] - c["bd"]
        if c.get("giong"):
            s = doc_file(os.path.join(thu_muc, c["giong"]))
        elif c.get("doc"):
            tts = tts or tao_tts()
            toc = toc_goc
            s = doc(tts, c["doc"], toc)
            while len(s) / SR > L - 0.25 and toc < 1.35:
                toc = round(toc + 0.05, 2)
                s = doc(tts, c["doc"], toc)
            if len(s) / SR > L - 0.15:
                print(f"CẢNH BÁO: câu đọc cảnh {c['bd']}–{c['kt']}s dài {len(s)/SR:.1f}s, rút ngắn câu 'doc'.")
        else:
            continue
        s = s / max(1e-6, np.abs(s).max()) * 0.9
        c["giay_doc"] = round(len(s) / SR, 2)
        i = int((c["bd"] + 0.12) * SR)
        bang[i:i + len(s)] += s[: len(bang) - i]
        print(f"  giọng {c['bd']:>4}–{c['kt']}s: {c['giay_doc']}s")
    return bang[: int(tong * SR)]


def chup_khung(html, kb, thu_muc_khung, trong_suot):
    from playwright.sync_api import sync_playwright
    tong = kb["canh"][-1]["kt"]
    n = int(round(tong * FPS))
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.add_init_script("window.KICH_BAN = " + json.dumps(kb, ensure_ascii=False) + ";")
        pg.goto("file://" + os.path.abspath(html))
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        hong = pg.evaluate("() => [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'))")
        if hong:
            sys.exit(f"LỖI: ảnh không tải được: {hong}")
        for k in range(n):
            pg.evaluate(f"ve({k / FPS:.4f})")
            pg.screenshot(path=os.path.join(thu_muc_khung, f"{k:05d}.png"), omit_background=trong_suot)
        tran = pg.evaluate("""() => [...document.querySelectorAll('.phu-de div')].filter(d => d.getBoundingClientRect().bottom > 1600)
                               .map(d => d.innerText.slice(0, 30))""")
        b.close()
    if tran:
        print("CẢNH BÁO: phụ đề xuống quá thấp (TikTok/Reels che đáy) — rút ngắn chữ:", tran)
    return n


def nen_video(kb, thu_muc, tam):
    """Ghép nền: cảnh có clip thì dùng clip (cắt 9:16), cảnh khác để đen (lớp vẽ phủ kín)."""
    doan = []
    for k, c in enumerate(kb["canh"]):
        L = c["kt"] - c["bd"]
        f = os.path.join(tam, f"nen{k}.mp4")
        if c.get("clip"):
            src = os.path.join(thu_muc, c["clip"])
            vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", src, "-t", str(L), "-an",
                            "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", f], check=True)
        else:
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=black:s=1080x1920:r=30:d={L}",
                            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", f], check=True)
        doan.append(f)
    ds = os.path.join(tam, "ds.txt")
    open(ds, "w").write("".join(f"file '{f}'\n" for f in doan))
    out = os.path.join(tam, "nen.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", ds, "-c", "copy", out], check=True)
    return out


def ghi_srt(kb, out):
    def tg(x):
        ms = int(round(x * 1000)); return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"
    dong = []
    for c in kb["canh"]:
        chu = c.get("chu") or c.get("moi") or ""
        chu = re.sub(r"<[^>]+>", "", chu).replace("*", "")
        if chu:
            dong.append(f"{len(dong)+1}\n{tg(c['bd'])} --> {tg(c['kt'])}\n{chu}\n")
    open(out, "w", encoding="utf-8").write("\n".join(dong))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kich_ban")
    p.add_argument("--out", required=True)
    p.add_argument("--html", default=None, help="mặc định: mau_video_30s.html cạnh kich_ban.json")
    p.add_argument("--toc", type=float, default=1.1, help="tốc độ đọc (1.0 = chuẩn)")
    a = p.parse_args()
    thu_muc = os.path.dirname(os.path.abspath(a.kich_ban))
    html = a.html or os.path.join(thu_muc, "mau_video_30s.html")
    kb = json.load(open(a.kich_ban, encoding="utf-8"))
    for k in range(1, len(kb["canh"])):
        if abs(kb["canh"][k]["bd"] - kb["canh"][k - 1]["kt"]) > 1e-6:
            sys.exit(f"LỖI: cảnh {k} bắt đầu {kb['canh'][k]['bd']}s không nối tiếp cảnh trước.")
    co_clip = any(c.get("clip") for c in kb["canh"])

    tam = tempfile.mkdtemp()
    try:
        print("1/4 Giọng đọc...")
        giong = lam_giong(kb, a.toc, thu_muc)
        import soundfile as sf
        wav = os.path.join(tam, "giong.wav")
        sf.write(wav, giong, SR, subtype="PCM_16")
        print("2/4 Chụp khung hình...")
        khung = os.path.join(tam, "khung"); os.makedirs(khung)
        chup_khung(html, kb, khung, co_clip)
        print("3/4 Ghép video...")
        anh = ["-framerate", str(FPS), "-i", os.path.join(khung, "%05d.png")]
        enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS),
               "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest"]
        if co_clip:
            nen = nen_video(kb, thu_muc, tam)
            cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", nen, *anh, "-i", wav,
                   "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto[v]", "-map", "[v]", "-map", "2:a", *enc, a.out]
        else:
            cmd = ["ffmpeg", "-loglevel", "error", "-y", *anh, "-i", wav, "-map", "0:v", "-map", "1:a", *enc, a.out]
        subprocess.run(cmd, check=True)
        print("4/4 Phụ đề .srt...")
        ghi_srt(kb, os.path.splitext(a.out)[0] + ".srt")
    finally:
        shutil.rmtree(tam, ignore_errors=True)
    print(f"OK: {a.out} — 1080x1920, {kb['canh'][-1]['kt']} giây, {len(kb['canh'])} cảnh, có giọng đọc, chưa có nhạc"
          + (" (có clip quay thật)" if co_clip else " (cảnh minh hoạ)"))


if __name__ == "__main__":
    main()
