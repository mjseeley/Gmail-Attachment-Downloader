# Description: This script downloads attachments from all emails in the user's Gmail account and saves them in a specified directory. It also sorts the attachments based on the user's preference.

import ast
import email
import hashlib
import getpass
import imaplib
import os
from collections import defaultdict, Counter
import organize
from enum import Enum

#TODO: prevent overwriting of files on resume since the count has been reset (tag the files with the message id?)

class SortMethod(Enum):
    EXTENSION = 1
    SIZE = 2
    TYPE = 3
    DATE = 4
    SENDER = 5
    DOMAIN = 6


def recover(resume_file, processed_id_file):
    user_name, save_path, sort_by = None, None, None
    ProcessedMsgIDs = set()
    if os.path.exists(resume_file):
        print("Recovery files found would you like to recover the last state? (y/n)")
        recover = input()
        if recover.lower() == "y":
            print("Recovering last state...")
            if os.path.exists(processed_id_file):
                with open(processed_id_file) as f:
                    processed_ids = f.read()
                    for ProcessedId in filter(None, processed_ids.split(",")):
                        ProcessedMsgIDs.add(ast.literal_eval(ProcessedId))
            with open(resume_file) as f:
                last_state = f.read()
                user_name = last_state.split("\n")[0].split(" = ")[1]
                save_path = last_state.split("\n")[1].split(" = ")[1]
                sort_by = SortMethod[last_state.split("\n")[2].split(" = ")[1]]
        else:
            print("Recovery file found but not recovered. Deleting recovery files...")
            os.remove(processed_id_file)
            os.remove(resume_file)
            return ProcessedMsgIDs
    else:
        print("No Recovery file found.")
    open(processed_id_file, "a").close()
    open(resume_file, "a").close()
    return user_name, save_path, sort_by, ProcessedMsgIDs


def save_state(resume_file, user_name, save_path, sort_by):
    with open(resume_file, "w") as f:
        f.write(f"user_name = {user_name}\n")
        f.write(f"save_path = {save_path}\n")
        f.write(f"sort_by = {sort_by.name}\n")
    open(resume_file, "a").close()


def decode_mime_words(s):
    """Decode MIME encoded words in a string to a UTF-8 string."""
    decoded_words = email.header.decode_header(s)
    return ''.join(word.decode(encoding or 'utf-8') if isinstance(word, bytes) else word 
                   for word, encoding in decoded_words)


def generate_mail_messages(gmail_user_name, password, processed_id_file, processed_ids, max_attempts=3):
    with imaplib.IMAP4_SSL("imap.gmail.com") as imap_session:
        imap_session.login(gmail_user_name, password)
        imap_session.select('"[Gmail]/All Mail"')
        session_typ, data = imap_session.search(None, '(X-GM-RAW "has:attachment")')
        if session_typ != "OK":
            raise Exception("Error searching Inbox.")
        for msg_id in data[0].split():
            if msg_id not in processed_ids:
                attempts = 0
                while attempts < max_attempts:
                    msg_typ, message_parts = imap_session.fetch(msg_id, "(RFC822)")
                    if msg_typ == "OK":
                        email_body = message_parts[0][1]
                        yield email.message_from_bytes(email_body)
                        processed_ids.add(msg_id)
                        with open(processed_id_file, "a") as resume:
                            resume.write(f"{msg_id},")
                        break  # Break out of the retry loop
                    else:
                        print(f"Error fetching mail {msg_id}, attempt {attempts + 1}/{max_attempts}")
                        attempts += 1
                if attempts == max_attempts:
                    print(f"Failed to fetch mail {msg_id} after {max_attempts} attempts.")


def save_attachments(message, directory, sort_by, file_name_counter, file_name_hashes):
    # Extract additional details needed for sorting
    msg_from = message["From"]
    msg_date = message["Date"]
    msg_domain = (msg_from.split("@")[-1]).replace(">","") if "@" in msg_from else None

    # Additional processing based on sort method
    if sort_by == SortMethod.DATE:
        directory = organize.ByDate(directory, msg_date)
    elif sort_by == SortMethod.SENDER:
        directory = organize.BySenderEmail(directory, msg_from)
    elif sort_by == SortMethod.DOMAIN:
        directory = organize.ByDomain(directory, msg_domain)

    for part in message.walk():
        if part.get_content_maintype() == "multipart" or part.get("Content-Disposition") is None:
            continue
        file_name = part.get_filename()
        if file_name:
            file_name = decode_mime_words(file_name)
            file_name = file_name.replace("/", "_")
            file_name = "".join(file_name.splitlines())
            payload = part.get_payload(decode=True)
            if payload:
                x_hash = hashlib.md5(payload).hexdigest()
                if x_hash not in file_name_hashes[file_name]:
                    file_name_counter[file_name] += 1
                    file_str, file_extension = os.path.splitext(file_name)
                    new_file_name = f"{file_str}(v.{file_name_counter[file_name]}){file_extension}" if file_name_counter[file_name] > 1 else file_name
                    # new_file_name = f"{file_str}(msgId.{message}){file_extension}" if file_name_counter[file_name] > 1 else file_name
                    print(f"\tStoring: {new_file_name}")
                    file_name_hashes[file_name].add(x_hash)
                    if sort_by == SortMethod.EXTENSION:
                        # If the file has no extension, store it in an 'other' folder
                        if file_extension == '':
                            file_dir = os.path.join(directory, 'other')
                        else:
                            file_dir = os.path.join(directory, file_extension.lower().strip("."))
                        organize.build_directory(file_dir)
                        file_path = os.path.join(file_dir, new_file_name)
                    elif sort_by == SortMethod.SIZE:
                        file_dir = os.path.join(directory, organize.BySize(len(payload)))
                        organize.build_directory(file_dir)
                        file_path = os.path.join(file_dir, new_file_name)
                    elif sort_by == SortMethod.TYPE:
                        # If the file has no extension, store it in an 'other' folder
                        if file_extension == '':
                            file_dir = os.path.join(directory, 'other')
                        else:
                            file_dir = os.path.join(directory, organize.ByType(file_extension))
                        organize.build_directory(file_dir)
                        file_path = os.path.join(file_dir, new_file_name)
                    else:
                        file_path = os.path.join(directory, new_file_name)
                    if not os.path.exists(file_path):
                        with open(file_path, "wb") as fp:
                            fp.write(payload)
                    else:
                        print(f"\tExists in destination: {new_file_name}")


def main():
    file_name_counter = Counter()
    file_name_hashes = defaultdict(set)
    resume_file = "resume.txt"
    processed_id_file = "processed_ids.txt"
    user_name = None
    password = None
    save_path = None
    sort_by = None
    
    user_name, save_path, sort_by, processed_ids = recover(resume_file, processed_id_file)
    if user_name is not None:
        password = getpass.getpass(f"Enter the password for {user_name}: ")
    else:
        user_name = input("Enter your GMail username: ")
        password = getpass.getpass("Enter your password: ")
        save_path = input("Enter Destination path: ")
        os.makedirs(save_path, exist_ok=True)
        print(f"Items will be saved in {save_path}.")
        input("Press enter to continue...")
        sort_by = SortMethod(int(input("""Enter sort method [1-6]:
            1. Extension
            2. Size
            3. Type
            4. Date
            5. Sender
            6. Domain\n""")))
        save_state(resume_file, user_name, save_path, sort_by)

    for msg in generate_mail_messages(user_name, password, processed_id_file, processed_ids):
        save_attachments(msg, save_path, sort_by, file_name_counter, file_name_hashes)

    os.remove(processed_id_file)
    os.remove(resume_file)

if __name__ == "__main__":
    main()
