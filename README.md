# Gmail Attachment Manager

## Description

This script connects to a Gmail account via IMAP, identifies all emails containing attachments, and downloads those attachments. Users can specify a directory to save the attachments and choose from various sorting methods, such as by file extension, size, type, sender, or date. The script also supports session recovery to handle interruptions and avoid redownloading previously processed emails.

## Features

- **IMAP Connection**: Connects securely to Gmail via IMAP to access emails.
- **Attachment Download**: Downloads all attachments found in the mailbox.
- **Sorting Methods**: Attachments can be sorted by:
  - File Extension
  - File Size
  - File MIME Type
  - Date Year -> Month -> Day
  - Sender Domain -> sender
- **Session Recovery**: Supports resuming the download process to avoid redownloading attachments.

## Requirements

- **Python 3.6+**
- **Required Libraries**:
  - `email` (Standard Library)
  - `hashlib` (Standard Library)
  - `getpass` (Standard Library)
  - `imaplib` (Standard Library)
  - `os` (Standard Library)
  - `logging` (Standard Library)
  - `collections` (Standard Library)
  - `pathlib` (Standard Library)
  - `enum` (Standard Library)
  - `organize` (Included Custom Module)

## Installation

Make sure you have Python 3.6 or later installed. You can verify your Python version with:

```sh
python --version
```

## Usage

1. **Clone the Repository**

   ```sh
   git clone <repository-url>
   cd Gmail-Attachment-Downloader
   ```

2. **Run the Script**

   ```sh
   python gmail_downer.py
   ```

3. **User Prompts**

   - The script will prompt for your Gmail credentials.
   - You will be asked to specify a directory where attachments should be saved.
   - You can select a sorting method to organize the attachments.

4. **Resuming Sessions**
   - If interrupted, the script can resume from where it left off by recovering from saved state files (`resume.txt` and `processed_ids.txt`).

## Sorting Methods Explained

- **Extension**: Organizes files by their extension (e.g., `.pdf`, `.jpg`).
- **Size**: Organizes files by their size (e.g., tiny, small, large).
- **MIMEType**: Organizes files by general type (e.g., image, text, video).
- **Date**: Organizes files into folders based on the email date.
- **Sender**: Organizes files based on the sender's email address.

## Security Note

The script uses `getpass` to securely input your Gmail password. You will need to set up an [App Password](https://support.google.com/accounts/answer/185833?hl=en) instead of using your regular main Gmail password.

## Example

To run the script and download all attachments from your Gmail account, use:

```sh
python gmail_downer.py
```

You'll be prompted to enter your Gmail credentials, specify a directory for saving attachments, and choose a sorting method.

## Contributing

Feel free to open issues or submit pull requests with improvements or bug fixes.

## License

This project is licensed under the MIT License.
