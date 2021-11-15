from typing import BinaryIO
from .bit_stream import BitReadStream, BitWriteStream
from .file_model import FileModel
from collections import defaultdict


class Node:
    def __init__(
        self, *,
        children: list['Node'] | None = None,
        word: str | None = None,
        frequency: int | None = None
    ):
        self.slug = None
        self.parent: Node | None = None
        self.word = word
        self.children = children
        self.frequency = frequency
        if self.children:
            self.frequency = 0
            for child in self.children:
                self.frequency += child.frequency
                child.parent = self

    def flatten(self) -> list['Node']:
        if self.word is not None:
            return [self]

        flatten_array = []
        for child in self.children:
            flatten_array.extend(child.flatten())
        return flatten_array

    def get_code(self) -> str:
        if not self.slug:
            raise ValueError('build a tree first or use on subnodes!')
        initial_slug = self.slug
        parent = self.parent
        if parent is None:
            parent = self
        while parent.parent is not None:
            initial_slug += parent.slug
            parent = parent.parent
        return initial_slug[::-1]


def build_tree(nodes: list[Node]) -> Node:
    if len(nodes) == 1:
        nodes[0].slug = '0'
    while len(nodes) > 1:
        nodes.sort(key=lambda node: -node.frequency)
        least_frequent_1 = nodes.pop()
        least_frequent_2 = nodes.pop()
        least_frequent_1.slug = '0'
        least_frequent_2.slug = '1'
        nodes.append(Node(
            children=[least_frequent_1, least_frequent_2]
        ))
    return nodes[0]


def build_conversation(frequencies: dict[str, int]):
    nodes = list(map(lambda pair: Node(word=pair[0], frequency=pair[1]), frequencies.items()))
    root_node = build_tree(nodes)
    return {
        node.word: node.get_code() for node in root_node.flatten()
    }


def get_frequencies_and_tail(source_content: bytes, wordbits: int) -> tuple[dict[str, int], str]:
    frequencies = defaultdict(int)
    source_stream = BitReadStream(source_content)
    while len(word := source_stream.read(wordbits)) == wordbits:
        frequencies[word] += 1
    return frequencies, word  # last word is tail


def compress_content(content: bytes, wordbits: int, conversation_table: dict[str, str]) -> tuple[bytes, int]:
    accumulator_stram = BitWriteStream()
    source_stream = BitReadStream(content)
    content_length = 0
    while len(word := source_stream.read(wordbits)) == wordbits:
        content_length += len(conversation_table[word])
        accumulator_stram.write(conversation_table[word])
    return accumulator_stram.get_bytes(), content_length


def code(source: BinaryIO, destination: BinaryIO, wordbits: int):
    source_content = source.read()
    if len(source_content) == 0:
        return
    frequencies, tail = get_frequencies_and_tail(source_content, wordbits)
    print(str(frequencies)[:100_000])
    conversation_table = build_conversation(frequencies)
    print(str(conversation_table)[:100_000])
    compressed_content, content_length = compress_content(source_content, wordbits, conversation_table)
    print(compressed_content[:1000])
    FileModel.write_to_file(destination, tail, compressed_content, conversation_table, content_length)
