# Minecraft Chunk Cacher

**ONLY COMPATIBLE WITH MINECRAFT 1.15.x**

support for more versions is on the todo list bellow.

I'm a Chinese, so sorry for my horrible English

This is a tool that can help you save your server's bandwidth. It will cache chunks in players' local storage (in "data" folder), and if the chunks (actually the chunk sections) is unchanged when the player logs in the second time, the proxy server will not send that chunk to the player.

If your server have a really small bandwidth, say 1M, players will not able to move shortly (usually 2-5s in 1M bandwidth) when they login or respawn. But if you use this tool, it will only happen when the first time the player joins.

This tool will setup a proxy between your minecraft server and your minecraft client, you need to run server.py on the server and client.py on every player's computer.

Disadvantages (may be eventually fixed): 

  - Server owners need to delete the player's proxy data file on the server (under "data/server/username") once a player deletes their proxy data folder (or they wont be able to receive data in the chunks that they cached, because the servers think they have the data. Maybe a easy fix).
  
  - Players need to copy the proxy's data if they want to play on a different PC or on a different folder.
    
  - ONLY SUPPORT OFFLINE MODE. If the server uses online mode, it will encrypt the data it sent, so that the proxy will not able to change the data. So it is not recommended to use this tool on a relatively large server or you may use plugins like AuthMeReloaded.
    
## How to use

**clone this repository or download zip**
    
    git clone https://github.com/xyqyear/MinecraftChunkCache.git

**install python3** (apparently)

**install requirements**

    pip3 install -r requirements.txt
    # or
    pip install -r requirements.txt

_If leveldb fails to be installed on windows, you can just ignore it, there is a alternative of leveldb installed. But If you really want to install leveldb on windows for better performance, you can use anaconda and run "conda install python-leveldb"._

**change config files**

_client.yaml:_
    
    # the ip that proxy client will listen on, usally no need to change
    listen_ip: 0.0.0.0
    
    # the port that your minecraft client will connect to
    # change to whatever you want or leave it as default
    listen_port: 25001
    
    # the proxy server's ip
    server_ip: 127.0.0.1
    
    # the proxy server's port
    server_port: 25000
    
    # just use default as follows
    compression_threshold: 256
    compression_method: zstd

_server.yaml:_
    
    # the ip that proxy clients will connect (not minecraft client)
    # notice: it says 0.0.0.0, but you need to connect to 127.0.0.1:port in minecraft client. 0.0.0.0 means every ip address the machine has.
    listen_ip: 0.0.0.0
    
    # the port that proxy clients will connect
    listen_port: 25000
    
    # minecraft server's ip. 
    # If the server is running on the same machine that the proxy is running on, then no need to change this
    server_ip: 127.0.0.1
    
    # the port that your minecraft server is on
    server_port: 25565
    
    # just leave them alone
    compression_threshold: 256
    compression_method: zstd

**modify server.properties**
    
    # the reason is being told in the "disadvantages" above.
    online-mode: false

**run**

    # on the server:
    python3 server.py
    # or
    python server.py
    
    # player:
    python3 client.py
    # or
    python client.py
    
Then, you can connect to the server using the ip and port defined in the config file.

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
- [x] add support for multiple clients (threading.local())
- [x] add support for multiple minecraft clients under a single proxy client
- [x] add support for multi dimension
- [x] **usable**
- [ ] let server know when local file changes (usually user deletion)
- [ ] make it possible that letting one player login in multiple locations (server add a number at the end of the username and tell the number to client)
- [ ] finish light data part
- [ ] force delete cached chunk when found a block update packet was sent within that chunk (maybe have some performance issues)
- [ ] build binary file
- [ ] **almost finished**
- [ ] multiple version compatibility
- [ ] **finished**
- [ ] (optional) find a way that wouldn't cause hash collision

Protocol:

0xA0:
    chunk data ack packet
    data:
        dimension: int
        chunk_x: varint
        chunk_z: varint
        section_y: array of sighed char (fmt='B')

0x22:
    chunk data packet
    data:
        \[same content as vanilla packet here\]
        cached_section_mask: int