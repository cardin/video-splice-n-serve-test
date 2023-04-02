"""Functions for performing video snapshot and video splicing.

References:
- https://ffmpeg.org/ffmpeg.html
- https://www.ffmpeg.org/ffmpeg-filters.html#fps-1
- https://www.ffmpeg.org/ffmpeg-filters.html#thumbnail
- https://stackoverflow.com/questions/24142119/extract-the-middle-frame-of-a-video-in-python-using-ffmpeg
- https://trac.ffmpeg.org/wiki/Create%20a%20thumbnail%20image%20every%20X%20seconds%20of%20the%20video
"""

import logging
import math
import shutil
import subprocess
import time
from datetime import timedelta
from pathlib import Path
from typing import Literal, Optional

from ffmpeg import FFmpeg, Progress

from video_meta import VideoMeta

logging.basicConfig(level=logging.INFO)


def _parse_start_stop(
    duration: float,
    pos_unit: Literal["percent"] | Literal["seconds"],
    pos_start: float,
    pos_stop: float,
):
    cfg = {}

    if pos_unit == "percent":
        pos_start_time = max(0, min(pos_start * duration, duration - 0.1))
        if pos_start_time != 0:
            # 0 means start from the beginning
            cfg["ss"] = f"{pos_start_time:.3f}"

        if pos_stop != -1 and pos_stop < 1 and pos_stop > pos_start:
            # -1 means run to the end
            pos_stop_time = max(pos_start_time, min(pos_stop * duration, duration))
            cfg["to"] = f"{pos_stop_time:.3f}"

    elif pos_unit == "seconds":
        pos_start = max(0, min(pos_start, duration - 0.1))
        if pos_start != 0:
            # 0 means start from the beginning
            cfg["ss"] = f"{pos_start:.3f}"

        if pos_stop != -1 and pos_stop < duration and pos_stop > pos_start:
            # -1 means run to the end
            pos_stop = max(pos_start, min(pos_stop, duration))
            cfg["to"] = f"{pos_stop:.3f}"

    else:
        raise ValueError(f"Invalid pos_unit given: {pos_unit}")

    if "ss" in cfg:
        print(f'Specified Start: {timedelta(seconds=math.floor(float(cfg["ss"])))}')
    if "to" in cfg:
        print(f'Specified Stop: {timedelta(seconds=math.floor(float(cfg["to"])))}')
    return cfg


def _parse_num_renders(
    pos_cfg: dict, num_renders: int, out_fps: float, duration: float
):
    if num_renders == -1:
        if "ss" in pos_cfg and "to" in pos_cfg:
            num_renders = round((float(pos_cfg["to"]) - float(pos_cfg["ss"])) / out_fps)
        elif "ss" in pos_cfg and "to" not in pos_cfg:
            num_renders = round((duration - float(pos_cfg["ss"])) / out_fps)
        elif "ss" not in pos_cfg and "to" in pos_cfg:
            num_renders = round(float(pos_cfg["to"]) / out_fps)
        else:
            num_renders = round(duration / out_fps)
    else:
        num_renders = max(1, num_renders)

    return num_renders


def snapshot_imgs(
    video_fp: Path,
    pos_unit: Optional[Literal["percent"] | Literal["seconds"]] = None,
    pos_start: float = 0,
    pos_stop: float = -1,
    out_fps: float = 1.0,
    num_renders: int = -1,
    out_dir: Optional[Path] = None,
    debug=False,
):
    """
    Take snapshots of a video. Note that the timestamps has a deviation offset due to decoding \
        issues.

    The setting for Ffmpeg's "ss" setting says:
        Note that in most formats it is not possible to seek exactly, so ffmpeg will seek to the
        closest seek point before position. When transcoding and -accurate_seek is enabled
        (the default), this extra segment between the seek point and position will be decoded
        and discarded.

    Args:
        video_fp: Input video's filepath
        pos_unit: What is the unit of reference for the position values
        pos_start: Starting point. 0 is the beginning of the video
        pos_stop: Stopping point. -1 is the ending of the video
        out_fps: Consider fps = snapshot per second.
            So 1 fps = 1 snapshot per second. 0.2 fps = 1 snapshot per 5 seconds
        num_renders: Number of snapshots to render.
            This parameter will override whatever "pos_stop" defines.
            -1 means to take as many snapshots as the "out_fps" and "pos_start"/"pos_stop" ranges allows.
        out_dir: Directory to save the snapshots to
        debug: If ffmpeg logs should print to console
    """
    print("==== Image Snapshot ====")
    out_dir = out_dir or Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    elapsed_start = time.time()

    duration = VideoMeta.get(video_fp).duration_secs
    print(f"Duration: {timedelta(seconds = duration)}")

    pos_unit = pos_unit or "percent"
    pos_cfg = _parse_start_stop(duration, pos_unit, pos_start, pos_stop)
    num_renders = _parse_num_renders(pos_cfg, num_renders, out_fps, duration)

    tens_places = round(math.log10(num_renders)) + 1
    fn_format = f"img-%0{tens_places}d.jpg"
    out_format = "image2"

    # Helpful info printing
    last_snapshot_sec = (
        num_renders / out_fps + float(pos_cfg["ss"]) if "ss" in pos_cfg else 0
    )
    if last_snapshot_sec > duration:
        print(
            f"Last snapshot {last_snapshot_sec}s is outside the video duration {duration}s"
        )
    elif "to" in pos_cfg and last_snapshot_sec > float(pos_cfg["to"]):
        print(
            f"Last snapshot {last_snapshot_sec}s is outside the truncation bounds of the job {pos_cfg['to']}s"
        )
    else:
        print(f"Estimated Last Snapshot: {timedelta(seconds = last_snapshot_sec)}")

    # Initializing
    ffmpeg = FFmpeg()

    if debug:

        @ffmpeg.on("progress")
        def on_progress(progress: Progress):
            logging.info(progress)

        @ffmpeg.on("stderr")
        def on_error(line: str):
            logging.error(line)

    # Run
    # Note: -r:v {out_fps} doesn't seem to work as snapshot 1 & 2 will be identical.
    # But -vf fps={out_fps} works fine.
    ffmpeg.input(video_fp, pos_cfg).output(
        out_dir / fn_format,
        {
            "frames:v": num_renders,
            "f": out_format,
            "vf": f"fps={out_fps}",
        },
    ).option("y").execute()

    elapsed_end = time.time()
    print(f"Time Taken: {(elapsed_end - elapsed_start):.1f}s")


def splice_vid(
    video_fp: Path,
    pos_unit: Optional[Literal["percent"] | Literal["seconds"]] = None,
    pos_start: float = 0,
    pos_stop: float = -1,
    out_dir: Optional[Path] = None,
    debug=False,
):
    """
    Splice a video. Note that the timestamps has a deviation offset due to decoding issues.

    The setting for Ffmpeg's "ss" setting says:
        Note that in most formats it is not possible to seek exactly, so ffmpeg will seek to the
        closest seek point before position. When transcoding and -accurate_seek is enabled
        (the default), this extra segment between the seek point and position will be decoded
        and discarded.

    Args:
        video_fp: Input video's filepath
        pos_unit: What is the unit of reference for the position values
        pos_start: Starting point. 0 is the beginning of the video
        pos_stop: Stopping point. -1 is the ending of the video
        out_dir: Directory to save the spliced video to
        debug: If ffmpeg logs should print to console
    """
    print("==== Video Splice ====")
    out_dir = out_dir or Path("out")
    out_fp = out_dir / (video_fp.stem + "-spliced" + video_fp.suffix)
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    elapsed_start = time.time()

    duration = VideoMeta.get(video_fp).duration_secs
    print(f"Duration: {timedelta(seconds = duration)}")

    pos_unit = pos_unit or "percent"
    pos_cfg = _parse_start_stop(duration, pos_unit, pos_start, pos_stop)

    if video_fp.suffix != out_fp.suffix:
        raise ValueError(
            f"Input format {video_fp.suffix} is not the same as \
                the output format {out_fp.suffix}!"
        )

    # Initializing
    ffmpeg = FFmpeg()

    if debug:

        @ffmpeg.on("progress")
        def on_progress(progress: Progress):
            logging.info(progress)

        @ffmpeg.on("stderr")
        def on_error(line: str):
            logging.error(line)

    # Run
    ffmpeg.input(video_fp, pos_cfg).output(
        out_fp,
        {},
    ).option("y").execute()

    elapsed_end = time.time()
    print(f"Time Taken: {(elapsed_end - elapsed_start):.1f}s")


def thumbnail(
    video_fp: Path,
    out_dir: Optional[Path] = None,
    debug=False,
):
    """
    Takes a thumbnail of a video. This tends to be one of the first frames.

    Args:
        video_fp: Input video's filepath
        out_dir: Directory to save the spliced video to
        debug: If ffmpeg logs should print to console
    """
    print("==== Thumbnail ====")
    out_dir = out_dir or Path("out")
    out_fp = (out_dir / (video_fp.stem + "-thumbnail")).with_suffix(".jpg")
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    elapsed_start = time.time()

    duration = VideoMeta.get(video_fp).duration_secs
    print(f"Duration: {timedelta(seconds = duration)}")

    # Run
    # There's a bug in the Python lib, so we subprocess it directly
    cmd = f"ffmpeg -i {video_fp} -vf thumbnail -frames:v 1 {out_fp}"
    subprocess.run(
        cmd,
        shell=True,
        stderr=subprocess.STDOUT,
        stdout=None if debug else subprocess.DEVNULL,
        check=True,
    )

    elapsed_end = time.time()
    print(f"Time Taken: {(elapsed_end - elapsed_start):.1f}s")


if __name__ == "__main__":
    SRC_FILE = Path("MathIncompleteness.mp4")
    shutil.rmtree("out/ffmpeg", ignore_errors=True)

    thumbnail(SRC_FILE, out_dir=Path("out/ffmpeg/thumbnail"))

    splice_vid(
        SRC_FILE,
        out_dir=Path("out/ffmpeg/vid/percent"),
        pos_unit="percent",
        pos_start=0.999,
    )

    splice_vid(
        SRC_FILE,
        out_dir=Path("out/ffmpeg/vid/time"),
        pos_unit="seconds",
        pos_start=400,
        pos_stop=460,
    )

    snapshot_imgs(
        SRC_FILE,
        out_dir=Path("out/ffmpeg/percent/jump_to_end"),
        pos_unit="percent",
        pos_start=0.9,
        out_fps=0.2,
        num_renders=10,
    )

    snapshot_imgs(
        SRC_FILE,
        out_dir=Path("out/ffmpeg/percent/many_frames"),
        pos_unit="percent",
        pos_start=0.9,
        out_fps=1,
        num_renders=60,
    )

    snapshot_imgs(
        SRC_FILE,
        out_dir=Path("out/ffmpeg/time/bounded"),
        pos_unit="seconds",
        pos_start=200,
        pos_stop=210,
    )

    snapshot_imgs(
        SRC_FILE,
        out_dir=Path("out/ffmpeg/time/inaccurate_timestamp"),
        pos_unit="seconds",
        pos_start=100,
        pos_stop=110,
        out_fps=1,
    )
