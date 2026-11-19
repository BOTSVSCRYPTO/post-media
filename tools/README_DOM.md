# Dom (Dasgasd3m x RUCKUS) auto-clipper kit
- stream_render.py SPEC.json OUTDIR Anton.ttf : facecam top 1080x860 (cam [x,y,540,430], left cam x=0 gx=560, right cam x=1380 gx=260), gameplay bottom, hook + credit overlay, loudnorm.
- bleep_detect.py a.mp4 b.mp4 ... out.json : Silero VAD + Whisper small.en (sherpa-onnx), flags swears/slurs, writes spans. Needs /tmp/sherpa-onnx-whisper-small.en and /tmp/silero_vad.onnx (GitHub release downloads).
- bleep_apply.py out.json OUTDIR : mutes spans, adds 1 kHz bleep. Repeat detect+apply until 0 hits.
- dom_used.json : Kick clip ids already used/skipped (append new ones; bump next_num).
