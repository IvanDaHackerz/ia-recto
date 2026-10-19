"""Windows-user DPAPI storage for local normalizer secrets; never plaintext files."""
from __future__ import annotations

import argparse
import ctypes
import getpass
import json
import os
import sys
from pathlib import Path

LOCAL = Path(__file__).resolve().parents[1] / ".local" / "normalizer"
DEFAULT_TOGETHER_MODEL = "openai/gpt-oss-120b"


def protect(data, *, decrypt=False):
    if os.name != "nt":
        raise ValueError("Local encrypted credentials require Windows; use environment variables on other systems")
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_byte))]

    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    target = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    fn = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                   ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    fn.restype = wintypes.BOOL
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise ValueError("Windows could not unlock/save the local credential for this user")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(ctypes.cast(target.data, ctypes.c_void_p))


def read_local_config():
    path = LOCAL / "provider.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if (type(data) is not dict or set(data) != {"provider", "model"}
            or data["provider"] not in {"together", "openai"}
            or not isinstance(data["model"], str) or not data["model"].strip()):
        raise ValueError("Invalid local normalizer configuration")
    return data


def read_key(provider):
    if provider not in {"together", "openai"}:
        raise ValueError("Unknown credential provider")
    path = LOCAL / (provider + ".key.dpapi")
    return protect(path.read_bytes(), decrypt=True).decode("utf-8") if path.exists() else ""


def save_together(key, model=DEFAULT_TOGETHER_MODEL):
    if not isinstance(key, str) or not key.strip() or any(c.isspace() for c in key.strip()):
        raise ValueError("The API key must be one nonempty value without spaces")
    encrypted = protect(key.strip().encode("utf-8"))
    LOCAL.mkdir(parents=True, exist_ok=True)
    (LOCAL / "together.key.dpapi").write_bytes(encrypted)
    (LOCAL / "provider.json").write_text(json.dumps({"provider": "together", "model": model}, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="Read key from a non-echoing stdin pipe")
    parser.add_argument("--model", default=DEFAULT_TOGETHER_MODEL)
    args = parser.parse_args()
    try:
        if args.stdin:
            print("Ready for credential on stdin; it will not be echoed.", flush=True)
            key = sys.stdin.readline().strip()
        else:
            key = getpass.getpass("Together API key (hidden): ")
        save_together(key, args.model)
        print("Together configured. API key saved only as a Windows-user encrypted local blob.")
        return 0
    except (ValueError, OSError, UnicodeError):
        print("Could not save credential. No secret value was logged.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
