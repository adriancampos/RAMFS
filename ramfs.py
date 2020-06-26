import os
import sys
import errno

from fuse import FUSE, FuseOSError, Operations
from stat import S_IFDIR, S_IFREG


from dataclasses import dataclass
from time import time


class RamFS(Operations):

    @dataclass
    class File:
        attr: None
        bytes: None

    def __init__(self):
        # key is path, value is of type File
        self.fs = {}
        self.mkdir('/', 0o777)

    def chmod(self, path, mode):
        print("chmod", path, mode)

        self.fs[path].attr['st_mode'] &= 0o770000
        self.fs[path].attr['st_mode'] |= mode

    def chown(self, path, uid, gid):
        print("chown", path, uid, gid)

        self.fs[path].attr['st_uid'] = uid
        self.fs[path].attr['st_gid'] = gid

    def getattr(self, path, fh=None):
        print("getattr", path)
        if path not in self.fs:
            print("raising ENOENT for", path)
            raise FuseOSError(errno.ENOENT)

        print("attr:", self.fs[path].attr)

        return self.fs[path].attr

    def _parentPath(self, path):
        parts = path.split('/')[:-1]

        if len(parts) == 1:
            return '/'

        return '/'.join(parts)

    def _tailPath(self, path):
        return path.split('/')[-1]

    def readdir(self, path, fh):
        print("readdir", path)

        # TODO I should have a better data structure than this flat, full-path thing
        #      This is horribly inefficient
        output = ['.', '..'] + \
            [self._tailPath(f) for f in self.fs
             if self._parentPath(f) == path and f != '/']

        print("output", output)
        return output

    def rmdir(self, path):
        print("rmdir", path)
        for k in [k for k in self.fs.keys() if k.startswith(path)]:
            self.fs.pop(k)

    def mkdir(self, path, mode):
        self.fs[path] = self.File(
            {
                'st_size': 0,
                'st_ctime': time(),
                'st_mtime': time(),
                'st_atime': time(),
                'st_mode': S_IFDIR | 0o777,

            },
            None)

    def statfs(self, path):
        return {
            'f_bsize': 1024,
            'f_frsize': 1024,
            'f_blocks': 4096000,
            'f_bfree': 4096000,
        }

    def rename(self, old, new):
        self.fs[new] = self.fs.pop(old)

    def unlink(self, path):
        self.fs.pop(path)

    def open(self, path, flags):
        print("open", path)
        return 0  # TODO

    def create(self, path, mode, fi=None):
        print("create", path, mode)
        self.fs[path] = self.File(
            {
                'st_size': 0,
                'st_ctime': time(),
                'st_mtime': time(),
                'st_atime': time(),
                'st_mode': (S_IFREG | 0o777),
                'st_nlink': 1,
            },
            b''
        )

        print(self.fs[path].attr['st_mode'])

        return 0

    def read(self, path, length, offset, fh):
        print("read", path)
        return self.fs[path].bytes[offset:offset+length]

    def readlink(self, path):
        return self.fs[path].bytes

    def write(self, path, buf, offset, fh):
        print("write", path)

        self.fs[path].bytes = \
            self.fs[path].bytes[:offset] + \
            buf + \
            self.fs[path].bytes[offset + len(buf):]

        self.fs[path].attr["st_size"] = len(self.fs[path].bytes)


def main(mountpoint):
    FUSE(RamFS(), mountpoint, nothreads=True, foreground=True)


if __name__ == '__main__':
    main(sys.argv[1])
