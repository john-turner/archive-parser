import argparse
import os
import tarfile
import re

HEADER_PATTERNS = {
    "date": re.compile("Date:\s*(.*)", flags=re.IGNORECASE),
    "continuation": re.compile("^\s+(.*)")
}


class InvalidArchiveFile(Exception):
    pass


def parse_header_iterator(archive, archive_file):
    extracted_file = archive.extractfile(archive_file)
    for line in extracted_file:
        if line == b"\n":
            break
        yield line


def parse_line_for_header(line):
    for header, pattern in HEADER_PATTERNS.iteritems():
        match = pattern.match(line)
        if match:
            return header, match

    return None, None


def parse_extracted_file(archive, archive_file):
    parsed_headers = {}
    last_parsed_header = ""
    for line in parse_header_iterator(archive, archive_file):
        header, match = parse_line_for_header(line)
        if match:
            if header == "continuation":
                parsed_headers[last_parsed_header] += match.group(1)
            else:
                parsed_headers[header] = match.group(1)
                last_parsed_header = header

    return parsed_headers


def parse_archive(archive_file_path):
    if not tarfile.is_tarfile(archive_file_path):
        raise InvalidArchiveFile("File is not a tar archive file.")

    results = []

    with tarfile.open(archive_file_path) as archive:
        for archive_file in archive.getmembers():
            is_file = archive_file.isfile()
            if is_file:
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

    parse_archive(args.archive)

if __name__ == "__main__":
    main()
