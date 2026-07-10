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
    pre-entrenados en el entorno de Google Colab de forma ultra-robusta.
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

    # 3. Instalar requerimientos de forma segura sin compilar versiones obsoletas
    print("Instalando dependencias de Python requeridas por el pipeline...")
    
    # Actualizar índices de apt e instalar ffmpeg
    os.system("apt-get update -y -qq && apt-get install -y -qq ffmpeg")
    
    # Lista de paquetes necesarios (sin pins obsoletos para evitar compilación desde código fuente)
    packages = [
        "edge-tts", 
        "moviepy", 
        "srt", 
        "yacs", 
        "gfpgan", 
        "facexlib", 
        "librosa", 
        "resampy", 
        "pydub", 
        "scipy", 
        "kornia", 
        "face_alignment", 
        "imageio", 
        "imageio-ffmpeg", 
        "numba", 
        "pyyaml", 
        "joblib", 
        "scikit-image"
    ]
    
    # Instalar paquetes en Colab
    os.system(f"pip install {' '.join(packages)}")
    print("[CONFIGURACIÓN] Entorno de SadTalker listo.")

def check_and_rename_assets():
    """
    Busca si existen archivos de imagen y los mapea a los nombres esperados.
    """
    avatar_img = "avatar.png"
    office_bg = "background.png"
    
    # Mapeo inteligente si el usuario subió las imágenes a la raíz
    images = [f for f in os.listdir(".") if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    for img in images:
        if img in [avatar_img, office_bg]:
            continue
        name_lower = img.lower()
        if "avatar" in name_lower or "presenta" in name_lower or "analista" in name_lower:
            shutil.copy(img, avatar_img)
            print(f"-> Mapeado avatar detectado: {img} -> avatar.png")
        elif "bg" in name_lower or "fondo" in name_lower or "despacho" in name_lower or "office" in name_lower:
            shutil.copy(img, office_bg)
            print(f"-> Mapeado fondo detectado: {img} -> background.png")

    if not os.path.exists(avatar_img):
        print(f"[ERROR] No se encontró el archivo del avatar '{avatar_img}' en la carpeta de ejecución.")
        print("Por favor, sube tu foto utilizando la barra lateral de archivos de Colab con el nombre 'avatar.png'.")
        return False
        
    if not os.path.exists(office_bg):
        print(f"[ERROR] No se encontró el archivo de fondo '{office_bg}' en la carpeta de ejecución.")
        print("Por favor, sube tu imagen utilizando la barra lateral de archivos de Colab con el nombre 'background.png'.")
        return False

    return True

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

    # 2. Verificar que el usuario haya subido las imágenes
    if not check_and_rename_assets():
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
    
    print("\n[PASO 1/3] Generando locución y alineando subtítulos...")
    generate_speech(custom_script, "es-ES-ElviraNeural", audio_mp3, srt_subs)

    # Convertir MP3 a WAV de 16kHz mono (formato requerido por SadTalker)
    print("Convirtiendo audio de locución a formato WAV compatible...")
    os.system(f"ffmpeg -y -i {audio_mp3} -acodec pcm_s16le -ac 1 -ar 16000 {audio_wav}")

    # 5. Ejecutar la animación facial con SadTalker en GPU
    print("\n[PASO 2/3] Animando el avatar mediante Inteligencia Artificial (GPU)...")
    sadtalker_cmd = (
        f"python SadTalker/inference.py "
        f"--driven_audio {audio_wav} "
        f"--source_image avatar.png "
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

    print("\n[PASO 3/3] Componiendo videos en formato Horizontal y Vertical...")
    
    # Compilar Horizontal (16:9)
    composite_video_for_format(
        bg_path="background.png",
        avatar_path=avatar_video,
        audio_path=audio_mp3,
        srt_path=srt_subs,
        output_path=output_horizontal,
        format_type="horizontal",
        chroma_settings={"detect_color": True, "thr": 85, "s": 5}
    )

    # Compilar Vertical (9:16)
    composite_video_for_format(
        bg_path="background.png",
        avatar_path=avatar_video,
        audio_path=audio_mp3,
        srt_path=srt_subs,
        output_path=output_vertical,
        format_type="vertical",
        chroma_settings={"detect_color": True, "thr": 85, "s": 5}
    )

    print("\n" + "="*75)
    print("  ¡VIDEO PIPELINE IA COMPLETADO CON ÉXITO!")
    print("="*75)
    print(f"1. Video Horizontal: {os.path.abspath(output_horizontal)}")
    print(f"2. Video Vertical:   {os.path.abspath(output_vertical)}")
    print("\n>>> Puedes descargar los videos directamente desde la barra lateral izquierda de Colab")
    print("    (carpeta: 'videos/output')")
    print(">>> O ejecutando en una nueva celda de Colab:")
    print("from google.colab import files")
    print("files.download('output/video_final_horizontal_16_9.mp4')")
    print("files.download('output/video_final_vertical_9_16.mp4')")
    print("="*75)

if __name__ == "__main__":
    main()
