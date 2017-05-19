""" Utilities which are used in any setup"""
import os
import sys

def get_path_to_root(appendLocation=None):
    """
    Work out the path to the root from where the script is being run. Allows for
    calling setup.py env from sub directories and directories outside the main dir
    """
    fullPath = os.path.dirname(os.path.abspath(os.path.join(os.getcwd(), sys.argv[0])))
    if appendLocation:
        return "%s/%s" % (fullPath, appendLocation)
    return fullPath


def list_packages(packageDirs=None,
                  recurse=True,
                  ignoreThese=None,
                  pyFiles=False):
    """
    Take a list of directories and return a list of all packages under those directories,
    Skipping 'CVS', '.svn', 'svn', '.git', '', 'dtnrmagent.egg-info' files.
    """
    if not packageDirs:
        packageDirs = []
    if not ignoreThese:
        ignoreThese = set(['CVS', '.svn', 'svn', '.git', '', 'dtnrmagent.egg-info'])
    else:
        ignoreThese = set(ignoreThese)
    packages = []
    modules = []
    # Skip the following files
    for aDir in packageDirs:
        if recurse:
            # Recurse the sub-directories
            for dirpath, dummyDirnames, dummyFilenames in os.walk('%s' % aDir, topdown=True):
                pathelements = dirpath.split('/')
                # If any part of pathelements is in the ignore_these set skip the path
                if len(set(pathelements) & ignoreThese) == 0:
                    relPath = os.path.relpath(dirpath, get_path_to_root())
                    relPath = relPath.split('/')[2:]
                    if not pyFiles:
                        packages.append('.'.join(relPath))
                    else:
                        for fileName in dummyFilenames:
                            if fileName.startswith('__init__.') or \
                               fileName.endswith('.pyc') or \
                               not fileName.endswith('.py'):
                                #print('Ignoring %s' % fileName)
                                continue
                            relName = fileName.rsplit('.', 1)
                            modules.append("%s.%s" % ('.'.join(relPath), relName[0]))
                else:
                    continue
                    #print('Ignoring %s' % dirpath)
        else:
            relPath = os.path.relpath(aDir, get_path_to_root())
            relPath = relPath.split('/')[2:]
            packages.append('.'.join(relPath))
    if pyFiles:
        return modules
    return packages


def get_py_modules(modulesDirs):
    """ Get py modules for setup.py """
    return list_packages(modulesDirs, pyFiles=True)
