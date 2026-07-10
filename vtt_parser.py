import os

def parse_time(time_str: str) -> float:
    """
    Convierte un string de tiempo en formato HH:MM:SS,mmm o HH:MM:SS.mmm a segundos (float).
    """
    time_str = time_str.strip().replace(',', '.')
    parts = time_str.split(':')
    if len(parts) == 3:
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        minutes = float(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    else:
        return float(parts[0])

def parse_subtitles(file_path: str):
    """
    Lee un archivo SRT o WebVTT y devuelve una lista de diccionarios con
    los tiempos de inicio, fin y el texto de cada subtítulo.
    """
    if not os.path.exists(file_path):
        print(f"Advertencia: El archivo de subtítulos {file_path} no existe.")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Normalizar saltos de línea y dividir por bloques de subtítulo
    blocks = content.replace('\r\n', '\n').split('\n\n')
    subtitles = []

    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue

        timing_line = None
        text_lines = []

        for line in lines:
            if "-->" in line:
                timing_line = line
            elif timing_line is not None:
                text_lines.append(line)

        if timing_line:
            try:
                times = timing_line.split("-->")
                start_sec = parse_time(times[0])
                end_sec = parse_time(times[1])
                text = " ".join(text_lines)
                
                # Omitir subtítulos vacíos
                if text:
                    subtitles.append({
                        "start": start_sec,
                        "end": end_sec,
                        "text": text
                    })
            except Exception as e:
                print(f"Error parseando bloque de subtítulo: '{block}'. Detalle: {e}")
                
    return subtitles

if __name__ == "__main__":
    # Prueba del parser
    import tempfile
    test_srt_content = """1
00:00:01,200 --> 00:00:03,500
Hola, esta es una
prueba de subtítulos.

2
00:00:03,500 --> 00:00:06,100
Segunda línea de
la prueba.
"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".srt", mode="w", encoding="utf-8") as f:
        f.write(test_srt_content)
        temp_name = f.name
        
    try:
        subs = parse_subtitles(temp_name)
        print("Subtítulos parseados con éxito:")
        for s in subs:
            print(f"[{s['start']:.2f}s -> {s['end']:.2f}s]: {s['text']}")
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)
