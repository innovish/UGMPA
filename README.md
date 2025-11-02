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

## API Key

The application uses the API key embedded in `app.py`. You can also set it as an environment variable:
```bash
set GEMINI_API_KEY=your_api_key_here
```

## Notes

- The application supports multiple speakers in the text (use "Speaker 1:" and "Speaker 2:" prefixes)
- Generated audio files are saved as WAV format
- The application runs on port 5000 by default



