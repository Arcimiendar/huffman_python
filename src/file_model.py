import struct

from typing import BinaryIO
from .bit_stream import BitWriteStream, BitReadStream


class FileCell:
    @staticmethod
    def read_from_bytes(byte_str: bytes) -> tuple[bytes, bytes]:
        length, = struct.unpack('>I', byte_str[0:4])  # 4 byte unsigned integer
        rest = byte_str[length + 4:]
        target = byte_str[4:length + 4]
        return target, rest

    @staticmethod
    def make_cell(byte_str: bytes) -> bytes:
        str_len = len(byte_str)
        byte_len = str_len.to_bytes(4, 'big', signed=False)
        cell = byte_len + byte_str
        return cell


class FileModel:
    def __init__(self):
        self.tail: None | bytes = None
        self.content: None | bytes = None
        self.conversation_table: None | dict[str, str] = None
        self.content_length: None | int = None

    @classmethod
    def write_to_file(
        cls, io_like: BinaryIO, tail: bytes, content: bytes, conversation_table: dict[str, str], content_length: int
    ):
        model = FileModel()
        model.tail = tail
        model.content = content
        model.conversation_table = conversation_table
        model.content_length = content_length
        model.write_to(io_like)

    @classmethod
    def read_from_file(cls, io_like: BinaryIO) -> tuple[dict[str, str], bytes, bytes, int]:
        content = io_like.read()
        model = FileModel()
        return model.read_from(content)

    def read_from(self, content: bytes) -> tuple[dict[str, str], bytes, bytes, int]:
        conversation_serialized, rest = FileCell.read_from_bytes(content)
        self.conversation_table = self.deserialize_conversation_table(conversation_serialized)
        self.content_length, = struct.unpack('>I', rest[:4])
        rest = rest[4:]
        self.content, rest = FileCell.read_from_bytes(rest)
        tail_serialized, _ = FileCell.read_from_bytes(rest)
        tail_length, = struct.unpack('>I', tail_serialized[:4])
        self.tail = BitReadStream(tail_serialized[4:]).read(tail_length)

        return self.conversation_table, self.content, self.tail, self.content_length

    def deserialize_conversation_table(self, serialized: bytes) -> dict[str, str]:
        conversation_table = {}
        while len(serialized) > 0:
            key_bytes, serialized = FileCell.read_from_bytes(serialized)
            value_bytes, serialized = FileCell.read_from_bytes(serialized)

            key_len, = struct.unpack('>I', key_bytes[:4])
            key_bytes = key_bytes[4:]

            value_len, = struct.unpack('>I', value_bytes[:4])
            value_bytes = value_bytes[4:]

            conversation_table[BitReadStream(key_bytes).read(key_len)] = BitReadStream(value_bytes).read(value_len)
        return conversation_table

    def write_to(self, io_like: BinaryIO):
        tail_stream = BitWriteStream()
        tail_stream.write(self.tail)
        tail_cell = FileCell.make_cell(len(self.tail).to_bytes(4, 'big') + tail_stream.get_bytes())

        content_cell = FileCell.make_cell(self.content)
        conversation_cell = FileCell.make_cell(self.serialize_conversation_table())

        content_length = self.content_length.to_bytes(4, 'big')

        io_like.write(conversation_cell)
        io_like.write(content_length)
        io_like.write(content_cell)
        io_like.write(tail_cell)

    def serialize_conversation_table(self):
        accumulator = b''
        for key, value in self.conversation_table.items():
            key_stream = BitWriteStream()
            key_stream.write(key)
            accumulator += FileCell.make_cell(len(key).to_bytes(4, 'big') + key_stream.get_bytes())
            value_stream = BitWriteStream()
            value_stream.write(value)
            accumulator += FileCell.make_cell(len(value).to_bytes(4, 'big') + value_stream.get_bytes())
        return accumulator
