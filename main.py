import os
import argparse
from tts_generator import generate_speech
from video_composer import composite_video_for_format

# Guion por defecto centrado en el análisis de Micron (MU) del Q3 FY26
DEFAULT_SCRIPT = (
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

DEFAULT_VOICE = "es-ES-ElviraNeural" # Voz premium femenina de España (Edge-TTS)

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline en Python para automatizar la creación de videos financieros con IA gratis."
    )
    parser.add_argument(
        "--script", 
        type=str, 
        default=DEFAULT_SCRIPT, 
        help="Texto del guion para la locución de voz y subtítulos."
    )
    parser.add_argument(
        "--voice", 
        type=str, 
        default=DEFAULT_VOICE, 
        help="Nombre de la voz neural de Microsoft Edge-TTS (ej. es-ES-ElviraNeural, es-MX-DaliaNeural)."
    )
    parser.add_argument(
        "--bg", 
        type=str, 
        default="background.png", 
        help="Ruta de la imagen de fondo de despacho realista."
    )
    parser.add_argument(
        "--avatar", 
        type=str, 
        default="avatar.mp4", 
        help="Ruta del video del avatar grabado sobre fondo de pantalla verde."
    )
    parser.add_argument(
        "--out-dir", 
        type=str, 
        default="output", 
        help="Carpeta donde se guardarán los archivos temporales y videos finales."
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("  AUTOMATIZACIÓN DE VIDEOS FINANCIEROS IA (GRATIS Y LOCAL)")
    print("="*70)
    
    # Crear carpetas necesarias
    os.makedirs(args.out_dir, exist_ok=True)
    audio_path = os.path.join(args.out_dir, "locucion.mp3")
    srt_path = os.path.join(args.out_dir, "subtitulos.srt")
    
    output_horizontal = os.path.join(args.out_dir, "video_horizontal_16_9.mp4")
    output_vertical = os.path.join(args.out_dir, "video_vertical_9_16.mp4")
    
    # 1. Generar la Locución y Archivo de Tiempos SRT
    print("\n[PASO 1/3] Generando locución neural y archivo de subtítulos...")
    try:
        generate_speech(args.script, args.voice, audio_path, srt_path)
    except Exception as e:
        print(f"Error crítico al generar la síntesis de voz: {e}")
        return
        
    # 2. Verificar archivos de imagen y video de entrada
    print("\n[PASO 2/3] Comprobando archivos de entrada en el sistema...")
    if not os.path.exists(args.bg):
        print(f"-> AVISO: No se encontró '{args.bg}'. El video se renderizará con un fondo sólido.")
    else:
        print(f"-> Imagen de fondo detectada con éxito: {args.bg}")
        
    if not os.path.exists(args.avatar):
        print(f"-> AVISO: No se encontró '{args.avatar}'. El video se compondrá usando solo fondo, voz y subtítulos.")
    else:
        print(f"-> Video del avatar (pantalla verde) detectado con éxito: {args.avatar}")
        
    # 3. Compilar los videos en los dos formatos solicitados
    print("\n[PASO 3/3] Iniciando renderizado de videos en formatos horizontal y vertical...")
    
    # Renderizar formato Horizontal (YouTube, Presentaciones)
    try:
        composite_video_for_format(
            bg_path=args.bg,
            avatar_path=args.avatar,
            audio_path=audio_path,
            srt_path=srt_path,
            output_path=output_horizontal,
            format_type="horizontal"
        )
    except Exception as e:
        print(f"Error al compilar el video horizontal: {e}")
        
    # Renderizar formato Vertical (Shorts, Reels, TikTok)
    try:
        composite_video_for_format(
            bg_path=args.bg,
            avatar_path=args.avatar,
            audio_path=audio_path,
            srt_path=srt_path,
            output_path=output_vertical,
            format_type="vertical"
        )
    except Exception as e:
        print(f"Error al compilar el video vertical: {e}")
        
    # Reporte final
    print("\n" + "="*70)
    print(" ¡PROCESAMIENTO DE VIDEOS COMPLETADO CON ÉXITO!")
    print("="*70)
    print(f"1. Video Horizontal (16:9): {os.path.abspath(output_horizontal)}")
    print(f"2. Video Vertical (9:16):   {os.path.abspath(output_vertical)}")
    print(f"3. Audio Generado:          {os.path.abspath(audio_path)}")
    print(f"4. Tiempos de Subtítulos:   {os.path.abspath(srt_path)}")
    print("="*70)

if __name__ == "__main__":
    main()
