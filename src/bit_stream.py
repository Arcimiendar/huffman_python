from typing import Union


class BitReadStream:
    def __init__(self, some_bytes: bytes = b''):
        self.some_bytes = some_bytes
        self.r_pointer = 0
        self.r_in_byte_pointer = 0

    def read(self, size: int = -1) -> str:
        bits = []
        while size != 0:
            bit = self.get_bit_at(self.r_pointer, self.r_in_byte_pointer)
            if bit is None:
                break
            self.inc_r_pointer()
            bits.append(bit)
            size -= 1
        return ''.join(bits)

    def inc_r_pointer(self):
        self.r_in_byte_pointer += 1
        if self.r_in_byte_pointer == 8:
            self.r_in_byte_pointer = 0
            self.r_pointer += 1

    def get_bit_at(self, pointer, in_byte_pointer) -> str | None:
        try:
            byte = self.some_bytes[pointer]
        except IndexError:
            return None

        bit_raw = byte & (1 << in_byte_pointer)

        return '1' if bit_raw else '0'


class BitWriteStream:
    def __init__(self):
        self.bytes = b''
        self.last_byte = b'\x00'
        self.w_pointer = 0
        self.w_in_byte_pointer = 0

    def inc_w_pointer(self):
        self.w_in_byte_pointer += 1
        if self.w_in_byte_pointer == 8:
            self.w_in_byte_pointer = 0
            self.w_pointer += 1
            self.bytes += self.last_byte
            self.last_byte = b'\x00'

    def write(self, bits: str):
        for bit in bits:
            self.write_to_last_byte(bit, self.w_in_byte_pointer)
            self.inc_w_pointer()

    def write_to_last_byte(self, bit, index):
        last_byte: int = self.last_byte[0]
        mask = 1 << index
        if bit == '0':
            last_byte &= ~mask
        else:
            last_byte |= mask
        self.last_byte = last_byte.to_bytes(1, 'big')

    def get_bytes(self) -> bytes:
        r_value = self.bytes
        if self.w_in_byte_pointer > 0:
            r_value += self.last_byte
        return r_value
