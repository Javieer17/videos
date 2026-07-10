import os
import numpy as np
from PIL import Image

# Importación compatible con MoviePy v1.x y v2.x
try:
    from moviepy.editor import ColorClip, VideoClip
    from moviepy.audio.AudioClip import AudioArrayClip
except ImportError:
    from moviepy import ColorClip, VideoClip
    from moviepy.audio.AudioClip import AudioArrayClip

from video_composer import composite_video_for_format

def create_dummy_assets():
    """
    Genera activos de prueba falsos para verificar la composición del video sin internet.
    """
    print("Creando activos ficticios para pruebas sin internet...")
    os.makedirs("test_assets", exist_ok=True)
    
    # 1. Crear fondo ficticio (Imagen de 1920x1080)
    bg_path = "test_assets/dummy_bg.png"
    if not os.path.exists(bg_path):
        img = Image.new("RGB", (1920, 1080), (45, 52, 54)) # Gris azulado oscuro
        img.save(bg_path)
        print(f"- Creado fondo de prueba: {bg_path}")
        
    # 2. Crear audio ficticio de silencio (10 segundos)
    audio_path = "test_assets/dummy_audio.mp3"
    if not os.path.exists(audio_path):
        # 10 segundos a 44.1 kHz, estéreo (silencio absoluto)
        silence_array = np.zeros((44100 * 10, 2))
        audio = AudioArrayClip(silence_array, fps=44100)
        audio.write_audiofile(audio_path, fps=44100)
        print(f"- Creado audio de prueba (silencioso): {audio_path}")

    # 3. Crear avatar ficticio en pantalla verde (10 segundos de video verde puro)
    avatar_path = "test_assets/dummy_avatar.mp4"
    if not os.path.exists(avatar_path):
        # Función para dibujar un círculo rojo moviéndose sobre fondo verde
        def make_frame(t):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:, :] = [0, 255, 0] # Fondo verde
            
            # Círculo rojo moviéndose
            cy = int(240 + 50 * np.sin(t * np.pi))
            cx = 320
            r = 80
            
            # Dibujar directamente en numpy
            y, x = np.ogrid[:480, :640]
            mask = (x - cx)**2 + (y - cy)**2 <= r**2
            frame[mask] = [231, 76, 60] # Rojo
            return frame
            
        motion_clip = VideoClip(make_frame)
        if hasattr(motion_clip, "with_duration"):
            motion_clip = motion_clip.with_duration(10)
        else:
            motion_clip = motion_clip.set_duration(10)
            
        motion_clip.write_videofile(avatar_path, fps=24, codec="libx264")
        print(f"- Creado avatar verde de prueba: {avatar_path}")

    # 4. Crear archivo SRT de prueba
    srt_path = "test_assets/dummy_subs.srt"
    test_srt = """1
00:00:00,500 --> 00:00:03,500
Hola, esta es una prueba del
compositor de video de Micron.

2
00:00:04,000 --> 00:00:07,000
El chroma key y los subtítulos
se aplican correctamente.

3
00:00:07,500 --> 00:00:09,500
¡El renderizado vertical y
horizontal funciona!
"""
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(test_srt)
    print(f"- Creado subtítulo de prueba: {srt_path}")

    return bg_path, avatar_path, audio_path, srt_path

def main():
    bg_path, avatar_path, audio_path, srt_path = create_dummy_assets()
    
    os.makedirs("test_output", exist_ok=True)
    
    print("\n--- Ejecutando composición de prueba horizontal (16:9) ---")
    composite_video_for_format(
        bg_path=bg_path,
        avatar_path=avatar_path,
        audio_path=audio_path,
        srt_path=srt_path,
        output_path="test_output/test_horizontal.mp4",
        format_type="horizontal",
        chroma_settings={"detect_color": True, "thr": 80, "s": 5}
    )
    
    print("\n--- Ejecutando composición de prueba vertical (9:16) ---")
    composite_video_for_format(
        bg_path=bg_path,
        avatar_path=avatar_path,
        audio_path=audio_path,
        srt_path=srt_path,
        output_path="test_output/test_vertical.mp4",
        format_type="vertical",
        chroma_settings={"detect_color": True, "thr": 80, "s": 5}
    )
    
    print("\nPruebas completadas con éxito. Verifica la carpeta 'test_output/'.")

if __name__ == "__main__":
    main()
