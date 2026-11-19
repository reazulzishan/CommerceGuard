#!/bin/zsh
OUT=~/Movies/"CS Funda"/commerceguard_ep1
cd ~/Projects/CommerceGuard/video && npx hyperframes render --quality delivery --output "$OUT/CommerceGuard_Ep1_YouTube_1080p.mp4" > ../render_yt.log 2>&1 && echo "YT done" || echo "YT FAILED"
for n in 1 2 3; do
  cd ~/Projects/CommerceGuard/reels/part$n && npx hyperframes render --quality delivery --output "$OUT/CommerceGuard_Ep1_Reel_Part${n}of3.mp4" > ../../render_reel$n.log 2>&1 && echo "Reel $n done" || echo "Reel $n FAILED"
done
