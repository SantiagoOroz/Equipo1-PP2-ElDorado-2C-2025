import os
import asyncio
import whisper
import torch
import edge_tts
import tempfile
from tempfile import NamedTemporaryFile

# --- Configuración de Whisper ---
# Carga el modelo una sola vez al iniciar el script.
# 'base' es un buen equilibrio entre velocidad y precisión.
try:
    WHISPER_MODEL = whisper.load_model("base")
    print("✅ Modelo Whisper 'base' cargado correctamente.")
except Exception as e:
    print(f"Error cargando modelo Whisper: {e}")
    WHISPER_MODEL = None

def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe un archivo de audio (en la ruta especificada) a texto.
    """
    if not WHISPER_MODEL:
        print("[ERROR Whisper] El modelo no está cargado.")
        return "[Error: Modelo Whisper no disponible]"
        
    try:
        # --- MEJORA ---
        # Ya no necesitamos crear un archivo temporal aquí,
        # usamos el que Flask nos pasa.
        
        # Cargar y procesar el audio
        audio = whisper.load_audio(audio_file_path) # <-- Usar la ruta directamente
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(WHISPER_MODEL.device)

        # Forzar idioma español y decodificar
        options = whisper.DecodingOptions(language="es", fp16=torch.cuda.is_available())
        result = whisper.decode(WHISPER_MODEL, mel, options)
        
        return result.text.strip()
    
    except Exception as e:
        print(f"[ERROR Whisper] No se pudo transcribir el audio: {e}")
        return ""

def synthesize_speech(text: str, voice_id: str) -> str | None:
    """
    Sintetiza texto a un archivo de audio .mp3 usando edge-tts.
    Retorna la RUTA al archivo temporal .mp3 generado.
    El archivo debe ser eliminado manualmente después de ser usado.
    """
    
    async def _async_synthesize():
        """Función interna asíncrona para manejar la generación de audio."""
        # Usamos tempfile para crear un nombre de archivo único
        # Dejamos que el sistema operativo maneje la carpeta temporal
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        mp3_path = temp_file.name
        temp_file.close() # Cerramos el handle para que edge_tts pueda escribir

        try:
            communicate = edge_tts.Communicate(text, voice_id)
            await communicate.save(mp3_path)
            return mp3_path
        except Exception as e:
            print(f"[ERROR TTS] No se pudo sintetizar el audio ({voice_id}): {e}")
            # Si falla, borramos el archivo temporal vacío
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
            return None

    # Manejo robusto del loop de asyncio
    try:
        audio_path = asyncio.run(_async_synthesize())
        return audio_path
    except RuntimeError:
        # Si ya hay un loop corriendo (común en algunos entornos)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_path = loop.run_until_complete(_async_synthesize())
        return audio_path