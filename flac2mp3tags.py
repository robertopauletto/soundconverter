import json
from os import path
import pathlib

from mutagen import id3
from mutagen.flac import FLAC
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC

ID3_KEYS = EasyID3.valid_keys.keys()


def load_tag_mapping(filename: str = "./easyID3toMp3Frame.json") -> dict:
    """Loads the tag mapping from a JSON file.

    Args:
        filename: The name of the JSON file to load.

    Returns:
        A dictionary containing the tag mappings.

    Raises:
        IOError: If the file cannot be loaded.
    """
    try:
        with open(filename) as fh:
            return json.load(fh)
    except IOError as ioerr:
        prompt = f"Error trying to load the id3 file mappings {filename}"
        raise IOError(f"{prompt}: {ioerr}")


class TagMappings:
    """A class to handle mappings between EasyID3 tags and MP3 frames."""

    def __init__(self, filename: str = "./easyID3toMp3Frame.json"):
        """Initializes the TagMappins class.

        Args:
            filename: The name of the JSON file with the tag mappings.
        """
        self._tag_mappings = load_tag_mapping(filename)

    @property
    def easy_id3_tags(self) -> list[str]:
        """Returns a list of EasyID3 tags.

        Returns:
            A list of strings, where each string is an EasyID3 tag.
        """
        tags = [item["easyID3_key"] for item in self._tag_mappings]
        return tags

    def get_mp3_frame_name(self, easy_id3_tag: str) -> tuple[str, str]:
        """Gets the MP3 frame name and description for a given EasyID3 tag.

        Args:
            easy_id3_tag: The EasyID3 tag to look up.

        Returns:
            A tuple containing the MP3 frame name and its description.

        Raises:
            ValueError: If the easy_id3_tag is not a valid EasyID3 tag.
        """
        if easy_id3_tag.lower() not in self.easy_id3_tags:
            raise ValueError(f"{easy_id3_tag} not an EasyID3 tag")
        result = [
            item for item in self._tag_mappings if item["easyID3_key"] == easy_id3_tag
        ]
        return result[0]["mp3_frame"], result[0]["description"]


def get_flac_tags(filename: str | pathlib.Path) -> tuple[dict, list]:
    """Gets the tags and pictures from a FLAC file.

    Args:
        filename: The path to the FLAC file.

    Returns:
        A tuple containing a dictionary of tags and a list of pictures.
    """
    audio = FLAC(filename)
    return audio.tags.as_dict(), audio.pictures


def copy_tags_to_mp3(
    flac_filename: str | pathlib.Path, mp3_filename: str | pathlib.Path, logger=None
):
    """Copies tags from a FLAC file to an MP3 file.

    Args:
        flac_filename: The path to the source FLAC file.
        mp3_filename: The path to the destination MP3 file.
        logger: A logger object for logging messages.
    """

    def log(message):
        if logger:
            logger(message)
        else:
            print(message)

    tm = TagMappings()
    tags, pics = get_flac_tags(flac_filename)
    mp3 = ID3(mp3_filename)
    for tag, flac_value in tags.items():
        tag = tag.lower()
        if tag not in ID3_KEYS:
            log(f"Unable to match {tag} to a ID3 frame")
            continue
        frame_name, frame_descr = tm.get_mp3_frame_name(tag.lower())
        frame = None
        try:
            if tag.startswith("TXXX:"):
                description = frame_name.split(":", 1)[1]
                frame_class = getattr(id3, "TXXX")
                frame = frame_class(encoding=3, desc=description, text=flac_value)
            elif tag.startswith("WOAR") or tag.startswith("WXXX"):
                frame_class = getattr(id3, "TXXX")
                frame = frame_class(
                    url=flac_value[0] if isinstance(flac_value, list) else flac_value
                )
            else:
                frame_class = getattr(id3, frame_name)
                frame = frame_class(encoding=3, text=flac_value)
            if not frame:
                continue
            log(f"Adding {frame_name} ({frame_descr}) with value {flac_value} ...")
            mp3.add(frame)
        except AttributeError:
            log(f"Frame {frame_name} not found in mutagen.id3")
        except Exception as e:
            log(f"Error adding tag {tag} ({frame_descr}): {e}")

    if not pics:
        log("No album cover to add")
    else:
        for pic in pics:
            log(f"Adding picture {pic.desc}")
            mp3.add(
                APIC(
                    encoding=3,
                    mime=pic.mime,
                    type=pic.type,
                    desc=pic.desc,
                    data=pic.data,
                )
            )
    mp3.save()
