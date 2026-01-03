import subprocess
import wave
import contextlib
import os

# Default Piper configuration - adjust paths as needed for the environment
# Assumes 'piper' binary is in PATH or alias.
# For Colab/Linux, usually: echo 'text' | piper --model ... --output_file ...

def get_audio_duration(wav_path):
    """Returns the duration of a wav file in seconds."""
    with contextlib.closing(wave.open(wav_path, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        return frames / float(rate)

def generate_speech(text, output_file="output.wav", model_path="en_US-lessac-medium.onnx"):
    """
    Generates speech from text using Piper TTS.
    Returns the duration of the generated audio in seconds.
    """
    
    # Check if model exists (optional, depends on setup)
    # command = f"echo '{text}' | piper --model {model_path} --output_file {output_file}"
    
    # Using subprocess securely
    try:
        # We assume 'piper' is installed and in PATH.
        # If running via a specific binary path, change 'piper' to that path.
        # This matches the architecture doc: echo 'Hello' | piper ...
        
        ps = subprocess.Popen(['echo', text], stdout=subprocess.PIPE)
        subprocess.run(
            ['piper', '--model', model_path, '--output_file', output_file],
            stdin=ps.stdout,
            check=True
        )
        ps.wait()
        
        if os.path.exists(output_file):
            duration = get_audio_duration(output_file)
            print(f"[Audio] Generated {output_file} ({duration:.2f}s)")
            return duration
        else:
            print(f"[Audio] Error: Output file {output_file} not created.")
            return 0.0
            
    except subprocess.CalledProcessError as e:
        print(f"[Audio] Piper execution failed: {e}")
        return 0.0
    except FileNotFoundError:
        print("[Audio] Error: 'piper' command not found. Please install Piper TTS.")
        return 0.0
