# Gmail Attachment Manager

## Description

This script connects to a Gmail account via IMAP, lets you select a mailbox folder, identifies all emails containing attachments, and downloads those attachments. Users can specify a directory to save the attachments and choose from various sorting methods, such as by file extension, size, type, sender, or date. The script supports session recovery to handle interruptions and avoid redownloading previously processed emails, with a persistent manifest file to prevent overwriting attachments across sessions.

## Features

- **IMAP Connection**: Connects securely to Gmail via IMAP to access emails.
- **Folder Selection**: Lists all available Gmail folders and lets you choose which one to process.
- **Attachment Download**: Downloads all attachments found in the selected folder.
- **Unnamed Attachment Handling**: Automatically generates a filename for attachments that have none.
- **Sorting Methods**: Attachments can be sorted by:
  - File Extension
  - File Size
  - File MIME Type
  - Date Year -> Month -> Day
  - Sender Domain -> sender
- **Session Recovery**: Supports resuming the download process to avoid redownloading attachments.
- **Manifest Persistence**: Saves a `file_manifest.json` file to track downloaded files across sessions, preventing overwrites on resume.
- **Windows Long Path Support**: Automatically applies the `\\?\` extended-length path prefix for file paths exceeding 260 characters on Windows.
- **Environment Variable Support**: Optionally set your password via the `EMAIL_PASSWORD` environment variable.

## Requirements

- **Python 3.6+**
- **Required Libraries**:
  - `email` (Standard Library)
  - `hashlib` (Standard Library)
  - `getpass` (Standard Library)
  - `imaplib` (Standard Library)
  - `os` (Standard Library)
  - `re` (Standard Library)
  - `json` (Standard Library)
  - `logging` (Standard Library)
  - `collections` (Standard Library)
  - `pathlib` (Standard Library)
  - `enum` (Standard Library)
  - `organize` (Included Custom Module)

## Additional requirements

- **Make sure you have IMAP enabled in your GMail settings.**
   - https://support.google.com/mail/troubleshooter/1668960?hl=en
    
- **If you are using 2 step verification you may need an APP Password.**
    - https://support.google.com/accounts/answer/185833
    - https://myaccount.google.com/apppasswords
    
- **Reference information for GMail IMAP extension can be found here.**
    - https://developers.google.com/gmail/imap_extensions

## Installation

1. **Clone the Repository**

   ```sh
   git clone https://github.com/mjseeley/Gmail-Attachment-Downloader.git
   cd Gmail-Attachment-Downloader
   ```

2. **Verify Python Version**

   Make sure you have Python 3.6 or later installed:

   ```sh
   python --version
   ```

## Usage

1. **Run the Script**

   ```sh
   python gmail_downer.py
   ```

2. **User Prompts**

   - The script will prompt for your Gmail credentials (or use the `EMAIL_PASSWORD` environment variable).
   - You will be shown a numbered list of available Gmail folders and asked to select one.
   - You will be asked to specify a directory where attachments should be saved.
   - You can select a sorting method to organize the attachments.

3. **Resuming Sessions**
   - If interrupted, the script can resume from where it left off by recovering from saved state files (`resume.txt`, `processed_ids.txt`, and `file_manifest.json`).
   - The manifest file tracks file counters and content hashes so attachments are never overwritten when resuming.

### Using Environment Variables

You can set your password as an environment variable to avoid entering it each time:

```sh
# Linux/macOS
export EMAIL_PASSWORD="your-app-password"

# Windows (PowerShell)
$env:EMAIL_PASSWORD="your-app-password"

# Windows (Command Prompt)
set EMAIL_PASSWORD=your-app-password
```

## Sorting Methods Explained

- **Extension**: Organizes files by their extension (e.g., `.pdf`, `.jpg`).
- **Size**: Organizes files by their size into categories:
  - Tiny: < 10 KB
  - Small: 10 KB - 100 KB
  - Medium: 100 KB - 1 MB
  - Large: 1 MB - 10 MB
  - Huge: > 10 MB
- **MIMEType**: Organizes files by general type (e.g., image, text, video).
- **Date**: Organizes files into folders based on the email date (Year/Month/Day).
- **Sender**: Organizes files based on the sender's domain and email address.

## Security Note

The script uses `getpass` to securely input your Gmail password. You will need to set up an [App Password](https://support.google.com/accounts/answer/185833?hl=en) instead of using your regular main Gmail password.

## Troubleshooting

- **Login failed**: Ensure IMAP is enabled in your Gmail settings and you are using an App Password if 2FA is enabled.
- **FileNotFoundError**: Make sure the destination directory path is valid and you have write permissions.
- **Connection errors**: Check your internet connection and firewall settings. Gmail IMAP uses port 993.
- **Empty folders created**: This can occur when sorting by date if attachments were already saved elsewhere and matched by hash (duplicate detection).

## Contributing

Feel free to open issues or submit pull requests with improvements or bug fixes.

## License

This project is licensed under the MIT License.
