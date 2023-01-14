import asyncio
import websockets
import websockets.exceptions
import inspect
import json
import logging
from contextlib import suppress

# Sorry
import nest_asyncio
nest_asyncio.apply()

def run_sync(func, *args):
    loop = None

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError as e:
        if str(e).startswith('There is no current event loop in thread'):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        else:
            raise

    return loop.run_until_complete(func(*args))

class Server:
    """
    Sends object of all registered commands with function signatures,
    type annotations, and defaults. Hopefully someone will appreciate this ;)

    To disable for an individual server instance, just do:
      ws.commands["help"] = None
    """
    def help(self) -> dict:
        out = {}
        for key in self.commands.keys():
            paramStr = ""
            signature = inspect.signature(self.commands[key])
            params = signature.parameters
            for param in params:
                paramData = params[param]
                paramStr += param
                if paramData.annotation is not None:
                    paramStr += f": {paramData.annotation.__name__}"
                if paramData.default is not inspect._empty:
                    paramStr += f"={paramData.default}"
                paramStr += ","

            out[key] = f"({paramStr[:-1]})"
            if signature.return_annotation is not inspect._empty:
                out[key] += f" -> {signature.return_annotation.__name__}"
        return out

    def register(self, *funcs, **kwfuncs):
        for func in funcs:
            self.commands[func.__name__] = func

        for key in kwfuncs.keys():
            self.commands[key] = kwfuncs[key]

    def getURI(self) -> str:
        return f"ws://{self._interface}:{self._port}"

    def __init__(self, interface = "0.0.0.0", port = 8765):
        self.clients = set()
        self._interface = interface
        self._port = port
        self.commands = {
            "help": self.help
        }
        self.running = False
        self.log = logging.getLogger()

    def start(self):
        self.task = asyncio.create_task(self.main())
        self.running = True

    async def main(self):
        await websockets.serve(self._clientHandler, self._interface, self._port)
        await asyncio.Future()  # run forever

    async def _clientHandler(self, client, path):
        logID = f"{client.id}, {', '.join(map(str, client.local_address))}"
        logHeader = f"<{logID}>:"
        self.log.info(f"{logHeader} Client connected")

        self.clients.add(client)
        
        try:
            while self.running:
                msg = await client.recv()
                msgSplit = msg.split(",")
                cmd = msgSplit[0]
                output = "OK"
                try:
                    if (cmd not in self.commands) or (self.commands[cmd] is None):
                        raise LookupError(f"Invalid Command ({cmd})")

                    output = self.commands[cmd](*msgSplit[1:])
                    if type(output) is dict:
                        output = json.dumps(output)

                    output = str(output)
                except LookupError as e:
                    self.log.warn(f"{logHeader} {e}")
                except Exception as e:
                    self.log.warn(f"{logHeader} Server error inside command function ({cmd}, {e}))")
                    output = "ERROR"
                await client.send(f"{cmd},{output}")
        except websockets.exceptions.ConnectionClosedOK as e:
            self.log.info(f"{logHeader} Client disconnected (OK)")
        except websockets.exceptions.ConnectionClosedError as e:
            self.log.info(f"{logHeader} Client disconnected (Connection error)")
        except Exception as e:
            self.log.warn(f"{logHeader} Client disconnected ({e})")

        self.clients.remove(client)

    async def sendAll(self, message):
        for client in self.clients:
            # We don't want other clients getting blocked by another, so no await
            asyncio.create_task(client.send(message))


class Client:
    def register(self, *funcs, **kwfuncs):
        for func in funcs:
            self.commands[func.__name__] = func

        for key in kwfuncs.keys():
            self.commands[key] = kwfuncs[key]

    @property
    def uri(self):
        return f"ws://{self._address}:{self._port}"

    def __init__(self, address = "0.0.0.0", port = 8765):
        self._address = address
        self._port = port
        self.commands = {}
        self.running = False
        self.log = logging.getLogger()
        self.retryInterval = 5

    def start(self):
        self.running = True
        self.task = asyncio.create_task(self.main())

    _ws = None

    async def mainLoop(self):
        msg = await self._ws.recv()
        msgSplit = msg.split(",")
        cmd = msgSplit[0]
        args = msgSplit[1:]

        if cmd not in self.commands:
            self.log.warn("Invalid Command")
            return

        # Try to convert args to json
        with suppress(Exception): args = [json.loads(",".join(args))]

        self.commands[cmd](*args)

    async def main(self):
        wsUri = f"ws://{self._address}:{self._port}"
        while self.running:
            self.log.info(f"Connecting to server ({wsUri})")
            try:
                self._ws = await websockets.connect(wsUri)
                self.log.info(f"Client connected to server ({wsUri})")
            except Exception as e:
                self._ws = None
                self.log.warn(f"Could not connect to server, retrying in {self.retryInterval} seconds...")
                await asyncio.sleep(self.retryInterval)
                continue

            try:
                while self.running:
                    await self.mainLoop()
            except websockets.exceptions.ConnectionClosedOK as e:
                self.log.info(f"Client disconnected (OK)")
            except websockets.exceptions.ConnectionClosedError as e:
                self.log.info(f"Client disconnected (Connection error)")
            except Exception as e:
                self.log.warn(f"Client disconnected ({e})")
            self._ws = None

    def send(self, *args):
        run_sync(self._sendAsync, *args)

    async def _sendAsync(self, *args):
        await self._ws.send(",".join(args))