import base64
import hashlib
from typing import Union

__all__ = (
    'aes_encrypt',
    'aes_decrypt',
)

_PASSWORD = "Who1sy0urDaddy?!"


class AESCipher(object):

    def __init__(self, key):
        from Crypto.Cipher import AES
        self.Cipher = AES

        self.bs = self.Cipher.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw: str) -> bytes:
        from Crypto import Random
        raw = self._pad(raw)
        iv = Random.new().read(self.Cipher.block_size)
        cipher = self.Cipher.new(self.key, self.Cipher.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc: Union[str, bytes]) -> bytes:
        if isinstance(enc, bytes):
            enc = base64.b64decode(enc)
        elif isinstance(enc, str):
            enc = base64.b64decode(enc.encode())
        else:
            raise ValueError(f"enc must be str or bytes, but got {type(enc)}")
        iv = enc[:self.Cipher.block_size]
        cipher = self.Cipher.new(self.key, self.Cipher.MODE_CBC, iv)
        return AESCipher._unpad(cipher.decrypt(enc[self.Cipher.block_size:]))

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
    import bcrypt
    return bcrypt.hashpw(message.encode(), bcrypt.gensalt(rounds=rounds, prefix=prefix)).decode()


def bcrypt_check(message: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(message.encode(), hashed.encode())
