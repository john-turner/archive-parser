import argparse
import os
import tarfile
import re
import pprint
import json

HEADER_PATTERNS = {
    "date": re.compile(r"Date:\s*(.*)", flags=re.IGNORECASE),
    "continuation": re.compile(r"^\s+(.*)"),
    "from": re.compile(r"from:\s*(.*)", flags=re.IGNORECASE),
    "subject": re.compile(r"subject:\s*(.*)", flags=re.IGNORECASE),
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
    for header, pattern in HEADER_PATTERNS.items():
        match = pattern.match(line.decode())
        if match:
            return header, match

    return None, None


def parse_extracted_file(archive, archive_file):
    parsed_headers = {}
    last_parsed_header = None
    for line in parse_header_iterator(archive, archive_file):
        header, match = parse_line_for_header(line)
        if match:
            if header == "continuation" and last_parsed_header:
                parsed_headers[last_parsed_header] += match.group(1)
            elif header != "continuation":
                parsed_headers[header] = match.group(1)
                last_parsed_header = header
        else:
            last_parsed_header = None

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


def save_parsing_results(output_file_path, results):
    result = {"results": results}
    with open(output_file_path, 'w') as output_file:
        json.dump(result, output_file, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Parse an archive of MSG files for date sent, the sender, "
        "and the subject of each message")
    parser.add_argument(
        "archive", type=str, help="the path to the archive file")
    parser.add_argument(
        "output_file_path", type=str, help="the path to write the results")

    args = parser.parse_args()

    if not os.path.isfile(args.archive):
        raise InvalidArchiveFile("{} is not a valid file path.".format(args.archive))

    result = parse_archive(args.archive)

    save_parsing_results(args.output_file_path, result)

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(result)

if __name__ == "__main__":
    main()
