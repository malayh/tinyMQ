## tinyMQ
It is a transient inmemory messaging queue for systems where you don't have enought resouces to use Kafka or RabbitMQ. 

It uses ProtocolBuffers underneath to pass messages over persistent websockets. The API is simple and you can install and setup the server in less than 3 minutes.

## Install
- clone this repo
- Run `python setup.py install` with your virtualenv activated
- Start the server with `tmqserver --startserver --host localhost --port 9800`
- Stop the server with `tmqserver --stopserver`

## Usage
The client API works using `tinyMQ.Producer` and `tinyMQ.Consumer` classes

Following is a simple `Producer` that writes "Hi" to a `topic` named *test-topic*

```python
from tinyMQ import Producer
import asyncio


async def producer(host: str, port: int, topic: str): 
    producer = Producer(host, port,topic)
    await producer.init_conn()
    for i in range(100):
        await producer.send("Hi", i)
        await asyncio.sleep(1)

async def main():
    await producer("localhost",9800,"test-topic")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
```

Following is a exmple of a `Consumer` consuming from `topic` *test-topic*

```python
import asyncio
from tinyMQ import Consumer

async def consumer(host:str, port:int, topic: str):
    consumer = Consumer(host, port, topic)
    await consumer.init_conn()

    # if there is nothing to consume, sleep for 1 sec
    while True:
        msg = await consumer.poll()
        if not msg:
            await asyncio.sleep(1)
            continue

        print(f"Msg id: {msg[0]} Msg:{msg[1]}")

async def main():
    await consumer("localhost",9800,"test-topic")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
```

## API
All the messages are stores inside `topics`. A `topic` is created whenever a Consumer or Producers is connected to tinyMQ with a topic name that does not exist yet.

### Client API
#### `tinyMQ.Producer`
This class is to be used to write messgess to the queue.
- `__init__(host: str, port: int , topic: str)`
    - Initialize a connection as a Producer to a tinyMQ instance running on `host` and on `port`. It will write to a topic named `topic` which will be created if doenot exist already
- `await init_conn()`
    - This has to be called to make a connection becomes usable.
    - Throws `ConnectionRefusedError` if unable to connect
- `await send(message:str, id:int)`
    - Writes `message` to the topic connected to with id `id`
    - Uniqueness of the messages send and recieved can be controlled by the users using the `id` that is sent with the message
    - Throws `tinyMQ.DeadConnectionUsed` if connection is closed by the server or if `init_conn` is not called
#### `tinyMQ.Consumer`
This class is used to consumed data from a topic. Only one consumer can consume from a given topic.
- `__init__(host: str, port: int , topic: str)`
    - Initialize a connection as a Consumer to a tinyMQ instance running on `host` and on `port`. It will read from a topic named `topic` which will be created if doenot exist already
- `await init_conn()`
    - This has to be called to make a connection becomes usable.
    - Throws `ConnectionRefusedError` if unable to connect
    - Throws `tinyMQ.InitFailed` if the mentiond topic is already being consumed by some other consumer

- `await poll()`
    - Checks if there is any message to be consumed.
    - Returns `None` if topic is empty. Otherwise returns tuple `(id,message`)
    - Throws `tinyMQ.DeadConnectionUsed` if connection is closed by the server
