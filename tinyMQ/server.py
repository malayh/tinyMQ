from queue import SimpleQueue
import asyncio
import websockets
from typing import List, Dict
import logging

from .message_pb2 import *
from .constants import Status, Roles

# TODO: to be read from config
HOST = "localhost"
PORT = 9800

class Connection:
    def __init__(self, ws:websockets.WebSocketClientProtocol, topic: str, role : int) -> None:
        self.ws = ws
        self.topic = topic
        self.role = role

class TinyMQServer:
    def __init__(self):
        self.storage : Dict([str,SimpleQueue]) = dict()
        self.producers : Dict([str,List(Connection)]) = dict()
        self.consumers : Dict([str,Connection]) = dict()
        self.log = logging.getLogger("TinyMQServer")

    async def handle_incomming_connection(self,ws,path):
        topic = path[1:] # Removing the starting "/"
        conn_status = ConnStatus()
        try:
            init = ConnInit()
            init.ParseFromString(await ws.recv())

            conn_status.status = Status.CON_OPEN

            # if there is already someone consuming this topic
            if topic in self.consumers and init.role == Roles.CONSUMER:
                self.log.info(f"Topic:{topic} Refused duplicate consumer")
                conn_status.status = Status.UNCONSUMABLE

            await ws.send(conn_status.SerializeToString())

        except websockets.exceptions.ConnectionClosedError:
            self.log.debug(f" Topic: {topic} : Connection broken while init")
            return
        
        if(conn_status.status != Status.CON_OPEN):
            return

        conn = Connection(ws, topic, init.role)

        # create queue if not present
        if topic not in self.storage:
            self.log.info(f"Topic created: {topic}")
            self.storage[topic] = SimpleQueue()

        if init.role == Roles.PRODUCER:
            if topic in self.producers:
                self.producers[topic].append(conn)
            else:
                self.producers[topic] = [conn]        
        elif init.role == Roles.CONSUMER:
            self.consumers[topic] = conn


        if init.role == Roles.PRODUCER:
            await self.read_forever(conn)
        if init.role == Roles.CONSUMER:
            await self.send_forever(conn)
    
    async def read_forever(self,conn:Connection):
        self.log.info(f"Topic:{conn.topic}: Producer connected")
        self.__log_internals()

        # do the reading here
        while True:
            try:
                msg = ContentWrite()
                msg.ParseFromString(await conn.ws.recv() )
                self.storage[conn.topic].put(msg)
                await conn.ws.send(Ack(id=msg.id).SerializeToString())
            except websockets.ConnectionClosedError:
                self.log.info(f"Topic:{conn.topic} : Connection closed by producer")
                break
            except Exception as e:
                self.log.error("Something happend!",exc_info=True)
                break

        await conn.ws.close()
        self.log.info(f"Topic:{conn.topic}: Producer diconnected")
        self.producers[conn.topic].remove(conn)

    async def send_forever(self,conn:Connection):
        self.log.info(f"Topic:{conn.topic}: Consumer connected")
        

        # do the sending here
        while True:
            try:
                _p = Poll()
                _p.ParseFromString(await conn.ws.recv())
                
                # nothing to send, send Q_EMPTY
                if self.storage[conn.topic].empty():
                    await conn.ws.send(ContentRead(id=0,status=Status.Q_EMPTY,body=bytes(1)).SerializeToString())
                    continue

                _top = self.storage[conn.topic].get()
                await conn.ws.send(ContentRead(id=_top.id,status=Status.SUCCESS,body=_top.body).SerializeToString())

                # Not waiting for ack here. Bcause once SimpleQueue.get() is called, item is removed from front and cannot be put infront again
                # TODO: Need to handle this
                
            except websockets.ConnectionClosedError:
                self.log.info(f"Topic:{conn.topic}: Consumer closed connection")
                break
            except Exception as e:
                self.log.error("Something happend!",exc_info=True)
                break

        await conn.ws.close()
        self.log.info(f"Topic:{conn.topic}: Consumer diconnected")
        del self.consumers[conn.topic]

    def __log_internals(self):
        for key in self.storage.keys():
            self.log.debug(f"INTERNALS: Topic:{key} Message count:{self.storage[key].qsize()}")
            self.log.debug(f"INTERNALS: Topic:{key} Consumer:{self.consumers[key] if key in self.consumers else None}")
            if key in self.producers:
                for p in self.producers[key]:
                    self.log.debug(f"INTERNALS: Topic:{key} Producer:{p}")


    async def __start_server(self):
        server = await websockets.serve(self.handle_incomming_connection,HOST,PORT) # host and port is still global vars
        await server.wait_closed()

    def start(self):
        asyncio.run(self.__start_server())


