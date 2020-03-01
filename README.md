NOT FINISHED YET

TODO list:

- [x] simple port forward
- [x] separate packets
- [x] separate chunk_data packet
- [x] separate chunk segment data
- [x] compress packet using the minecraft way
- [x] setup database
- [x] store chunk section hash (server side)
- [ ] finish custom chunk data protocol
- [ ] store chunk section data (client side)
- [ ] finish biomes data part
- [ ] add support for multiple clients (client send client ID to server when establish connection, maybe)
- [ ] **usable**
- [ ] finish light data part
- [ ] acknowledge server when local file changes (usually user deletion)
- [ ] force delete cached chunk when found a block update packet was sent within that chunk (maybe have some performance issues)
- [ ] **almost finished**
- [ ] multiple version compatibility
- [ ] **finished**
- [ ] (optional) find a way that wouldn't cause hash collision