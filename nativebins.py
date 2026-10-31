import os
import re
import certifi
import select
import shutil
import subprocess
import threading
import time

os.environ["SSL_CERT_FILE"] = certifi.where()

STEGO_LINE_MAX = 2047
STEGO_BYTES_PER_BYTE = 24
PICK_REQUEST = 7311

AUDIO_FORMATS = ("mp3", "wav", "m4a", "opus", "ogg", "flac", "aac")
VIDEO_FORMATS = ("mp4", "mkv")

AUDIO_CODECS = {
    "mp3": ["-c:a", "libmp3lame", "-b:a", "192k"],
    "wav": ["-c:a", "pcm_s16le"],
    "m4a": ["-c:a", "aac", "-b:a", "192k"],
    "opus": ["-c:a", "libopus", "-b:a", "128k"],
    "ogg": ["-c:a", "libvorbis", "-q:a", "5"],
    "flac": ["-c:a", "flac"],
    "aac": ["-c:a", "aac", "-b:a", "192k"],
}

DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
TIME_RE = re.compile(r"time=\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def native_dir():
    try:
        from jnius import autoclass

        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        return str(activity.getApplicationInfo().nativeLibraryDir)
    except Exception:
        return None


def native_bin(lib, cmd=None):
    folder = native_dir()
    if folder:
        path = os.path.join(folder, f"lib{lib}.so")
        if os.path.isfile(path):
            return path
    return shutil.which(cmd or lib)


def prepare_ffmpeg(base):
    exe = native_bin("ffmpeg")
    if not exe:
        return None
    folder = os.path.join(base, "bin")
    os.makedirs(folder, exist_ok=True)
    link = os.path.join(folder, "ffmpeg")
    if os.path.lexists(link):
        os.remove(link)
    os.symlink(exe, link)
    return folder


def stego_max_secret(cover):
    return (STEGO_LINE_MAX - len(cover.encode())) // STEGO_BYTES_PER_BYTE


def one_line(text):
    return " ".join(text.splitlines()).strip()


class Stego:
    MENU = "3. Выход\n> ".encode()
    END = "\n\n1. Зашифровать"

    def __init__(self, path):
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.fd = self.proc.stdout.fileno()
        self.expect(self.MENU)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def expect(self, marker, timeout=10):
        end = time.monotonic() + timeout
        buf = b""
        while not buf.endswith(marker):
            left = end - time.monotonic()
            if left <= 0 or not select.select([self.fd], [], [], left)[0]:
                raise TimeoutError("бинарник не отвечает")
            chunk = os.read(self.fd, 65536)
            if not chunk:
                raise EOFError("бинарник завершился")
            buf += chunk
        return buf.decode("utf-8", "replace")

    def send(self, text):
        self.proc.stdin.write(text.encode() + b"\n")

    def encrypt(self, cover, secret):
        cover, secret = one_line(cover), one_line(secret)
        limit = stego_max_secret(cover)
        if len(secret.encode()) > limit:
            raise ValueError(
                f"слишком длинно: при такой маскировке максимум {limit} байт "
                "секрета (кириллица = 2 байта на букву)"
            )
        self.send("1")
        self.expect("Маскировка: ".encode())
        self.send(cover)
        self.expect("Внутри: ".encode())
        self.send(secret)
        out = self.expect(self.MENU)
        return out.split("Результат: ", 1)[1].rsplit(self.END, 1)[0]

    def decrypt(self, text):
        text = one_line(text)
        if len(text.encode()) > STEGO_LINE_MAX:
            raise ValueError(f"текст длиннее {STEGO_LINE_MAX} байт, бинарник его не прочитает")
        self.send("2")
        self.expect("Маскировка: ".encode())
        self.send(text)
        out = self.expect(self.MENU)
        return out.split("\nВнутри: ", 1)[1].rsplit(self.END, 1)[0]

    def close(self):
        try:
            self.send("3")
            self.proc.wait(timeout=2)
        except Exception:
            self.proc.kill()
        finally:
            for pipe in (self.proc.stdin, self.proc.stdout):
                try:
                    pipe.close()
                except Exception:
                    pass


def seconds_of(match):
    return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))


def clock(sec):
    sec = int(sec)
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def silent_remove(path):
    try:
        os.remove(path)
    except OSError:
        pass


def unique_path(path):
    root, ext = os.path.splitext(path)
    candidate = path
    i = 1
    while os.path.exists(candidate):
        candidate = f"{root} ({i}){ext}"
        i += 1
    return candidate


def run_ffmpeg(ffmpeg, args, on_status, cancelled, label):
    cmd = [ffmpeg, "-hide_banner", "-nostdin", "-y"] + args
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
    )
    fd = proc.stdout.fileno()
    total = None
    tail = b""
    recent = []
    try:
        while True:
            if cancelled():
                proc.kill()
                proc.wait()
                raise InterruptedError
            if not select.select([fd], [], [], 0.3)[0]:
                if proc.poll() is not None:
                    break
                continue
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            parts = re.split(rb"[\r\n]+", tail + chunk)
            tail = parts.pop()
            for part in parts:
                line = part.decode("utf-8", "replace").strip()
                if not line:
                    continue
                recent = (recent + [line])[-6:]
                if total is None:
                    m = DURATION_RE.search(line)
                    if m:
                        total = seconds_of(m)
                m = TIME_RE.search(line)
                if m:
                    cur = seconds_of(m)
                    if total:
                        on_status(f"{label}: {min(99, int(cur * 100 / total))}%")
                    else:
                        on_status(f"{label}: {clock(cur)}")
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        try:
            proc.stdout.close()
        except Exception:
            pass
    if proc.returncode != 0:
        raise RuntimeError(" | ".join(recent[-2:]) or f"ffmpeg код {proc.returncode}")


def run_attempts(ffmpeg, attempts, out, on_status, cancelled, label):
    error = None
    for args in attempts:
        try:
            run_ffmpeg(ffmpeg, args, on_status, cancelled, label)
            return out
        except InterruptedError:
            silent_remove(out)
            raise
        except RuntimeError as e:
            error = e
            silent_remove(out)
    raise error


def convert_media(ffmpeg, src, out_dir, fmt, on_status, cancelled, label="Конвертирую"):
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    out = unique_path(os.path.join(out_dir, f"{base}.{fmt}"))
    if fmt in AUDIO_FORMATS:
        attempts = [
            ["-i", src, "-vn", "-map", "0:a:0"] + AUDIO_CODECS[fmt] + [out],
            ["-i", src, "-vn", out],
        ]
    else:
        flags = ["-movflags", "+faststart"] if fmt == "mp4" else []
        maps = ["-map", "0:v:0", "-map", "0:a?", "-sn"]
        attempts = [
            ["-i", src] + maps + ["-c", "copy"] + flags + [out],
            ["-i", src] + maps
            + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "192k"]
            + flags + [out],
        ]
    return run_attempts(ffmpeg, attempts, out, on_status, cancelled, label)


def merge_media(ffmpeg, video, audio, out_dir, fmt, on_status, cancelled, label="Склеиваю"):
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(video))[0]
    out = unique_path(os.path.join(out_dir, f"{base}_merged.{fmt}"))
    flags = ["-movflags", "+faststart"] if fmt == "mp4" else []
    maps = ["-map", "0:v:0", "-map", "1:a:0", "-shortest"]
    head = ["-i", video, "-i", audio] + maps
    attempts = [
        head + ["-c", "copy"] + flags + [out],
        head + ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"] + flags + [out],
        head
        + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "192k"]
        + flags + [out],
    ]
    return run_attempts(ffmpeg, attempts, out, on_status, cancelled, label)


def display_name(resolver, uri):
    cursor = resolver.query(uri, None, None, None, None)
    if cursor is None:
        return None
    try:
        idx = cursor.getColumnIndex("_display_name")
        if idx >= 0 and cursor.moveToFirst():
            return str(cursor.getString(idx))
    finally:
        cursor.close()
    return None


def real_path_from_uri(uri, context):
    from jnius import autoclass

    if str(uri.getScheme()) == "file":
        return str(uri.getPath())
    DocumentsContract = autoclass("android.provider.DocumentsContract")
    if not DocumentsContract.isDocumentUri(context, uri):
        return None
    authority = str(uri.getAuthority())
    doc = str(DocumentsContract.getDocumentId(uri))
    if authority == "com.android.externalstorage.documents":
        volume, _, rel = doc.partition(":")
        base = "/storage/emulated/0" if volume == "primary" else "/storage/" + volume
        return os.path.join(base, rel)
    if authority == "com.android.providers.downloads.documents" and doc.startswith("raw:"):
        return doc[4:]
    return None


def resolve_uri(uri, cache_dir):
    try:
        from jnius import autoclass

        context = autoclass("org.kivy.android.PythonActivity").mActivity
        path = real_path_from_uri(uri, context)
        if path and os.path.isfile(path) and os.access(path, os.R_OK):
            return path, None
        resolver = context.getContentResolver()
        name = display_name(resolver, uri) or "file"
        name = re.sub(r'[\\/:*?"<>|]+', "_", name)
        os.makedirs(cache_dir, exist_ok=True)
        dst = unique_path(os.path.join(cache_dir, name))
        pfd = resolver.openFileDescriptor(uri, "r")
        fd = pfd.detachFd()
        with os.fdopen(fd, "rb") as src, open(dst, "wb") as out:
            shutil.copyfileobj(src, out, 1 << 20)
        return dst, None
    except Exception as e:
        return None, str(e)


def pick_system_file(callback, cache_dir):
    try:
        from jnius import autoclass
        from android import activity

        Intent = autoclass("android.content.Intent")
        context = autoclass("org.kivy.android.PythonActivity").mActivity
    except Exception:
        return False

    def on_result(request, result, intent):
        if request != PICK_REQUEST:
            return
        try:
            activity.unbind(on_activity_result=on_result)
        except Exception:
            pass
        if result != -1 or intent is None or intent.getData() is None:
            callback(None, None)
            return
        uri = intent.getData()
        threading.Thread(
            target=lambda: callback(*resolve_uri(uri, cache_dir)), daemon=True
        ).start()

    try:
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("*/*")
        activity.bind(on_activity_result=on_result)
        context.startActivityForResult(intent, PICK_REQUEST)
        return True
    except Exception:
        try:
            activity.unbind(on_activity_result=on_result)
        except Exception:
            pass
        return False


def yt_format(height, codec, ai):
    sr = "" if ai else "[format_id!*=-sr]"
    return (
        f"bestvideo[vcodec*={codec}][height<={height}]{sr}+bestaudio[format_id!*=-sr]"
        f"/best[height<={height}]{sr}"
    )


class SilentLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


def download_python(url, height, codec, ai, fmt, path, ffmpeg_dir, on_status, cancelled):
    import yt_dlp
    from yt_dlp.utils import DownloadCancelled

    audio = fmt in AUDIO_FORMATS

    def hook(d):
        if cancelled():
            raise DownloadCancelled()
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes") or 0
            pct = f"{done * 100 / total:.0f}%" if total else "..."
            on_status(f"Качаю: {pct}")
        elif d.get("status") == "finished":
            on_status("Обрабатываю..." if audio else "Склеиваю...")

    opts = {
        "paths": {"home": path},
        "outtmpl": "%(title)s.%(ext)s",
        "ffmpeg_location": ffmpeg_dir,
        "progress_hooks": [hook],
        "logger": SilentLogger(),
        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
        "cachedir": False,
    }
    if audio:
        opts["format"] = "bestaudio/best" if ai else "bestaudio[format_id!*=-sr]/bestaudio/best"
    else:
        opts["format"] = yt_format(height, codec, ai)
        opts["merge_output_format"] = fmt

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    try:
        src = info["requested_downloads"][0]["filepath"]
    except (KeyError, IndexError, TypeError):
        return path
    if audio and not src.lower().endswith("." + fmt):
        out = convert_media(
            os.path.join(ffmpeg_dir, "ffmpeg"), src, path, fmt, on_status, cancelled
        )
        silent_remove(src)
        return out
    return src
