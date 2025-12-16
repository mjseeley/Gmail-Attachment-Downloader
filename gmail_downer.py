# Description: This script connects to a Gmail account via IMAP, identifies all emails containing attachments, and downloads those attachments. Users can specify a directory to save the attachments and choose from various sorting methods, such as by file extension, size, type, sender, or date. The script also supports session recovery to handle interruptions and avoid redownloading previously processed emails.

from email import message, header, message_from_bytes
from hashlib import md5
from getpass import getpass
import imaplib
import os
import json
import logging
from collections import defaultdict, Counter
from pathlib import Path
from enum import Enum
import organize

# Setting up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# TODO: prevent overwriting of files on resume since the count has been reset (tag the files with the message id?)


class SortMethod(Enum):
    EXTENSION = 1  # working
    SIZE = 2  # working
    MIMETYPE = 3  # working
    DATE = 4  # working but creates empty folders may be due to files already being saved elsewhere and matching the hash.
    SENDER = 5  #  working


IMAP_SERVER = "imap.gmail.com"
MANIFEST_FILE = Path("file_manifest.json")


def recover(
    resume_file: Path, processed_id_file: Path
) -> tuple[str, Path, SortMethod, set]:
    """
    Recovers the last state of the script from saved files if available.

    Args:
        resume_file (Path): The file containing saved state information.
        processed_id_file (Path): The file containing IDs of processed messages.

    Returns:
        tuple: A tuple containing user_name, save_path, sort_by, and processed_msg_ids.
    """
    user_name, save_path, sort_by = None, None, None
    processed_msg_ids = set()
    if resume_file.exists():
        recover = input(
            "Recovery files found. Would you like to recover the last state? (y/n) "
        ).lower()
        if recover == "y":
            logging.info("Recovering last state...")
            if processed_id_file.exists():
                with processed_id_file.open() as f:
                    processed_ids = f.read()
                    processed_msg_ids = set(filter(None, processed_ids.split(",")))
            processed_msg_ids = {msg_id.strip() for msg_id in processed_msg_ids}
            with resume_file.open() as f:
                last_state = f.read().splitlines()
                user_name = last_state[0].split(" = ")[1]
                save_path = Path(last_state[1].split(" = ")[1])
                sort_by = SortMethod[last_state[2].split(" = ")[1]]
        else:
            logging.info(
                "Recovery file found but not recovered. Deleting recovery files..."
            )
            processed_id_file.unlink(missing_ok=True)
            resume_file.unlink(missing_ok=True)
    else:
        logging.info("No Recovery file found.")
    resume_file.touch()
    processed_id_file.touch()
    return user_name, save_path, sort_by, processed_msg_ids


def save_state(resume_file: Path, user_name: str, save_path: Path, sort_by: SortMethod):
    """
    Saves the current state of the script for recovery in case of interruption.

    Args:
        resume_file (Path): The file to save the state information.
        user_name (str): The Gmail username.
        save_path (Path): The directory path where attachments are saved.
        sort_by (SortMethod): The sorting method used for organizing attachments.
    """
    with resume_file.open("w") as f:
        f.write(f"user_name = {user_name}\n")
        f.write(f"save_path = {save_path}\n")
        f.write(f"sort_by = {sort_by.name}\n")


def load_manifest(manifest_path: Path) -> tuple[Counter, defaultdict]:
    """Load persisted counters and hashes to avoid overwriting on resume."""
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text())
            counters = Counter(data.get("counters", {}))
            hashes_raw = data.get("hashes", {})
            hashes = defaultdict(set, {k: set(v) for k, v in hashes_raw.items()})
            return counters, hashes
        except Exception:
            logging.warning("Manifest file unreadable; starting fresh.")
    return Counter(), defaultdict(set)


def save_manifest(manifest_path: Path, counters: Counter, hashes: defaultdict):
    data = {
        "counters": counters,
        "hashes": {k: list(v) for k, v in hashes.items()},
    }
    manifest_path.write_text(json.dumps(data, indent=2))


def decode_mime_words(s: str) -> str:
    """
    Decodes MIME-encoded words in an email header to a UTF-8 string.

    Args:
        s (str): The MIME-encoded string.

    Returns:
        str: The decoded string.
    """
    decoded_words = header.decode_header(s)
    return "".join(
        word.decode(encoding or "utf-8") if isinstance(word, bytes) else word
        for word, encoding in decoded_words
    )


def generate_mail_messages(
    gmail_user_name: str,
    password: str,
    processed_id_file: Path,
    processed_ids: set,
    max_attempts: int = 3,
):
    """
    Generates email messages from the Gmail account that have attachments.

    Args:
        gmail_user_name (str): The Gmail username.
        password (str): The Gmail password.
        processed_id_file (Path): The file containing IDs of processed messages.
        processed_ids (set): The set of processed message IDs.
        max_attempts (int, optional): Maximum attempts to fetch a message. Defaults to 3.

    Yields:
        message.Message: The email message with attachments.
    """
    with imaplib.IMAP4_SSL(IMAP_SERVER) as imap_session:
        try:
            imap_session.login(gmail_user_name, password)
            logging.info("Login successful.")
        except imaplib.IMAP4.error:
            logging.error("Login failed. Please check your credentials.")
            return
        imap_session.select('"[Gmail]/All Mail"')
        session_typ, data = imap_session.search(None, '(X-GM-RAW "has:attachment")')
        if session_typ != "OK":
            raise Exception("Error searching Inbox.")
        for msg_id in data[0].split():
            msg_id_str = msg_id.decode()
            if msg_id_str not in processed_ids:
                for attempt in range(max_attempts):
                    msg_typ, message_parts = imap_session.fetch(msg_id, "(RFC822)")
                    if msg_typ == "OK":
                        yield message_from_bytes(message_parts[0][1])
                        processed_ids.add(msg_id_str)
                        with processed_id_file.open("a") as resume:
                            resume.write(f"{msg_id_str},")
                        break
                    else:
                        logging.warning(
                            f"Error fetching mail {msg_id_str}, attempt {attempt + 1}/{max_attempts}"
                        )
                else:
                    logging.error(
                        f"Failed to fetch mail {msg_id_str} after {max_attempts} attempts."
                    )


def save_attachments(
    message: message.Message,
    directory: Path,
    sort_by: SortMethod,
    file_name_counter: Counter,
    file_name_hashes: defaultdict,
    manifest_path: Path,
):
    """
    Saves attachments from an email message to the specified directory.

    Args:
        message (message.Message): The email message containing attachments.
        directory (Path): The base directory where attachments will be saved.
        sort_by (SortMethod): The sorting method used for organizing attachments.
        file_name_counter (Counter): A counter to manage duplicate file names.
        file_name_hashes (defaultdict): A dictionary to track unique attachments by hash.
    """
    msg_from = message.get("From") or "unknown_sender"
    msg_date = message.get("Date")

    if sort_by == SortMethod.DATE:
        directory = organize.by_date(directory, msg_date)
    elif sort_by == SortMethod.SENDER:
        directory = organize.by_sender_email(directory, msg_from)

    for part in message.walk():
        if (
            part.get_content_maintype() == "multipart"
            or part.get("Content-Disposition") is None
        ):
            continue
        file_name = part.get_filename()
        if not file_name:
            # Fallback for nameless attachments
            file_name_counter["__unnamed__"] += 1
            subtype = part.get_content_subtype() or "bin"
            file_name = f"attachment{file_name_counter['__unnamed__']}.{subtype}"

        logging.debug(f"Original file name: {file_name}")
        file_name = (
            decode_mime_words(file_name)
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("*", "_")
            .replace("?", "_")
            .replace('"', "_")
            .replace("<", "_")
            .replace(">", "_")
            .replace("|", "_")
            .replace("\n", "")
            .replace("\r", "")
        )
        logging.debug(f"Sanitized file name: {file_name}")
        # Limit the file name length to avoid exceeding the Windows path length limit
        max_length = 150
        if len(file_name) > max_length:
            file_name = file_name[:max_length] + os.path.splitext(file_name)[1]
        payload = part.get_payload(decode=True)
        if not payload:
            logging.info("Skipped attachment with empty payload")
            continue

        x_hash = md5(payload).hexdigest()
        if x_hash not in file_name_hashes[file_name]:
            file_name_counter[file_name] += 1
            file_str, file_extension = os.path.splitext(file_name)
            new_file_name = (
                f"{file_str}(v.{file_name_counter[file_name]}){file_extension}"
                if file_name_counter[file_name] > 1
                else file_name
            )
            file_name_hashes[file_name].add(x_hash)
            if sort_by == SortMethod.EXTENSION:
                file_dir = directory / (
                    file_extension.lower().strip(".")
                    if file_extension
                    else "other"
                )
            elif sort_by == SortMethod.SIZE:
                file_dir = directory / organize.by_size(
                    len(payload)
                )
            elif sort_by == SortMethod.MIMETYPE:
                file_dir = directory / (
                    organize.by_mime_type(file_name)
                )
            else:
                file_dir = directory
            file_dir = organize.build_and_return_directory(file_dir)
            file_path = (file_dir / new_file_name).resolve()
            # Use Windows extended-length path prefix for long paths on Windows only
            if os.name == 'nt' and len(str(file_path)) > 260:
                file_path = Path(rf"\\?\{file_path}")
            if not file_path.exists():
                with file_path.open("wb") as fp:
                    fp.write(payload)
                save_manifest(manifest_path, file_name_counter, file_name_hashes)
            else:
                logging.info(f"\tExists in destination: {new_file_name}")


def main():
    """
    Main function that drives the script, handling user input, downloading attachments, and organizing them.
    """
    file_name_counter, file_name_hashes = load_manifest(MANIFEST_FILE)
    resume_file = Path("resume.txt")
    processed_id_file = Path("processed_ids.txt")

    user_name, save_path, sort_by, processed_ids = recover(
        resume_file, processed_id_file
    )
    if user_name is not None:
        password = os.getenv("EMAIL_PASSWORD") or getpass(
            f"Enter the password for {user_name}: "
        )
    else:
        user_name = input("Enter your Gmail username: ")
        password = os.getenv("EMAIL_PASSWORD") or getpass("Enter your password: ")
        save_path = Path(input("Enter Destination path: "))
        save_path.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                sort_choice = int(
                    input(
                        """Enter sort method [1-5]:
            1. Extension
            2. Size
            3. MIME Type
            4. Date Year -> Month -> Day
            5. Domain -> Sender
        """
                    ).strip()
                )
                sort_by = SortMethod(sort_choice)
                break
            except (ValueError, KeyError):
                print("Please enter a number between 1 and 5.")
        save_state(resume_file, user_name, save_path, sort_by)

    for msg in generate_mail_messages(
        user_name, password, processed_id_file, processed_ids
    ):
        save_attachments(
            msg,
            save_path,
            sort_by,
            file_name_counter,
            file_name_hashes,
            MANIFEST_FILE,
        )

    processed_id_file.unlink(missing_ok=True)
    resume_file.unlink(missing_ok=True)
    save_manifest(MANIFEST_FILE, file_name_counter, file_name_hashes)


if __name__ == "__main__":
    main()
