import base64
import hashlib
import bcrypt
from Crypto import Random
from Crypto.Cipher import AES
from typing import Union

_PASSWORD = "Who1sy0urDaddy?!"


class AESCipher(object):

    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw: str) -> bytes:
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc: Union[str, bytes]) -> bytes:
        if isinstance(enc, bytes):
            enc = base64.b64decode(enc)
        elif isinstance(enc, str):
            enc = base64.b64decode(enc.encode())
        else:
            raise ValueError(f"enc must be str or bytes, but got {type(enc)}")
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return AESCipher._unpad(cipher.decrypt(enc[AES.block_size:]))

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]


def aes_encrypt(message: str, password: str = _PASSWORD) -> str:
    return AESCipher(password).encrypt(message).decode()


def aes_decrypt(enc_message: str, password: str = _PASSWORD) -> str:
    return AESCipher(password).decrypt(enc_message).decode()


def bcrypt_hash(message: str, *, rounds: int = 12, prefix: bytes = b'2b') -> str:
    return bcrypt.hashpw(message.encode(), bcrypt.gensalt(rounds=rounds, prefix=prefix)).decode()


def bcrypt_check(message: str, hashed: str) -> bool:
    return bcrypt.checkpw(message.encode(), hashed.encode())
