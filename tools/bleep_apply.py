# Usage: python3 bleep_apply.py <bleeps.json> <outdir>
# Mutes each detected span and mixes a 1 kHz bleep (spans capped at 2 s).
import json, subprocess, os, sys
B=json.load(open(sys.argv[1])); outdir=sys.argv[2]; os.makedirs(outdir,exist_ok=True)
for f,spans in B.items():
    sp=[]
    for s,e in spans:
        if e-s>2.0: c=(s+e)/2; s,e=c-1.0,c+1.0
        sp.append((round(s,2),round(e,2)))
    out=os.path.join(outdir,os.path.basename(f))
    if not sp:
        subprocess.run(["cp",f,out]); continue
    expr="+".join(f"between(t,{s},{e})" for s,e in sp)
    dur=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
    fc=(f"[0:a]volume=0:enable='{expr}'[m];"
        f"sine=f=1000:sample_rate=48000:d={dur},volume=0.25,volume=0:enable='not({expr})'[b];"
        f"[m][b]amix=inputs=2:normalize=0:duration=first[a]")
    subprocess.run(["ffmpeg","-loglevel","error","-y","-i",f,"-filter_complex",fc,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","160k","-movflags","+faststart",out])
    print(out,len(sp),"bleeps")
