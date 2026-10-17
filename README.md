# POVA — Personal Operating Voice Assistant

POVA is a secure, modular Windows desktop voice assistant written in Python. It uses Windows System.Speech for command-grammar microphone recognition and local SAPI text-to-speech. Commands are converted to structured intents and checked against an allowlist before any Windows action is performed.

## Quick start

POVA supports Windows 10/11 and Python 3.10 or later. In PowerShell, from the repository root:

```powershell
cd POVA
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

No PyAudio, API key, or online speech service is required. Install Pillow from `requirements.txt` for screenshot support. See the [complete project guide](POVA/README.md) for supported commands, settings, security details, troubleshooting, tests, and packaging.

The optional **AI Chat** feature uses [Ollama](https://ollama.com) running locally. Install Ollama and run `ollama pull llama3.2` to use the default model; POVA sends chat prompts only to a loopback address and never turns AI replies into computer commands.

## Command safety

POVA never executes recognized speech as a shell command. Only explicit application, website, known-folder, Windows, media, and information intents are supported. Shutdown, restart, sleep, and hibernate require a separate confirmation.

```mermaid
flowchart LR
    Voice[Voice] --> Recognize[Windows speech grammar]
    Recognize --> Parse[Structured intent]
    Parse --> Validate[Allowlist and confirmation]
    Validate --> Execute[Fixed Windows action]
    Execute --> Respond[Dashboard and local speech]
```

## Development checks

From the `POVA` directory, install development requirements and run:

```powershell
python -m pip install -r requirements-dev.txt
pytest
python -m compileall .
```
