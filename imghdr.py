# imghdr.py -- minimal shim implementing what() for common image types

def _read_bytes(f, n=32):
    try:
        return f.read(n)
    except Exception:
        return b''


def what(file, h=None):
    """
    Minimal implementation of imghdr.what:
    - file may be a filename, file-like object, or bytes already read (h).
    Returns 'jpeg','png','gif','bmp','webp' or None.
    """
    if h is None:
        if isinstance(file, (bytes, bytearray)):
            h = bytes(file)
        elif isinstance(file, str):
            try:
                with open(file, 'rb') as _f:
                    h = _f.read(32)
            except Exception:
                return None
        else:
            # file-like object
            pos = None
            try:
                pos = file.tell()
            except Exception:
                pos = None
            h = _read_bytes(file, 32)
            try:
                if pos is not None:
                    file.seek(pos)
            except Exception:
                pass

    if not h:
        return None

    b = h
    if b.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    if b.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if b[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    if b.startswith(b'BM'):
        return 'bmp'
    # WEBP has 'RIFF'......'WEBP' structure
    if len(b) >= 12 and b[0:4] == b'RIFF' and b[8:12] == b'WEBP':
        return 'webp'
    return None
