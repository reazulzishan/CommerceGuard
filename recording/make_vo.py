"""One p270 voice file per [S##] scene of script_ep1.md, plus vo/scenes.json with durations."""
import json, re, sys
from pathlib import Path
import numpy as np, soundfile as sf
sys.path.insert(0, str(Path.home() / "Movies/CS Funda/assets/voice"))
from cs_funda_voice import MODEL, SPEAKER, prep
from TTS.api import TTS

here = Path(__file__).parent
blocks = re.findall(r"\[(S\d+)\]\s*(REEL \d+)\n(.+?)(?=\n\[S|\Z)", (here / "script_ep1.md").read_text(), re.S)
tts = TTS(MODEL, progress_bar=False); sr = tts.synthesizer.output_sample_rate
meta = []
for sid, reel, text in blocks:
    wav = np.asarray(tts.tts(text=prep(text.strip()), speaker=SPEAKER), dtype=np.float32)
    sf.write(here / f"vo/{sid}.wav", wav, sr)
    meta.append({"id": sid, "reel": int(reel.split()[1]), "text": " ".join(text.split()), "dur": round(len(wav) / sr, 2)})
    print(sid, meta[-1]["dur"], flush=True)
(here / "vo/scenes.json").write_text(json.dumps(meta, indent=1))
print("total", round(sum(m["dur"] for m in meta), 1), "s")
