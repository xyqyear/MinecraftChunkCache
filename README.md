usable, but lack of documentation (lazy)

TODO list:

- [x] simple port forward
- [x] separate packets
- [x] separate chunk_data packet
- [x] separate chunk segment data
- [x] compress packet using the minecraft way
- [x] setup database
- [x] store chunk section hash (server side)
- [x] finish custom chunk data protocol
- [x] store chunk section data (client side)
- [x] send back ack packet (if server received ack, write hash into the database)
- [x] add support for multiple clients (client send client ID to server when establish connection. threading.local())
- [x] add support for multiple minecraft clients under a single proxy client
- [x] **usable**
- [ ] delete session from session list when it's not active anymore (to save memory and release file pointer, maybe no need for this)
- [ ] finish light data part
- [ ] finish biomes data part
- [ ] let server know when local file changes (usually user deletion)
- [ ] or preserve chunk packet in the server. when received ack packet, delete it from preservation table
- [ ] force delete cached chunk when found a block update packet was sent within that chunk (maybe have some performance issues)
- [ ] **almost finished**
- [ ] multiple version compatibility
- [ ] **finished**
- [ ] (optional) find a way that wouldn't cause hash collision

Protocol:

0xA0: 

    chunk data ack packet
    data:
        chunk_x: varint
        chunk_z: varint
        section_y: array of sighed char (fmt='B')

