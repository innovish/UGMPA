# Google TTS Web Application

A web application for generating text-to-speech audio using Google's Gemini TTS API.

## Features

- 📁 Upload text files (.txt)
- ✏️ Customizable prompts for voice tone
- 🎤 Configure voice names for Speaker 1 and Speaker 2
- 🎵 Generate and download audio files

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Upload a text file** (optional): Click "Choose File" to upload a `.txt` file containing your text content
2. **Enter a prompt**: Add instructions for how the text should be read (e.g., "Read aloud in a warm, welcoming tone")
3. **Set voice names**: 
   - Speaker 1 Voice Name (default: "Zephyr")
   - Speaker 2 Voice Name (default: "Puck")
4. **Enter text content**: If not uploading a file, type your text directly in the text area. Use "Speaker 1:" and "Speaker 2:" prefixes to assign different speakers.
5. **Generate**: Click the "Generate Audio" button to create your TTS audio file

The generated audio file will automatically download when ready.

## API Key Configuration

**IMPORTANT: API keys are sensitive and should never be committed to Git!**

The application requires a Gemini API key to function. You can set it in one of two ways:

### Method 1: Using config.json (Recommended)

1. Copy the example configuration file:
   ```bash
   copy config.json.example config.json
   ```
   (On Linux/Mac: `cp config.json.example config.json`)

2. Edit `config.json` and add your API key:
   ```json
   {
     "prompt": "Please read carefully and don't mis-read any word.",
     "voice1": "Puck",
     "voice2": "Zephyr",
     "api_key": "YOUR_GEMINI_API_KEY_HERE"
   }
   ```

**Note:** `config.json` is already in `.gitignore` and will not be pushed to GitHub, keeping your API key safe.

### Method 2: Using Environment Variable

Set the `GEMINI_API_KEY` environment variable:

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

**Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY=your_api_key_here
```

### Priority Order

The application will use the API key in this order:
1. `config.json` file (if `api_key` field is set)
2. `GEMINI_API_KEY` environment variable
3. If neither is set, the application will show a warning and may not work properly

## Notes

- The application supports multiple speakers in the text (use "Speaker 1:" and "Speaker 2:" prefixes)
- Generated audio files are saved as WAV format
- The application runs on port 5000 by default



