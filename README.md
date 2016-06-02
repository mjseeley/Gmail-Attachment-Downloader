* patch-10 and up will likely only work with Python 3 due to minor differences in the impalib and email modules.

# Gmail-Attachment-Downloader
Downloads all unique files from Gmail attachments.

``gmail_downer.py`` is hosted at Github <https://github.com/mjseeley/Gmail-Attachment-Downloader/>

# Use:

1. Script needs to be run via console not in an IDE, getpass.getpass() will fail otherwise.
    * <https://docs.python.org/3/library/getpass.html>
2. Make sure you have IMAP enabled in your GMail settings.
    * <https://support.google.com/mail/troubleshooter/1668960?hl=en>
3. If you are using 2 step verification you may need an APP Password.
    * <https://support.google.com/accounts/answer/185833>
4. Reference information for GMail IMAP extension can be found here.
    * <https://developers.google.com/gmail/imap_extensions>
