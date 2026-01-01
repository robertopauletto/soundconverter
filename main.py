from pathlib import Path
import shutil

from loguru import logger
from pydub import AudioSegment

from flac2mp3tags import copy_tags_to_mp3

FFMPEG_PROGRAM = "ffmpeg"
default_args = {"bitrate": "192k"}

INPUT_EXTENSION = "flac"
OUTPUT_EXTENSION = "mp3"


class DependencyMissing(Exception):
    """Exception raised when a required dependency is missing."""

    pass


def check_ffmpeg_exists() -> bool:
    """Checks if FFmpeg is installed and available in the system's PATH.

    Returns:
        True if FFmpeg is found, False otherwise.

    Raises:
        DependencyMissing: If FFmpeg is not found.
    """
    if not shutil.which(FFMPEG_PROGRAM):
        raise DependencyMissing("FFmpeg is needed to handle MP3/FLAC files.")
    return True


def _create_output_filename(file_in: str | Path, output_fmt: str) -> Path:
    """Creates an output filename based on the input file and output format.

    Args:
        file_in: The input file path.
        output_fmt: The desired output format.

    Returns:
        A Path object representing the output file.
    """
    if isinstance(file_in, str):
        file_in = Path(file_in)
    file_out = f"{file_in.parent}/{file_in.stem}.{output_fmt}"
    return Path(file_out)


def convert(
    file_in: str | Path, bitrate: str = "192k", file_out: str | Path | None = None
) -> Path | None:
    """Converts an audio file to a different format.

    Args:
        file_in: The input audio file.
        bitrate: The mp3 bitrate
        file_out: The optional output filename.
        **kwargs: Additional arguments to pass to the pydub export function.

    Returns:
        The name of the converted file, or None if the conversion failed.
    """
    if isinstance(file_in, str):
        file_in = Path(file_in)
    if file_out is None:
        out_file: Path = _create_output_filename(file_in, OUTPUT_EXTENSION)
    elif isinstance(file_out, str):
        out_file = Path(file_out)
    else:
        out_file = file_out

    audio = AudioSegment.from_file(file_in)
    logger.info(f"Converting {file_in.name} => {out_file.name}...")
    params = {
        "out_f": out_file,
        "format": OUTPUT_EXTENSION,
        "bitrate": bitrate,
    }
    audio.export(**params)
    if out_file.exists() and out_file.stat().st_size > 0:
        return file_out
    else:
        return None


def batch_convert(folder: str, bitrate: str = "192k"):
    """Converts all files of a given format in a folder to another format.

    This function is a generator that yields progress information.

    Args:
        folder: The folder containing the files to convert.
        bitrate: The mp3 bitrate. Defaults to 192k

    Yields:
        A tuple containing the progress percentage and a log message.

    Raises:
        ValueError: If the folder does not exist or if the audio formats are
            not supported.
    """
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise ValueError(f"{folder} is not a directory")

    files_to_convert = list(folder_path.glob(f"*.{INPUT_EXTENSION}"))
    sorted_files_to_convert = sorted(files_to_convert, key=lambda p: p.name)
    total_files = len(sorted_files_to_convert)

    for i, flac_file in enumerate(sorted_files_to_convert):
        progress = int((i + 1) / total_files * 100)
        yield progress, f"Converting {flac_file.name}..."
        converted_file = convert(flac_file, bitrate)

        log_messages = []
        if converted_file:

            def logger(msg):
                log_messages.append(msg)

            copy_tags_to_mp3(flac_file, converted_file, logger=logger)
            for msg in log_messages:
                yield progress, msg
        else:
            log_messages.append(f"WARNING: Conversion of {flac_file} appears unsuccesful")

    yield 100, "Conversion complete."


def main(path_in: str):
    """The main function.

    Args:
        path_in: The input path.
    """
    pass
