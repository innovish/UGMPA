import os
import mimetypes
import struct
import re
import json
import time
from flask import Flask, render_template, request, jsonify, send_file
from google import genai
from google.genai import types
import tempfile
import io
import shutil
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
    print("✓ pydub successfully imported")
except ImportError as e:
    PYDUB_AVAILABLE = False
    print(f"⚠ Warning: pydub not installed, concatenation feature will not work: {e}")
except Exception as e:
    PYDUB_AVAILABLE = False
    print(f"⚠ Warning: pydub import failed, concatenation feature will not work: {e}")

app = Flask(__name__)

# API key
API_KEY = os.environ.get("GEMINI_API_KEY") or "AIzaSyC2h3TmDjRwkGsy48kSh6p8Tb46VyAxGcI"

# Create outputs directory if it doesn't exist
OUTPUT_DIR = os.path.join(os.getcwd(), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Default config file path
CONFIG_FILE = os.path.join(os.getcwd(), "config.json")

def load_config():
    """Load default configuration from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {
        'prompt': 'Please read carefully and don\'t mis-read any word.',
        'voice1': 'Puck',
        'voice2': 'Zephyr'
    }

def save_config(config):
    """Save default configuration to file."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

# Load default config on startup
DEFAULT_CONFIG = load_config()

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
    config = load_config()
    return render_template('index.html', default_config=config)

@app.route('/save-config', methods=['POST'])
def save_config_endpoint():
    """Endpoint to save default configuration."""
    try:
        data = request.json
        config = {
            'prompt': data.get('prompt', ''),
            'voice1': data.get('voice1', 'Puck'),
            'voice2': data.get('voice2', 'Zephyr')
        }
        save_config(config)
        return jsonify({'success': True, 'message': 'Configuration saved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

def parse_chapters(text: str) -> list[dict]:
    """
    Parse text into chapters based on "第x章" pattern.
    
    Args:
        text: The full text content
        
    Returns:
        List of dictionaries with 'title' and 'content' keys
    """
    # Pattern to match chapter markers: 第 followed by numbers or Chinese numbers, then 章
    # Examples: 第1章, 第一章, 第10章, etc.
    # Also captures optional chapter name after 章
    chapter_pattern = r'(第[0-9一二三四五六七八九十百千万]+章[^\n]*)'
    
    chapters = []
    # Find all chapter markers
    matches = list(re.finditer(chapter_pattern, text))
    
    if not matches:
        # No chapters found, return entire text as single item with paragraphs
        full_text = text.strip()
        paragraphs = parse_paragraphs(full_text)
        return [{'title': '全文', 'content': full_text, 'paragraphs': paragraphs}]
    
    # Handle content before first chapter
    if matches[0].start() > 0:
        preface_content = text[:matches[0].start()].strip()
        preface_paragraphs = parse_paragraphs(preface_content)
        # Prepend chapter title as the first paragraph
        preface_paragraphs.insert(0, '前言')
        chapters.append({
            'title': '前言',
            'content': preface_content,
            'paragraphs': preface_paragraphs
        })
    
    # Split text by chapter markers
    for i, match in enumerate(matches):
        chapter_start = match.start()
        chapter_title = match.group(1).strip()
        
        # Get content until next chapter or end of text
        if i < len(matches) - 1:
            next_match = matches[i + 1]
            chapter_end = next_match.start()
            chapter_content = text[chapter_start:chapter_end]
        else:
            # Last chapter - get remaining text
            chapter_content = text[chapter_start:]
        
        # Remove the chapter title from content (it's already in title)
        chapter_content = chapter_content.replace(chapter_title, '', 1).strip()
        
        # Parse paragraphs from chapter content
        paragraphs = parse_paragraphs(chapter_content)
        
        # Prepend chapter title as the first paragraph
        paragraphs.insert(0, chapter_title)
        
        chapters.append({
            'title': chapter_title,
            'content': chapter_content,
            'paragraphs': paragraphs
        })
    
    return chapters

def parse_paragraphs(text: str) -> list[str]:
    """
    Parse text into paragraphs.
    Paragraphs are separated by double newlines or significant whitespace.
    
    Args:
        text: The text content to parse
        
    Returns:
        List of paragraph strings
    """
    if not text:
        return []
    
    # Split by double newlines first (common paragraph separator)
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Further split by single newlines if paragraphs are too long
    # This handles cases where paragraphs are separated by single newlines
    result = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # If paragraph is very long and contains single newlines, 
        # it might be multiple paragraphs separated by single newlines
        if len(para) > 500 and '\n' in para:
            # Split by single newlines and treat each as a paragraph
            sub_paras = re.split(r'\n+', para)
            for sub_para in sub_paras:
                sub_para = sub_para.strip()
                if sub_para:
                    result.append(sub_para)
        else:
            result.append(para)
    
    return result if result else [text.strip()]

@app.route('/decode-file', methods=['POST'])
def decode_file():
    """Endpoint to decode uploaded file and return content and chapters for preview."""
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
        chapters = parse_chapters(text_content)
        
        return jsonify({
            'content': text_content,
            'chapters': chapters
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check-audio-files', methods=['POST'])
def check_audio_files():
    """Endpoint to check which paragraph audio files exist."""
    try:
        data = request.json
        chapter_title = data.get('chapter_title', '')
        total_paragraphs = data.get('total_paragraphs', 0)
        
        if not chapter_title or not total_paragraphs:
            return jsonify({'error': 'Chapter title and paragraph count required'}), 400
        
        safe_title = sanitize_filename(chapter_title)
        existing_files = {}
        
        # Check for each paragraph file
        for index in range(1, total_paragraphs + 1):
            filename = f"{safe_title}_{index:03d}.wav"
            file_path = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(file_path):
                existing_files[index] = filename
        
        return jsonify({
            'success': True,
            'existing_files': existing_files
        })
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

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem compatibility."""
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    return sanitized

def read_wav_header(file_path: str) -> dict:
    """Read WAV file header and return audio parameters."""
    with open(file_path, 'rb') as f:
        # Read RIFF header
        riff_chunk = f.read(12)
        if riff_chunk[:4] != b'RIFF' or riff_chunk[8:12] != b'WAVE':
            raise ValueError("Not a valid WAV file")
        
        # Read fmt chunk
        fmt_chunk_id = f.read(4)
        if fmt_chunk_id != b'fmt ':
            raise ValueError("Missing fmt chunk")
        
        fmt_chunk_size = struct.unpack('<I', f.read(4))[0]
        fmt_data = f.read(fmt_chunk_size)
        
        # Parse fmt data
        audio_format, num_channels, sample_rate = struct.unpack('<HHI', fmt_data[:8])
        byte_rate, block_align = struct.unpack('<IH', fmt_data[8:14])
        bits_per_sample = struct.unpack('<H', fmt_data[14:16])[0] if fmt_chunk_size >= 16 else 16
        
        # Find data chunk
        while True:
            chunk_id = f.read(4)
            if chunk_id == b'data':
                data_size = struct.unpack('<I', f.read(4))[0]
                data_offset = f.tell()
                break
            elif chunk_id == b'':
                raise ValueError("Missing data chunk")
            else:
                chunk_size = struct.unpack('<I', f.read(4))[0]
                f.seek(chunk_size, 1)
        
        return {
            'num_channels': num_channels,
            'sample_rate': sample_rate,
            'bits_per_sample': bits_per_sample,
            'byte_rate': byte_rate,
            'block_align': block_align,
            'data_size': data_size,
            'data_offset': data_offset
        }

def read_wav_data(file_path: str, header: dict) -> bytes:
    """Read audio data from WAV file."""
    with open(file_path, 'rb') as f:
        f.seek(header['data_offset'])
        return f.read(header['data_size'])

def concatenate_wav_files_pure_python(audio_files: list[str], output_path: str, silence_seconds: float = 1.5):
    """
    Concatenate multiple WAV files without requiring ffmpeg.
    Assumes all WAV files have the same format.
    """
    if not audio_files:
        raise ValueError("No audio files provided")
    
    # Read first file to get format
    first_header = read_wav_header(audio_files[0])
    sample_rate = first_header['sample_rate']
    bits_per_sample = first_header['bits_per_sample']
    num_channels = first_header['num_channels']
    bytes_per_sample = bits_per_sample // 8
    
    # Calculate silence duration
    silence_samples = int(sample_rate * silence_seconds)
    silence_bytes = silence_samples * num_channels * bytes_per_sample
    silence_data = b'\x00' * silence_bytes
    
    # Read all audio data
    all_audio_data = []
    for i, file_path in enumerate(audio_files):
        header = read_wav_header(file_path)
        
        # Verify format matches
        if header['sample_rate'] != sample_rate or header['bits_per_sample'] != bits_per_sample or header['num_channels'] != num_channels:
            print(f"Warning: {file_path} has different format, skipping...")
            continue
        
        audio_data = read_wav_data(file_path, header)
        all_audio_data.append(audio_data)
        
        # Add silence between files (except after the last one)
        if i < len(audio_files) - 1:
            all_audio_data.append(silence_data)
    
    # Combine all audio data
    combined_data = b''.join(all_audio_data)
    total_data_size = len(combined_data)
    
    # Write WAV file
    byte_rate = sample_rate * num_channels * bytes_per_sample
    block_align = num_channels * bytes_per_sample
    chunk_size = 36 + total_data_size
    
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
        total_data_size
    )
    
    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(combined_data)

@app.route('/outputs/<filename>')
def serve_audio(filename):
    """Serve audio files from the outputs directory."""
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='audio/wav')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        # Check if this is a chapter generation request
        chapter_title = request.form.get('chapter_title', '')
        save_to_file = request.form.get('save_to_file', 'false').lower() == 'true'
        
        if not text_content:
            error_msg = 'No text content provided. Please upload a file or enter text.'
            print(f"ERROR: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        print(f"Generating TTS: prompt={prompt[:50]}..., voice1={voice1}, voice2={voice2}, save_to_file={save_to_file}, chapter_title={chapter_title}")
        
        # Call the generate function with parameters
        audio_data, extension = generate_tts(text_content, prompt, voice1, voice2)
        
        print(f"Generated audio: {len(audio_data)} bytes, extension={extension}")
        
        # Save to outputs folder with timestamp if requested or always for main generate button
        if save_to_file and chapter_title:
            # Chapter generation - save with chapter title
            safe_title = sanitize_filename(chapter_title)
            output_path = os.path.join(OUTPUT_DIR, f"{safe_title}{extension}")
        else:
            # Main generate button - save with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(OUTPUT_DIR, f"tts_output_{timestamp}{extension}")
        
        # Save audio to outputs folder
        print(f"Saving audio to: {output_path}")
        with open(output_path, 'wb') as f:
            f.write(audio_data)
        print(f"Audio saved successfully to {output_path}")
        
        # Save config if this is a chapter generation
        if save_to_file and chapter_title:
            return jsonify({
                'success': True,
                'message': f'Audio saved to outputs/{os.path.basename(output_path)}',
                'file_path': output_path,
                'filename': os.path.basename(output_path)
            })
        
        # Return file for download (main generate button)
        return send_file(
            output_path,
            mimetype=f'audio/{extension[1:]}',
            as_attachment=True,
            download_name=f'tts_output{extension}'
        )
        
    except Exception as e:
        error_msg = f'Failed to generate audio: {str(e)}'
        print(f"EXCEPTION in generate_endpoint: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/generate-paragraphs', methods=['POST'])
def generate_paragraphs_endpoint():
    """Route handler for generating TTS audio paragraph by paragraph."""
    try:
        paragraphs = request.form.getlist('paragraphs[]')
        chapter_title = request.form.get('chapter_title', '')
        prompt = request.form.get('prompt', '')
        voice1 = request.form.get('voice1', 'Puck')
        voice2 = request.form.get('voice2', 'Zephyr')
        
        if not paragraphs:
            return jsonify({'error': 'No paragraphs provided'}), 400
        
        if not chapter_title:
            return jsonify({'error': 'Chapter title required'}), 400
        
        safe_title = sanitize_filename(chapter_title)
        saved_files = []
        
        # Generate TTS for each paragraph
        for index, paragraph in enumerate(paragraphs, start=1):
            if not paragraph.strip():
                continue
                
            try:
                audio_data, extension = generate_tts(paragraph, prompt, voice1, voice2)
                
                # Save to outputs folder with sequence number
                output_filename = f"{safe_title}_{index:03d}{extension}"
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                
                saved_files.append(output_filename)
            except Exception as e:
                # Continue with next paragraph if one fails
                print(f"Error generating paragraph {index}: {e}")
                continue
        
        if not saved_files:
            return jsonify({'error': 'Failed to generate any paragraphs'}), 500
        
        return jsonify({
            'success': True,
            'message': f'Generated {len(saved_files)} paragraph(s)',
            'files': saved_files,
            'output_dir': OUTPUT_DIR
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/concatenate-audio', methods=['POST'])
def concatenate_audio():
    """Concatenate multiple audio files into one with pauses."""
    try:
        data = request.json
        chapter_title = data.get('chapter_title', '')
        audio_files = data.get('audio_files', [])
        pause_seconds = data.get('pause_seconds', 1.5)  # Default 1.5 seconds
        
        print(f"Concatenate request: chapter_title={chapter_title}, audio_files={audio_files}, pause_seconds={pause_seconds}")
        
        if not chapter_title or not audio_files:
            print(f"ERROR: Missing parameters - chapter_title={chapter_title}, audio_files={audio_files}")
            return jsonify({'error': 'Chapter title and audio files required'}), 400
        
        if not isinstance(audio_files, list):
            return jsonify({'error': 'audio_files must be a list'}), 400
        
        # Save concatenated audio
        safe_title = sanitize_filename(chapter_title)
        output_filename = f"{safe_title}_cat.wav"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Try to use pydub first (if available and ffmpeg is installed)
        if PYDUB_AVAILABLE:
            try:
                combined_audio = None
                pause_ms = int(pause_seconds * 1000)
                
                for i, filename in enumerate(audio_files):
                    file_path = os.path.join(OUTPUT_DIR, filename)
                    if not os.path.exists(file_path):
                        print(f"Warning: File not found: {file_path}, skipping...")
                        continue
                    
                    audio = AudioSegment.from_wav(file_path)
                    
                    if combined_audio is None:
                        combined_audio = audio
                    else:
                        silence = AudioSegment.silent(duration=pause_ms)
                        combined_audio = combined_audio + silence + audio
                    
                    print(f"Added audio file {i+1}/{len(audio_files)}: {filename}")
                
                if combined_audio is None:
                    return jsonify({'error': 'No valid audio files found to concatenate'}), 400
                
                combined_audio.export(output_path, format="wav")
                print(f"Concatenated audio saved using pydub: {output_path}")
                
                return jsonify({
                    'success': True,
                    'message': f'Concatenated {len(audio_files)} audio file(s) with {pause_seconds}s pauses',
                    'filename': output_filename,
                    'file_path': output_path
                })
            except Exception as e:
                print(f"pydub concatenation failed: {e}, falling back to pure Python method")
        
        # Fall back to pure Python concatenation
        file_paths = []
        for filename in audio_files:
            file_path = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(file_path):
                file_paths.append(file_path)
        
        if not file_paths:
            return jsonify({'error': 'No valid audio files found to concatenate'}), 400
        
        concatenate_wav_files_pure_python(file_paths, output_path, pause_seconds)
        print(f"Concatenated audio saved using pure Python: {output_path}")
        
        return jsonify({
            'success': True,
            'message': f'Concatenated {len(file_paths)} audio file(s) with {pause_seconds}s pauses',
            'filename': output_filename,
            'file_path': output_path
        })
        
    except Exception as e:
        error_msg = f'Failed to concatenate audio: {str(e)}'
        print(f"EXCEPTION in concatenate_audio: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

