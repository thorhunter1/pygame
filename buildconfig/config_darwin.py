"""Config on Darwin w/ frameworks"""

import os
from distutils.sysconfig import get_python_inc


try:
    from config_unix import DependencyProg
except ImportError:
    from buildconfig.config_unix import DependencyProg


try:
    basestring_ = basestring
except NameError:
    #python 3.
    basestring_ = str

class Dependency:
    libext = '.dylib'
    def __init__(self, name, checkhead, checklib, libs):
        self.name = name
        self.inc_dir = None
        self.lib_dir = None
        self.libs = libs
        self.found = 0
        self.checklib = checklib + self.libext
        self.checkhead = checkhead
        self.cflags = ''

    def configure(self, incdirs, libdirs):
        incnames = self.checkhead
        libnames = self.checklib, self.name.lower()
        for dir in incdirs:
            if isinstance(incnames, basestring_):
                incnames = [incnames]

            for incname in incnames:
                path = os.path.join(dir, incname)
                if os.path.isfile(path):
                    self.inc_dir = os.path.dirname(path)
                    break

        for dir in libdirs:
            for name in libnames:
                path = os.path.join(dir, name)
                if os.path.isfile(path):
                    self.lib_dir = dir
                    break
        if self.lib_dir and self.inc_dir:
            print (self.name + '        '[len(self.name):] + ': found')
            self.found = 1
        else:
            print (self.name + '        '[len(self.name):] + ': not found')

class FrameworkDependency(Dependency):
    def configure(self, incdirs, libdirs):
        BASE_DIRS = '/', os.path.expanduser('~/'), '/System/'
        for n in BASE_DIRS:
            n += 'Library/Frameworks/'
            fmwk = n + self.libs + '.framework/Versions/Current/'
            if os.path.isfile(fmwk + self.libs):
                print ('Framework ' + self.libs + ' found')
                self.found = 1
                self.inc_dir = fmwk + 'Headers'
                self.cflags = (
                    '-Xlinker "-framework" -Xlinker "' + self.libs + '"' +
                    ' -Xlinker "-F' + n + '"')
                self.origlib = self.libs
                self.libs = ''
                return
        print ('Framework ' + self.libs + ' not found')


class DependencyPython:
    def __init__(self, name, module, header):
        self.name = name
        self.lib_dir = ''
        self.inc_dir = ''
        self.libs = []
        self.cflags = ''
        self.found = 0
        self.ver = '0'
        self.module = module
        self.header = header

    def configure(self, incdirs, libdirs):
        self.found = 1
        if self.module:
            try:
                self.ver = __import__(self.module).__version__
            except ImportError:
                self.found = 0
        if self.found and self.header:
            fullpath = os.path.join(get_python_inc(0), self.header)
            if not os.path.isfile(fullpath):
                self.found = 0
            else:
                self.inc_dir = os.path.split(fullpath)[0]
        if self.found:
            print (self.name + '        '[len(self.name):] + ': found', self.ver)
        else:
            print (self.name + '        '[len(self.name):] + ': not found')

def find_freetype():
    """ modern freetype uses pkg-config. However, some older systems don't have that.
    """
    pkg_config = DependencyProg(
        'FREETYPE', 'FREETYPE_CONFIG', 'pkg-config freetype2', '2.0',
        ['freetype2'], '--modversion'
    )
    if pkg_config.found:
        return pkg_config

    #DependencyProg('FREETYPE', 'FREETYPE_CONFIG', '/usr/X11R6/bin/freetype-config', '2.0',
    freetype_config = DependencyProg(
        'FREETYPE', 'FREETYPE_CONFIG', 'freetype-config', '2.0', ['freetype'], '--ftversion'
    )
    if freetype_config.found:
        return freetype_config
    return pkg_config





def main(sdl2=False):

    if sdl2:
        DEPS = [
            [DependencyProg('SDL', 'SDL_CONFIG', 'sdl2-config', '2.0', ['sdl'])],
            [Dependency('FONT', ['SDL_ttf.h', 'SDL2/SDL_ttf.h'], 'libSDL2_ttf', ['SDL2_ttf'])],
            [Dependency('IMAGE', ['SDL_image.h', 'SDL2/SDL_image.h'], 'libSDL2_image', ['SDL2_image'])],
            [Dependency('MIXER', ['SDL_mixer.h', 'SDL2/SDL_mixer.h'], 'libSDL2_mixer', ['SDL2_mixer'])],
        ]
    else:
        DEPS = [
            [DependencyProg('SDL', 'SDL_CONFIG', 'sdl-config', '1.2', ['sdl']),
                 FrameworkDependency('SDL', 'SDL.h', 'libSDL', 'SDL')],
            [Dependency('FONT', ['SDL_ttf.h', 'SDL/SDL_ttf.h'], 'libSDL_ttf', ['SDL_ttf']),
                 FrameworkDependency('FONT', 'SDL_ttf.h', 'libSDL_ttf', 'SDL_ttf')],
            [Dependency('IMAGE', ['SDL_image.h', 'SDL/SDL_image.h'], 'libSDL_image', ['SDL_image']),
                 FrameworkDependency('IMAGE', 'SDL_image.h', 'libSDL_image', 'SDL_image')],
            [Dependency('MIXER', ['SDL_mixer.h', 'SDL/SDL_mixer.h'], 'libSDL_mixer', ['SDL_mixer']),
                 FrameworkDependency('MIXER', 'SDL_mixer.h', 'libSDL_mixer', 'SDL_mixer')],
        ]


    DEPS.extend([
        FrameworkDependency('PORTTIME', 'CoreMidi.h', 'CoreMidi', 'CoreMIDI'),
        FrameworkDependency('QUICKTIME', 'QuickTime.h', 'QuickTime', 'QuickTime'),
        Dependency('PNG', 'png.h', 'libpng', ['png']),
        Dependency('JPEG', 'jpeglib.h', 'libjpeg', ['jpeg']),
        Dependency('PORTMIDI', 'portmidi.h', 'libportmidi', ['portmidi']),
        find_freetype(),
        # Scrap is included in sdlmain_osx, there is nothing to look at.
        # Dependency('SCRAP', '','',[]),
    ])

    print ('Hunting dependencies...')
    incdirs = ['/usr/local/include', '/opt/homebrew/include']
    if sdl2:
        incdirs.extend(['/usr/local/include/SDL2', '/opt/homebrew/include/SDL2', '/opt/local/include/SDL2'])
    else:
        incdirs.extend(['/usr/local/include/SDL', '/opt/homebrew/include/SDL', '/opt/local/include/SDL'])

    incdirs.extend([
       #'/usr/X11/include',
       '/opt/local/include',
       '/opt/local/include/freetype2/freetype']
    )
    #libdirs = ['/usr/local/lib', '/usr/X11/lib', '/opt/local/lib']
    libdirs = ['/usr/local/lib', '/opt/local/lib', '/opt/homebrew/lib']

    for d in DEPS:
        if isinstance(d, (list, tuple)):
            for deptype in d:
                deptype.configure(incdirs, libdirs)
        else:
            d.configure(incdirs, libdirs)

    for d in DEPS:
        if type(d)==list:
            found = False
            for deptype in d:
                if deptype.found:
                    found = True
                    DEPS[DEPS.index(d)] = deptype
                    break
            if not found:
                DEPS[DEPS.index(d)] = d[0]

    DEPS[0].cflags = '-Ddarwin '+ DEPS[0].cflags
    return DEPS


if __name__ == '__main__':
    print ("""This is the configuration subscript for OSX Darwin.
             Please run "config.py" for full configuration.""")
