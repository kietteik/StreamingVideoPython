# StreamingVideoPython

## Run Server

```shell
python Server.py <PORT>
python Server.py 5050
```

## Run Client

```shell
python ClientLauncher.py <SERVER_ADDR> <SERVER_PORT> <CLIENT_PORT> <MOVIE_NAME>
python ClientLauncher.py '' 5050 4040 movie.Mjpeg
```

## Maybe needed (change maximum UDP datagram receive [client OS])

```
sudo sysctl -w net.inet.udp.maxdgram=20480
```
