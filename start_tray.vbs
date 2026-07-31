Set WshShell = CreateObject("WScript.Shell")

WshShell.Run _
    """C:\Projects\ElectricityTray\.venv\Scripts\pythonw.exe"" " & _
    """C:\Projects\ElectricityTray\main.py""", _
    0, _
    False