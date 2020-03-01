import struct


from quarry.types.buffer import BufferUnderrun
from quarry.types.buffer.v1_14 import Buffer1_14


class CustomOriginalBuffer114(Buffer1_14):
    def unpack_chunk_section_palette_bytes(self, value_width):
        """
        origin: quarry.types.buffer.v1_13.Buffer1_13
        if value_width > 8:
            return []
        else:
            return [self.unpack_varint() for _ in xrange(self.unpack_varint())]
        """
        palette_bytes = b''
        if value_width > 8:
            return palette_bytes
        else:
            palette_num = self.unpack_varint()
            for _ in range(palette_num):
                palette_bytes += self.unpack_varint_bytes()

            palette_num_bytes = self.pack_varint(palette_num)
            return palette_num_bytes + palette_bytes

    def unpack_chunk_section_array_bytes(self):
        long_num = self.unpack_varint()
        section_array_bytes = self.read(long_num * 8)
        return self.pack_varint(long_num) + section_array_bytes

    def unpack_varint_bytes(self):
        """
        # origin: quarry.types.buffer.v1_7.Buffer1_7
        """

        varint_bytes = b''
        for _ in range(10):
            b = self.read(1)
            varint_bytes += b
            u_char = struct.unpack("B", b)[0]
            if not u_char & 0x80:
                break
        return varint_bytes

    def unpack_chunk_section(self, overworld=True):
        """
        Unpacks a chunk section. Returns bytes.
        origin: quarry.types.buffer.v1_9.Buffer1_9
        """

        non_air_bytes = self.read(2)
        value_width_bytes = self.read(1)
        value_width = struct.unpack('B', value_width_bytes)[0]
        palette = self.unpack_chunk_section_palette_bytes(value_width)
        array = self.unpack_chunk_section_array_bytes()

        return non_air_bytes + value_width_bytes + palette + array


class CustomBaseBuffer:
    """
    origin: quarry.types.buffer.v1_7.Buffer1_7
    """
    buff = b""
    pos = 0

    def __init__(self, data: bytes = b''):
        if data:
            self.buff = data

    def add(self, data: bytes):
        """
        Add some bytes to the end of the buffer.
        """

        self.buff += data

    def save(self):
        """
        Saves the buffer contents.
        """

        self.buff = self.buff[self.pos:]
        self.pos = 0

    def restore(self):
        """
        Restores the buffer contents to its state when :meth:`save` was last
        called.
        """

        self.pos = 0

    def read(self, length: int = 0):
        """
        Read *length* bytes from the beginning of the buffer, or all bytes if
        *length* is ``None``
        """

        if not length:
            data = self.buff[self.pos:]
            self.pos = len(self.buff)
        else:
            if self.pos + length > len(self.buff):
                raise BufferUnderrun()

            data = self.buff[self.pos:self.pos+length]
            self.pos += length

        return data

    def unpack(self, fmt: str):
        """
        Unpack a struct. The format accepted is the same as for
        ``struct.unpack()``.
        """
        fmt = ">" + fmt
        data = self.read(struct.calcsize(fmt))
        fields = struct.unpack(fmt, data)
        if len(fields) == 1:
            fields = fields[0]
        return fields

    def unpack_varint(self, max_bits: int = 32):
        """
        Unpacks a varint.
        """

        number = 0
        for i in range(10):
            b = self.unpack("B")
            number |= (b & 0x7F) << 7*i
            if not b & 0x80:
                break

        if number & (1 << 31):
            number -= 1 << 32

        number_min = -1 << (max_bits - 1)
        number_max = +1 << (max_bits - 1)
        if not (number_min <= number < number_max):
            raise ValueError("varint does not fit in range: %d <= %d < %d"
                             % (number_min, number, number_max))

        return number

    def unpack_packet(self) -> bytes:
        """
        Unpacks a packet frame. This method handles length-prefixing and
        compression.
        """
        return self.read(self.unpack_varint())
