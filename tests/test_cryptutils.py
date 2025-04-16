from qqutils.cryptutils import aes_decrypt, aes_encrypt, bcrypt_hash, bcrypt_check


def test_aes():
    print(aes_encrypt('hello'))
    assert aes_decrypt(aes_encrypt('hello')) == 'hello'

    text = "abcdefg" * 1000
    assert aes_decrypt(aes_encrypt(text)) == text


def test_bcrypt():
    bh = bcrypt_hash('hello')
    print(bh)
    assert bcrypt_check('hello', bh)
    bh2a = bcrypt_hash('hello', prefix=b'2a')
    print(bh2a)
    assert bcrypt_check('hello', bh2a)
