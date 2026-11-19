import json, re, sys
from pathlib import Path
import numpy as np, soundfile as sf
sys.path.insert(0, str(Path.home() / "Movies/CS Funda/assets/voice"))
from cs_funda_voice import MODEL, SPEAKER, prep
from TTS.api import TTS
here = Path(__file__).parent
src = (here / "script_ep2.md").read_text()
items = re.findall(r"\[(E\d+)\]\s*PART (\d)\n(.+?)(?=\n\[|\n\n#|\Z)", src, re.S)
outs = re.findall(r"\[(F\d)\] (.+)", src)
only = set(sys.argv[1:])
tts = TTS(MODEL, progress_bar=False); sr = tts.synthesizer.output_sample_rate
meta = json.loads((here / "vo/scenes.json").read_text()) if (here / "vo/scenes.json").exists() else {}
for sid, part, text in [(a, int(b), c) for a, b, c in items] + [(a, 0, b) for a, b in outs]:
    if only and sid not in only: continue
    text = " ".join(text.split())
    t2 = text.replace("Evaly", "Ee-vaa-lee").replace("e-Orange", "ee Orange").replace("Pickaboo", "Picka-boo").replace("Daraz", "Da-raaz")
    w = np.asarray(tts.tts(text=prep(t2), speaker=SPEAKER), dtype=np.float32)
    sf.write(here / f"vo/{sid}.wav", w, sr)
    meta[sid] = {"id": sid, "part": part, "text": text, "dur": round(len(w) / sr, 2)}
    print(sid, meta[sid]["dur"], flush=True)
(here / "vo/scenes.json").write_text(json.dumps(meta, indent=1))
print("total", round(sum(m["dur"] for m in meta.values()), 1))
