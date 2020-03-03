import struct
import zstd
import zlib

from quarry.types.buffer import BufferUnderrun
from quarry.types.buffer.v1_14 import Buffer1_14
from quarry.types.buffer.v1_7 import Buffer1_7


class CustomCompressBuffer17(Buffer1_7):
    """
    using custom compression method
    """
    @classmethod
    def pack_packet_custom(cls, data, compression_threshold, compression_method):
        """
        Unpacks a packet frame. This method handles length-prefixing and
        compression.
        """

        if compression_method == 'zstd':
            comp_lib = zstd
        else:
            comp_lib = zlib

        if compression_threshold >= 0:
            # Compress data and prepend uncompressed data length
            if len(data) >= compression_threshold:
                data = cls.pack_varint(len(data)) + comp_lib.compress(data)
            else:
                data = cls.pack_varint(0) + data

        # Prepend packet length
        return cls.pack_varint(len(data), max_bits=32) + data

    def unpack_packet_custom(self, compression_threshold, compression_method):
        """
        Unpacks a packet frame. This method handles length-prefixing and
        compression.
        """
        if compression_method == 'zstd':
            comp_lib = zstd
        else:
            comp_lib = zlib

        cls = self.__class__
        body = self.read(self.unpack_varint(max_bits=32))
        buff = cls(body)
        if compression_threshold >= 0:
            uncompressed_length = buff.unpack_varint()
            if uncompressed_length > 0:
                body = comp_lib.decompress(buff.read())
                buff = cls(body)

        return buff


class CustomVanillaBuffer114(Buffer1_14):
    def unpack_chunk_section_palette_bytes(self, value_width):
        """
        origin: quarry.types.buffer.v1_13.Buffer1_13
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


class BaseBuffer:
    """
    origin: quarry.types.buffer.v1_7.Buffer1_7
    """
    buff = b''
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

    def read(self, length: int = 0) -> bytes:
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

    @classmethod
    def pack(cls, fmt, *fields):
        """
        Pack *fields* into a struct. The format accepted is the same as for
        ``struct.pack()``.
        """

        return struct.pack(">"+fmt, *fields)

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


class VarIntBuffer(BaseBuffer):
    @classmethod
    def pack_varint(cls, number):
        """
        Packs a varint.
        """
        if number < 0:
            number += 1 << 32

        out = b""
        for i in range(10):
            b = number & 0x7F
            number >>= 7
            out += cls.pack("B", b | (0x80 if number > 0 else 0))
            if number == 0:
                break
        return out

    def unpack_varint(self):
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

        return number


class BasicPacketBuffer(VarIntBuffer):
    def recv_packet(self) -> bytes:
        """
        Unpacks a packet frame. This method handles length-prefixing and
        compression.
        """
        packet_len = self.unpack_varint()
        packet_len_bytes = Buffer1_14.pack_varint(packet_len)
        return packet_len_bytes + self.read(packet_len)
