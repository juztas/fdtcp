from distutils.core import setup
from setupUtilities import get_py_modules


print get_py_modules(['src/python/'])

setup(name='fdtcplib',
      version='0.12',
      description='Fast Data Transfers daemon and third part copy tool',
      author='Justas Balcas',
      author_email='justas.balcas@cern.ch',
      url='https://github.com/juztas/fdtcp',
      download_url='https://github.com/juztas/fdtcp/tarball/0.1',
      keywords=['FDT', 'fast', 'transfers', 'caltech', 'data'],
      packages=['fdtcplib'],
      package_dir={'': 'src/python'},
      data_files=[('/etc/fdtcp/', ['conf/fdtcp.conf', 'conf/fdtd-system-conf.sh', 'conf/fdtd.conf']),
                  # (PYTHON_LIB_PATH, ['src/python/__init__.py', 'src/python/fdtcp', 'src/python/fdtd-log-analyzer', 'src/python/fdtd']),
                  # (str(PYTHON_LIB_PATH + "common/"), ['src/python/common/%s' % x for x in ['TransferFile.py', '__init__.py', 'actions.py', 'errors.py']]),
                  # (str(PYTHON_LIB_PATH + "utils/"), ['src/python/utils/%s' % x for x in ['Config.py', 'Executor.py', 'Logger.py', '__init__.py', 'utils.py']]),],
                 ],
      py_modules=get_py_modules(['src/python/']),
      scripts=["bin/fdtd.sh", "bin/wrapper_fdt.sh", "bin/wrapper_kill.sh",
               "src/python/fdtcp", "src/python/fdtd-log-analyzer", "bin/wrapper_auth.sh"])
