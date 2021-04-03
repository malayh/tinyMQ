import argparse
import os
from .server import TinyMQServer
import time
from pathlib import Path
from daemonize import Daemonize
import logging

home = Path.home()
log_dir = home.joinpath('tinyMQ/')
pid_file = home.joinpath('tinyMQ/tinymq.pid')

def runserver(host:str, port:int, log_level: str):
    #setup
    if not os.path.exists(log_dir) or not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(log_dir.joinpath(f"tinymq.log"),"a")
    fh.setFormatter(formatter)
    fh.setLevel(getattr(logging,log_level))

    server = TinyMQServer(logfh=fh)    

    def _wraper():
        server.start(host, port)

    daemon = Daemonize(app="tmqServer", pid=pid_file, action=_wraper, keep_fds=[fh.stream.fileno()])
    daemon.start()

def execute_cli():
    parser = argparse.ArgumentParser(description="Control interface for tinyMQ server")
    mxgroup = parser.add_mutually_exclusive_group(required=True)
    mxgroup.add_argument("--runserver",action="store_true")
    mxgroup.add_argument("--stopserver",action="store_true")

    parser.add_argument("--host")
    parser.add_argument("--port")
    parser.add_argument("--log-level",default="INFO",choices=["INFO","DEBUG","ERROR"])

    args = parser.parse_args()

    if args.runserver:
        if not (args.host and args.port):
            raise ValueError("Host and Port needed to start server")

        runserver(args.host, args.port, args.log_level)

    if args.stopserver:
        pid = open(pid_file,"r").read().strip()
        os.kill(int(pid),15)
        


