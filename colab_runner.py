import os
import sys
import shutil
import glob

def check_colab() -> bool:
    """
    Verifica si el entorno de ejecución es Google Colab.
    """
    try:
        import google.colab
        return True
    except ImportError:
        return False

def setup_sadtalker():
    """
    Descarga e instala automáticamente el repositorio de SadTalker y sus modelos
    pre-entrenados en el entorno de Google Colab.
    """
    print("\n[CONFIGURACIÓN] Preparando entorno de SadTalker...")
    
    # 1. Clonar SadTalker si no existe
    if not os.path.exists("SadTalker"):
        print("Clonando el repositorio oficial de SadTalker...")
        os.system("git clone https://github.com/Winfredy/SadTalker.git")
        
    # 2. Descargar checkpoints usando el script oficial
    if not os.path.exists("SadTalker/checkpoints"):
        print("Descargando modelos pre-entrenados de SadTalker (peso aprox 1-2 GB)...")
        current_dir = os.getcwd()
        os.chdir("SadTalker")
        # Ejecutar el script bash de descarga
        os.system("bash scripts/download_models.sh")
        os.chdir(current_dir)
        print("Descarga de modelos completada con éxito.")
    else:
        print("Modelos pre-entrenados ya detectados.")

    # 3. Instalar requerimientos específicos
    print("Instalando dependencias de Python requeridas por el pipeline...")
    # Asegurar distutils en Colab para evitar fallos de librerías antiguas
    os.system("apt-get install -y python3-pip ffmpeg")
    os.system("pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113")
    os.system("pip install -r SadTalker/requirements.txt")
    print("[CONFIGURACIÓN] Entorno de SadTalker listo.")

def upload_assets():
    """
    Solicita al usuario subir su foto del avatar y el fondo de oficina,
    identificándolos inteligentemente por nombre o tipo.
    """
    from google.colab import files
    print("\n[SUBIDA] Sube la foto del avatar (rostro claro, preferiblemente con fondo verde sólido) y el fondo de la oficina:")
    uploaded = files.upload()
    
    avatar_path = None
    bg_path = None
    
    # Intentar identificar según el nombre del archivo subido
    for filename in uploaded.keys():
        name_lower = filename.lower()
        if "avatar" in name_lower or "presenta" in name_lower or "analista" in name_lower:
            shutil.copy(filename, "avatar.png")
            avatar_path = "avatar.png"
            print(f"-> Identificado Avatar: {filename} (guardado como avatar.png)")
        elif "bg" in name_lower or "fondo" in name_lower or "despacho" in name_lower or "office" in name_lower:
            shutil.copy(filename, "background.png")
            bg_path = "background.png"
            print(f"-> Identificado Fondo: {filename} (guardado como background.png)")

    # Fallback si los nombres no contienen las palabras clave
    images = [f for f in uploaded.keys() if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not avatar_path and len(images) > 0:
        shutil.copy(images[0], "avatar.png")
        avatar_path = "avatar.png"
        print(f"-> Asignado {images[0]} como avatar.png (primer archivo)")
    if not bg_path and len(images) > 1:
        shutil.copy(images[1], "background.png")
        bg_path = "background.png"
        print(f"-> Asignado {images[1]} como background.png (segundo archivo)")

    return avatar_path, bg_path

def main():
    if not check_colab():
        print("[ERROR] Este script está diseñado para ejecutarse exclusivamente dentro de Google Colab.")
        print("Si deseas probarlo localmente, utiliza 'python main.py' con tus archivos locales.")
        sys.exit(1)

    print("="*75)
    print("  PROCESADOR CLOUD AUTOMÁTICO DE VIDEO IA - FINANZAS (GOOGLE COLAB)")
    print("="*75)

    # 1. Configurar instalación de dependencias y modelos (esto instala edge-tts, moviepy, etc.)
    setup_sadtalker()

    # Importación diferida para evitar ModuleNotFoundError antes de la instalación de paquetes
    print("\nCargando módulos de composición y locución...")
    from tts_generator import generate_speech
    from video_composer import composite_video_for_format

    # 2. Solicitar al usuario subir las imágenes
    avatar_img, office_bg = upload_assets()
    
    if not avatar_img or not office_bg:
        print("[ERROR] Debes subir al menos la imagen de avatar y la imagen de fondo para proceder.")
        sys.exit(1)

    # 3. Preguntar por el guion
    print("\n[GUION] Introduce el texto que dirá tu presentadora.")
    print("Presiona ENTER para usar el guion por defecto sobre Micron (MU):")
    custom_script = input("> ").strip()
    
    # Guion por defecto si no introduce nada
    if not custom_script:
        custom_script = (
            "Hola a todos. Si estás buscando las mejores oportunidades en el sector tecnológico, "
            "hay un gigante del que tienes que estar hablando hoy mismo: Micron Technology, ticker M-U. "
            "Micron reportó ingresos trimestrales récord por 41.460 millones de dólares, lo que representa "
            "un aumento brutal del 346% interanual impulsado por el superciclo de memoria HBM para servidores "
            "de Inteligencia Artificial. Esto disparó su beneficio por acción a 25,11 dólares. "
            "Sin embargo, la acción cotiza a un ratio P-E futuro de solo 6,5 veces, reflejando escepticismo "
            "del mercado sobre la sostenibilidad a largo plazo de este ciclo. Expertos que ganaron más de "
            "un 150% con la empresa ya han vendido posiciones. Para trading de corto plazo, Micron ofrece "
            "volatilidad y oportunidades increíbles, pero para inversión a largo plazo es prudente esperar "
            "confirmación técnica de cambio de tendencia."
        )

    # 4. Generar locución de voz y subtítulos (Edge-TTS)
    os.makedirs("output", exist_ok=True)
    audio_mp3 = "output/locucion.mp3"
    audio_wav = "output/locucion.wav"
    srt_subs = "output/subtitulos.srt"
    
    print("\n[PASO 1/4] Generando locución y alineando subtítulos...")
    generate_speech(custom_script, "es-ES-ElviraNeural", audio_mp3, srt_subs)

    # Convertir MP3 a WAV de 16kHz mono (formato requerido por SadTalker)
    print("Convirtiendo audio de locución a formato WAV compatible...")
    os.system(f"ffmpeg -y -i {audio_mp3} -acodec pcm_s16le -ac 1 -ar 16000 {audio_wav}")

    # 5. Ejecutar la animación facial con SadTalker en GPU
    print("\n[PASO 2/4] Animando el avatar mediante Inteligencia Artificial (GPU)...")
    sadtalker_cmd = (
        f"python SadTalker/inference.py "
        f"--driven_audio {audio_wav} "
        f"--source_image {avatar_img} "
        f"--result_dir output/sadtalker_temp "
        f"--still "
        f"--preprocess full "
        f"--enhancer gfpgan"
    )
    os.system(sadtalker_cmd)

    # Buscar el video del avatar generado en la carpeta de resultados temporales
    generated_videos = glob.glob("output/sadtalker_temp/*.mp4")
    if not generated_videos:
        print("[ERROR] Falló la generación del presentador animado de SadTalker.")
        sys.exit(1)
    
    avatar_video = "output/avatar_talking.mp4"
    # Copiar el último video generado a nuestra ruta estándar
    shutil.copy(sorted(generated_videos)[-1], avatar_video)
    print(f"-> Presentador animado guardado en: {avatar_video}")

    # 6. Composición final usando nuestro video_composer
    output_horizontal = "output/video_final_horizontal_16_9.mp4"
    output_vertical = "output/video_final_vertical_9_16.mp4"

    print("\n[PASO 3/4] Componiendo videos en formato Horizontal y Vertical...")
    
    # Compilar Horizontal (16:9)
    composite_video_for_format(
        bg_path=office_bg,
        avatar_path=avatar_video,
        audio_path=audio_mp3,
        srt_path=srt_subs,
        output_path=output_horizontal,
        format_type="horizontal",
        chroma_settings={"detect_color": True, "thr": 85, "s": 5}
    )

    # Compilar Vertical (9:16)
    composite_video_for_format(
        bg_path=office_bg,
        avatar_path=avatar_video,
        audio_path=audio_mp3,
        srt_path=srt_subs,
        output_path=output_vertical,
        format_type="vertical",
        chroma_settings={"detect_color": True, "thr": 85, "s": 5}
    )

    # 7. Descargar automáticamente los videos finales generados
    print("\n[PASO 4/4] Iniciando descarga automática de los videos compilados...")
    from google.colab import files
    
    if os.path.exists(output_horizontal):
        print(f"Descargando Video Horizontal: {output_horizontal}")
        files.download(output_horizontal)
        
    if os.path.exists(output_vertical):
        print(f"Descargando Video Vertical: {output_vertical}")
        files.download(output_vertical)

    print("\n" + "="*75)
    print("  ¡VIDEO PIPELINE IA COMPLETADO CON ÉXITO!")
    print("="*75)

if __name__ == "__main__":
    main()
