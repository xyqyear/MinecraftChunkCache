NOT FINISHED YET

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
- [ ] send back ack packet (if server not receive ack, rollback hash in the database)
- [ ] finish biomes data part
- [ ] add support for multiple clients (client send client ID to server when establish connection, maybe)
- [ ] **usable**
- [ ] finish light data part
- [ ] let server know when local file changes (usually user deletion)
- [ ]     or preserve chunk packet in the server. when received ack packet, delete it from preservation table
- [ ] force delete cached chunk when found a block update packet was sent within that chunk (maybe have some performance issues)
- [ ] **almost finished**
- [ ] multiple version compatibility
- [ ] **finished**
- [ ] (optional) find a way that wouldn't cause hash collision