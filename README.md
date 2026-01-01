# FLAC to MP3 Batch Converter

This project is written in Python and does one thing and one thing only: it converts audio files from FLAC to MP3 while preserving metadata tags.
Basically I wanted to study how to execute a long running operation on a separate thread  in a Pyside6 application.

For a more featured audio file converter for Linux systems you can try [SoundConverter](https://soundconverter.org) for Gnome desktops or [soundKonverter](https://store.kde.org/p/1126634) for KDE desktops.

## Features

- Batch convert all files in a directory from FLAC to MP3 format. The user can choose the conversion bitrate.
- Copy metadata tags from FLAC files to MP3 files during conversion.
- Preserves album art.
- GUI interface

## Requirements

- Python 3.12+
- FFmpeg

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/robertopauletto/soundconverter.git
   cd soundconverter
   ```

2. This project and his dependencies are managed by [uv](https://docs.astral.sh/uv/getting-started/installation/). To sync the environment run `uv sync`

3. FFmpeg needs to be installed. You can usually install it using your system's package manager. For example, on Debian/Ubuntu:

   ```bash
   sudo apt-get install ffmpeg
   ```

Be aware that this project is intended to be run on Linux systems only. If you want to run it on other OSs, you may need to do some modifications.

## Usage

To convert all FLAC files in a directory to MP3, you can use the GUI running the `gui.py` script.

## How it Works

The script uses `pydub` to handle the audio conversion and `mutagen` to read and write metadata tags.

It uses a JSON file (`easyID3toMp3Frame.json`) to map FLAC tags to ID3 frames for MP3s.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
