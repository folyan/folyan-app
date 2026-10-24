import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def generate_password(master_password, salt, site):
    b = (str(salt) + str(site)).encode("utf-8")
    x = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b, iterations=3637142)
    c = x.derive(str(master_password).encode("utf-8"))
    c = base64.b64encode(c).decode("utf-8")
    c = (c.replace("/", "_"))[:30] + "_!"
    return c
