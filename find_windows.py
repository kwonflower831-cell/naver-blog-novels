import ctypes

user32 = ctypes.windll.user32

def enum_windows():
    titles = []
    def cb(hwnd, extra):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, 512)
            if buf.value:
                titles.append((hwnd, buf.value))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    for h, t in titles:
        if any(k in t for k in ["Chrome", "네이버", "블로그", "Antigravity", "크로노스"]):
            print(f"[{h}] {t}")

if __name__ == "__main__":
    enum_windows()
