import os
from glob import glob
from typing import List, Dict, Optional

DATA_DIR = os.getenv("DATA_DIR", "./data")

def _read_txt_sidecar(wav_path: str) -> Optional[str]:
    txt_path = os.path.splitext(wav_path)[0] + ".txt"
    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def _whisper_transcribe(wav_path: str) -> Optional[str]:
    try:
        import whisper  # type: ignore
    except Exception:
        return None
    try:
        model = whisper.load_model("base")  # CPU ok; It is possible to change model
        res = model.transcribe(wav_path, fp16=False, language="en")
        return (res.get("text") or "").strip()
    except Exception:
        return None

def transcribe_batch() -> List[Dict]:
    """
    Returns list of dicts:
    [{"external_id": <str>, "file_uri": <path>, "transcript": <str>}]
    """
    audio_dir = os.path.join(DATA_DIR, "raw_calls")
    wavs = sorted(glob(os.path.join(audio_dir, "*.wav")))
    out = []
    for w in wavs:
        base = os.path.basename(w)
        external_id = os.path.splitext(base)[0]
        transcript = _read_txt_sidecar(w) or _whisper_transcribe(w)
        if not transcript:
            print(f"⚠️ No transcript for {w} (missing .txt and Whisper unavailable). Skipping.")
            continue
        out.append({
            "external_id": external_id,
            "file_uri": w,
            "transcript": transcript
        })
    print(f"ASR produced {len(out)} items.")
    return out
