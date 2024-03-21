# for each file extension in attachments create a subdolder in the main directory for that extenstion
# move each file into the corresponding subfolder

from distutils import extension
import os


def build_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def BySize(size):

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

    return subfolder


def ByType(extension):
    ext = extension.lstrip(".").lower()
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
            "html",
        ],
    }


    for key, value in general_types.items():
        if ext in value:
            return key
        elif ext is None:
            return "other"
    return "other"


def ByDate(save_folder, date):
    # sample date format: 'Fri, 1 Jul 2011 16:21:50 -0500'
    day, month, year = date.split(" ")[1:4]
    if not year.isnumeric():
        day, month, year = date.split(" ")[0:3]
    if len(year) == 2:
        year = "20" + year
    if len(year) == 1 and not day.isnumeric():
        day, month, year = date.split(" ")[2:5]
    day = day.lstrip("0")
    build_directory(save_folder + "\\" + year + "\\" + month + "\\" + day)
    new_save_folder = save_folder + "\\" + year + "\\" + month + "\\" + day
    return new_save_folder


def BySenderEmail(save_folder, sender):
    domain = (sender.split("@")[-1]).replace(">","") if "@" in sender else None
    if "<" in sender:
        sender = sender.split("<")[1].split(">")[0]
    new_save_folder = save_folder + "\\" + domain + "\\" + sender
    build_directory(new_save_folder)
    return new_save_folder


def ByDomain(save_folder, domain):
    sender_domain = "unknown_sender"
    sender_domain = domain if domain is not None else "unknown_sender_domain"
    build_directory(save_folder + "\\" + sender_domain)
    new_save_folder = save_folder + "\\" + sender_domain
    return new_save_folder



if __name__ == "__main__":
    pass
