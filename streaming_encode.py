"""
Encodes a video as a HTTP Live Streaming (HLS) playlist suitable for any basic HTTP Server.

References:
- https://github.com/hadronepoch/python-ffmpeg-video-streaming
"""
import datetime
import shutil
import sys
from pathlib import Path
import time
from typing import Optional

import ffmpeg_streaming
from ffmpeg_streaming import Formats

import ffmpeg_utils


def _monitor(_, duration, time_, time_left, __):
    per = round(time_ / duration * 100)
    sys.stdout.write(
        "\rTranscoding...(%s%%) %s left [%s%s]"
        % (
            per,
            datetime.timedelta(seconds=int(time_left)),
            "#" * per,
            "-" * (100 - per),
        )
    )
    sys.stdout.flush()


def create_hls(video_fp: Path, out_dir: Optional[Path] = None, debug=False):
    print("==== HLS Create ====")
    out_dir = out_dir or Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_fp = (out_dir / (video_fp.stem + "-converted")).with_suffix(".m3u8")
    elapsed_start = time.time()

    video = ffmpeg_streaming.input(str(video_fp))
    hls = video.hls(Formats.h264())
    hls.auto_generate_representations()
    hls.output(out_fp, monitor=_monitor if debug else None)

    elapsed_end = time.time()
    print(f"Time Taken: {(elapsed_end - elapsed_start):.1f}s")


if __name__ == "__main__":
    SRC_FILE = Path("MathIncompleteness.mp4")
    SPLICE_DIR = Path("out/streaming")
    CREATE_DIR = Path("www/vid")
    shutil.rmtree(SPLICE_DIR, ignore_errors=True)
    shutil.rmtree(CREATE_DIR, ignore_errors=True)

    ffmpeg_utils.splice_vid(
        SRC_FILE, pos_unit="percent", pos_start=0.9, out_dir=SPLICE_DIR
    )

    ffmpeg_utils.thumbnail(
        SPLICE_DIR / "MathIncompleteness-spliced.mp4", out_dir=CREATE_DIR
    )

    create_hls(
        SPLICE_DIR / "MathIncompleteness-spliced.mp4",
        out_dir=CREATE_DIR,
    )
