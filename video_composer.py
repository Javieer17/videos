import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Importación compatible con MoviePy v1.x y v2.x
try:
    from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip
    from moviepy.video.fx.all import mask_color, loop
    HAS_MOVIEPY_1 = True
except ImportError:
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip
    import moviepy.video.fx as fx
    HAS_MOVIEPY_1 = False

from vtt_parser import parse_subtitles

# Capa de compatibilidad para métodos renombrados en MoviePy 2.x
def clip_with_duration(clip, duration):
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)

def clip_with_position(clip, position):
    if hasattr(clip, "with_position"):
        return clip.with_position(position)
    return clip.set_position(position)

def clip_with_audio(clip, audio):
    if hasattr(clip, "with_audio"):
        return clip.with_audio(audio)
    return clip.set_audio(audio)

def clip_subclipped(clip, start, end):
    if hasattr(clip, "subclipped"):
        return clip.subclipped(start, end)
    if hasattr(clip, "subclip"):
        return clip.subclip(start, end)
    return clip

def clip_resized(clip, size):
    if hasattr(clip, "resized"):
        return clip.resized(size)
    if hasattr(clip, "resize"):
        return clip.resize(size)
    return clip

def apply_mask_color(clip, color, thr=100, s=5):
    # Convertir a flotantes estándar para evitar desbordamiento/envoltura de uint8 en NumPy
    color_float = [float(c) for c in color]
    if HAS_MOVIEPY_1:
        return mask_color(clip, color=color_float, thr=thr, s=s)
    else:
        return clip.with_effects([fx.MaskColor(color=color_float, threshold=thr, stiffness=s)])

def apply_loop(clip, duration):
    if HAS_MOVIEPY_1:
        return loop(clip, duration=duration)
    else:
        return clip.with_effects([fx.Loop(duration=duration)])

def apply_transform(clip, func):
    if hasattr(clip, "transform"):
        return clip.transform(func)
    return clip.fl(func)

def resize_background(bg_path: str, target_w: int, target_h: int) -> Image.Image:
    """
    Redimensiona y recorta una imagen de fondo para que llene exactamente
    las dimensiones especificadas (crop-to-fill) sin deformarla.
    """
    if not os.path.exists(bg_path):
        # Crear un fondo de color sólido (gris oscuro cinemático) si no existe la imagen
        print(f"Advertencia: No se encontró la imagen de fondo en {bg_path}. Creando un fondo sólido.")
        return Image.new("RGB", (target_w, target_h), (30, 30, 35))

    im = Image.open(bg_path)
    target_aspect = target_w / target_h
    im_w, im_h = im.size
    im_aspect = im_w / im_h
    
    if im_aspect > target_aspect:
        # La imagen es más ancha que la proporción objetivo -> redimensionar por altura
        new_h = target_h
        new_w = int(im_w * (target_h / im_h))
        im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
        # Recortar el centro horizontalmente
        left = (new_w - target_w) // 2
        im_cropped = im_resized.crop((left, 0, left + target_w, target_h))
    else:
        # La imagen es más alta que la proporción objetivo -> redimensionar por ancho
        new_w = target_w
        new_h = int(im_h * (target_w / im_w))
        im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
        # Recortar el centro verticalmente
        top = (new_h - target_h) // 2
        im_cropped = im_resized.crop((0, top, target_w, top + target_h))
        
    return im_cropped

def get_system_font(font_name: str = "arial.ttf") -> str:
    """
    Busca una fuente TrueType estándar en las carpetas comunes de Windows.
    """
    paths = [
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", font_name),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft\\Windows\\Fonts", font_name),
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    # Intentar retornar la fuente en el directorio de ejecución actual
    if os.path.exists(font_name):
        return font_name
    return None

def draw_subtitles_on_frame(
    frame: np.ndarray,
    t: float,
    subtitles: list,
    width: int,
    height: int,
    font_path: str,
    font_size: int,
    y_position: int,
    text_color: tuple = (255, 255, 255),
    outline_color: tuple = (0, 0, 0)
) -> np.ndarray:
    """
    Dibuja los subtítulos activos en el segundo 't' sobre el frame de video.
    """
    active_text = ""
    for sub in subtitles:
        if sub['start'] <= t <= sub['end']:
            active_text = sub['text']
            break
            
    if not active_text:
        return frame

    # Crear una imagen PIL a partir del frame (copia de seguridad por si es de solo lectura)
    img = Image.fromarray(frame.copy())
    draw = ImageDraw.Draw(img)
    
    # Cargar fuente
    if font_path and os.path.exists(font_path):
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    # Ajuste de línea automático (Word Wrapping) al 80% del ancho de pantalla
    max_width = int(width * 0.8)
    words = active_text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        try:
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
        except AttributeError:
            line_width, _ = draw.textsize(test_line, font=font)
            
        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))

    # Calcular la altura total del bloque de texto
    line_heights = []
    for line in lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            h = bbox[3] - bbox[1]
        except AttributeError:
            _, h = draw.textsize(line, font=font)
        line_heights.append(h if h > 0 else font_size)
        
    total_text_height = sum(line_heights) + (len(lines) - 1) * 6
    
    # Y inicial centrado respecto a la posición y_position configurada
    current_y = y_position - (total_text_height // 2)
    
    for i, line in enumerate(lines):
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
        except AttributeError:
            w, _ = draw.textsize(line, font=font)
            
        # Centrar horizontalmente
        x = (width - w) // 2
        
        # Dibujar texto con contorno para garantizar legibilidad
        try:
            draw.text((x, current_y), line, font=font, fill=text_color, stroke_width=3, stroke_fill=outline_color)
        except TypeError:
            # Fallback para versiones muy antiguas de Pillow sin stroke_width
            for dx in [-2, -1, 1, 2]:
                for dy in [-2, -1, 1, 2]:
                    draw.text((x + dx, current_y + dy), line, font=font, fill=outline_color)
            draw.text((x, current_y), line, font=font, fill=text_color)
            
        current_y += line_heights[i] + 6
        
    return np.array(img)

def composite_video_for_format(
    bg_path: str,
    avatar_path: str,
    audio_path: str,
    srt_path: str,
    output_path: str,
    format_type: str = "horizontal",
    chroma_settings: dict = None
):
    """
    Compone el video final aplicando chroma key, redimensionamiento,
    combinación de audio y renderizado de subtítulos según el formato.
    """
    if chroma_settings is None:
        chroma_settings = {"detect_color": True, "color": [0, 255, 0], "thr": 25, "s": 5}

    # Definir resoluciones de salida
    if format_type == "horizontal":
        target_w, target_h = 1920, 1080
        font_size = 42
        y_pos = int(target_h * 0.85) # Cerca de la parte inferior
    else:
        target_w, target_h = 1080, 1920
        font_size = 58
        y_pos = int(target_h * 0.45) # Parte media-superior (ideal para Shorts/Reels)

    print(f"\n--- Iniciando composición para formato {format_type.upper()} ({target_w}x{target_h}) ---")
    
    # Cargar audio de voz
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"No se encontró el audio de locución en: {audio_path}")
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    
    # 1. Crear el clip de fondo adaptado al formato
    bg_img = resize_background(bg_path, target_w, target_h)
    bg_clip = clip_with_duration(ImageClip(np.array(bg_img)), duration)
    
    # 2. Cargar e integrar el avatar en croma si existe
    if os.path.exists(avatar_path):
        print(f"Cargando avatar de video: {avatar_path}")
        avatar_clip = clip_with_audio(VideoFileClip(avatar_path), None)
        
        # Ajustar duración (repetir en bucle si es más corto, recortar si es más largo)
        if avatar_clip.duration < duration:
            print("El video del avatar es más corto que el audio, repitiéndolo en bucle...")
            avatar_clip = apply_loop(avatar_clip, duration=duration)
        else:
            avatar_clip = clip_subclipped(avatar_clip, 0, duration)
            
        # Detectar el color de fondo para el croma
        if chroma_settings.get("detect_color", True):
            first_frame = avatar_clip.get_frame(0)
            bg_color = [int(x) for x in first_frame[0, 0]]
            print(f"Color de fondo detectado en el primer pixel (croma): {bg_color}")
        else:
            bg_color = chroma_settings.get("color", [0, 255, 0])
            
        # Aplicar el efecto de Croma Key
        masked_avatar = apply_mask_color(
            avatar_clip, 
            color=bg_color, 
            thr=chroma_settings.get("thr", 100), 
            s=chroma_settings.get("s", 5)
        )
        
        # Redimensionar el avatar
        if format_type == "horizontal":
            # Ocupar el 70% de la altura de la pantalla
            avatar_h = int(target_h * 0.70)
        else:
            # En vertical el avatar se hace más grande, ocupando el 60%
            avatar_h = int(target_h * 0.60)
            
        avatar_w = int(avatar_clip.w * (avatar_h / avatar_clip.h))
        scaled_avatar = clip_resized(masked_avatar, (avatar_w, avatar_h))
        
        # Componer avatar sobre fondo
        # El avatar siempre se posiciona abajo al centro
        composite_clip = CompositeVideoClip([
            bg_clip, 
            clip_with_position(scaled_avatar, ("center", "bottom"))
        ])
    else:
        print("No se encontró archivo de avatar.mp4. Se generará el video usando solo el fondo y la locución.")
        composite_clip = bg_clip

    # Vincular el audio al video compuesto
    composite_clip = clip_with_audio(composite_clip, audio_clip)

    # 3. Cargar y parsear subtítulos
    subtitles = parse_subtitles(srt_path)
    font_path = get_system_font("arial.ttf")
    
    if font_path:
        print(f"Usando fuente del sistema: {font_path}")
    else:
        print("No se encontró Arial. Se usará la fuente por defecto de Pillow.")

    # Aplicar filtro de fotograma para renderizar los subtítulos
    final_clip = apply_transform(
        composite_clip,
        lambda gf, t: draw_subtitles_on_frame(
            gf(t), t, subtitles, target_w, target_h,
            font_path=font_path, font_size=font_size, y_position=y_pos
        )
    )

    # 4. Renderizar y exportar el archivo de video final
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    print(f"Exportando video a: {output_path}")
    
    # Usar settings eficientes para la codificación
    final_clip.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="medium"
    )
    
    # Cerrar clips para liberar memoria
    audio_clip.close()
    composite_clip.close()
    if os.path.exists(avatar_path):
        avatar_clip.close()
    final_clip.close()
    print(f"Exportación de {format_type.upper()} completada con éxito.")

if __name__ == "__main__":
    # Prueba rápida del compositor si existen archivos
    try:
        composite_video_for_format(
            bg_path="output/test_bg.png",
            avatar_path="output/test_avatar.mp4",
            audio_path="output/test_audio.mp3",
            srt_path="output/test_subs.srt",
            output_path="output/test_horizontal.mp4",
            format_type="horizontal"
        )
    except Exception as e:
        print(f"Prueba del script: {e} (Esto es normal si no hay archivos de prueba creados)")
