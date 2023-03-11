#!/usr/bin/env python3
''' NowPlaying as run via python -m '''
#import faulthandler
import logging
import multiprocessing
import platform
import socket
import sys

from pid import PidFile
from pid.base import PidFileAlreadyLockedError

from PySide6.QtCore import QCoreApplication, Qt  # pylint: disable=no-name-in-module
from PySide6.QtGui import QIcon  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import QApplication  # pylint: disable=no-name-in-module

import nowplaying
import nowplaying.bootstrap
import nowplaying.config
import nowplaying.db
import nowplaying.frozen
import nowplaying.systemtray
import nowplaying.upgrade

# pragma: no cover
#
# as of now, there isn't really much here to test... basic bootstrap stuff
#


def run_bootstrap(bundledir=None):
    ''' bootstrap the app '''
    # we are in a hurry to get results.  If it takes longer than
    # 5 seconds, consider it a failure and move on.  At some
    # point this should be configurable but this is good enough for now
    socket.setdefaulttimeout(5.0)
    logpath = nowplaying.bootstrap.setuplogging(rotate=True)
    plat = platform.platform()
    logging.info('starting up v%s on %s',
                 nowplaying.version.get_versions()['version'], plat)
    nowplaying.upgrade.upgrade(bundledir=bundledir)
    logging.debug('ending upgrade')

    # fail early if metadatadb can't be configured
    metadb = nowplaying.db.MetadataDB()
    metadb.setupsql()
    return logpath


def actualmain(beam=False):
    ''' main entrypoint '''

    multiprocessing.freeze_support()
    #faulthandler.enable()

    bundledir = nowplaying.frozen.frozen_init(None)
    exitval = 1
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)
    nowplaying.bootstrap.set_qt_names()
    piddir = nowplaying.bootstrap.get_pid_dir()
    try:
        with PidFile(pidname='nowplaying.pid',
                     piddir=piddir,
                     register_term_signal_handler=False,
                     register_atexit=False) as pid:

            logpath = run_bootstrap(bundledir=bundledir)

            if not nowplaying.bootstrap.verify_python_version():
                sys.exit(1)

            config = nowplaying.config.ConfigFile(logpath=logpath,
                                                  bundledir=bundledir)
            logging.getLogger().setLevel(config.loglevel)
            logging.captureWarnings(True)
            logging.debug('Using pidfile %s/%s', pid.piddir, pid.pidname)
            tray = nowplaying.systemtray.Tray(beam=beam)  # pylint: disable=unused-variable
            icon = QIcon(str(config.iconfile))
            qapp.setWindowIcon(icon)
            exitval = qapp.exec_()
            logging.info('shutting main down v%s',
                         nowplaying.version.get_versions()['version'])
    except (PidFileAlreadyLockedError, BlockingIOError):
        pass

    sys.exit(exitval)


def main():
    ''' Normal mode '''
    actualmain(beam=False)


def beammain():
    ''' beam mode '''
    actualmain(beam=True)


if __name__ == '__main__':
    main()
