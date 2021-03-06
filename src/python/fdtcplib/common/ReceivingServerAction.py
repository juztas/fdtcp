"""
Classes holding details of communication transmitted between fdtcp and fdtd.

Implementations of actions - factual starting of FDT Java client/server
    processes by fdtd

ReceivingServerAction starts FDT process for further communication.
SendingClientAction will connect to this FDT process and will transmit data.

"""
from __future__ import print_function
# TODO remove logger as function argument and use class one
import os
import re
import datetime
import psutil
import apmon
import Pyro4
from past.utils import old_div
from fdtcplib.utils.Executor import Executor
from fdtcplib.utils.utils import getHostName, getApmonObj
from fdtcplib.common.actions import Action
from fdtcplib.common.actions import Result
from fdtcplib.common.errors import FDTDException, PortInUseException


@Pyro4.expose
class ReceivingServerAction(Action):
    """ Receiving Server Action """

    def __init__(self, options):
        """
        Instance of this class is created by fdtcp and some parameters are
        passed (options), options is a dictionary.

        """
        self.apMon = None
        self.id = options['transferId']
        Action.__init__(self, self.id)
        self.options = options
        self.command = None
        self.status = -1
        self.logger = self.options['logger']
        self.caller = self.options['caller']
        self.conf = self.options['conf']
        self.executor = None
        self.port = None
        if 'apmonObj' in self.options.keys():
            self.apMon = self.options['apmonObj']

    def _setUp(self, conf, port):
        """ Setup Receiver server action objects """
        # separate method for testing purposes, basically sets up command
        self.options["sudouser"] = self.options["gridUserDest"]
        self.options["port"] = port
        if 'monID' not in self.options:
            self.options["monID"] = self.id
        newOptions = self.options
        newOptions['apmonDest'] = conf.get("apMonDestinations")
        if not self.apMon:
            self.apMon = getApmonObj(newOptions['apmonDest'])
        self.command = conf.get("fdtReceivingServerCommand") % newOptions

    def _checkTargetFileNames(self, destFiles):
        """
        #36 - additional checks to debug AlreadyBeingCreatedException
        Check all the paths in the supplied list and log whether the files
        as well as the dotName form of the files exist.
        The intention is to help debug HDFS AlreadyBeingCreatedException
        """
        out = ""
        ind = ' ' * 4
        for fileName in destFiles:
            exists = os.path.exists(fileName)
            out = ind.join([out, "exists %5s: %s\n" % (exists, fileName)])
            dotName = '.' + os.path.basename(fileName)
            dotNameFull = os.path.join(os.path.dirname(fileName), dotName)
            exists = os.path.exists(dotNameFull)
            out = ind.join([out, "exists %5s: %s\n" % (exists, dotNameFull)])
        return out

    def _checkAddrAlreadyInUseError(self, exMsg):
        """
        Check if "Address already in use" error occurred and if so
        try to find out which process has the port.
        Also return what to raise.
        """
        errMsg = "Address already in use"
        self.logger.debug("Checking for '%s' error message (port: %s) ... " %
                          (errMsg, self.port))
        addressUsedObj = re.compile(errMsg)
        match = addressUsedObj.search(exMsg)
        if not match:
            self.logger.debug("Error message '%s' not found, different failure.")
            return FDTDException, exMsg
        self.logger.debug("'%s' problem detected, analyzing running "
                          "processes ..." % errMsg)
        startTime = datetime.datetime.now()
        found = False
        procs = psutil.pids()
        self.logger.debug("Going to check %s processes ..." % len(procs))
        for pid in procs:
            try:
                proc = psutil.Process(pid)
                conns = proc.connections()
            except psutil.AccessDenied:
                self.logger.debug("Access denied to process PID: %s, "
                                  "continue ..." % pid)
                continue
            for conn in conns:
                # It can have multiple connections, so need to check all
                try:
                    connPort = int(conn.local_address[1])
                    if self.port == connPort:
                        msg = ("Detected: process PID: %s occupies port: %s "
                               "(user: %s, cmdline: %s)" %
                               (pid, self.port, proc.username, " ".join(proc.cmdline)))
                        self.logger.debug(msg)
                        exMsg += msg
                        found = True
                except AttributeError as ex:
                    self.logger.debug("Got unnexpected attribute error. %s %s" % (conn, ex))
                    continue
            if found:
                return PortInUseException, exMsg
        endTime = datetime.datetime.now()
        elapsed = old_div(((endTime - startTime).microseconds), 1000)
        self.logger.debug("Process checking is over, took %s ms." % elapsed)
        return FDTDException, exMsg

    def execute(self):
        """
        This method is is called on the remote site where fdtd runs - here
        are also known all configuration details, thus final set up has to
        happen here.
        """
        startTime = datetime.datetime.now()
        # may fail with subset of FDTDException which will be propagated
        if 'portServer' in self.options and self.options['portServer']:
            self.logger.info("Forcing to use user specified port %s" % self.options['portServer'])
            try:
                self.port = int(self.options['portServer'])
            except TypeError as ex:
                self.logger.info("Provided portServer key is not convertable to integer: %s, Error: %s"
                                 % (self.options['portServer'], ex))
                self.port = int(self.caller.getFreePort())
        else:
            self.logger.info("Try to get a free port")
            self.port = int(self.caller.getFreePort())
        self._setUp(self.conf, self.port)
        destFiles = self.options["destFiles"]
        self.logger.info("%s - checking presence of files at target "
                         "location ..." % self.__class__.__name__)
        self.logger.debug("Results:\n%s" % self._checkTargetFileNames(destFiles))
        user = self.options["sudouser"]
        self.logger.debug("Local grid user is '%s'" % user)
        self.executor = Executor(self.id,
                                 caller=self.caller,
                                 command=self.command,
                                 port=self.port,
                                 userName=user,
                                 logger=self.logger)
        try:
            output = self.executor.execute()
        # on errors, do not do any cleanup or port releasing, from
        # Executor.execute() the instance is in the container and shall
        # be handled by CleanupProcessesAction
        except Exception as ex:
            raiser, ex = self._checkAddrAlreadyInUseError(str(ex))
            msg = ("Could not start FDT server on %s port: %s, reason: %s" %
                   (getHostName(), self.port, ex))
            self.logger.critical(msg, traceBack=True)
            self.status = -2
            raise raiser(msg)
        else:
            rObj = Result(self.id)
            rObj.status = 0
            self.status = 0
            # port on which FDT Java server runs
            rObj.serverPort = self.port
            rObj.msg = "FDT server is running"
            rObj.log = output
            self.logger.debug("Response to client: %s" % rObj)

            endTime = datetime.datetime.now()
            elapsed = (endTime - startTime).seconds
            par = dict(id=self.id, fdt_server_init=elapsed)
            self.logger.debug("Starting FDT server lasted: %s [s]." % elapsed)
            if self.apMon:
                self.logger.debug("Sending data to ApMon ...")
                self.apMon.sendParameters("fdtd_server_writer", None, par)
            return rObj

    def getID(self):
        """ Returns transfer ID """
        return self.id

    def getStatus(self):
        """ Returns class status """
        return self.status

    def getHost(self):
        """ Returns hostname. """
        return self.conf.get("hostname") or getHostName()

    def getMsg(self):
        """ Returns last raised message in the queue """
        return self.executor.lastMessage()

    def getLog(self):
        """ Returns log file lines """
        return self.executor.getLogs()

    def getServerPort(self):
        """Returns server port on which it is listening"""
        return self.port

    def executeWithLogOut(self):
        """ Execute transfer which will log everything back to calling client """
        for line in self.executor.executeWithLogOut():
            yield line

    def executeWithOutLogOut(self):
        """ Execute without log output to the client on the fly. Logs can be received from getLog """
        return self.executor.executeWithOutLogOut()
