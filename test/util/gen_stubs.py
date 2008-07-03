#################################### IMPORTS ###################################

from __future__ import with_statement
from optparse import OptionParser
from inspect import isclass, ismodule, getdoc, isgetsetdescriptor, getmembers
from unittest import TestCase

import pygame, sys, datetime, re, types
import relative_indentation

################################ TESTS DIRECTORY ###############################

from os.path import normpath, join, dirname, abspath

sys.path.append( abspath(normpath( join(dirname(__file__), '../') )) )

#################################### IGNORES ###################################

# pygame.sprite.Sprite.__module__ = 'pygame.sprite' 
# pygame.sprite.Rect.__module__   = 'pygame'

# In [7]: pygame.overlay.Overlay.__name__
# Out[7]: 'overlay'

# Mapping of callable to module where it's defined

REAL_HOMES = {
    pygame.rect.Rect         : pygame.rect,
    pygame.mask.from_surface : pygame.mask,
    pygame.time.get_ticks    : pygame.time,
    pygame.event.Event       : pygame.event,
    pygame.event.event_name  : pygame.event,
    pygame.font.SysFont      : pygame.font,
    pygame.font.get_fonts    : pygame.font,
    pygame.font.match_font   : pygame.font,
}
  
MUST_INSTANTIATE = {
    # BaseType                        # Instance

    pygame.cdrom.CDType            :  (pygame.cdrom.CD, (1,)),
    pygame.mixer.ChannelType       :  (pygame.mixer.Channel, (1,)),
    pygame.time.Clock              :  (pygame.time.Clock, ()),

    # pygame.event.Event         :  None,
    # pygame.joystick.Joystick   :  None,
    # pygame.movie.Movie       :  None,
    # pygame.mask.Mask         :  None,
    # pygame.display.Info      :  None,
}

def get_instance(type_):
    pygame.init()

    helper = MUST_INSTANTIATE.get(type_)
    if callable(helper): return helper()
    helper, arg = helper

    try:
        return helper(*arg)
    except:
        # TODO: raise or not to raise??
        raw_input("FAILED TO CREATE INSTANCE OF %s" % type_)
        return type_

##################################### TODO #####################################

"""

Test

"""

################################ STUB TEMPLATES ################################

date = datetime.datetime.now().date()

STUB_TEMPLATE = relative_indentation.Template ( '''
    def ${test_name}(self):

        # __doc__ (as of %s) for ${unitname}:

          ${comments}

        self.assert_(test_not_implemented()) ''' % date, 

        strip_common = 0, strip_excess = 0
)

############################## REGULAR EXPRESSIONS #############################

module_re = re.compile(r"pygame\.([^.]*)\.?")

#################################### OPTIONS ###################################

opt_parser = OptionParser()

opt_parser.add_option (
     "-l",  "--list", dest = "list", action = 'store_true',
     help   = "list only callable names not stubs" )

opt_parser.set_usage(
"""
$ %prog ROOT

eg. 

$ %prog sprite.Sprite

def test_add(self):

    # Doc string for pygame.sprite.Sprite:

    ...
"""
)

################################### FUNCTIONS ##################################

def module_in_package(module, pkg):
    return ("%s." % pkg.__name__) in module.__name__

def get_package_modules(pkg):
    modules = (getattr(pkg, x) for x in dir(pkg) if is_public(x))
    return [m for m in modules if ismodule(m) and module_in_package(m, pkg)]
                                                 # Don't want to pick up 
                                                 # string module for example
def py_comment(input_str):
    return '\n'.join (
        [('# ' + l) for l in input_str.split('\n')]
    )

def is_public(obj_name):
    try: obj_name += ''
    except TypeError: obj_name = obj_name.__name__
    return not obj_name.startswith(('__','_'))

def is_test(f):
    return f.__name__.startswith('test_')

def get_callables(obj, if_of = None, check_where_defined=False):
    publics = (getattr(obj, x) for x in dir(obj) if is_public(x))
    callables = (x for x in publics if callable(x) or isgetsetdescriptor(x))

    if check_where_defined:
        callables = (c for c in callables if ( 'pygame' in c.__module__ or
                    ('__builtin__' == c.__module__ and isclass(c)) )
                    and REAL_HOMES.get(c, 0) in (0, obj))

    if if_of:
        callables = (x for x in callables if if_of(x)) # isclass, ismethod etc

    return set(callables)

def get_class_from_test_case(TC):
    TC = TC.__name__
    if 'Type' in TC:
        return '.' + TC[:TC.index('Type')]

def names_of(*args):
    return tuple(map(lambda o: getattr(o, "__name__", str(o)), args))

def callable_name(*args):
    args = [a for a in args if a]
    return ('.'.join(['%s'] * len(args))) % names_of(*args)

################################################################################

def test_stub(f, module, parent_class = None):
    test_name = 'test_%s' % f.__name__
    unit_name = callable_name(module, parent_class, f)

    stub = STUB_TEMPLATE.render (

        test_name = test_name,
        comments = py_comment(getdoc(f) or ''),
        unitname = unit_name,
    )

    return unit_name, stub

def make_stubs(seq, module, class_=None):
    return dict( test_stub(c, module, class_) for c in seq )

def module_stubs(module):
    stubs = {}
    all_callables = get_callables(module, check_where_defined = True)
    classes = set (
        c for c in all_callables if isclass(c) or c in MUST_INSTANTIATE
    )

    for class_ in classes:
        base_type = class_

        if class_ in MUST_INSTANTIATE:
            class_ = get_instance(class_)

        stubs.update (
            make_stubs(get_callables(class_), module, base_type)
        )

    stubs.update(make_stubs(all_callables - classes, module))

    return stubs

def package_stubs(package):
    stubs = dict()

    for module in get_package_modules(package):
        stubs.update(module_stubs(module))

    return stubs

################################################################################

def already_tested_in_module(module):
    already = []

    mod_name =  module.__name__
    test_name = "%s_test" % mod_name[7:]

    try: test_file = __import__(test_name)
    except ImportError:                              #TODO:  create a test file?
        return []

    classes = get_callables(test_file, isclass)
    test_cases = (t for t in classes if TestCase in t.__bases__)
    
    for class_ in test_cases:
        class_tested = get_class_from_test_case(class_) or ''

        for test in get_callables(class_, is_test):
            fname = test.__name__[5:].split('__')[0]
            already.append("%s%s.%s" % (mod_name, class_tested, fname))
    
    return already

def already_tested_in_package(package):
    already = []

    for module in get_package_modules(package):
        already += already_tested_in_module(module)

    return already

################################################################################

def get_stubs(root):    
    module_root = module_re.search(root)
    if module_root:
        module = getattr(pygame, module_root.group(1))
        stubs = module_stubs(module)
        tested = already_tested_in_module(module)
    else:
        stubs = package_stubs(pygame)
        tested = already_tested_in_package(pygame)

    return stubs, tested

if __name__ == "__main__":
    options, args = opt_parser.parse_args()
    if not sys.argv[1:]:
        sys.exit(opt_parser.print_help())

    root = args and args[0] or 'pygame'
    if not root.startswith('pygame'):
        root = '%s.%s' % ('pygame', root)

    stubs, tested = get_stubs(root)

    for fname in sorted(s for s in stubs.iterkeys() if s not in tested):
        if not fname.startswith(root): continue  # eg. module.Class
        print options.list and fname or stubs[fname]

################################################################################