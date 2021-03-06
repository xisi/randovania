# -*- mode: python -*-

block_cipher = None
import os
icon_path = "randovania/data/icons/sky_temple_key_NqN_icon.ico"

a = Analysis(['randovania/__main__.py', 'randovania/cli/__init__.py'],
             pathex=[],
             binaries=[],
             datas=[
                 ("randovania/data/icons", "data/icons"),
                 ("randovania/data/ClarisEchoesMenu", "data/ClarisEchoesMenu"),
                 ("randovania/data/ClarisPrimeRandomizer", "data/ClarisPrimeRandomizer"),
                 ("randovania/data/binary_data", "data/binary_data"),
             ],
             hiddenimports=[
                "unittest.mock",
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='randovania',
          debug=False,
          strip=False,
          upx=False,
          icon=icon_path,
          console=True)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='randovania')
