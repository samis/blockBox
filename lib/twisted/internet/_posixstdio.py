# -*- test-case-name: twisted.test.test_stdio -*-
import warnings, errno, os
from lib.zope.interface import implements
from twisted.internet import process, error, interfaces
from twisted.python import log, failure

class PipeAddress(object):
    implements(interfaces.IAddress)

class StandardIO(object):
    implements(interfaces.ITransport, interfaces.IProducer, interfaces.IConsumer, interfaces.IHalfCloseableDescriptor)
    _reader = None
    _writer = None
    disconnected = False
    disconnecting = False

    def __init__(self, proto, stdin=0, stdout=1):
        from twisted.internet import reactor
        self.protocol = proto
        self._writer = process.ProcessWriter(reactor, self, 'write', stdout)
        try:
            self._writer.startReading()
        except IOError, e:
            if e.errno == errno.EPERM:
                raise RuntimeError(
                    "This reactor does not support this type of file "
                    "descriptor (fd %d, mode %d) (for example, epollreactor "
                    "does not support normal files.  See #4429)." % (
                        stdout, os.fstat(stdout).st_mode))
            raise

        self._reader = process.ProcessReader(reactor, self, 'read', stdin)
        self._reader.startReading()
        self.protocol.makeConnection(self)

    def loseWriteConnection(self):
        if self._writer is not None:
            self._writer.loseConnection()

    def write(self, data):
        if self._writer is not None:
            self._writer.write(data)

    def writeSequence(self, data):
        if self._writer is not None:
            self._writer.writeSequence(data)

    def loseConnection(self):
        self.disconnecting = True

        if self._writer is not None:
            self._writer.loseConnection()
        if self._reader is not None:
            self._reader.stopReading()

    def getPeer(self):
        return PipeAddress()

    def getHost(self):
        return PipeAddress()

    def childDataReceived(self, fd, data):
        self.protocol.dataReceived(data)

    def childConnectionLost(self, fd, reason):
        if self.disconnected:
            return

        if reason.value.__class__ == error.ConnectionDone:
            if fd == 'read':
                self._readConnectionLost(reason)
            else:
                self._writeConnectionLost(reason)
        else:
            self.connectionLost(reason)

    def connectionLost(self, reason):
        self.disconnected = True
        _reader = self._reader
        _writer = self._writer
        protocol = self.protocol
        self._reader = self._writer = None
        self.protocol = None

        if _writer is not None and not _writer.disconnected:
            _writer.connectionLost(reason)

        if _reader is not None and not _reader.disconnected:
            _reader.connectionLost(reason)

        try:
            protocol.connectionLost(reason)
        except:
            log.err()

    def _writeConnectionLost(self, reason):
        self._writer=None
        if self.disconnecting:
            self.connectionLost(reason)
            return

        p = interfaces.IHalfCloseableProtocol(self.protocol, None)
        if p:
            try:
                p.writeConnectionLost()
            except:
                log.err()
                self.connectionLost(failure.Failure())

    def _readConnectionLost(self, reason):
        self._reader=None
        p = interfaces.IHalfCloseableProtocol(self.protocol, None)
        if p:
            try:
                p.readConnectionLost()
            except:
                log.err()
                self.connectionLost(failure.Failure())
        else:
            self.connectionLost(reason)

    def registerProducer(self, producer, streaming):
        if self._writer is None:
            producer.stopProducing()
        else:
            self._writer.registerProducer(producer, streaming)

    def unregisterProducer(self):
        if self._writer is not None:
            self._writer.unregisterProducer()

    def stopProducing(self):
        self.loseConnection()

    def pauseProducing(self):
        if self._reader is not None:
            self._reader.pauseProducing()

    def resumeProducing(self):
        if self._reader is not None:
            self._reader.resumeProducing()

    def closeStdin(self):
        warnings.warn("This function is deprecated, use loseWriteConnection instead.",
                      category=DeprecationWarning, stacklevel=2)
        self.loseWriteConnection()

    def stopReading(self):
        self.pauseProducing()

    def startReading(self):
        self.resumeProducing()
