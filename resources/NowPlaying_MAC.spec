# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['now_playing.py'],
             pathex=['.'],
             binaries=[],
             datas=[('resources/icon.ico', './resources'),
                    ('templates/*', 'templates')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
          a.scripts, [],
          exclude_binaries=True,
          name='NowPlaying',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon='resources/osx.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='NowPlaying')
app = BUNDLE(coll,
             name='NowPlaying.app',
             icon='resources/osx.icns',
             bundle_identifier=None,
             info_plist={'LSUIElement': True})
