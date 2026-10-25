import base64
import hashlib

DEFAULT_ITERATIONS = 500000
DEFAULT_SALT = "FolyanApp"


def generate_password(master_password, salt, site, iterations=DEFAULT_ITERATIONS):
    b = (str(salt) + str(site)).encode("utf-8")
    c = hashlib.pbkdf2_hmac(
        "sha256",
        str(master_password).encode("utf-8"),
        b,
        int(iterations),
        dklen=32,
    )
    c = base64.b64encode(c).decode("utf-8")
    c = (c.replace("/", "_"))[:30] + "_!"
    return c
