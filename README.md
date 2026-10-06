# POVA 🎙️

### Personal Operating Voice Assistant

POVA is a lightweight Windows desktop voice assistant built with Python and Tkinter. It listens to voice commands through a microphone, converts speech into text, identifies user intent, executes predefined Windows actions, and responds using text-to-speech.

Designed with **safety, reliability, and modularity** in mind, POVA provides hands-free desktop control without executing arbitrary commands generated from speech.

## ✨ Features

* **Modern Desktop Interface:** Dark-themed Tkinter UI with listening controls, command history, and status updates.
* **Continuous Voice Listening:** Start and stop microphone listening directly from the application.
* **Reliable Microphone Handling:** Uses `sounddevice` for audio capture, with recoverable errors for unavailable or inaccessible input devices.
* **Flexible Command Recognition:** Supports natural variations such as "Open Notepad," "Launch Notepad," and "Please open Notepad."
* **Windows Application Control:** Launch Notepad, Calculator, Chrome, File Explorer, VS Code, Command Prompt, and PowerShell.
* **Browser Shortcuts:** Open YouTube, Google, and GitHub in the default browser.
* **System Controls:** Lock Windows, take screenshots, adjust volume, show the desktop, and retrieve the current time and date.
* **Voice Feedback:** Uses Windows SAPI text-to-speech to communicate results and errors.
* **Safe Shutdown and Restart:** Requires explicit confirmation before scheduling destructive system actions.
* **Command History:** Displays recognized commands and execution results.
* **Error Recovery:** Reports microphone, recognition, and application-launch errors without unnecessarily terminating the UI.
* **Thread-Safe UI Updates:** Uses a worker thread and event queue to keep the Tkinter interface responsive during voice operations.
* **Allowlisted Actions:** Speech is interpreted as a structured command. Arbitrary spoken text is never executed as a shell command.

## 🛠️ Technology Stack

| Technology                 | Purpose                                |
| -------------------------- | -------------------------------------- |
| Python 3.10+               | Core application logic                 |
| Tkinter                    | Desktop user interface                 |
| `sounddevice`              | Microphone audio capture               |
| `SpeechRecognition`        | Speech-to-text processing              |
| Google Speech Recognition  | Default online recognition provider    |
| Windows SAPI               | Text-to-speech feedback                |
| Windows APIs and utilities | System actions and desktop control     |
| Threading and event queues | Responsive UI and background listening |

**Compatibility:** Windows 10 or later. Python 3.14 is a target environment; individual audio-device drivers and dependencies may affect compatibility.

## 🏗️ Architecture

```text
          Microphone
               |
               v
       sounddevice Capture
               |
               v
      Speech Recognition
               |
               v
       command.py
  Normalize and Parse Intent
               |
               v
       Allowlist Validation
               |
               v
        actions.py
               |
               v
      Windows / Browser
               |
               v
       Voice Feedback
```

### Project Structure

```text
POVA/
├── main.py          # Tkinter UI and application lifecycle
├── voice.py         # Microphone capture, speech recognition,
│                    # and Windows SAPI text-to-speech
├── command.py       # Text normalization and intent matching
├── actions.py       # Allowlisted Windows and browser actions
├── config.py        # Aliases, URLs, and application settings
├── requirements.txt # Python dependencies
├── pova_icon.ico    # Application icon
└── README.md
```

### Module Responsibilities

* **`main.py`:** Manages the desktop interface, background worker, event queue, listening controls, and application shutdown.
* **`voice.py`:** Captures audio through `sounddevice`, submits audio for speech recognition, and provides spoken feedback.
* **`command.py`:** Normalizes recognized text and maps supported phrases to structured intents.
* **`actions.py`:** Executes predefined actions and validates confirmation for sensitive operations.
* **`config.py`:** Maintains application aliases, website URLs, and configurable settings.

## 📋 Requirements

* Windows 10 or later
* Python 3.10 or later
* A working microphone and appropriate Windows microphone permissions
* Internet connectivity for the default Google Speech Recognition provider
* Working Windows audio input and output devices

**Note:** POVA deliberately avoids PyAudio. It uses `sounddevice` to capture raw microphone samples and passes the audio to the speech-recognition pipeline.

## 🚀 Installation

### 1. Clone the Repository

```powershell
git clone https://github.com/Princekumarsahu-321/POVA.git
cd POVA
```

### 2. Create a Virtual Environment

```powershell
py -3.14 -m venv .venv
```

If Python 3.14 is unavailable, use another installed Python version supported by your dependencies.

### 3. Activate the Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, allow it for the current session only:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Start POVA

```powershell
python main.py
```

Click **Start Listening**, speak a supported command, and click **Stop Listening** when finished.

## 🎤 Example Voice Commands

| Category             | Example                    |
| -------------------- | -------------------------- |
| Applications         | "Open Notepad"             |
| Alternative phrasing | "Please launch Calculator" |
| Browser              | "Open Chrome"              |
| Websites             | "Open YouTube"             |
| System security      | "Lock my computer"         |
| Screenshots          | "Take a screenshot"        |
| Desktop control      | "Show desktop"             |
| Audio                | "Increase volume"          |
| Time                 | "What time is it?"         |
| Date                 | "What is today's date?"    |
| Wake phrase          | "Hey POVA"                 |

Supported phrases depend on the configured aliases and command handlers. A wake phrase is not necessarily a continuously active wake-word detector.

Shutdown and restart require a separate confirmation response, such as "yes" or "no," before the action proceeds.

## 🛡️ Safety and Reliability

POVA is designed around a strict boundary between speech recognition and system execution.

* **Structured intent matching:** Recognized speech is mapped to known commands instead of being treated as executable code.
* **Explicit action allowlist:** Applications, websites, and system operations are defined in advance.
* **No arbitrary shell execution:** User speech is never passed directly to `cmd.exe`, PowerShell, or `shell=True`.
* **Confirmation for destructive actions:** Shutdown and restart require a separate confirmation step.
* **Responsive interface:** Background voice processing and queued UI updates help prevent long-running recognition operations from freezing the window.
* **Recoverable failures:** Expected device, network, and application errors should be reported clearly so the user can retry.

Speech recognition can misinterpret words, particularly in noisy environments. Sensitive actions should therefore remain confirmation-protected, and command handlers should validate their inputs independently.

## 🔧 Troubleshooting

### Microphone Not Found

1. Open Windows Settings and check microphone privacy permissions.
2. Confirm that the correct input device is selected in Windows.
3. Check whether another application is exclusively using the microphone.
4. Verify that `sounddevice` can access an available input device.

To inspect audio devices, run:

```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### Speech Recognition Fails

* Verify your internet connection.
* Speak clearly and reduce background noise.
* Check the configured speech-recognition provider.
* Retry after temporary network or service errors.

The default Google Speech Recognition provider requires internet connectivity.

### Application Not Installed

POVA should report when a configured application executable cannot be found. Verify the installation path or update the corresponding application alias in `config.py`.

### Screenshot Fails

Check that the Pictures directory exists and is writable. Confirm that any required screenshot dependency is installed.

### Tkinter Window Freezes

Long-running microphone capture or recognition should not block the main UI thread. Check that background workers publish results through the event queue and that Tkinter widgets are updated only from the main thread.

### Audio Dependency Errors

Ensure the virtual environment is active and install the project's declared dependencies. Check microphone permissions, audio-device availability, and compatibility between Python, `sounddevice`, and the system audio driver.

## 🔮 Future Enhancements

* Offline speech recognition for reduced internet dependency
* Dedicated wake-word detection
* Improved recognition confidence handling and command disambiguation
* Configurable microphone selection and audio-device recovery
* Hindi and English voice-command support
* Custom user-defined commands
* Application and file search
* A plugin-based action registry
* Optional AI-assisted intent classification with strict action validation
* Automated unit and integration tests
* Packaging as a standalone Windows executable

Any future AI intent layer should remain separate from the trusted action registry. AI-generated interpretations must never bypass the allowlist or confirmation requirements.

## 🎯 Project Goals

POVA aims to make everyday Windows interactions faster and more accessible through a lightweight, voice-controlled desktop application.

The project emphasizes modular Python development, desktop UI programming, speech processing, background task management, error handling, and secure operating-system integration.

## 👨‍💻 Author

**Prince Kumar**

* GitHub: [Princekumarsahu-321](https://github.com/Princekumarsahu-321)
* Project: [POVA Repository](https://github.com/Princekumarsahu-321/POVA)

---

*POVA: Your desktop, your voice, your control.*
