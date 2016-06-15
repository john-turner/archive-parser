import argparse
import os


class InvalidArchiveFile(Exception):
    pass


def main():
    parser = argparse.ArgumentParser(
        description="Parse an archive of MSG files for date sent, the sender, "
        "and the subject of each message")
    parser.add_argument(
        "archive", type=str, help="the path to the archive file")

    args = parser.parse_args()

    if not os.path.isfile(args.archive):
        raise InvalidArchiveFile("{} is not a valid file path.".format(args.archive))

if __name__ == "__main__":
    main()
