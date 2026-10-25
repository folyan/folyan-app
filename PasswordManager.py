import base64
import hashlib

DEFAULT_ITERATIONS = 3637142
METHODS = ("standard", "openssl")


def _pbkdf2(method, password, salt, iterations):
    if method == "openssl":
        try:
            import _hashlib
        except ImportError:
            raise RuntimeError("OpenSSL недоступен в этой сборке")
        return _hashlib.pbkdf2_hmac("sha256", password, salt, iterations, 32)
    return hashlib.pbkdf2_hmac("sha256", password, salt, iterations, dklen=32)


def generate_password(master_password, salt, site,
                      iterations=DEFAULT_ITERATIONS, method="standard"):
    b = (str(salt) + str(site)).encode("utf-8")
    c = _pbkdf2(method, str(master_password).encode("utf-8"), b, int(iterations))
    c = base64.b64encode(c).decode("utf-8")
    c = (c.replace("/", "_"))[:30] + "_!"
    return c


def backend_info():
    parts = ["hashlib.pbkdf2_hmac из модуля: %s"
             % getattr(hashlib.pbkdf2_hmac, "__module__", "?")]
    try:
        import _hashlib
        parts.append("_hashlib: есть (%s)" % getattr(_hashlib, "OPENSSL_VERSION", "?"))
    except ImportError:
        parts.append("_hashlib: нет")
    return "; ".join(parts)
