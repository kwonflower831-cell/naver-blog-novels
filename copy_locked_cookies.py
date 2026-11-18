import ctypes
from ctypes import wintypes
import os

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80

kernel32 = ctypes.windll.kernel32

def copy_locked_file(src_path, dst_path):
    handle = kernel32.CreateFileW(
        src_path,
        GENERIC_READ,
        FILE_SHARE_READ,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None
    )
    if handle == -1 or handle == 0xFFFFFFFFFFFFFFFF:
        err = kernel32.GetLastError()
        raise Exception(f"Failed to open source file, error code: {err}")

    try:
        size = kernel32.GetFileSize(handle, None)
        print(f"Locked file size: {size} bytes")
        
        # Read file contents
        buf = ctypes.create_string_buffer(size)
        bytes_read = wintypes.DWORD()
        if not kernel32.ReadFile(handle, buf, size, ctypes.byref(bytes_read), None):
            err = kernel32.GetLastError()
            raise Exception(f"Failed to read file, error code: {err}")
        
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        with open(dst_path, "wb") as f_out:
            f_out.write(buf.raw[:bytes_read.value])
        print(f"Successfully copied locked file to {dst_path} ({bytes_read.value} bytes)")
    finally:
        kernel32.CloseHandle(handle)

if __name__ == "__main__":
    src = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Profile 1\Network\Cookies")
    dst = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile\Default\Network\Cookies"
    copy_locked_file(src, dst)
