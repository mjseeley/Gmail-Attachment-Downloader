# Converted to Python3
# Download ALL attachments from GMail
# 1. Script needs to be run via console not in an IDE, getpass.getpass() will fail otherwise.
#    https://docs.python.org/3/library/getpass.html
# 2. Make sure you have IMAP enabled in your GMail settings.
#    https://support.google.com/mail/troubleshooter/1668960?hl=en
# 3. If you are using 2 step verification you may need an APP Password.
#    https://support.google.com/accounts/answer/185833
#    https://myaccount.google.com/apppasswords
# 4. Reference information for GMail IMAP extension can be found here.
#    https://developers.google.com/gmail/imap_extensions


import email
import hashlib
import getpass
import imaplib
import os
from collections import defaultdict, Counter
import platform
import organize

fileNameCounter = Counter()
fileNameHashes = defaultdict(set)
NewMsgIDs = set()
ProcessedMsgIDs = set()


def recover(resume_file):
    if os.path.exists(resume_file):
        print("Recovery file found resuming...")
        with open(resume_file) as f:
            processed_ids = f.read()
            for ProcessedId in processed_ids.split(","):
                ProcessedMsgIDs.add(ProcessedId)
    else:
        print("No Recovery file found.")
        open(resume_file, "a").close()


def generate_mail_messages(gmail_user_name, p_word, resume_file):
    imap_session = imaplib.IMAP4_SSL("imap.gmail.com")

    typ, account_details = imap_session.login(gmail_user_name, p_word)

    print(f"Status: {typ}")
    print(account_details[0])
    if typ != "OK":
        print("Not able to sign in!")
        raise NameError("Not able to sign in!")
    imap_session.select('"[Gmail]/All Mail"')
    typ, data = imap_session.search(None, '(X-GM-RAW "has:attachment")')
    # typ, data = imapSession.search(None, 'ALL')
    if typ != "OK":
        print("Error searching Inbox.")
        raise NameError("Error searching Inbox.")

    # Iterating over all emails
    for msgId in data[0].split():
        NewMsgIDs.add(msgId)
        typ, message_parts = imap_session.fetch(msgId, "(RFC822)")
        if typ != "OK":
            print("Error fetching mail.")
            raise NameError("Error fetching mail.")
        email_body = message_parts[0][1]
        if msgId not in ProcessedMsgIDs:
            yield email.message_from_bytes(email_body)
            ProcessedMsgIDs.add(msgId)
            with open(resume_file, "a") as resume:
                resume.write("{id},".format(id=msgId))

    imap_session.close()
    imap_session.logout()


def save_attachments(message, directory, sort_by):

    # get additional details..
    msg_from = message["From"]
    msg_from_domain = message["From"]
    msg_to = message["To"]
    msg_date = message["Date"]

    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            # print(part.as_string())
            continue
        if part.get("Content-Disposition") is None:
            # print(part.as_string())
            continue
        file_name = part.get_filename()
        if file_name is not None:
            file_name = "".join(file_name.splitlines())
        if file_name:
            # print('Processing: {file}'.format(file=fileName))
            payload = part.get_payload(decode=True)
            if payload:
                x_hash = hashlib.md5(payload).hexdigest()

                if x_hash in fileNameHashes[file_name]:
                    print("\tSkipping duplicate file: {file}".format(file=file_name))
                    continue
                fileNameCounter[file_name] += 1
                file_str, file_extension = os.path.splitext(file_name)
                if fileNameCounter[file_name] > 1:
                    new_file_name = "{file}({suffix}){ext}".format(
                        suffix=fileNameCounter[file_name],
                        file=file_str,
                        ext=file_extension,
                    )
                    print(
                        "\tRenaming and storing: {file} to {new_file}".format(
                            file=file_name, new_file=new_file_name
                        )
                    )
                else:
                    new_file_name = file_name
                    print("\tStoring: {file}".format(file=file_name))
                fileNameHashes[file_name].add(x_hash)
                file_path = os.path.join(directory, new_file_name)
                if os.path.exists(file_path):
                    print("\tExists in destination: {file}".format(file=new_file_name))
                    continue
                try:
                    with open(file_path, "wb") as fp:
                        fp.write(payload)
                except EnvironmentError:
                    print(
                        "Could not store: {file} it has an invalid file name or path under {op_sys}.".format(
                            file=file_path, op_sys=platform.system()
                        )
                    )
            else:
                print(
                    "Attachment {file} was returned as type: {ftype} skipping...".format(
                        file=file_name, ftype=type(payload)
                    )
                )
                continue


if __name__ == "__main__":
    resumeFile = os.path.join("resume.txt")
    user_name = input("Enter your GMail username: ")
    password = getpass.getpass("Enter your password: ")

    recover(resumeFile)
    save_path = input("Enter Destination path: ")
    if not os.path.exists(save_path):
        try:
            os.makedirs(save_path)
        except EnvironmentError:
            print(f"Could not create directory {save_path}")
            raise
    print(f"Items will be saved in {save_path}.")
    input("Press enter to continue...")
    sort_by = input(
        """Enter sort method [1-5]:
        1. Extension (after download)
        2. Size (after download)
        3. File Type (after download)
        4. Date
        5. Sender
        6. Sender Domain
        7. Test\n"""
    )

    match sort_by:
        case "1":
            for msg in generate_mail_messages(user_name, password, resumeFile):
                save_attachments(msg, save_path)
            organize.ByExtension(f"{save_path}")
        case "2":
            for msg in generate_mail_messages(user_name, password, resumeFile):
                save_attachments(msg, save_path)
            organize.BySize(f"{save_path}")
        case "3":
            for msg in generate_mail_messages(user_name, password, resumeFile):
                save_attachments(msg, save_path)
            organize.ByType(f"{save_path}")
        case "4":
            for msg in generate_mail_messages(user_name, password, resumeFile):
                save_attachments(msg, organize.ByDate(f"{save_path}", msg))
        case "5":
            for msg in generate_mail_messages(user_name, password, resumeFile):
                save_attachments(msg, organize.BySenderEmail(f"{save_path}", msg))
        case "6":
            for msg in generate_mail_messages(user_name, password, resumeFile):
                save_attachments(msg, organize.ByDomain(f"{save_path}", msg))
        case "7":
            for msg in generate_mail_messages(user_name, password, resumeFile):
                save_attachments(msg, organize.ByExtTest(f"{save_path}", msg))
        case other:
            for msg in generate_mail_messages(user_name, password, resumeFile):
                save_attachments(msg, f"{save_path}")

    os.remove(resumeFile)
