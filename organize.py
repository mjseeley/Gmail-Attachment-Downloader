# Description: This module provides functions to organize downloaded email attachments based on various criteria such as size, type, date, sender, or domain.

from pathlib import Path
from enum import Enum
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


def by_mime_type(extension: str) -> str:
    """
    Determines the general type of a file based on its MIME type.

    Args:
        extension (str): The file extension (e.g., ".jpg", ".pdf").

    Returns:
        str: The general type of the file (e.g., "image", "text", "other").
    """
    mime_type, _ = mimetypes.guess_type(extension)
    if mime_type:
        main_type, sub_type = mime_type.split("/")
        return os.path.join(main_type, sub_type)
    if mime_type is None:
        return "other"


def by_date(save_folder: Path, date: str) -> Path:
    """
    Creates a folder structure based on the date of an email.
    I tried using datetime.strptime(date, date_format), but it was not able to parse all date formats.
    Args:
        save_folder (Path): The base folder where the attachments will be saved.
        date (str): The date string from the email header.

    Returns:
        Path: The path to the created directory.
    """
    # sample date format: 'Fri, 1 Jul 2011 16:21:50 -0500'
    day, month, year = date.split(" ")[1:4]
    if not year.isnumeric():
        day, month, year = date.split(" ")[0:3]
    if len(year) == 2:
        year = "20" + year
    if len(year) == 1 and not day.isnumeric():
        day, month, year = date.split(" ")[2:5]
    day = day.lstrip("0")
    return build_and_return_directory(save_folder / year / month / day)


def by_sender_email(save_folder: Path, sender: str) -> Path:
    """
    Creates a folder structure based on the sender's email address.

    Args:
        save_folder (Path): The base folder where the attachments will be saved.
        sender (str): The sender's email address.

    Returns:
        Path: The path to the created directory.
    """
    domain = (
        (sender.split("@")[-1]).replace(">", "") if "@" in sender else "unknown_sender"
    )
    if "<" in sender:
        sender = sender.split("<")[1].split(">")[0]
    return build_and_return_directory(save_folder / domain / sender)


if __name__ == "__main__":
    pass
