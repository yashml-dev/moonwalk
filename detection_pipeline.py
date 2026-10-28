"""Detection helpers for MOONWALK. Thin wrappers around the existing YOLO workflow.

Nothing here invents results: counts and confidences come straight from the model.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Callable, Optional

import cv2

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTS = {".mp4", ".mov", ".avi"}


@dataclass
class ScanResult:
    kind: str                      # "image" | "video"
    annotated_jpg: bytes           # annotated image, or the annotated best frame of a video
    count: int                     # image: detections; video: most detections in a single frame
    confidences: list = field(default_factory=list)  # confidences for `annotated_jpg`
    frames: int = 0                # video only: frames processed
    video_path: Optional[str] = None
    video_bytes: Optional[bytes] = None
    video_playable: bool = False


def _encode_jpg(frame_bgr) -> bytes:
    ok, buf = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not ok:
        raise RuntimeError("Could not encode the annotated image.")
    return buf.tobytes()


def _confs(result) -> list:
    if result.boxes is None or len(result.boxes) == 0:
        return []
    return sorted((float(c) for c in result.boxes.conf.tolist()), reverse=True)


def scan_image(model, path: str, conf: float) -> ScanResult:
    result = model.predict(source=path, conf=conf, verbose=False)[0]
    confs = _confs(result)
    return ScanResult("image", _encode_jpg(result.plot()), len(confs), confs)


def make_browser_playable(src: str, dst: str) -> bool:
    """Re-encode to H.264 so browsers can play the result. Returns False if ffmpeg is unavailable."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    try:
        proc = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-i", src, "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-preset", "veryfast", "-movflags", "+faststart", dst],
            capture_output=True, timeout=600)
        return proc.returncode == 0
    except Exception:
        return False


def scan_video(model, path: str, out_path: str, conf: float,
               on_progress: Optional[Callable[[int, int], None]] = None) -> ScanResult:
    cap = cv2.VideoCapture(path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()
    if width <= 0 or height <= 0:
        raise ValueError("Could not read this video. Try an MP4 or AVI file.")
    fps = fps if fps and fps > 0 else 20.0
    # Keep a local CPU prototype responsive; reject long clips rather than silently truncating.
    if total > 0 and total / fps > 120:
        raise ValueError("This prototype supports videos up to 120 seconds. Trim the clip and try again.")

    raw_path = out_path + ".raw.mp4"
    writer = cv2.VideoWriter(raw_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    processed, best_count, best_frame, best_confs = 0, -1, None, []
    try:
        for r in model(source=path, stream=True, conf=conf, verbose=False):
            frame = r.plot()
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))
            writer.write(frame)
            processed += 1
            confs = _confs(r)
            if len(confs) > best_count:
                best_count, best_frame, best_confs = len(confs), frame.copy(), confs
            if on_progress:
                on_progress(processed, max(total, processed))
    finally:
        writer.release()
    if not processed:
        raise ValueError("No frames could be processed from this video.")

    playable = make_browser_playable(raw_path, out_path)
    final = out_path if playable else raw_path
    with open(final, "rb") as fh:
        data = fh.read()
    return ScanResult("video", _encode_jpg(best_frame), max(best_count, 0), best_confs,
                      frames=processed, video_path=final, video_bytes=data, video_playable=playable)
