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
fileNameList_dict = defaultdict(list)


def get_hash(file_to_hash):
    # return unique hash of file
    blocksize = 65536
    hasher = hashlib.md5()
    try:
        with open(file_to_hash, 'rb') as afile:
            buf = afile.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(blocksize)
    except IOError as err:
        print err
    return hasher.hexdigest()


detach_dir = '.'
if 'attachments' not in os.listdir(detach_dir):
    os.mkdir('attachments')

userName = raw_input('Enter your GMail username: ')
password = getpass.getpass('Enter your password: ')

imapSession = imaplib.IMAP4_SSL('imap.gmail.com')
typ, accountDetails = imapSession.login(userName, passwd)

print typ
print accountDetails
if typ != 'OK':
    print 'Not able to sign in!'
    raise

imapSession.select('[Gmail]/All Mail')
typ, data = imapSession.search(None, 'ALL')
if typ != 'OK':
    print 'Error searching Inbox.'
    raise

# Iterating over all emails
for msgId in data[0].split():
    typ, messageParts = imapSession.fetch(msgId, '(RFC822)')
    if typ != 'OK':
        print 'Error fetching mail.'
        raise
    emailBody = messageParts[0][1]
    mail = email.message_from_string(emailBody)
    for part in mail.walk():
        if part.get_content_maintype() == 'multipart':
            # print part.as_string()
            continue
        if part.get('Content-Disposition') is None:
            # print part.as_string()
            continue
        fileName = part.get_filename()
        if fileName is not None:
            fileName = ''.join(x for x in fileName.splitlines())
        if bool(fileName):
            filePath = os.path.join(detach_dir, 'attachments', 'temp.attachment')
            if os.path.isfile(filePath):
                os.remove(filePath)
            if not os.path.isfile(filePath):
                # print 'Processing: {file}'.format(file=fileName)
                fp = open(filePath, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()
                x_hash = get_hash(filePath)

                if x_hash in fileNameList_dict[fileName]:
                    print '\tSkipping duplicate file: {file}'.format(file=fileName)

                else:
                    fileNameCounter[fileName] += 1
                    fileStr, fileExtension = os.path.splitext(fileName)
                    if fileNameCounter[fileName] > 1:
                        new_fileName = '{file}({suffix}){ext}'.format(suffix=fileNameCounter[fileName],
                                                                      file=fileStr, ext=fileExtension)
                    else:
                        new_fileName = fileName
                    fileNameList_dict[fileName].append(x_hash)
                    hash_path = os.path.join(detach_dir, 'attachments', new_fileName)
                    if not os.path.isfile(hash_path):
                        if new_fileName == fileName:
                            print '\tStoring: {file}'.format(file=fileName)
                        else:
                            print('\tRenaming and storing: {file} to {new_file}'.format(file=fileName,
                                                                                        new_file=new_fileName))
                        try:
                            os.rename(filePath, hash_path)
                        except:
                            print 'Could not store: {file} it has a shitty file name or path under {op_sys}.'.format(
                                file=hash_path, op_sys=platform.system())
                    elif os.path.isfile(hash_path):
                        print '\tExists in destination: {file}'.format(file=new_fileName)
                if os.path.isfile(filePath):
                    os.remove(filePath)

imapSession.close()
imapSession.logout()
