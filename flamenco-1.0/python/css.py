# Copyright (c) 2004-2006 The Regents of the University of California.

"""CSS generation utilities."""

from colorsys import rgb_to_hsv, hsv_to_rgb

# ----------------------------------------------------------------- CSS rules
_rename={'bg': 'background-color', 'fg': 'color',
         'xform': 'text-transform', 'decoration': 'text-decoration',
         'align': 'text-align', 'valign': 'vertical-align',
         'family': 'font-family', 'weight': 'font-weight',
         'size': 'font-size', 'style': 'font-style',
         'bordert': 'border-top', 'borderb': 'border-bottom',
         'borderl': 'border-left', 'borderr': 'border-right',
         'padt': 'padding-top', 'padb': 'padding-bottom',
         'padl': 'padding-left', 'padr': 'padding-right',
         'margint': 'margin-top', 'marginb': 'margin-bottom',
         'marginl': 'margin-left', 'marginr': 'margin-right'}.get

class rule:
    """A single CSS rule."""

    def __init__(self, selector='', **props):
        """Create a rule, given a selector string and keyword arguments
        for the properties.  Each keyword argument sets a property in the
        rule, where underscores stand for hyphens in the property name."""
        self.__dict__['selector'] = selector
        self.__dict__['props'] = {}
        for name, value in props.items():
            setattr(self, _rename(name, name), value)

    def __str__(self):
        items = self.props.items()
        items.sort()
        props = ['    %s: %s;\n' % (name.replace('_', '-'), value)
                 for name, value in items]
        return self.selector + ' {\n' + ''.join(props) + '}\n'

    def __setattr__(self, name, value):
        self.props[name.replace('-', '_')] = value

    def __getattr__(self, name):
        return self.props[name.replace('-', '_')]

    def within(self, selector):
        """Embed this rule in the context of a selector."""
        return rule(selector + ' ' + self.selector, **self.props)

def comment(text):
    """A CSS comment (single or multiple lines)."""
    lines = ['// ' + line + '\n' for line in text.split('\n')]
    return ''.join(lines).replace('// \n', '\n')

def within(selector, *stuff):
    """Embed a set of rules in the context of a selector."""
    results = []
    for item in stuff:
        if isinstance(item, list) or isinstance(item, tuple):
            results += within(selector, *item)
        elif isinstance(item, rule):
            results.append(item.within(selector))
        else:
            results.append(item)
    return results

# ------------------------------------------------------ colour manipulation
class rgb:
    """A colour with red, green, blue components in [0.0, 1.0]."""

    def __init__(self, *args):
        """Construct a colour.  Give a single argument from 0.0 to 1.0 to get
        a grey value; give a single colour argument; or give three arguments
        containing red, green, blue components from 0.0 to 1.0."""
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, float):
                self.red, self.green, self.blue = arg, arg, arg
            elif isinstance(arg, str):
                code = arg.replace('#', '')
                if len(code) != 6:
                    raise TypeError, 'rgb() string arg should be 6 hex digits'
                self.red = int(code[:2], 16)/255.0
                self.green = int(code[2:4], 16)/255.0
                self.blue = int(code[4:], 16)/255.0
            elif isinstance(arg, rgb):
                self.red, self.green, self.blue = arg.red, arg.green, arg.blue
            elif isinstance(arg, hsv):
                self.red, self.green, self.blue = arg.rgb()
            else:
                raise TypeError, 'rgb() single arg should be float or colour'
        elif len(args) == 3:
            self.red, self.green, self.blue = args
        else:
            raise TypeError, 'rgb() needs 1 arg or 3 args'

    def __repr__(self):
        return 'rgb(%f, %f, %f)' % (self.red, self.green, self.blue)

    def __str__(self):
        red = min(int(self.red * 256.0), 255)
        green = min(int(self.green * 256.0), 255)
        blue = min(int(self.blue * 256.0), 255)
        return '#%02x%02x%02x' % (red, green, blue)

    def __add__(self, other):
        """Add this colour to another colour (Photoshop 'screen').
        The result will always be lighter than each input.  Adding
        white to any colour gives white."""
        if isinstance(other, str):
            return str(self) + other
        return -((-self) * (-rgb(other)))

    def __radd__(self, other):
        if isinstance(other, str):
            return other + str(self)
        raise TypeError, 'colour cannot be added to %r' % other

    def __sub__(self, other):
        """Add this colour to the inverse of another colour."""
        other = rgb(other)
        return self + (-other)

    def __neg__(self):
        """Get the inverse of this colour."""
        return rgb(1.0 - self.red, 1.0 - self.green, 1.0 - self.blue)

    def __mul__(self, other):
        """Filter this colour through another colour (Photoshop 'multiply').
        The result will always be darker than each input.  Multiplying
        black by any colour gives black."""
        other = rgb(other)
        return rgb(self.red * other.red,
                   self.green * other.green,
                   self.blue * other.blue)

    def rgb(self):
        """Convert to red, green, blue components."""
        return self.red, self.green, self.blue

    def hsv(self):
        """Convert to hue, saturation, value components."""
        return rgb_to_hsv(self.red, self.green, self.blue)

    def blend(self, target, factor=0.5):
        """Blend this colour with a target colour to get something in between.
        If the factor is 0, result is exactly the original colour; if the
        factor is 1, the result is exactly the target colour."""
        return rgb(self.red + (target.red - self.red) * factor,
                   self.green + (target.green - self.green) * factor,
                   self.blue + (target.blue - self.blue) * factor)

    def saturate(self, factor=0.5):
        """Saturate by a factor from 0 (no effect) to 1 (pure colour)."""
        return hsv(self).saturate(factor)

    def desaturate(self, factor=0.5):
        """Desaturate by a factor from 0 (no effect) to 1 (pure white)."""
        return hsv(self).desaturate(factor)

    def lighten(self, factor=0.5):
        """Lighten by a factor from 0 (no effect) to 1 (pure white)."""
        return self.blend(white, factor)

    def brighten(self, factor=0.5):
        """Brighten by a factor from 0 (no effect) to 1 (maximum intensity)."""
        return hsv(self).brighten(factor)

    def darken(self, factor=0.5):
        """Darken by a factor from 0 (no effect) to 1 (pure black)."""
        return hsv(self).darken(factor)

    def complement(self):
        """Get the complement of this colour."""
        return self.rotate(180)

    def rotate(self, degrees):
        """Shift hue by a number of degrees from 0 to 360."""
        return hsv(self).rotate(degrees)

class hsv:
    """A colour with hue, saturation, value components in [0.0, 1.0]."""

    def __init__(self, *args):
        """Construct a colour.  Give a single argument from 0.0 to 1.0 to get
        a pure hue; give a single colour argument; or give three arguments
        containing hue, saturation, value components from 0.0 to 1.0.  A hue
        of 0 is red; a hue of 1/3 is green; a hue of 2/3 is blue."""
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, float):
                self.hue, self.sat, self.value = arg, 1.0, 1.0
            elif isinstance(arg, rgb):
                self.hue, self.sat, self.value = arg.hsv()
            elif isinstance(arg, hsv):
                self.hue, self.sat, self.value = arg.hue, arg.sat, arg.value
            else:
                raise TypeError, 'hsv() argument should be float or colour'
        elif len(args) == 3:
            self.hue, self.sat, self.value = args
            self.hue = self.hue % 1.0
        else:
            raise TypeError, 'hsv() needs 1 arg or 3 args'

    def __repr__(self):
        return 'hsv(%f, %f, %f)' % (self.hue, self.sat, self.value)

    def __str__(self):
        return str(rgb(self))

    def __add__(self, other):
        """Add this colour to another colour (Photoshop 'screen').
        The result will always be lighter than each input.  Adding
        white to any colour gives white."""
        return rgb(self) + other

    def __radd__(self, other):
        if isinstance(other, str):
            return other + str(self)
        raise TypeError, 'colour cannot be added to %r' % other

    def __sub__(self, other):
        """Add this colour to the inverse of another colour."""
        return rgb(self) - other

    def __neg__(self):
        """Get the inverse of this colour."""
        return -rgb(self)

    def __mul__(self, other):
        """Filter this colour through another colour (Photoshop 'multiply').
        The result will always be darker than each input.  Multiplying
        black by any colour gives black."""
        return rgb(self) * other

    def rgb(self):
        """Convert to red, green, blue components."""
        return hsv_to_rgb(self.hue, self.sat, self.value)

    def hsv(self):
        """Convert to hue, saturation, value components."""
        return self.hue, self.sat, self.value

    def blend(self, other, factor=0.5):
        """Blend this colour with a target colour to get something in between.
        If the factor is 0, result is exactly the original colour; if the
        factor is 1, the result is exactly the target colour."""
        return rgb(self).blend(other, factor)

    def saturate(self, factor=0.5):
        """Saturate by a factor from 0 (no effect) to 1 (pure colour)."""
        return hsv(self.hue, self.sat + (1.0 - self.sat)*factor, self.value)

    def desaturate(self, factor=0.5):
        """Desaturate by a factor from 0 (no effect) to 1 (greyscale)."""
        return hsv(self.hue, self.sat * (1.0 - factor), self.value)

    def lighten(self, factor=0.5):
        """Lighten by a factor from 0 (no effect) to 1 (pure white)."""
        return self.blend(white, factor)

    def brighten(self, factor=0.5):
        """Brighten by a factor from 0 (no effect) to 1 (maximum intensity)."""
        return hsv(self.hue, self.sat, self.value + (1.0 - self.value)*factor)

    def darken(self, factor=0.5):
        """Darken by a factor from 0 (no effect) to 1 (pure black)."""
        return hsv(self.hue, self.sat, self.value * (1.0 - factor))

    def complement(self):
        """Get the complement of this colour."""
        return self.rotate(180)

    def rotate(self, degrees):
        """Shift hue by a number of degrees from 0 to 360."""
        return hsv(self.hue + degrees/360.0, sat, value)

def dsv(degrees, sat, value):
    """Construct a colour from a hue given in degrees, saturation, and value.
    A hue of 0 degrees is red, 120 degrees is green, 240 degrees is blue."""
    return hsv(degrees/360.0, sat, value)

# ---------------------------------------------------------- handy constants
white = rgb(1, 1, 1)
grey = rgb(0.5)
black = rgb(0, 0, 0)
red = rgb(1, 0, 0)
orange = rgb(1, 0.5, 0)
yellow = rgb(1, 1, 0)
green = rgb(0, 1, 0)
cyan = rgb(0, 1, 1)
blue = rgb(0, 0, 1)
magenta = rgb(1, 0, 1)

def light(colour, factor=0.5): return colour.lighten(factor)
def dark(colour, factor=0.5): return colour.darken(factor)

sans = 'lucida grande, arial, sans-serif'
serif = 'times new roman, times roman, serif'
bold = 'bold'
italic = 'italic'
