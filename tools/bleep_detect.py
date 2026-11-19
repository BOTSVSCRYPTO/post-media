import sys, subprocess, numpy as np, sherpa_onnx, json, re
M="/tmp/sherpa-onnx-whisper-small.en/small.en-"
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M+"encoder.int8.onnx",decoder=M+"decoder.int8.onnx",tokens=M+"tokens.txt",num_threads=4)
BAD=re.compile(r"(fuck|fuk|shit|bitch|nigg|nigga|n-word|motherf|cunt|dick|pussy|cock|whore|hoe\b|slut|asshole|bastard|retard|fag|wank|twat|porn|titties|tits\b|boobs|sex)",re.I)
def audio(f):
    b=subprocess.run(["ffmpeg","-loglevel","error","-i",f,"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout
    return np.frombuffer(b,np.int16).astype(np.float32)/32768
def segments(a):
    c=sherpa_onnx.VadModelConfig(); c.silero_vad.model="/tmp/silero_vad.onnx"; c.silero_vad.min_silence_duration=0.15; c.silero_vad.min_speech_duration=0.15; c.silero_vad.max_speech_duration=4.0; c.silero_vad.threshold=0.35; c.sample_rate=16000
    v=sherpa_onnx.VoiceActivityDetector(c,buffer_size_in_seconds=120)
    for i in range(0,len(a),512): v.accept_waveform(a[i:i+512])
    v.flush(); segs=[]
    while not v.empty(): segs.append((v.front.start/16000,len(v.front.samples)/16000)); v.pop()
    return segs
def decode(x):
    s=rec.create_stream(); s.accept_waveform(16000,x); rec.decode_stream(s); return s.result.text.strip()
def plan(f):
    a=audio(f); spans=[]; log=[]
    for st,du in segments(a):
        x=a[int(st*16000):int((st+du)*16000)]
        t=decode(np.concatenate([np.zeros(1600,np.float32),x,np.zeros(1600,np.float32)]))
        words=t.split()
        if not words: continue
        hit=[i for i,w in enumerate(words) if BAD.search(w)]
        if not hit: continue
        # weight positions by characters for a better estimate
        L=[len(w)+1 for w in words]; tot=sum(L); cum=np.cumsum([0]+L)
        for i in hit:
            s=st+du*cum[i]/tot; e=st+du*cum[i+1]/tot
            spans.append([max(0,s-0.3),e+0.3])
        log.append(f"{st:.1f}s: {t}")
    spans.sort(); merged=[]
    for s,e in spans:
        if merged and s<=merged[-1][1]+0.1: merged[-1][1]=max(merged[-1][1],e)
        else: merged.append([s,e])
    return merged, log
if __name__=="__main__":
    res={}
    for f in [a for a in sys.argv[1:] if a.endswith(".mp4")]:
        m,log=plan(f); res[f]=m
        print("==",f.split('/')[-1],len(m),"bleeps, total",round(sum(e-s for s,e in m),1),"s"); print("\n".join(log)[:900],flush=True)
    json.dump(res,open(sys.argv[-1] if sys.argv[-1].endswith(".json") else "/tmp/bleeps.json","w"))
