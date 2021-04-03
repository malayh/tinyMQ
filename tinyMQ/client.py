
import websockets
import asyncio
import logging
from typing import Tuple
from concurrent.futures import TimeoutError as ConnectionTimeoutError

from .constants import Status, Roles
from .message_pb2 import *
from .execeptions import *

class Producer:
    def __init__(self,host:str, port:int,topic: int, timeout:int=2):
        """
        NOT USED NOW: timeout is the number of "seconds" to wait before raising a TimeoutError if 'Ack' is not recieved for a send
        """
        self.topic : str = topic
        self.host : str = host
        self.port : str = port
        self.ws : WebSocketClientProtocol = None
        self.log = logging.getLogger("tMQ-Producer")
        self.timeout = timeout

    async def init_conn(self):
        # Throws ConnectionRefusedError if unable to connect
        
        self.ws = await websockets.connect(f"ws://{self.host}:{self.port}/{self.topic}")
        init = ConnInit()
        init.role = Roles.PRODUCER
        init.topic = self.topic
        await self.ws.send(init.SerializeToString())
        
        status = ConnStatus()
        status.ParseFromString(await self.ws.recv())
        
        if status.status != Status.CON_OPEN:
            raise InitFailed()

        self.log.info(f"Topic:{self.topic} : Producer opened")


    async def send(self,message:str,id:int) -> None:
        """
        Raises WrongAck if Ack.id != id sent
        Raises DeadConnectionUsed if self.ws = None
        """
        if not self.ws:
            raise DeadConnectionUsed()

        _pb = ContentWrite(id=id,topic=self.topic,body=bytes(message,encoding='utf-8'))

        try:
            await self.ws.send(_pb.SerializeToString())

            ack = Ack()
            ack.ParseFromString(await self.ws.recv())
            if ack.id != id:
                raise WrongAck
        except websockets.ConnectionClosedError:
            self.ws = None
            raise DeadConnectionUsed()


class Consumer:
    def __init__(self,host:str, port:int,topic: int, timeout:int=2):
        """
        NOT USED NOW: timeout is the number of "seconds" to wait before raising a TimeoutError if 'Ack' is not recieved for a send
        """
        self.topic : str = topic
        self.host : str = host
        self.port : str = port
        self.ws : WebSocketClientProtocol = None
        self.log = logging.getLogger("tMQ-Consumer")
        self.timeout = timeout

        self._poll = Poll(topic=self.topic).SerializeToString()

    async def init_conn(self):
        # Throws ConnectionRefusedError if unable to connect
        
        self.ws = await websockets.connect(f"ws://{self.host}:{self.port}/{self.topic}")
        init = ConnInit()
        init.role = Roles.CONSUMER
        init.topic = self.topic
        await self.ws.send(init.SerializeToString())
        
        status = ConnStatus()
        status.ParseFromString(await self.ws.recv())
        
        if status.status != Status.CON_OPEN:
            raise InitFailed()

        self.log.info(f"Topic:{self.topic} : Consumer opened")

    async def poll(self) -> (int,str):
        """
        Return Tuple(id,message) or None
        """
        if not self.ws:
            raise DeadConnectionUsed()

        try:
            await self.ws.send(self._poll)
            msg = ContentRead()
            msg.ParseFromString(await self.ws.recv())

            if msg.status == Status.Q_EMPTY:
                return None

            # await ws.send(Ack(id=msg.id).SerializeToString())
            return msg.id, msg.body.decode('utf-8')
        
        except websockets.ConnectionClosedError:
            self.ws = None
            return None
        except Exception as e:
            self.log.error("Something happend!",exc_info=True)

        return None

        
        


