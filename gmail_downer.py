# Download ALL attachments from GMail
# 1. Script needs to be run via console not in an IDE, getpass.getpass() will fail otherwise.
#    https://docs.python.org/2/library/getpass.html
# 2. Make sure you have IMAP enabled in your GMail settings.
#    https://support.google.com/mail/troubleshooter/1668960?hl=en
# 3. If you are using 2 step verification you may need an APP Password.
#    https://support.google.com/accounts/answer/185833
# 4. Reference information for GMail IMAP extension can be found here.
#    https://developers.google.com/gmail/imap_extensions


import email
import hashlib
import getpass
import imaplib
import os
from collections import defaultdict, Counter
import platform

fileNameCounter = Counter()
fileNameHashes = defaultdict(set)
NewMsgIDs = set()
ProcessedMsgIDs = set()


def recover(resumeFile):
    if os.path.exists(resumeFile):
        print('Recovery file found resuming...')
        with open(resumeFile) as f:
            processedIds = f.read()
            for ProcessedId in processedIds.split(','):
                ProcessedMsgIDs.add(ProcessedId)
    else:
        print('No Recovery file found.')
        open(resumeFile, 'a').close()


def GenerateMailMessages(userName, password, resumeFile):
    imapSession = imaplib.IMAP4_SSL('imap.gmail.com')
    typ, accountDetails = imapSession.login(userName, password)

    print(typ)
    print(accountDetails)
    if typ != 'OK':
        print('Not able to sign in!')
        raise

    imapSession.select('[Gmail]/All Mail')
    typ, data = imapSession.search(None, '(X-GM-RAW "has:attachment")')
    # typ, data = imapSession.search(None, 'ALL')
    if typ != 'OK':
        print('Error searching Inbox.')
        raise

    # Iterating over all emails
    for msgId in data[0].split():
        NewMsgIDs.add(msgId)
        typ, messageParts = imapSession.fetch(msgId, '(RFC822)')
        if typ != 'OK':
            print('Error fetching mail.')
            raise
        emailBody = messageParts[0][1]
        if msgId not in ProcessedMsgIDs:
            yield email.message_from_string(emailBody)
            ProcessedMsgIDs.add(msgId)
            with open(resumeFile, "a") as resume:
                resume.write('{id},'.format(id=msgId))

    imapSession.close()
    imapSession.logout()


def SaveAttachmentsFromMailMessage(message, directory):
    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            # print(part.as_string())
            continue
        if part.get('Content-Disposition') is None:
            # print(part.as_string())
            continue
        fileName = part.get_filename()
        if fileName is not None:
            fileName = ''.join(fileName.splitlines())
        if fileName:
            # print('Processing: {file}'.format(file=fileName))
            payload = part.get_payload(decode=True)
            if payload:
                x_hash = hashlib.md5(payload).hexdigest()

                if x_hash in fileNameHashes[fileName]:
                    print('\tSkipping duplicate file: {file}'.format(file=fileName))
                    continue
                fileNameCounter[fileName] += 1
                fileStr, fileExtension = os.path.splitext(fileName)
                if fileNameCounter[fileName] > 1:
                    new_fileName = '{file}({suffix}){ext}'.format(suffix=fileNameCounter[fileName],
                                                                  file=fileStr, ext=fileExtension)
                    print('\tRenaming and storing: {file} to {new_file}'.format(file=fileName,
                                                                                new_file=new_fileName))
                else:
                    new_fileName = fileName
                    print('\tStoring: {file}'.format(file=fileName))
                fileNameHashes[fileName].add(x_hash)
                file_path = os.path.join(directory, new_fileName)
                if os.path.exists(file_path):
                    print('\tExists in destination: {file}'.format(file=new_fileName))
                    continue
                try:
                    with open(file_path, 'wb') as fp:
                        fp.write(payload)
                except:
                    print('Could not store: {file} it has a shitty file name or path under {op_sys}.'.format(
                        file=file_path,
                        op_sys=platform.system()))
            else:
                print('Attachment {file} was returned as type: {ftype} skipping...'.format(file=fileName,
                                                                                           ftype=type(payload)))
                continue

if __name__ == '__main__':
    resumeFile = file_path = os.path.join('resume.txt')
    userName = raw_input('Enter your GMail username: ')
    password = getpass.getpass('Enter your password: ')
    recover(resumeFile)
    if 'attachments' not in os.listdir(os.getcwd()):
        os.mkdir('attachments')
    for msg in GenerateMailMessages(userName, password, resumeFile):
        SaveAttachmentsFromMailMessage(msg, 'attachments')
    os.remove(file_path)
