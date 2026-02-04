import os
import subprocess
import requests
import uuid
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class VideoRequest(BaseModel):
    video_url: str

@app.post("/extract-keyframes")
def extract_keyframes(req: VideoRequest):
    job_id = str(uuid.uuid4())
    workdir = f"/tmp/{job_id}"
    os.makedirs(workdir, exist_ok=True)

    video_path = f"{workdir}/video.mp4"
    frames_dir = f"{workdir}/frames"
    os.makedirs(frames_dir, exist_ok=True)

    # download video
    r = requests.get(req.video_url, stream=True, timeout=120)
    r.raise_for_status()
    with open(video_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    # extract keyframes (I-frames)
    subprocess.run([
        "ffmpeg",
        "-i", video_path,
        "-vf", "select=eq(pict_type\\,I)",
        "-vsync", "vfr",
        f"{frames_dir}/frame_%03d.jpg"
    ], check=True)

    frames = sorted(os.listdir(frames_dir))

    return {
        "job_id": job_id,
        "frames_count": len(frames),
        "frames": frames
    }
