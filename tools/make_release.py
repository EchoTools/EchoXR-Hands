"""Builds the EchoXR Hands release: out/release/EchoXR-Hands-v<VERSION>.zip, published at
github.com/heisthecat31/EchoXR-Hands (EchoXR.exe downloads it from there).

    python tools/make_release.py              build, then package
    python tools/make_release.py --no-build   package what's already built

The zip unpacks into Echo VR's bin\\win10 folder:

    EchoXR\\Hands\\                   finger bridge (EchoXRHands.exe), its SteamVR files,
                                    settings window, README.txt, version.txt
    EchoXR\\Hands\\install\\           hand tracking plugin, default settings, plugin loader;
                                    EchoXR.exe or EchoXRHands.exe puts these into the game folder

version.txt holds the release tag; EchoXR.exe compares it with the latest release to
offer updates. Raise VERSION for every release.

Two inputs aren't built here: third_party/openvr_api.dll (Valve's OpenVR runtime
library, from github.com/ValveSoftware/openvr bin/win64) and stage/dbgcore.dll (the
plugin loader, copied from an Echo install that has it; ECHO_BIN points at one).
"""
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VERSION = open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
ECHO_BIN = os.environ.get("ECHO_BIN", r"C:\Oculus\Games\Software\Software\ready-at-dawn-echo-arena\bin\win10")

# (source relative to ROOT, path inside the zip)
FILES = [
    ("out/EchoXRHands.exe",                  "EchoXR/Hands/EchoXRHands.exe"),
    ("out/EchoXRSettings.exe",               "EchoXR/Hands/EchoXRSettings.exe"),
    ("out/htv_actions.json",                 "EchoXR/Hands/htv_actions.json"),
    ("out/htv_bindings_knuckles.json",       "EchoXR/Hands/htv_bindings_knuckles.json"),
    ("third_party/openvr_api.dll",           "EchoXR/Hands/openvr_api.dll"),
    ("tools/fake_index.py",                  "EchoXR/Hands/fake_index.py"),
    ("out/EchoXRHands.dll",                  "EchoXR/Hands/install/EchoXRHands.dll"),
    ("out/EchoXRHands.txt",                  "EchoXR/Hands/install/EchoXRHands.txt"),
    ("stage/dbgcore.dll",                    "EchoXR/Hands/install/dbgcore.dll"),
]
FOLDERS = ("EchoXR/", "EchoXR/Hands/", "EchoXR/Hands/install/")

README = """EchoXR Hands {version}
=================
Per-finger hand tracking for Echo VR: your own fingers on your chassis hands, and
other players'. Works however you run Echo: the Oculus / Meta runtime, or EchoXR
(https://github.com/heisthecat31/EchoXR/releases).

With EchoXR
-----------
Set AutoStartHands = 1 in EchoXR\\echoxr.ini and EchoXR.exe installs this for you,
runs the finger bridge alongside Echo and offers hand tracking updates. Or unzip it
into bin\\win10 as below; EchoXR.exe then does the rest.

Install
-------
1. Unzip into Echo VR's bin\\win10 folder, the one with echovr.exe. You should end
   up with an EchoXR\\Hands folder there.
2. Install SteamVR (free, on Steam): the finger bridge reads your fingers from it.
3. Run EchoXR\\Hands\\EchoXRHands.exe. Each start, it puts the hand tracking plugin
   into bin\\win10\\plugins\\ and, if needed, the plugin loader (dbgcore.dll). An
   older 45 KB dbgcore.dll moves to plugins\\dbgcore_legacy.dll and keeps loading;
   a different plugin loader is kept; anything else is left alone (run
   EchoXRSetup.exe then). EchoXRHands.exe --setup does only this and exits.
4. Start Echo VR while the bridge is running.

Hand tracking
-------------
In-game, hold both hands fully open once: that calibrates the open-hand pose.
Press Ctrl+Alt+C (hands open) to recalibrate at any time.
Valve Index controllers give full finger sensing; other controllers and
controller-free hand tracking use the SteamVR hand skeleton.
Settings: run EchoXR\\Hands\\EchoXRSettings.exe. Changes show in-game as you make
them; they're stored in bin\\win10\\plugins\\EchoXRHands.txt (re-read while the game runs).
Finger sharing: the plugin sends your fingers through a relay so other players
running it can see them, and shows theirs (Network = 0 turns this off; it sends
your display name and your match's player names so the relay can pair you up).

Log: plugins\\EchoXRHands.log. openvr_api.dll is Valve's (BSD-3-Clause).
"""


def main():
    if "--no-build" not in sys.argv:
        subprocess.check_call(["cmd", "/c", os.path.join(ROOT, "build.bat")], cwd=ROOT)
    loader = os.path.join(ROOT, "stage", "dbgcore.dll")
    if not os.path.isfile(loader) and os.path.isfile(os.path.join(ECHO_BIN, "dbgcore.dll")):
        os.makedirs(os.path.dirname(loader), exist_ok=True)
        shutil.copyfile(os.path.join(ECHO_BIN, "dbgcore.dll"), loader)
    missing = [src for src, _ in FILES if not os.path.isfile(os.path.join(ROOT, src))]
    if missing:
        sys.exit("missing inputs:\n  " + "\n  ".join(missing))
    out = os.path.join(ROOT, "out", "release")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "EchoXR-Hands-v%s.zip" % VERSION)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for d in FOLDERS:   # explicit folder entries, so every unzip tool creates them
            z.writestr(zipfile.ZipInfo(d), "")
        for src, dst in FILES:
            info = zipfile.ZipInfo.from_file(os.path.join(ROOT, src), dst)
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(ROOT, src), "rb") as f:
                z.writestr(info, f.read())
        z.writestr("EchoXR/Hands/README.txt", README.format(version="v" + VERSION).replace("\n", "\r\n"))
        z.writestr("EchoXR/Hands/version.txt", "v%s\r\n" % VERSION)
    print("%s  %.1f KB  -> heisthecat31/EchoXR-Hands, tag v%s" %
          (os.path.relpath(path, ROOT), os.path.getsize(path) / 1024, VERSION))


if __name__ == "__main__":
    main()
