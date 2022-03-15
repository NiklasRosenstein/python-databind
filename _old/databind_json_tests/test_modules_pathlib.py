
import pathlib

from databind.json import mapper


def test_pathlib_converter():
  assert mapper().serialize(pathlib.PosixPath('/bin/bash'), pathlib.Path) == '/bin/bash'
  assert mapper().deserialize('/bin/bash', pathlib.PosixPath) == pathlib.PosixPath('/bin/bash')
