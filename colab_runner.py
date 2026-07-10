import os
import sys
import shutil
import glob
import subprocess
import site


def check_colab() -> bool:
    try:
        import google.colab
        return True
    except ImportError:
        return False


def _download_file(url, dest):
    """Descarga un archivo con verificación. Reintenta si falla."""
    import urllib.request
    dest_dir = os.path.dirname(dest)
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 1_000_000:
        return  # ya descargado y tiene tamaño razonable
    basename = os.path.basename(dest)
    print(f"   ↓ Descargando {basename}...")
    for attempt in range(3):
        try:
            urllib.request.urlretrieve(url, dest)
            size_mb = os.path.getsize(dest) / 1_048_576
            print(f"     ✓ {basename} ({size_mb:.0f} MB)")
            return
        except Exception as e:
            print(f"     ⚠ Intento {attempt+1} fallido: {e}")
    print(f"     ✗ ERROR: No se pudo descargar {basename}")
    sys.exit(1)


def download_sadtalker_models():
    """Descarga cada checkpoint de SadTalker individualmente con verificación."""
    base = "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc"
    gfpgan_base = "https://github.com/xinntao/facexlib/releases/download"
    gfpgan_v1 = "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0"

    # Checkpoints principales de SadTalker
    models = [
        (f"{base}/mapping_00109-model.pth.tar",         "SadTalker/checkpoints/mapping_00109-model.pth.tar"),
        (f"{base}/mapping_00229-model.pth.tar",         "SadTalker/checkpoints/mapping_00229-model.pth.tar"),
        (f"{base}/SadTalker_V0.0.2_256.safetensors",    "SadTalker/checkpoints/SadTalker_V0.0.2_256.safetensors"),
        (f"{base}/SadTalker_V0.0.2_512.safetensors",    "SadTalker/checkpoints/SadTalker_V0.0.2_512.safetensors"),
        ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2/epoch_20.pth", "SadTalker/checkpoints/epoch_20.pth"),
        # Pesos de GFPGAN para el enhancer facial
        (f"{gfpgan_base}/v0.1.0/alignment_WFLW_4HG.pth",     "SadTalker/gfpgan/weights/alignment_WFLW_4HG.pth"),
        (f"{gfpgan_base}/v0.1.0/detection_Resnet50_Final.pth","SadTalker/gfpgan/weights/detection_Resnet50_Final.pth"),
        (f"{gfpgan_v1}/GFPGANv1.4.pth",                      "SadTalker/gfpgan/weights/GFPGANv1.4.pth"),
        (f"{gfpgan_base}/v0.2.2/parsing_parsenet.pth",        "SadTalker/gfpgan/weights/parsing_parsenet.pth"),
    ]

    # Verificar si todos ya existen
    all_present = all(
        os.path.exists(dest) and os.path.getsize(dest) > 1_000_000
        for _, dest in models
    )
    if all_present:
        print("Modelos pre-entrenados ya verificados ✓")
        return

    print("Descargando modelos pre-entrenados (~2 GB)...")
    for url, dest in models:
        _download_file(url, dest)
    print("Descarga de modelos completada ✓")


def setup_sadtalker():
    """
    Descarga e instala SadTalker y sus modelos pre-entrenados,
    luego parchea todas las incompatibilidades conocidas con Python 3.12
    y las versiones modernas de numpy/torchvision instaladas en Colab.
    """
    print("\n[CONFIGURACIÓN] Preparando entorno de SadTalker...")

    # 1. Clonar SadTalker
    if not os.path.exists("SadTalker"):
        print("Clonando el repositorio oficial de SadTalker...")
        os.system("git clone https://github.com/Winfredy/SadTalker.git")

    # 2. Descargar checkpoints individualmente (el script bash falla silenciosamente)
    download_sadtalker_models()

    # 3. Instalar paquetes (sin bajar numpy — eso rompe jax, opencv, cupy, etc.)
    print("Instalando dependencias de Python...")
    os.system("apt-get update -y -qq && apt-get install -y -qq ffmpeg")

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
        "scikit-image",
    ]
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-q"] + packages
    )

    # 4. Parchear incompatibilidades conocidas
    patch_compatibility()
    print("[CONFIGURACIÓN] Entorno listo.\n")


# ────────────────────────────────────────────────────────────────
#  PARCHES DE COMPATIBILIDAD
#  SadTalker + gfpgan + basicsr fueron escritos para Python 3.8,
#  numpy 1.x y torchvision < 0.18.  Colab 2026 usa Python 3.12,
#  numpy 2.x y torchvision 0.26.  En vez de degradar numpy
#  (rompe 10+ paquetes de Colab), parcheamos las líneas exactas.
# ────────────────────────────────────────────────────────────────
def patch_compatibility():
    """Aplica todos los parches necesarios para que SadTalker funcione
    con las versiones modernas de numpy, torchvision y Python."""

    print("[PARCHES] Aplicando correcciones de compatibilidad...")
    count = 0

    # --- Parche 1: numpy.VisibleDeprecationWarning (eliminado en numpy 2.0) ---
    # Archivo: SadTalker/src/face3d/util/preprocess.py
    p1 = os.path.join("SadTalker", "src", "face3d", "util", "preprocess.py")
    if os.path.exists(p1):
        count += _replace_in_file(
            p1,
            "np.VisibleDeprecationWarning",
            "DeprecationWarning",
            "numpy.VisibleDeprecationWarning → DeprecationWarning",
        )
        count += _replace_in_file(
            p1,
            "trans_params = np.array([w0, h0, s, t[0], t[1]])",
            "trans_params = np.array([float(w0), float(h0), float(s), float(t[0]), float(t[1])])",
            "Inhomogeneous shape in trans_params → float cast",
        )

    # --- Parche 2: torchvision.transforms.functional_tensor (eliminado en torchvision ≥ 0.18) ---
    # Archivo: basicsr/data/degradations.py  (paquete instalado en site-packages)
    sp = site.getsitepackages()[0]
    p2 = os.path.join(sp, "basicsr", "data", "degradations.py")
    if os.path.exists(p2):
        count += _replace_in_file(
            p2,
            "from torchvision.transforms.functional_tensor import rgb_to_grayscale",
            "from torchvision.transforms.functional import rgb_to_grayscale",
            "torchvision.transforms.functional_tensor → functional",
        )

    # --- Parche 3: numpy.bool / numpy.int / numpy.float / numpy.complex (eliminados en numpy 1.24+) ---
    # Pueden aparecer en múltiples archivos de SadTalker y basicsr.
    # Recorremos todos los .py de SadTalker buscando usos obsoletos.
    for root, dirs, files in os.walk("SadTalker"):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            new_content = content
            new_content = new_content.replace("np.bool,", "bool,")
            new_content = new_content.replace("np.bool)", "bool)")
            new_content = new_content.replace("np.int,", "int,")
            new_content = new_content.replace("np.int)", "int)")
            new_content = new_content.replace("np.float,", "float,")
            new_content = new_content.replace("np.float)", "float)")
            new_content = new_content.replace("np.complex,", "complex,")
            new_content = new_content.replace("np.complex)", "complex)")
            # np.str y np.object
            new_content = new_content.replace("np.str,", "str,")
            new_content = new_content.replace("np.str)", "str)")
            new_content = new_content.replace("np.object,", "object,")
            new_content = new_content.replace("np.object)", "object)")

            if new_content != content:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                count += 1

    # --- Parche 4: distutils.version.LooseVersion (eliminado en Python 3.12) ---
    # Puede aparecer en basicsr u otros paquetes.
    for pkg_name in ["basicsr", "gfpgan", "facexlib"]:
        pkg_dir = os.path.join(sp, pkg_name)
        if not os.path.isdir(pkg_dir):
            continue
        for root, dirs, files in os.walk(pkg_dir):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue

                new_content = content
                # Reemplazar import de distutils.version
                new_content = new_content.replace(
                    "from distutils.version import LooseVersion",
                    "from packaging.version import Version as LooseVersion",
                )
                # Torchvision functional_tensor en cualquier archivo de basicsr
                new_content = new_content.replace(
                    "from torchvision.transforms.functional_tensor import rgb_to_grayscale",
                    "from torchvision.transforms.functional import rgb_to_grayscale",
                )

                if new_content != content:
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    count += 1

    print(f"[PARCHES] {count} archivo(s) parcheado(s) correctamente.")


def _replace_in_file(filepath, old, new, description):
    """Reemplaza una cadena en un archivo. Devuelve 1 si se hizo cambio, 0 si no."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if old in content:
            content = content.replace(old, new)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"   ✓ {description}")
            return 1
    except Exception as e:
        print(f"   ✗ Error parcheando {filepath}: {e}")
    return 0


# ────────────────────────────────────────────────────────────────
def check_and_rename_assets():
    """Verifica que avatar.png y background.png existan."""
    avatar_img = "avatar.png"
    office_bg = "background.png"

    images = [
        f for f in os.listdir(".")
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    for img in images:
        if img in (avatar_img, office_bg):
            continue
        lo = img.lower()
        if any(k in lo for k in ("avatar", "presenta", "analista")):
            shutil.copy(img, avatar_img)
            print(f"   → Mapeado: {img} → avatar.png")
        elif any(k in lo for k in ("bg", "fondo", "despacho", "office")):
            shutil.copy(img, office_bg)
            print(f"   → Mapeado: {img} → background.png")

    ok = True
    if not os.path.exists(avatar_img):
        print("[ERROR] Falta avatar.png — súbelo con la barra lateral de Colab.")
        ok = False
    if not os.path.exists(office_bg):
        print("[ERROR] Falta background.png — súbelo con la barra lateral de Colab.")
        ok = False
    return ok


# ────────────────────────────────────────────────────────────────
def main():
    if not check_colab():
        print("[ERROR] Usa 'python main.py' para ejecución local.")
        sys.exit(1)

    print("=" * 75)
    print("  PROCESADOR CLOUD AUTOMÁTICO DE VIDEO IA — FINANZAS (GOOGLE COLAB)")
    print("=" * 75)

    # 1. Instalar y parchear
    setup_sadtalker()

    # 2. Importar nuestros módulos (edge-tts y moviepy ya están instalados)
    print("Cargando módulos de composición y locución...")
    from tts_generator import generate_speech
    from video_composer import composite_video_for_format

    # 3. Verificar activos
    if not check_and_rename_assets():
        sys.exit(1)

    # 4. Guion
    print("\n[GUION] Introduce el texto que dirá tu presentadora.")
    print("Presiona ENTER para usar el guion por defecto sobre Micron (MU):")
    custom_script = input("> ").strip()
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

    # Preguntar por el mejorador facial (GFPGAN)
    print("\n[MEJORADOR FACIAL] ¿Deseas activar el mejorador facial (GFPGAN)?")
    print("⚠ ADVERTENCIA: En videos largos (>30 segundos) en Google Colab gratuito, suele agotar la memoria RAM y abortar (Killed).")
    print("Presiona ENTER para NO activarlo (recomendado, más rápido y estable) o escribe 's' para activarlo:")
    use_enhancer = input("> ").strip().lower()
    enhancer_arg = "--enhancer gfpgan" if use_enhancer == 's' else ""

    # 5. Generar voz + subtítulos
    os.makedirs("output", exist_ok=True)
    audio_mp3 = "output/locucion.mp3"
    audio_wav = "output/locucion.wav"
    srt_subs = "output/subtitulos.srt"

    print("\n[PASO 1/3] Generando locución y subtítulos...")
    generate_speech(custom_script, "es-ES-ElviraNeural", audio_mp3, srt_subs)

    print("Convirtiendo a WAV 16 kHz mono...")
    os.system(f"ffmpeg -y -i {audio_mp3} -acodec pcm_s16le -ac 1 -ar 16000 {audio_wav}")

    # 6. Animación facial (SadTalker en GPU)
    print("\n[PASO 2/3] Animando avatar con IA (GPU)...")
    
    # Rutas absolutas para evitar fallos de resolución al cambiar de directorio
    audio_wav_abs = os.path.abspath(audio_wav)
    avatar_img_abs = os.path.abspath("avatar.png")
    result_dir_abs = os.path.abspath("output/sadtalker_temp")
    
    # Cambiar al directorio de SadTalker para ejecutar la inferencia
    current_dir = os.getcwd()
    os.chdir("SadTalker")
    
    sadtalker_cmd = (
        f"python inference.py "
        f"--driven_audio {audio_wav_abs} "
        f"--source_image {avatar_img_abs} "
        f"--result_dir {result_dir_abs} "
        f"--still "
        f"--preprocess full "
        f"{enhancer_arg}"
    )
    ret = os.system(sadtalker_cmd)
    
    # Restaurar directorio de trabajo
    os.chdir(current_dir)

    generated = glob.glob("output/sadtalker_temp/*.mp4")
    if not generated:
        print("[ERROR] SadTalker no generó ningún video.")
        print("Revisa los mensajes de error anteriores.")
        sys.exit(1)

    avatar_video = "output/avatar_talking.mp4"
    shutil.copy(sorted(generated)[-1], avatar_video)
    print(f"   → Avatar animado: {avatar_video}")

    # 7. Composición final
    out_h = "output/video_final_horizontal_16_9.mp4"
    out_v = "output/video_final_vertical_9_16.mp4"

    print("\n[PASO 3/3] Componiendo videos finales...")
    composite_video_for_format(
        bg_path="background.png", avatar_path=avatar_video,
        audio_path=audio_mp3, srt_path=srt_subs,
        output_path=out_h, format_type="horizontal",
        chroma_settings={"detect_color": True, "thr": 85, "s": 5},
    )
    composite_video_for_format(
        bg_path="background.png", avatar_path=avatar_video,
        audio_path=audio_mp3, srt_path=srt_subs,
        output_path=out_v, format_type="vertical",
        chroma_settings={"detect_color": True, "thr": 85, "s": 5},
    )

    print("\n" + "=" * 75)
    print("  ¡PIPELINE COMPLETADO CON ÉXITO!")
    print("=" * 75)
    print(f"  Horizontal → {os.path.abspath(out_h)}")
    print(f"  Vertical   → {os.path.abspath(out_v)}")
    print()
    print("  Para descargar, ejecuta en una nueva celda:")
    print("    from google.colab import files")
    print("    files.download('output/video_final_horizontal_16_9.mp4')")
    print("    files.download('output/video_final_vertical_9_16.mp4')")
    print("=" * 75)


if __name__ == "__main__":
    main()
