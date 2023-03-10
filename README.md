# pyWSConsole
Console-like client/server WebSockets wrapper for Python.

> ⚠️ WARNING: This has no security mechanisms or permissions management! That's left as an exercise to the user and not planned for this package. The primary purpose of this library is stability.

## Basic Usage Examples

### Server
```python
from pyWSConsole import Server

def ping(arg: int):
  return f"pong! {arg}" # Function outputs are automatically returned to the Client.

ws = Server() # By default, listens on all interfaces at port 8765.
ws.register(
  ping,       # Register command names automatically...
  p=ping      # or define them manually!
)
ws.start()
```

### Client
```python
from pyWSConsole import Client

ws = Client() # By default, connects to localhost at port 8765.
ws.register(  # For the client, this registers response callbacks.
  ping=print  # eg. If you send a "ping", you will get a "ping" command back with the response
)
ws.start()
ws.send("ping", 123) # Prints "pong! 123" on response!
```

## Syntax
Connecting to the server with a standard WebSockets client uses the following syntax:
```
command[,arg1,arg2,...]
```
Sending the `help` command will respond with a list of available commands with their corresponding function signatures, including type annotations.
