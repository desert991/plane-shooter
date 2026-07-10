import subprocess, threading, os

_sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
_music_proc = None

def init():
    """Verify sounds directory exists."""
    return os.path.isdir(_sounds_dir)

def play(name):
    """Play a sound effect in background thread."""
    path = os.path.join(_sounds_dir, name + ".wav")
    if os.path.exists(path):
        threading.Thread(target=lambda: subprocess.Popen(
            ["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).wait(), daemon=True).start()

def start_music():
    """Start looping background music."""
    global _music_proc
    stop_music()
    path = os.path.join(_sounds_dir, "bgm.wav")
    if os.path.exists(path):
        def loop_music():
            global _music_proc
            while True:
                _music_proc = subprocess.Popen(
                    ["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                _music_proc.wait()
        t = threading.Thread(target=loop_music, daemon=True)
        t.start()

def stop_music():
    """Stop background music."""
    global _music_proc
    if _music_proc:
        try:
            _music_proc.terminate()
        except Exception:
            pass
        _music_proc = None
