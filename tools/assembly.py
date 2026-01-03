import subprocess
import os

def combine_video_audio(video_path, audio_path, output_path="final_output.mp4"):
    """
    Merges video and audio using FFmpeg.
    """
    if not os.path.exists(video_path):
        print(f"[Assembly] Error: Video file {video_path} not found.")
        return False
        
    if not os.path.exists(audio_path):
        print(f"[Assembly] Warning: Audio file {audio_path} not found. Returning video only.")
        # If no audio, just rename/copy video to output
        os.rename(video_path, output_path)
        return True

    # command: ffmpeg -y -i video.mp4 -i audio.wav -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-map', '0:v:0',
        '-map', '1:a:0',
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[Assembly] Success: Merged into {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[Assembly] FFmpeg failed: {e}")
        return False
    except FileNotFoundError:
        print("[Assembly] Error: 'ffmpeg' not found. Please install FFmpeg.")
        return False
