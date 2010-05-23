import sys
import time
from crypto.keys import KeyManager
from crypto.curve import Key
from core.util import getPublicIP, encode, decode, encodeAddress
from core.data_packet import DataPacket
from server.router import PacketRouter

from tracker.trackerClient import TrackerClient
from dustmail.dustmailClient import DustmailClient

passwd=sys.argv[1]
inport=int(sys.argv[2])
dest=sys.argv[3]
outport=int(sys.argv[4])
ipv=int(sys.argv[5])
if ipv==6:
  v6=True
else:
  v6=False

host=getPublicIP(v6)
print('Host: '+str(host))

keys=KeyManager()
keys.setInvitePassword(passwd)
keys.loadKnownHosts('config/knownhosts.yaml')
keys.loadKeypair('config/id.yaml')
keys.loadIncomingInvites('config/incoming_invites.ip')
keys.loadOutgoingInvites('config/outgoing_invites.ip')

endpoint=keys.loadEndpoint('~/.dust/endpoint.yaml')

keypair=keys.getKeypair()
pubkey=keypair.public
destpubkey=pubkey
pubkeyhex=encode(pubkey.bytes)
destpubkeyhex=pubkeyhex

router=PacketRouter(v6, inport, keys, passwd)
router.connect(dest, outport)

dustmail=DustmailClient(router)

tracker=TrackerClient(router)
trackback=router.getService('trackback')

router.start()

class PendingMessage:
  def __init__(self, tracker, trackback, dustmail, keypair, endkey, msg):
    self.dustmail=dustmail
    self.keypair=keypair
    self.endkey=endkey
    self.msg=msg
    trackback.setPutPeerForEndpointCallback(encode(endkey.bytes), self.foundPeer)
    tracker.getPeerForEndpoint(encode(endkey.bytes))

  def foundPeer(self, endkey, peer):
    print('foundPeer!!! '+str(endkey)+' '+str(peer))
    destkey=decode(peer[0])
    addr=peer[1]
    data=self.msg.encode('ascii')
    sessionKey=keypair.createSession(Key(destkey, False))
    print('session '+str(sessionKey.bytes))
    packet=DataPacket()
    packet.createDataPacket(sessionKey.bytes, data, keys.entropy)
    self.dustmail.sendMessage(encode(self.keypair.public.bytes), encode(destkey), encode(packet.packet))

tracker.putPeerForEndpoint(pubkeyhex, [pubkeyhex, encodeAddress((host,inport))])

msg='message.........'
msg=PendingMessage(tracker, trackback, dustmail, keypair, destpubkey, msg)

while True:
  try:
    time.sleep(1)
  except:
    sys.exit(0)