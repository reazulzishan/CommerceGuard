#!/bin/zsh
cd ~/Projects/CommerceGuard/video_ep2/film && npx hyperframes render --quality delivery --output "/Users/zishan/Movies/CS Funda/commerceguard_ep2/CommerceGuard_Ep2_YouTube_1080p.mp4" > ../render_yt.log 2>&1 && echo "YT done" || echo "YT FAILED"
for n in 1 2; do cd ~/Projects/CommerceGuard/video_ep2/reels/part$n && npx hyperframes render --quality delivery --output "/Users/zishan/Movies/CS Funda/commerceguard_ep2/CommerceGuard_Ep2_Reel_Part${n}of2.mp4" > ../../render_reel$n.log 2>&1 && echo "Reel $n done" || echo "Reel $n FAILED"; done
