# for each file extension in attachments create a subdolder in the main directory for that extenstion
# move each file into the corresponding subfolder

from distutils import extension
import os
import shutil


def file_move(file, path, new_path):
    if not os.path.exists(new_path):
        os.mkdir(new_path)

    orig_file_path = f"{path}\\{file}"
    new_file_path = f"{new_path}\\{file}"
    # os.replace(orig_file_path, new_file_path)
    shutil.copy(orig_file_path, new_file_path)
    print(f"{file} moved to {new_path}")


def build_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def ByExtension(path):

    files = (
        file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))
    )

    for file in files:
        file_extension = file.split(".")
        if len(file_extension) < 2:
            subfolder = "other"
        else:
            subfolder = file_extension[-1]

        new_path = f"{path}\\{subfolder}"
        file_move(file, path, new_path)


def BySize(path):
    files = (
        file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))
    )

    for file in files:
        size = os.path.getsize(os.path.join(path, file))
        if size < 10240:
            subfolder = "tiny"
        elif size < 102400:
            subfolder = "small"
        elif size < 1024000:
            subfolder = "medium"
        elif size < 10240000:
            subfolder = "large"
        else:
            subfolder = "huge"

        new_path = f"{path}\\{subfolder}"
        file_move(file, path, new_path)


def ByType(path):
    general_types = {
        "application": [
            "exe",
            "bat",
            "msi",
            "com",
            "vbs",
            "vbe",
            "js",
            "jse",
            "wsf",
            "wsh",
            "ws",
        ],
        "audio": ["mp3", "wav", "aiff", "aif", "au", "snd", "mid", "midi"],
        "image": ["gif", "jpg", "jpeg", "png", "bmp", "tif", "tiff", "ico"],
        "text": [
            "txt",
            "doc",
            "docx",
            "odt",
            "pdf",
            "rtf",
            "tex",
            "wks",
            "wps",
            "wpd",
            "ppt",
            "pptx",
            "pps",
            "ppsx",
            "pot",
            "xls",
            "xlsx",
            "csv",
        ],
        "video": [
            "mp4",
            "m4v",
            "mov",
            "wmv",
            "mpg",
            "mpeg",
            "m2v",
            "avi",
            "flv",
            "3gp",
            "3g2",
        ],
        "compressed": [
            "zip",
            "rar",
            "7z",
            "gz",
            "bz2",
            "tar",
            "tgz",
            "z",
            "ace",
            "arj",
            "bz",
            "cab",
            "dmg",
            "iso",
            "lzh",
            "lzma",
            "rar",
            "uue",
            "xz",
            "zoo",
        ],
        "other": [
            "bin",
            "dat",
            "dll",
            "o",
            "obj",
            "so",
            "class",
            "jar",
            "war",
            "ear",
            "psd",
            "psp",
            "xcf",
        ],
    }

    files = (
        file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))
    )
    for file in files:
        file_extension = file.split(".")
        if len(file_extension) < 2:
            ext = None
        else:
            ext = file_extension[-1]

        for key, value in general_types.items():
            if ext in value:
                new_path = f"{path}\\{key}"
                file_move(file, path, new_path)
            elif ext is None:
                new_path = f"{path}\\other"
                file_move(file, path, new_path)


def ByDate(save_folder, msg):
    date_index = next(i for i, (v, *_) in enumerate(msg._headers) if v == "Date")
    day, month, year = msg._headers[date_index][1].split(" ")[1:4]
    if not year.isnumeric():
        day, month, year = msg._headers[date_index][1].split(" ")[0:3]
    if len(year) == 2:
        year = "20" + year
    if len(year) == 1 and not day.isnumeric():
        day, month, year = msg._headers[date_index][1].split(" ")[2:5]
    day = day.lstrip("0")
    build_directory(save_folder + "\\" + year + "\\" + month + "\\" + day)
    new_save_folder = save_folder + "\\" + year + "\\" + month + "\\" + day
    return new_save_folder


def BySenderEmail(save_folder, msg):
    from_index = next(i for i, (v, *_) in enumerate(msg._headers) if v == "From")
    if "<" in msg._headers[from_index][1]:
        sender = msg._headers[from_index][1].split("<")[1].split(">")[0]
    else:
        sender = msg._headers[from_index][1]
    build_directory(save_folder + "\\" + sender)
    new_save_folder = save_folder + "\\" + sender
    return new_save_folder


def ByDomain(save_folder, msg):
    sender_domain = "unknown_sender"
    from_index = next(i for i, (v, *_) in enumerate(msg._headers) if v == "From")
    if "<" in msg._headers[from_index][1]:
        sender = msg._headers[from_index][1].split("<")[1].split(">")[0]
    else:
        sender = msg._headers[from_index][1]
    if "@" in sender:
        sender_domain = sender.split("@")[1]
    else:
        sender_domain = "unknown_sender_domain"
    build_directory(save_folder + "\\" + sender_domain)
    new_save_folder = save_folder + "\\" + sender_domain
    return new_save_folder


def ByExtTest(save_folder, msg):
    # Broken, If multiples files are attached, it will put all files in the same folder with the extension of the first file.
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition") is None:
            continue
        filename = part.get_filename()
        if filename is not None:
            file_extension = filename.split(".")
            if len(file_extension) < 2:
                subfolder = "other"
            else:
                subfolder = file_extension[-1]
            build_directory(save_folder + "\\" + subfolder)
            new_save_folder = save_folder + "\\" + subfolder
            return new_save_folder


if __name__ == "__main__":
    path = f"{os.getcwd()}\\attachments"
    # ByExtension(path)
    # ByDate(path)
    # ByType(path)
    # BySize(path)
    # BySenderDomain(path)
    # BySenderEmail(path)
    pass
