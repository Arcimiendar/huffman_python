import argparse

from src.coder import code
from src.decoder import decode


def main():
    parser = argparse.ArgumentParser(description='hoffman parser')
    parser.add_argument(
        '-w', '--wordbits', default=8, type=int,
        help='number of bits for one word', metavar='N'
    )
    parser.add_argument(
        '-u', '--unzip',
        help='unzip file if provided, zip otherwise',
        action='store_true'
    )
    parser.add_argument(
        'source_file',
        type=argparse.FileType('rb'),
        help='source file'
    )
    parser.add_argument(
        'destination_file',
        nargs='?',
        type=argparse.FileType('wb'),
        help='destination file [add or remove ".d" prefix by default]'
    )
    namespace = parser.parse_args()

    if not namespace.destination_file:
        original_filename = namespace.source_file.name
        if namespace.unzip:
            match original_filename.split('.'):
                case [*rest, 'hf']:
                    namespace.destination_file = open('.'.join(rest), 'wb')
                case _:
                    namespace.destination_file = open(original_filename + '.dec', 'wb')
        else:
            namespace.destination_file = open(original_filename + '.hf', 'wb')

    if namespace.unzip:
        decode(namespace.source_file, namespace.destination_file)
    else:
        code(namespace.source_file, namespace.destination_file, namespace.wordbits)


if __name__ == '__main__':
    main()
