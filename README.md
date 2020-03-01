NOT FINISHED YET

TODO list:

- [x] simple port forward
- [x] separate packets
- [x] separate chunk_data packet
- [x] separate chunk segment data
- [x] compress packet using the minecraft way
- [ ] assign each segment data a coordinate and store data in a simple form (maybe single json file)
- [ ] hash chunk segment data and design protocol
- [ ] finished custom chunk_data protocol implementation
- [ ] **usable**
- [ ] store chunk segment data compressed
- [ ] store chunk segment data in sqlite or leveldb for better performance
- [ ] force delete cached chunk when found a block update packet was sent within that chunk (maybe have some performance issues)
- [ ] **almost finished**
- [ ] multiple version compatibility
- [ ] **finished**
- [ ] (optional) find a way that wouldn't cause hash collision