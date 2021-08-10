# This file was auto-generated by Shut. DO NOT EDIT
# For more information about Shut, check out https://pypi.org/project/shut/

from __future__ import print_function
import io
import os
import setuptools
import sys

def _tempcopy(src, dst):
  import atexit, shutil
  if not os.path.isfile(dst):
    if not os.path.isfile(src):
      raise RuntimeError('error: "{}" does not exist, and cannot copy it from "{}" either'.format(dst, src))
    shutil.copyfile(src, dst)
    atexit.register(lambda: os.remove(dst))


_tempcopy('../LICENSE.txt', 'LICENSE.txt')

readme_file = 'README.md'
if os.path.isfile(readme_file):
  with io.open(readme_file, encoding='utf8') as fp:
    long_description = fp.read()
else:
  print("warning: file \"{}\" does not exist.".format(readme_file), file=sys.stderr)
  long_description = None

requirements = [
  'databind.core >=1.1.4,<2.0.0',
  'typing_extensions >=3.10.0,<4.0.0',
  'nr.parsing.date >=1.0.1,<2.0.0',
  'nr.preconditions >=0.0.4,<1.0.0',
]
test_requirements = [
  'pytest',
]
extras_require = {}
extras_require['test'] = test_requirements

setuptools.setup(
  name = 'databind.json',
  version = '1.1.4',
  author = 'Niklas Rosenstein',
  author_email = 'rosensteinniklas@gmail.com',
  description = 'De-/serialize Python dataclasses to or from JSON payloads. Compatible with Python 3.7 and newer.',
  long_description = long_description,
  long_description_content_type = 'text/markdown',
  url = 'https://github.com/NiklasRosenstein/python-databind',
  license = 'MIT',
  packages = setuptools.find_packages('src', ['test', 'test.*', 'tests', 'tests.*', 'docs', 'docs.*']),
  package_dir = {'': 'src'},
  include_package_data = True,
  install_requires = requirements,
  extras_require = extras_require,
  tests_require = test_requirements,
  python_requires = '>=3.7.0,<4.0.0',
  data_files = [],
  entry_points = {},
  cmdclass = {},
  keywords = [],
  classifiers = [],
  zip_safe = False,
)
