import os.path
from pathlib import Path
import shutil
import sys

from loguru import logger
from pydub import AudioSegment

from flac2mp3tags import copy_tags_to_mp3

FFMPEG_PROGRAM = 'ffmpeg'
default_args = {
    "bitrate": "192k"
}

audo_formats = ["mp3", "flac"]


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
    outdir = file_in.parent
    file_out = f"{file_in.parent}/{file_in.stem}.{output_fmt}"
    return Path(file_out)


def convert(
        file_in: str | Path, output_fmt: str, file_out: str | None = None, **kwargs
) -> str | None:
    """Converts an audio file to a different format.

    Args:
        file_in: The input audio file.
        output_fmt: The desired output format.
        file_out: The optional output filename.
        **kwargs: Additional arguments to pass to the pydub export function.

    Returns:
        The name of the converted file, or None if the conversion failed.
    """
    if isinstance(file_in, str):
        file_in = Path(file_in)
    audio = AudioSegment.from_file(file_in)
    file_out = file_out or _create_output_filename(file_in, output_fmt)
    logger.info(f"Converting {file_in.name} => {file_out.name}...")
    params = {
        "out_f": file_out,
        "format": output_fmt,
        **kwargs,
    }
    result = audio.export(**params)
    if result and result.name:
        return result.name
    return None


def batch_convert(folder: str, input_fmt: str, output_fmt: str, **kwargs):
    """Converts all files of a given format in a folder to another format.

    This function is a generator that yields progress information.

    Args:
        folder: The folder containing the files to convert.
        input_fmt: The input audio format.
        output_fmt: The output audio format.
        **kwargs: Additional arguments to pass to the convert function.

    Yields:
        A tuple containing the progress percentage and a log message.

    Raises:
        ValueError: If the folder does not exist or if the audio formats are
            not supported.
    """
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise ValueError(f'{folder} is not a directory')
    if input_fmt not in audo_formats:
        raise ValueError(f'Unknown input audio format: {input_fmt}')
    if output_fmt not in audo_formats:
        raise ValueError(f'Unknown output audio format: {output_fmt}')

    files_to_convert = list(folder_path.glob(f'*.{input_fmt}'))
    total_files = len(files_to_convert)

    for i, flac_file in enumerate(files_to_convert):
        progress = int((i + 1) / total_files * 100)
        yield progress, f"Converting {flac_file.name}..."
        converted_file = convert(flac_file, output_fmt, **kwargs)

        if converted_file:
            log_messages = []
            def logger(msg):
                log_messages.append(msg)

            copy_tags_to_mp3(flac_file, converted_file, logger=logger)
            for msg in log_messages:
                yield progress, msg
    yield 100, "Conversion complete."



def main(path_in: str):
    """The main function.

    Args:
        path_in: The input path.
    """
    pass
    # convert(path_in, "mp3", bitrate="192k")


if __name__ == "__main__":
    batch_convert("./ra", 'flac', 'mp3', bitrate="192k")
