# POVA

**POVA (Personal Operating Voice Assistant)** is a lightweight Windows desktop voice assistant written in Python. It listens through a microphone, converts speech to text, matches it against a safe allowlist, performs the Windows action, and replies with Windows text-to-speech.

## Features

- Modern dark Tkinter desktop interface
- Continuous microphone listening with start/stop control
- Natural variations such as “launch Notepad” and “please open Notepad”
- Notepad, Calculator, Chrome, File Explorer, VS Code, Command Prompt, and PowerShell
- YouTube, Google, and GitHub in the default browser
- Lock Windows, screenshots, volume controls, Show Desktop, time, and date
- Confirmation required for shutdown and restart
- Command history and recoverable error messages
- No arbitrary shell commands are generated from speech

## Architecture

`Microphone -> SpeechRecognition -> command.py -> allowlisted actions.py -> Windows`

- `main.py`: Tkinter UI, worker thread, event queue, and application lifecycle
- `voice.py`: microphone capture, Google speech recognition, and Windows SAPI text-to-speech
- `command.py`: normalization and structured intent matching
- `actions.py`: safe Windows/browser action implementations
- `config.py`: application aliases, URLs, and settings

## Requirements

- Windows 10 or later
- Python 3.10+ (tested with Python 3.14)
- A working microphone
- Internet access for the default Google speech-recognition provider

The project deliberately does not use PyAudio. `sounddevice` captures raw microphone samples, which are passed to `SpeechRecognition` for recognition.

## Installation

Open PowerShell in this directory:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process Bypass` and activate again.

## Run

```powershell
python main.py
```

Click **Start Listening**, speak a command, and click **Stop Listening** when finished.

## Example commands

- “Open Notepad”
- “Please launch Calculator”
- “Open Chrome”
- “Lock my computer”
- “Take a screenshot”
- “Open YouTube”
- “What time is it?”
- “Hey POVA”

Shutdown and restart are intentionally not in the default examples; if spoken, POVA asks for a confirmation before scheduling the Windows action.

## Safety design

Speech is converted into a `ParsedCommand` and only known intent handlers can run. User speech is never passed to `cmd.exe`, PowerShell, or `shell=True`. Applications, websites, and system operations are defined in explicit allowlists. Destructive operations require a separate “yes” or “no” response.

## Troubleshooting

- **No microphone found:** check Windows microphone permissions and the selected default input device.
- **Recognition unavailable:** check internet access; the default provider is Google Speech Recognition.
- **Application not installed:** POVA reports the missing executable instead of crashing.
- **Screenshot errors:** ensure the Pictures folder is writable.

## Future extensions

The command parser and action registry are intentionally independent of the UI and voice provider. Offline recognition, a wake-word engine, custom commands, application/file search, plugins, and an AI intent layer can be added without changing the Windows action safety boundary.
