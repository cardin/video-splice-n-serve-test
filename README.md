- [Requisites](#requisites)
- [Components](#components)
- [Usage](#usage)
    - [Snapshot/Splicing](#snapshotsplicing)
        - [Performance](#performance)
    - [Serving](#serving)
        - [Performance](#performance-1)

# Requisites

A Linux OS with Python 3.10+ is needed.

Clone the git repository:

```sh
git clone <GIT URL>
cd video-test
```

Install Ffmpeg:

```sh
sudo apt install ffmpeg
```

Install Python deps in your favorite venv / conda:

```sh
pip install -r requirements.txt
```

Get the VideoJS lib:

```sh
wget https://unpkg.com/video.js/dist/video-js.min.css -P www/lib
wget https://unpkg.com/video.js/dist/video.min.js -P www/lib
```

Download this YouTube video (using various means) and save it as `MathIncompleteness.mp4`:  
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
python ffmpeg_utils.py
```

### Performance

What affects the time performance:

- [ ] Seek Position
- [x] Duration of Snapshot/Splice
- [x] Number of Snapshots

On a 30 min video & an AMD Ryzen 7 with Nvidia Geforce GTX 1650 Ti

- 10 snapshots at 1 snapshot per second, runs within 1 second
- 60 snapshots at 1 snapshot per second, runs within 2 seconds
- 60 seconds of video splice, runs within 14 seconds
- 3:23 minutes of video splice, runs within 1 minute

## Serving

The output is written to `out/streaming` folder.

```sh
python streaming_encode.py # Generate a m3u8 playlist
./server.sh # Launch a simple webserver
```

Then, visit http://localhost:8000 to see the web player.

### Performance

On a 3:23 minute video & an AMD Ryzen 7 with Nvidia Geforce GTX 1650 Ti

- Encoding to HLS, runs ~ 2 minutes
- The HTML web player loads and scrubs instantaneously
