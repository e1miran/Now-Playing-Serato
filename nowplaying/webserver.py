#!/usr/bin/env python3
''' WebServer process '''

import asyncio
import base64
import logging
import logging.config
import os
import pathlib
import secrets
import signal
import string
import sys
import threading
import traceback
import time
import weakref

import requests
import aiohttp
from aiohttp import web, WSCloseCode
import aiosqlite

from PySide6.QtCore import QStandardPaths  # pylint: disable=no-name-in-module

#
# quiet down our imports
#

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})

# pylint: disable=wrong-import-position

import nowplaying.bootstrap
import nowplaying.config
import nowplaying.db
import nowplaying.imagecache
import nowplaying.utils

INDEXREFRESH = \
    '<!doctype html><html lang="en">' \
    '<head><meta http-equiv="refresh" content="5" ></head>' \
    '<body></body></html>\n'


TRANSPARENT_PNG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC'\
                  '1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAA'\
                  'ASUVORK5CYII='
TRANSPARENT_PNG_BIN = base64.b64decode(TRANSPARENT_PNG)


class WebHandler():  # pylint: disable=too-many-public-methods
    ''' aiohttp built server that does both http and websocket '''

    def __init__(self, databasefile, testmode=False):
        threading.current_thread().name = 'WebServer'
        self.testmode = testmode
        config = nowplaying.config.ConfigFile(testmode=testmode)
        self.port = config.cparser.value('weboutput/httpport', type=int)
        enabled = config.cparser.value('weboutput/httpenabled', type=bool)
        self.databasefile = databasefile

        while not enabled:
            try:
                time.sleep(5)
                config.get()
                enabled = config.cparser.value('weboutput/httpenabled',
                                               type=bool)
            except KeyboardInterrupt:
                sys.exit(0)

        self.magicstopurl = ''.join(
            secrets.choice(string.ascii_letters) for _ in range(32))

        logging.info('Secret url to quit websever: %s', self.magicstopurl)

        signal.signal(signal.SIGINT, self.forced_stop)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(
            self.start_server(host='0.0.0.0', port=self.port))
        self.loop.run_forever()

    def _base64ifier(self, metadata):  # pylint: disable=no-self-use
        ''' replace all the binary data with base64 data '''
        for key in nowplaying.db.MetadataDB.METADATABLOBLIST:
            if metadata.get(key):
                newkey = key.replace('raw', 'base64')
                metadata[newkey] = base64.b64encode(
                    metadata[key]).decode('utf-8')
            del metadata[key]
        return metadata

    def _transparentifier(self, metadata):
        ''' base64 encoding + transparent missing '''
        for key in nowplaying.db.MetadataDB.METADATABLOBLIST:
            if not metadata.get(key):
                metadata[key] = TRANSPARENT_PNG_BIN
        return self._base64ifier(metadata)

    async def indexhtm_handler(self, request):
        ''' handle web output '''
        return await self.htm_handler(
            request,
            request.app['config'].cparser.value('weboutput/htmltemplate'))

    async def artistbannerhtm_handler(self, request):
        ''' handle web output '''
        return await self.htm_handler(
            request, request.app['config'].cparser.value(
                'weboutput/artistbannertemplate'))

    async def artistlogohtm_handler(self, request):
        ''' handle web output '''
        return await self.htm_handler(
            request, request.app['config'].cparser.value(
                'weboutput/artistlogotemplate'))

    async def artistthumbhtm_handler(self, request):
        ''' handle web output '''
        return await self.htm_handler(
            request, request.app['config'].cparser.value(
                'weboutput/artistthumbtemplate'))

    async def artistfanartlaunchhtm_handler(self, request):
        ''' handle web output '''
        return await self.htm_handler(
            request, request.app['config'].cparser.value(
                'weboutput/artistfanarttemplate'))

    async def htm_handler(self, request, template):  # pylint: disable=unused-argument
        ''' handle static html files'''

        source = os.path.basename(template)
        htmloutput = ""
        request.app['config'].get()
        metadata = request.app['metadb'].read_last_meta()
        lastid = await self.getlastid(request, source)
        once = request.app['config'].cparser.value('weboutput/once', type=bool)

        # | dbid  |  lastid | once |
        # |   x   |   NA    |      |  -> update lastid, send template
        # |   x   |  diff   |   NA |  -> update lastid, send template
        # |   x   |  same   |      |  -> send template
        # |   x   |  same   |   x  |  -> send refresh
        # |       |   NA    |      |  -> send refresh because not ready or something broke

        if not metadata or not metadata.get('dbid') or not template:
            return web.Response(status=202,
                                content_type='text/html',
                                text=INDEXREFRESH)

        if lastid == 0 or lastid != metadata['dbid'] or not once:
            await self.setlastid(request, metadata['dbid'], source)
            try:
                templatehandler = nowplaying.utils.TemplateHandler(
                    filename=template)
                htmloutput = templatehandler.generate(metadata)
            except Exception as error:  #pylint: disable=broad-except
                logging.error('indexhtm_handler: %s', error)
                htmloutput = INDEXREFRESH
            return web.Response(content_type='text/html', text=htmloutput)

        return web.Response(content_type='text/html', text=INDEXREFRESH)

    async def setlastid(self, request, lastid, source):  # pylint: disable=no-self-use
        ''' get the lastid sent by http/html '''
        await request.app['statedb'].execute(
            'INSERT OR REPLACE INTO lastprocessed(lastid, source) VALUES (?,?) ',
            [lastid, source])
        await request.app['statedb'].commit()

    async def getlastid(self, request, source):  # pylint: disable=no-self-use
        ''' get the lastid sent by http/html '''
        cursor = await request.app['statedb'].execute(
            f'SELECT lastid FROM lastprocessed WHERE source="{source}"')
        row = await cursor.fetchone()
        if not row:
            lastid = 0
        else:
            lastid = row[0]
        await cursor.close()
        return lastid

    async def indextxt_handler(self, request):  # pylint: disable=no-self-use
        ''' handle static index.txt '''
        metadata = request.app['metadb'].read_last_meta()
        txtoutput = ""
        if metadata:
            request.app['config'].get()
            try:
                templatehandler = nowplaying.utils.TemplateHandler(
                    filename=request.app['config'].cparser.value(
                        'textoutput/txttemplate'))
                txtoutput = templatehandler.generate(metadata)
            except Exception as error:  #pylint: disable=broad-except
                logging.error('indextxt_handler: %s', error)
                txtoutput = ''
        return web.Response(text=txtoutput)

    async def favicon_handler(self, request):  # pylint: disable=no-self-use
        ''' handle favicon.ico '''
        return web.FileResponse(path=request.app['config'].iconfile)

    async def cover_handler(self, request):  # pylint: disable=no-self-use
        ''' handle cover image '''
        metadata = request.app['metadb'].read_last_meta()
        if 'coverimageraw' in metadata:
            return web.Response(content_type='image/png',
                                body=metadata['coverimageraw'])
        # rather than return an error, just send a transparent PNG
        # this makes the client code significantly easier
        return web.Response(content_type='image/png', body=TRANSPARENT_PNG_BIN)

    async def artistbanner_handler(self, request):  # pylint: disable=no-self-use
        ''' handle cover image '''
        metadata = request.app['metadb'].read_last_meta()
        if 'artistbannerraw' in metadata:
            return web.Response(content_type='image/png',
                                body=metadata['artistbannerraw'])
        # rather than return an error, just send a transparent PNG
        # this makes the client code significantly easier
        return web.Response(content_type='image/png', body=TRANSPARENT_PNG_BIN)

    async def artistlogo_handler(self, request):  # pylint: disable=no-self-use
        ''' handle cover image '''
        metadata = request.app['metadb'].read_last_meta()
        if 'artistlogoraw' in metadata:
            return web.Response(content_type='image/png',
                                body=metadata['artistlogoraw'])
        # rather than return an error, just send a transparent PNG
        # this makes the client code significantly easier
        return web.Response(content_type='image/png', body=TRANSPARENT_PNG_BIN)

    async def artistthumb_handler(self, request):  # pylint: disable=no-self-use
        ''' handle cover image '''
        metadata = request.app['metadb'].read_last_meta()
        if 'artistthumbraw' in metadata:
            return web.Response(content_type='image/png',
                                body=metadata['artistthumbraw'])
        # rather than return an error, just send a transparent PNG
        # this makes the client code significantly easier
        return web.Response(content_type='image/png', body=TRANSPARENT_PNG_BIN)

    async def api_v1_last_handler(self, request):  # pylint: disable=no-self-use
        ''' handle static index.txt '''
        metadata = request.app['metadb'].read_last_meta()
        del metadata['dbid']
        return web.json_response(self._base64ifier(metadata))

    async def websocket_artistfanart_streamer(self, request):  # pylint: disable=no-self-use
        ''' handle continually streamed updates '''
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        request.app['websockets'].add(websocket)

        try:
            while True:
                metadata = request.app['metadb'].read_last_meta()
                if not metadata or not metadata.get('artist'):
                    await asyncio.sleep(5)
                    continue

                artist = metadata['artist']
                imagedata = None
                try:
                    imagedata = request.app['imagecache'].random_image_fetch(
                        artist=artist, imagetype='artistfanart')
                except KeyError:
                    pass

                if metadata:
                    metadata['artistfanartraw'] = imagedata
                else:
                    metadata['artistfanartraw'] = TRANSPARENT_PNG_BIN
                await websocket.send_json(self._transparentifier(metadata))
                delay = request.app['config'].cparser.value(
                    'artistextras/fanartdelay', type=int)
                await asyncio.sleep(delay)
        except Exception as error:  #pylint: disable=broad-except
            logging.error('websocket artistfanart streamer exception: %s',
                          error)
            logging.error(traceback.print_exc())
        finally:
            logging.debug('artistfanart ended in finally')
            await websocket.close()
            request.app['websockets'].discard(websocket)
        return websocket

    async def websocket_lastjson_handler(self, request, websocket):  # pylint: disable=no-self-use
        ''' handle singular websocket request '''
        metadata = request.app['metadb'].read_last_meta()
        del metadata['dbid']
        await websocket.send_json(self._base64ifier(metadata))

    async def websocket_streamer(self, request):  # pylint: disable=no-self-use
        ''' handle continually streamed updates '''

        async def do_update(websocket, database):
            # early launch can be a bit weird so
            # pause a bit
            await asyncio.sleep(1)
            metadata = None
            while not metadata:
                metadata = database.read_last_meta()
                await asyncio.sleep(1)
            del metadata['dbid']
            await websocket.send_json(self._transparentifier(metadata))
            return time.time()

        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        request.app['websockets'].add(websocket)

        try:
            mytime = await do_update(websocket, request.app['metadb'])
            while True:
                while mytime > request.app['watcher'].updatetime:
                    await asyncio.sleep(1)

                mytime = await do_update(websocket, request.app['metadb'])
                await asyncio.sleep(1)
        except Exception as error:  #pylint: disable=broad-except
            logging.error('websocket streamer exception: %s', error)
        finally:
            logging.debug('ended in finally')
            await websocket.close()
            request.app['websockets'].discard(websocket)
        return websocket

    async def websocket_handler(self, request):
        ''' handle inbound websockets '''
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        request.app['websockets'].add(websocket)
        try:
            async for msg in websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == 'close':
                        await websocket.close()
                    elif msg.data == 'last':
                        logging.debug('got last')
                        await self.websocket_lastjson_handler(
                            request, websocket)
                    else:
                        await websocket.send_str(
                            'some websocket message payload')
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logging.error('ws connection closed with exception %s',
                                  websocket.exception())
        except Exception as error:  #pylint: disable=broad-except
            logging.error('Websocket handler error: %s', error)
        finally:
            request.app['websockets'].discard(websocket)

        return websocket

    def create_runner(self):
        ''' setup http routing '''
        threading.current_thread().name = 'WebServer-runner'
        app = web.Application()
        app['websockets'] = weakref.WeakSet()
        app.on_startup.append(self.on_startup)
        app.on_cleanup.append(self.on_cleanup)
        app.on_shutdown.append(self.on_shutdown)
        app.add_routes([
            web.get('/', self.indexhtm_handler),
            web.get('/v1/last', self.api_v1_last_handler),
            web.get('/cover.png', self.cover_handler),
            web.get('/artistfanart.htm', self.artistfanartlaunchhtm_handler),
            web.get('/artistbanner.png', self.artistbanner_handler),
            web.get('/artistbanner.htm', self.artistbannerhtm_handler),
            web.get('/artistlogo.png', self.artistlogo_handler),
            web.get('/artistlogo.htm', self.artistlogohtm_handler),
            web.get('/artistthumb.png', self.artistthumb_handler),
            web.get('/artistthumb.htm', self.artistthumbhtm_handler),
            web.get('/favicon.ico', self.favicon_handler),
            web.get('/index.htm', self.indexhtm_handler),
            web.get('/index.html', self.indexhtm_handler),
            web.get('/index.txt', self.indextxt_handler),
            web.get('/ws', self.websocket_handler),
            web.get('/wsstream', self.websocket_streamer),
            web.get('/wsartistfanartstream',
                    self.websocket_artistfanart_streamer),
            web.get(f'/{self.magicstopurl}', self.stop_server)
        ])
        return web.AppRunner(app)

    async def start_server(self, host="127.0.0.1", port=8899):
        ''' start our server '''
        runner = self.create_runner()
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

    async def on_startup(self, app):
        ''' setup app connections '''
        app['config'] = nowplaying.config.ConfigFile(testmode=self.testmode)
        if self.testmode:
            app['config'].templatedir = os.path.join(
                os.path.dirname(self.databasefile), 'templates')
            app['metadb'] = nowplaying.db.MetadataDB(databasefile=os.path.join(
                os.path.dirname(self.databasefile), 'test.db'))
        else:
            app['metadb'] = nowplaying.db.MetadataDB()
        app['imagecache'] = nowplaying.imagecache.ImageCache()
        app['watcher'] = app['metadb'].watcher()
        app['watcher'].start()
        app['statedb'] = await aiosqlite.connect(self.databasefile)
        app['statedb'].row_factory = aiosqlite.Row
        cursor = await app['statedb'].cursor()
        await cursor.execute('CREATE TABLE IF NOT EXISTS lastprocessed ('
                             'source TEXT PRIMARY KEY, '
                             'lastid INTEGER '
                             ')')
        await app['statedb'].commit()

    async def on_shutdown(self, app):  # pylint: disable=no-self-use
        ''' handle shutdown '''
        for websocket in set(app['websockets']):
            await websocket.close(code=WSCloseCode.GOING_AWAY,
                                  message='Server shutdown')

    async def on_cleanup(self, app):  # pylint: disable=no-self-use
        ''' cleanup the app '''
        await app['statedb'].close()
        app['watcher'].stop()

    async def stop_server(self, request):  # pylint: disable=unused-argument
        ''' stop our server '''
        await request.app.shutdown()
        await request.app.cleanup()
        self.loop.stop()

    def forced_stop(self, signum, frame):  # pylint: disable=unused-argument
        ''' caught an int signal so tell the world to stop '''
        try:
            logging.debug('telling webserver to stop via http')
            requests.get(f'http://localhost:{self.port}/{self.magicstopurl}',
                         timeout=5)
        except Exception as error:  # pylint: disable=broad-except
            logging.info(error)


def stop(pid):
    ''' stop the web server -- called from Tray '''
    logging.info('sending INT to %s', pid)
    try:
        os.kill(pid, signal.SIGINT)
    except ProcessLookupError:
        pass


def start(bundledir, testdir=None):
    ''' multiprocessing start hook '''
    threading.current_thread().name = 'WebServer'

    if not bundledir:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundledir = getattr(sys, '_MEIPASS',
                                os.path.abspath(os.path.dirname(__file__)))
        else:
            bundledir = os.path.abspath(os.path.dirname(__file__))

    if testdir:
        nowplaying.bootstrap.set_qt_names(appname='testsuite')
        databasefile = pathlib.Path(testdir).joinpath('web.db')
        testmode = True
    else:
        testmode = False
        nowplaying.bootstrap.set_qt_names()
        databasefile = pathlib.Path(
            QStandardPaths.standardLocations(
                QStandardPaths.CacheLocation)[0]).joinpath(
                    'webserver', 'web.db')

    logging.debug('Using %s as web databasefile', databasefile)
    if databasefile.exists():
        try:
            databasefile.unlink()
        except PermissionError as error:
            logging.error('WebServer process already running?')
            logging.error(error)
            sys.exit(1)

    databasefile.parent.mkdir(parents=True, exist_ok=True)
    config = nowplaying.config.ConfigFile(bundledir=bundledir,
                                          testmode=testmode)
    if testdir:
        config.templatedir = os.path.join(testdir, 'templates')
    logging.info('boot up')
    try:
        webserver = WebHandler(databasefile, testmode=testmode)  # pylint: disable=unused-variable
    except Exception as error:  #pylint: disable=broad-except
        logging.error('Webserver crashed: %s', error, exc_info=True)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    start(None)
