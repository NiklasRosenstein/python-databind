
import pathlib

from databind.json import mapper


def test_pathlib_converter():
  assert mapper().deserialize(pathlib.PosixPath('/bin/bash'), pathlib.Path) == '/bin/bash'
  assert mapper().serialize('/bin/bash', pathlib.PosixPath) == pathlib.PosixPath('/bin/bash')
