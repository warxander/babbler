# Babbler
Twitch TTS desktop application

## Features
* Automatic language detection
* Based on Google Text-to-Speech
* Advanced customization

## Building EXE
`pyinstaller --hidden-import=_cffi_backend --noconsole --onefile --icon=icon.ico babbler.py`
