import sys
import time

from struct import unpack
from socket import inet_ntoa

import monocle
from monocle import _o, Return
monocle.init('tornado')

from monocle.stack import eventloop
from monocle.stack.network import add_service, Service, Client, ConnectionLost
from loopback import FakeSocket

from shared import *
from socks import *

@_o
def handle_dust(conn):
  print('handle_dust')
  myAddr=conn.iostream.socket.getsockname()
  dest=conn.iostream.socket.getpeername()
  coder=DustCoder(myAddr, dest)
  buffer=FakeSocket()
  monocle.launch(handle_socks, buffer.invert())

  monocle.launch(pump, conn, buffer, coder.dirtyPacket)
  yield pump(buffer, conn, coder.dustPacket)

@_o
def handle_socks(conn):
  print('handle_socks')
  yield readHandshake(conn)
  print('read handshake')
  yield sendHandshake(conn)
  print('send handshake')
  dest=yield readRequest(conn)
  print('read request: '+str(dest))
  yield sendResponse(dest, conn)
  print('sent response')

  addr, port=uncompact(dest)
  print(addr)
  print(port)

  client = Client()
  yield client.connect(addr, port)
  print('connected '+str(addr)+', '+str(port))
  monocle.launch(pump, conn, client, None)
  yield pump(client, conn, None)

add_service(Service(handle_dust, port=7051))
eventloop.run()
