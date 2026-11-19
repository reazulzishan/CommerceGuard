# SPEC · CommerceGuard Episode 1

GOAL:    The viewer understands why "will this order arrive on time?" is hard, sees every step done honestly, and wants the next part.
OUTPUT:  HyperFrames. YouTube 1920x1080 30fps (one film). FB/Insta 1080x1920 30fps (7 parts, each ends on a spoken hook to the next).
TIME:    voice is the clock: 31 scenes, each = 0.35 s lead + VO + 0.45 s tail (~7:15). Reels: their scenes + outro hook + 1.2 s end card.
LOOK:    medium = "lab notebook on a graphite desk". Ground #141517 with 1 px grid at 3.5% white, 120 px pitch (no void: every shot's hero fills >= 40%).
         Real Jupyter captures are white paper sheets: radius 14 px, shadow 0 40 px 90 px rgba(0,0,0,.55).
         Ink #F3F0E8. One accent per shot: amber #FFB224 (the number that matters). Late/failure only: #FF5C4D. Fixed/good only: #3CC6A4.
         Display Inter 800, 7.5% of short side, tracking -3%. Body Inter 600 at 3.6%. Numbers/code JetBrains Mono 700.
         Highlight = amber marker box 5 px, radius 8, drawn left-to-right in 10 frames; everything outside dims to 45%.
OBJECTS: notebook cell sheets (real captures), parcel boxes (kraft #C49A6C with tape stripe) for orders, a padlock for the locked July holdout,
         bar charts with direct labels (no legends), a timeline axis with real dates.
MOTION:  enter power3.out 15 f; camera push sine.inOut over the shot; exit power2.in 8 f. Staggers 4 f. No springs on text.
         Text lands on the word that says it (word timings from transcripts).
SHOTS:   S01 kinetic hook · S02 parcels stream, 3 go wrong · S03 kinetic · S04 logotype mask reveal · S05 modules -> one question ·
         S06 9-table schema · S07 cell 2 · S08 cell 6 "3.1%" · S09 cells 8->9 · S10 promised 24 vs actual 11 bars · S11 kinetic ·
         S12 cell 15 · S13 live run footage (speed ramp) · S14 seller-history timeline · S15 cell 20 + leaky list struck ·
         S16 70/15/15 time split + lock · S17 PR-AUC bars · S18 test unlock · S19 0.30 -> 0.10 drop · S20 risk bands ·
         S21 real SHAP chart · S22 kinetic "month" · S23 promise concept · S24 Exp 1 failed · S25 weekly drift line ·
         S26 30-day window · S27 July unlock · S28 cell 47 + final bars · S29 trade-off · S30 limits + next · S31 logotype + handles.
SOUND:   voice only + few effects: whoosh (rotate 3 takes) on chapter cuts, pop on a number landing (max 1 per shot), key ticks on
         typed code, riser->impact once (S24 "failed"). No music yet (no source; ask user). Mix -14 LUFS, peaks <= -1 dBTP.
CAPTIONS: English, bottom band (YT) / lower third (reels), 2 lines max, numbers in amber, from transcripts corrected to the script.
BANNED:  navy void with small floating elements; glow, neon, flares, particles; purple/blue gradients; glass cards; three cards in a row;
         KPI grids; title over dimmed screenshot; logo docked in a corner; everything fading up at once; text moving while read.
QA:      each scene midpoint; every highlight box on its number; captions inside title-safe; no black frames; -14 LUFS.
