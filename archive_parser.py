import argparse
import os
import tarfile
import re

HEADER_PATTERNS = {
    "date": re.compile("Date: (.*)")
}


class InvalidArchiveFile(Exception):
    pass


def extract_header_iterator(archive, archive_file):
    extracted_file = archive.extractfile(archive_file)
    for line in extracted_file:
        if line == b"\n":
            break
        yield line


def parse_extracted_file(archive, archive_file):
    is_file = archive_file.isfile()
    if is_file:
        parsed_headers = {}
        for line in extract_header_iterator(archive, archive_file):
            date = HEADER_PATTERNS["date"].match(line)
            if date:
                parsed_headers["date"] = date.group(1)

        return parsed_headers


def archive_extractor(archive_file_path):
    if not tarfile.is_tarfile(archive_file_path):
        raise InvalidArchiveFile("File is not a tar archive file.")

    results = []

    with tarfile.open(archive_file_path) as archive:
        for archive_file in archive.getmembers():
            results.append(parse_extracted_file(archive, archive_file))

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Parse an archive of MSG files for date sent, the sender, "
        "and the subject of each message")
    parser.add_argument(
        "archive", type=str, help="the path to the archive file")

    args = parser.parse_args()

    if not os.path.isfile(args.archive):
        raise InvalidArchiveFile("{} is not a valid file path.".format(args.archive))

    archive_extractor(args.archive)

if __name__ == "__main__":
    main()
