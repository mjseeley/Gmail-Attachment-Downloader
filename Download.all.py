# Download ALL attachments from GMAIL
# Make sure you have IMAP enabled in your gmail settings.
# If you are using 2 step verification you may need an APP Password.
# https://support.google.com/accounts/answer/185833
#

import email
import hashlib
import getpass
import imaplib
import os
from collections import defaultdict, Counter
import platform

fileNameCounter = Counter()
fileNameHashes = defaultdict(set)


def GenerateMailMessages(userName, password):
    imapSession = imaplib.IMAP4_SSL('imap.gmail.com')
    typ, accountDetails = imapSession.login(userName, password)

    print(typ)
    print(accountDetails)
    if typ != 'OK':
        print('Not able to sign in!')
        raise

    imapSession.select('[Gmail]/All Mail')
    typ, data = imapSession.search(None, 'ALL')
    if typ != 'OK':
        print('Error searching Inbox.')
        raise

    # Iterating over all emails
    for msgId in data[0].split():
        typ, messageParts = imapSession.fetch(msgId, '(RFC822)')
        if typ != 'OK':
            print('Error fetching mail.')
            raise
        emailBody = messageParts[0][1]
        yield email.message_from_string(emailBody)
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
                print('Could not store: {file} it has a shitty file name or path under {op_sys}.'.format())
                    file=file_path, op_sys=platform.system())


if __name__ == '__main__':
    userName = raw_input('Enter your GMail username: ')
    password = getpass.getpass('Enter your password: ')
    if 'attachments' not in os.listdir(os.getcwd()):
        os.mkdir('attachments')
    for msg in GenerateMailMessages(userName, password):
        SaveAttachmentsFromMailMessage(msg, 'attachments')
