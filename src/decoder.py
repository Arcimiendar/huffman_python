from itertools import count
from typing import BinaryIO
from .file_model import FileModel
from .bit_stream import BitReadStream, BitWriteStream


def get_possible_options(possible_word: str, unzip_table: dict[str, str]) -> list[str]:
    return [
        unzip_table[key] for key in unzip_table if key.startswith(possible_word)
    ]


def unzip_content(content: bytes, unzip_table: dict[str, str], tail: bytes, content_length: int) -> bytes:
    w_stream = BitWriteStream()
    r_stream = BitReadStream(content)

    i = 0
    while i < content_length:
        possible_word = ''
        possible_options = []
        while len(possible_options) != 1:
            possible_word += r_stream.read(1)
            i += 1
            possible_options = get_possible_options(possible_word, unzip_table)

        w_stream.write(possible_options[0])
    w_stream.write(tail)
    return w_stream.get_bytes()


def decode(source: BinaryIO, destination: BinaryIO):
    conversation_table, content, tail, content_length = FileModel.read_from_file(source)
    unzip_table = {
        value: key for key, value in conversation_table.items()
    }
    raw_content = unzip_content(content, unzip_table, tail, content_length)
    destination.write(raw_content)
