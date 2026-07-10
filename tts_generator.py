import asyncio
import os
import edge_tts

async def generate_speech_async(text: str, voice: str, output_audio_path: str, output_srt_path: str):
    """
    Genera el audio en MP3 y los subtítulos con tiempos en formato SRT.
    """
    print(f"Iniciando síntesis de voz con la voz '{voice}'...")
    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    
    # Creamos las carpetas de salida si no existen
    os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(output_srt_path)), exist_ok=True)

    with open(output_audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
                
    # Obtener el SRT y guardarlo
    srt_content = submaker.get_srt()
    with open(output_srt_path, "w", encoding="utf-8") as srt_file:
        srt_file.write(srt_content)
        
    print(f"Audio guardado en: {output_audio_path}")
    print(f"Subtítulos guardados en: {output_srt_path}")

def generate_speech(text: str, voice: str, output_audio_path: str, output_srt_path: str):
    """
    Sincrónico wrapper para facilitar la integración en otros scripts de Python.
    """
    asyncio.run(generate_speech_async(text, voice, output_audio_path, output_srt_path))

if __name__ == "__main__":
    # Prueba rápida del generador
    test_text = "Hola, esta es una prueba de la síntesis de voz en español para nuestro video financiero."
    test_voice = "es-ES-ElviraNeural"
    generate_speech(test_text, test_voice, "output/test_audio.mp3", "output/test_subs.srt")
