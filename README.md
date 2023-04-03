**Table of Contents**

- [Requisites](#requisites)
- [Components](#components)
- [Usage](#usage)
  - [Snapshot/Splicing](#snapshotsplicing)
    - [Performance](#performance)
  - [Serving](#serving)
    - [Performance](#performance-1)

# Requisites

Linux/Windows OS Agnostic. Python 3.10+ is needed.

1. Clone the git repository:
   ```sh
   git clone <GIT URL>
   cd video-test
   ```
2. Install Ffmpeg:
   ```sh
   sudo apt install ffmpeg # Ubuntu
   # OR
   https://github.com/BtbN/FFmpeg-Builds/releases # Windows
   ```
3. Install Python deps in your favorite venv / conda:
   ```sh
   pip install -r requirements.txt
   ```
4. Get the VideoJS lib:
   ```sh
   pushd www/lib
   curl https://unpkg.com/video.js/dist/video-js.min.css -O
   curl https://unpkg.com/video.js/dist/video.min.js -O
   popd
   ```
5. Download this YouTube video (using various means) and save it as `MathIncompleteness.mp4`:  
   https://www.youtube.com/watch?v=HeQX2HjkcNo

# Components

- ffmpeg_utils.py
  - Takes image snapshots of videos
  - Splices videos
  - Generate thumbnail of videos
- streaming_encode.py
  - Encodes videos as a HTTP Live Streaming (HLS) playlist
- server.py
  - Uses a simple HTTP Server to serve HLS playlists
- index.html
  - Uses JS to play a HLS playlist video in modern browsers

# Usage

## Snapshot/Splicing

The output is written to `out/ffmpeg` folder.

```sh
# Activate your venv / conda
python ffmpeg_utils.py
```

### Performance

What affects the time performance:

- [ ] Seek Position
- [ ] Number of Snapshots
- [x] Duration of Snapshot/Splice

On a 30 min video

- with an AMD Ryzen 7 with Nvidia Geforce GTX 1650 Ti & 24 GB RAM

| Task                   | Time Taken |
| ---------------------- | ---------- |
| Thumbnail generation   | ~1 sec     |
| 10 snapshots @ 0.2 FPS | ~1 sec     |
| 60 snapshots @ 1 FPS   | ~2 sec     |
| 1 min splice           | ~14 sec    |
| 3:23 min splice        | ~1 min     |

- with an Intel i5-10300H with Nvidia Quadro P620 & 8 GB RAM

| Task                   | Time Taken |
| ---------------------- | ---------- |
| Thumbnail generation   | ~2 sec     |
| 10 snapshots @ 0.2 FPS | ~5 sec     |
| 60 snapshots @ 1 FPS   | ~5 sec     |
| 1 min splice           | ~40 sec    |
| 3:23 min splice        | ~2.5 min   |

## Serving

The output is written to `out/streaming` folder.

```sh
# Activate your venv / conda
python streaming_encode.py # Generate a m3u8 playlist

# For Linux
./server.sh # Launch a simple webserver

# For Windows
cmd < server.sh
```

Then, visit http://localhost:8000 to see the web player.

### Performance

On a 3:23 minute video

- with an AMD Ryzen 7 with Nvidia Geforce GTX 1650 Ti & 24 GB RAM

| Task           | Time Taken |
| -------------- | ---------- |
| HLS Encoding   | ~2 min     |
| HTML Scrubbing | ~0 sec     |

- with an Intel i5-10300H with Nvidia Quadro P620 & 8 GB RAM

| Task           | Time Taken |
| -------------- | ---------- |
| HLS Encoding   | ~5 min     |
| HTML Scrubbing | ~0 sec     |
