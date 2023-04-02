import datetime
import io
import json
import re
from pathlib import Path

from ffmpeg import FFmpeg, FFmpegError


class VideoMeta:
    __create_key = object()

    def __init__(self, create_key: object, raw: str):
        """Use static factory method .get(), don't use this constructor."""
        if create_key is self.__create_key:
            self.raw = raw
            self.duration_secs = VideoMeta._extract_duration(raw)
        else:
            raise RuntimeError("Do not call the constructor directly!")

    def __str__(self):
        return json.dumps(self.__dict__, indent=2)

    @staticmethod
    def _extract_duration(raw: str):
        """https://stackoverflow.com/questions/24142119/extract-the-middle-frame-of-a-video-in-python-using-ffmpeg"""
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", raw)
        if not match:
            raise KeyError("Cannot determine duration")
        # Avoiding strptime here because it has some issues handling milliseconds.
        time_obj = [int(match.group(i)) for i in range(1, 5)]
        duration = datetime.timedelta(
            hours=time_obj[0],
            minutes=time_obj[1],
            seconds=time_obj[2],
            # * 10 because truncated to 2 decimal places
            milliseconds=time_obj[3] * 10,
        ).total_seconds()
        return duration

    @classmethod
    def get(cls, video_fp: Path) -> "VideoMeta":
        ffmpeg = FFmpeg()
        err_buffer = io.StringIO()

        @ffmpeg.on("stderr")
        def on_error(line: str):
            err_buffer.write(line + "\n")

        try:
            ffmpeg.input(video_fp).execute()
        except FFmpegError:
            pass

        meta = err_buffer.getvalue()
        err_buffer.close()

        return VideoMeta(cls.__create_key, meta)


if __name__ == "__main__":
    SRC_FILE = Path("MathIncompleteness.mp4")
    print(VideoMeta.get(SRC_FILE))
