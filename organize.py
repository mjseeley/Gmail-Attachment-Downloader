# Description: This module provides functions to organize downloaded email attachments based on various criteria such as size, type, date, sender, or domain.

from pathlib import Path
from enum import Enum
from email.utils import parsedate_to_datetime
import mimetypes
import os


class SizeCategoryEnum(Enum):
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"


def build_and_return_directory(directory: Path) -> Path:
    """
    Builds the directory if it does not exist and returns the directory path.

    Args:
        directory (Path): The path to the directory to be created.

    Returns:
        Path: The path to the created (or existing) directory.
    """
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def by_size(size: int) -> str:
    """
    Categorizes a file based on its size.

    Args:
        size (int): Size of the file in bytes.

    Returns:
        str: The size category (e.g., "tiny", "small").
    """
    if size < 10240:
        return SizeCategoryEnum.TINY.value
    elif size < 102400:
        return SizeCategoryEnum.SMALL.value
    elif size < 1024000:
        return SizeCategoryEnum.MEDIUM.value
    elif size < 10240000:
        return SizeCategoryEnum.LARGE.value
    else:
        return SizeCategoryEnum.HUGE.value


def by_mime_type(extension: str) -> Path:
    """
    Determines the general type of a file based on its MIME type.

    Args:
        extension (str): The file extension (e.g., ".jpg", ".pdf").

    Returns:
        Path: The path segment for the file type (e.g., Path("image/jpeg"), Path("other")).
    """
    mime_type, _ = mimetypes.guess_type(extension)
    if mime_type:
        main_type, sub_type = mime_type.split("/")
        return Path(main_type) / sub_type
    return Path("other")


def by_date(save_folder: Path, date: str | None) -> Path:
    """
    Creates a folder structure based on the date of an email, falling back to
    an `unknown_date` folder when parsing fails.

    Args:
        save_folder (Path): The base folder where the attachments will be saved.
        date (str | None): The date string from the email header.

    Returns:
        Path: The path to the created directory.
    """
    try:
        parsed = parsedate_to_datetime(date) if date else None
    except Exception:
        parsed = None

    if not parsed:
        return build_and_return_directory(save_folder / "unknown_date")

    parsed_date = parsed.date()
    year = str(parsed_date.year)
    month = parsed_date.strftime("%b")  # Use month abbreviation for readability
    day = str(parsed_date.day)
    return build_and_return_directory(save_folder / year / month / day)


def by_sender_email(save_folder: Path, sender: str | None) -> Path:
    """
    Creates a folder structure based on the sender's email address.

    Args:
        save_folder (Path): The base folder where the attachments will be saved.
        sender (str | None): The sender's email address.

    Returns:
        Path: The path to the created directory.
    """
    if not sender:
        return build_and_return_directory(save_folder / "unknown_sender" / "unknown_sender")

    domain = (sender.split("@")[-1]).replace(">", "") if "@" in sender else "unknown_sender"
    if "<" in sender:
        sender = sender.split("<")[1].split(">")[0]
    sender = sender or "unknown_sender"
    return build_and_return_directory(save_folder / domain / sender)


if __name__ == "__main__":
    pass
