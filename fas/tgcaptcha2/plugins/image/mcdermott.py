import random
import Image
import ImageFont
import ImageDraw
import ImageFilter
from pkg_resources import resource_filename
import os.path
from turbogears import config

# get the font path 
font_path =  config.get('tgcaptcha.plugin.mcdermott.font_path')
if not font_path:
    font_path = os.path.abspath(
                resource_filename('tgcaptcha2', 'static/fonts/tuffy/Tuffy.ttf'))
if not os.path.exists(font_path):
    font_path = os.path.normpath('/usr/share/fonts/tulrich-tuffy/Tuffy.ttf')
assert os.path.exists(font_path), \
                'The font_path "%s" does not exist' % (font_path,)

# get the font size (default 36 pt)
font_size = int(config.get('tgcaptcha.plugin.mcdermott.font_size', 36))

# Code taken from
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/440588
# written by Robert McDermott

def generate_jpeg(text, file_obj):
    """Generate a captcha image"""
    # randomly select the foreground color
    fgcolor = random.randint(0,0xffff00)
    # make the background color the opposite of fgcolor
    bgcolor = fgcolor ^ 0xffffff
    # create a font object 
    font = ImageFont.truetype(font_path, font_size)
    # determine dimensions of the text
    dim = font.getsize(text)
    # create a new image slightly larger that the text
    im = Image.new('RGB', (dim[0]+5,dim[1]+5), bgcolor)
    d = ImageDraw.Draw(im)
    x, y = im.size
    r = random.randint
    # draw 100 random colored boxes on the background
    for num in range(100):
        d.rectangle((r(0,x),r(0,y),r(0,x),r(0,y)),fill=r(0, bgcolor ^ 0xffffff))
    # add the text to the image
    d.text((3,3), text, font=font, fill=fgcolor)
    im = im.filter(ImageFilter.EDGE_ENHANCE_MORE)
    # save the image to a file
    im.save(file_obj, format='JPEG')
