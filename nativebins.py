import os
import certifi
import select
import shutil
import subprocess
import time

os.environ["SSL_CERT_FILE"] = certifi.where()

STEGO_LINE_MAX = 2047
STEGO_BYTES_PER_BYTE = 24


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


def download_python(url, height, codec, ai, path, ffmpeg_bin, on_status, cancelled):
    import yt_dlp
    from yt_dlp.utils import DownloadCancelled

    def hook(d):
        if cancelled():
            raise DownloadCancelled()
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes") or 0
            on_status(f"Качаю: {done * 100 / total:.0f}%" if total else "Качаю...")
        elif d.get("status") == "finished":
            on_status("Склеиваю...")

    opts = {
        "format": yt_format(height, codec, ai),
        "paths": {"home": path},
        "outtmpl": "%(title)s.%(ext)s",
        "merge_output_format": "mkv",
        "ffmpeg_location": ffmpeg_bin,
        "progress_hooks": [hook],
        "logger": SilentLogger(),
        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
        "cachedir": False,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    try:
        return info["requested_downloads"][0]["filepath"]
    except (KeyError, IndexError, TypeError):
        return path
