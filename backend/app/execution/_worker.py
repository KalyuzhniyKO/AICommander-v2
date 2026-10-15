"""Windows launch gate: no target code runs until assignment to a Job Object.

Executed by an isolated Python interpreter, not imported by the application.
The actual interpreter assigns itself BEFORE reading the approved argv, including
when a Windows Store/venv launcher delegates to a different interpreter process.
"""
import json
import ctypes
from ctypes import wintypes
import subprocess
import sys


if __name__ == "__main__":
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.OpenJobObjectW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    api.OpenJobObjectW.restype = wintypes.HANDLE
    api.GetCurrentProcess.restype = wintypes.HANDLE
    api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    api.AssignProcessToJobObject.restype = wintypes.BOOL
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = api.OpenJobObjectW(0x0001, False, sys.argv[1])  # JOB_OBJECT_ASSIGN_PROCESS
    if not handle:
        sys.exit(125)
    assigned = api.AssignProcessToJobObject(handle, api.GetCurrentProcess())
    api.CloseHandle(handle)
    if not assigned:
        sys.exit(125)
    argv = json.loads(sys.stdin.readline())
    result = subprocess.run(argv, stdin=subprocess.DEVNULL, shell=False)
    sys.exit(result.returncode)
