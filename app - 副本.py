import os
import mimetypes
import struct
from flask import Flask, render_template, request, jsonify, send_file
from google import genai
from google.genai import types
import tempfile
import io

app = Flask(__name__)

# API key
API_KEY = os.environ.get("GEMINI_API_KEY") or "AIzaSyC2h3TmDjRwkGsy48kSh6p8Tb46VyAxGcI"

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters."""
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string."""
    bits_per_sample = 16
    rate = 24000

    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass

    return {"bits_per_sample": bits_per_sample, "rate": rate}

@app.route('/')
def index():
    return render_template('index.html')

def decode_file_content(file_data: bytes) -> str:
    """Decode file content trying multiple encodings, prioritizing Chinese encodings."""
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin-1', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            return file_data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    # Fallback: use UTF-8 with error replacement
    return file_data.decode('utf-8', errors='replace')

@app.route('/decode-file', methods=['POST'])
def decode_file():
    """Endpoint to decode uploaded file and return content for preview."""
    try:
        if 'text_file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['text_file']
        if not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        file_data = file.read()
        # Reset file stream position if possible (for Flask file objects)
        if hasattr(file, 'seek'):
            file.seek(0)
        
        text_content = decode_file_content(file_data)
        
        return jsonify({'content': text_content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_tts(text_content: str, prompt: str, speaker1_voice: str, speaker2_voice: str):
    """
    Generate TTS audio from text content.
    
    Args:
        text_content: The text content to convert to speech
        prompt: The prompt/instruction for how to read the text
        speaker1_voice: Voice name for Speaker 1
        speaker2_voice: Voice name for Speaker 2
    
    Returns:
        Tuple of (audio_data: bytes, file_extension: str)
    """
    # Combine prompt and text content
    full_text = f"{prompt}\n{text_content}" if prompt else text_content
    
    # Initialize client
    client = genai.Client(api_key=API_KEY)
    
    # Prepare content
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=full_text)],
        ),
    ]
    
    # Configure speech generation
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=[
                    types.SpeakerVoiceConfig(
                        speaker="Speaker 1",
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=speaker1_voice
                            )
                        ),
                    ),
                    types.SpeakerVoiceConfig(
                        speaker="Speaker 2",
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=speaker2_voice
                            )
                        ),
                    ),
                ]
            ),
        ),
    )
    
    # Generate audio
    model = "gemini-2.5-pro-preview-tts"
    audio_chunks = []
    
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue
        
        if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            
            if file_extension is None:
                file_extension = ".wav"
                data_buffer = convert_to_wav(inline_data.data, inline_data.mime_type)
            
            audio_chunks.append((data_buffer, file_extension))
    
    if not audio_chunks:
        raise Exception('No audio generated')
    
    # Return the first audio chunk (or combine all if needed)
    return audio_chunks[0]

@app.route('/generate', methods=['POST'])
def generate_endpoint():
    """Route handler for generating TTS audio - only called when Generate button is clicked."""
    try:
        # Get form data - prioritize uploaded file over text_content field
        text_content = ''
        
        # Handle file upload first (takes priority)
        if 'text_file' in request.files:
            file = request.files['text_file']
            if file.filename:
                file_data = file.read()
                text_content = decode_file_content(file_data)
        
        # If no file uploaded, use text_content field
        if not text_content:
            text_content = request.form.get('text_content', '')
        
        # Get other parameters
        prompt = request.form.get('prompt', '')
        voice1 = request.form.get('voice1', 'Puck')
        voice2 = request.form.get('voice2', 'Zephyr')
        
        if not text_content:
            return jsonify({'error': 'No text content provided. Please upload a file or enter text.'}), 400
        
        # Call the generate function with parameters
        audio_data, extension = generate_tts(text_content, prompt, voice1, voice2)
        
        # Create a temporary file to store the audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
        temp_file.write(audio_data)
        temp_file.close()
        
        return send_file(
            temp_file.name,
            mimetype=f'audio/{extension[1:]}',  # Remove the dot from extension
            as_attachment=True,
            download_name=f'tts_output{extension}'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

