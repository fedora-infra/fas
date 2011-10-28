""" Captcha

Classes to implement a Captcha system in TurboGears

(c) 2006 jonathan vanasco <jvanasco@gmail.com>

Based in part on 
    "PyCAPTCHA Package Copyright (C) 2004 Micah Dowty <micah@navi.cx>" 
        *   _PyCaptcha_ prefaced classes are directly from that library (with a 
            few naming adjustments)
        *   other items are influenced by it, including the 'layering' idea.  
        Full Resource - http://svn.navi.cx/misc/trunk/pycaptcha/
    "Human verification test (captcha) by Robert McDermott 2005/09/21"
        Full Resource - http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/440588 
        
Licensing:

Copyright (c) 2006 Jonathan Vanasco

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to 
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do 
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.

The PyCaptcha Sections have licensing as follows:

Copyright (c) 2004 Micah Dowty

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to 
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do 
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.

"""

try:
    from hashlib import md5 as md5_constructor
except ImportError:
    from md5 import new as md5_constructor
import random
import math 
import os
import time

import Image
import ImageFont
import ImageDraw
import ImageFilter

captcha__site_secret = ";lkjsadfiqwrmbasfyuvb"
captcha__font_range = (30,45)
captcha__text_length = 6
captcha__img_width = 300
captcha__img_height = 100
captcha__img_color_bg = "#DDDDDD"
captcha__img_color_fg = 'RANDOM'
captcha__expiry_time = 300
captcha__future_expiry_time = 30

data_dir = os.path.join( os.path.split(os.path.abspath(__file__))[0], "captcha_data" )
captcha__img_expired__text = """IMAGE EXPIRED"""
captcha__img_expired__font = os.path.join( data_dir , 'fonts','vera','VeraBd.ttf')
captcha__img_expired__fontsize = 14

captcha__text__render_mode = 'by_letter' # ( by_letter | whole_word )

font__paths = []
# _font_path = os.path.join(data_dir, 'fonts')
# for item in os.listdir(_font_path):
#     if item == '.svn':
#         continue
#     item_path = os.path.join(_font_path,item)
#     if os.path.isdir(item_path):
#         for _font in os.listdir(item_path):
#             if _font.endswith('.ttf'):
#                 font__paths.append( os.path.join(item_path,_font) )

class _ErrorLoggingObject(object):
    def get_error( self , function ):
        if function not in self._errors:
            return None
        return self._errors[function]
    
    def set_error( self , function , error ):
        self._errors[function] = error

class _Captcha(_ErrorLoggingObject) :
    """Captcha implementation for TurboGears"""
    def __init__( self  , captcha_seed=None ):
        """initialize the captcha"""
        self.captcha_text = None
        self.captcha_seed = captcha_seed
        self._errors = {}
    
    def generate_key(self):
        """Generates a key that can be used to ( generate a captcha ) or ( validate a captcha )"""
        self.captcha_time_start = int(time.time())
        self.captcha_key = self._generate_key( captcha_time_start=self.captcha_time_start , captcha_seed=self.captcha_seed )
        self._captcha_key__combine()

    def _generate_key( self , captcha_time_start=None , captcha_seed=None ):
        """Returns a hash based on text , seed , and site_secrect"""
        return md5_constructor("%s|%s|%s" %(captcha__site_secret,captcha_time_start,captcha_seed)).hexdigest()

    def generate_captcha_text(self):
        """Automagically generates a string of text based on a key (length is from file default or override)"""
        return ''.join(md5_constructor("%s|%s|%s" %(captcha__site_secret,self.captcha_key,self.captcha_time_start)).hexdigest()[0:6])

    def _captcha_key__uncombine( self ):
        ( self.captcha_key , self.captcha_time_start ) = self.captcha_key_combined.split('_')
        self.captcha_time_start = int(self.captcha_time_start)

    def _captcha_key__combine( self ):
        self.captcha_key_combined = '_'.join( [ self.captcha_key , "%s"%self.captcha_time_start ] )



class CaptchaNew( _Captcha ):
    def __init__( self , captcha_seed=None , text_length=captcha__text_length ):
        _Captcha.__init__( self , captcha_seed=None )


class CaptchaExisting( _Captcha ):
    def __init__( self , captcha_seed=None , captcha_key_combined=None , img_width=captcha__img_width , img_height=captcha__img_height , img_color_bg=captcha__img_color_bg , img_color_fg=captcha__img_color_fg ):
        _Captcha.__init__( self , captcha_seed=None )
        if captcha_key_combined is None:
            raise ValueError( "captcha_key_combined must be 'key_timestart'")
        self.captcha_key_combined = captcha_key_combined
        self._captcha_key__uncombine()
        self.img_width = img_width
        self.img_height = img_height
        self.img_color_bg = img_color_bg
        self.img_color_fg = img_color_fg
        self.time_now = int(time.time())

    def is_timely( self ):
    
        # is the captcha too old?
        if self.time_now > ( self.captcha_time_start + captcha__expiry_time) :
            self.set_error('is_timely','EXPIRED captcha time')
            return 0

        # is the captcha too new?
        if self.captcha_time_start > ( self.time_now + captcha__future_expiry_time ) :
            self.set_error('is_timely','FUTURE captcha time')
            return 0

        return 1

    def validate( self , user_text=None ):
        """Validates a text against the key/time"""
        
        self.success = False
        
        if not self.is_timely() :
            self.set_error('validate',self.get_error('is_timely'))
            return 0
        
        if user_text == self.generate_captcha_text():
            self.success = True
            return 1

        self.set_error('validate',"INVALID user_text")
        return 0


    def generate_image( self ):
        """Generate a captcha image"""
        
        
        t_start = time.time()
        
        captcha_text = self.captcha_text
        if captcha_text is None:  
            captcha_text = self.generate_captcha_text()

        img_color_bg = self.img_color_bg
        img_color_fg = self.img_color_fg
        if img_color_fg == 'RANDOM':
            img_color_fg = random.choice(["#330000","#660000","#003300","#006600","#000033","#000066"])

        img = None
        if not self.is_timely() :
            img = _Captcha__ImgExpired( width=self.img_width , height=self.img_height , color_bg=img_color_bg )
        else:
           img = _Captcha__Img( 
                text = captcha_text,
                width=self.img_width,
                height=self.img_height,
                font_size = random.randint(captcha__font_range[0],captcha__font_range[1]),
                color_fg = img_color_fg,
                color_bg = img_color_bg
            )
        img.render()
        #print "Time To Render: %s " % ( time.time() - t_start )
        self.img = img
        return self

    def render_img( self ):
        return self.img.getImg().tostring( "jpeg" , "RGB" )

    def save(self):
        self.img.getImg().save('b.jpg')
        return True


class _Captcha__ImgExpired:
    def __init__( self, width=captcha__img_width , height=captcha__img_height , color_bg="#FFFFFF"):
        self.width = width
        self.height = height
        self.color_bg = color_bg
        self.color_fg = "#000000"

    def getImg(self):
        """Get a PIL image representing this IMG test, creating it if necessary"""
        if not self._image:
            self._image = self.render()
        return self._image

    def render(self):
        """Render this CAPTCHA, returning a PIL image"""
        size = (self.width,self.height)
        img = Image.new("RGB", size )
        
        #first the bg
        img.paste( self.color_bg )

        #then the text
        font = ImageFont.truetype( captcha__img_expired__font , captcha__img_expired__fontsize )
        text_dimensions = font.getsize(captcha__img_expired__text)

        draw = ImageDraw.Draw(img)
        draw.text( 
            (
                ((self.width - text_dimensions[0])/2) ,
                ((self.height - text_dimensions[1])/2) 
            ) , 
            captcha__img_expired__text, font=font, fill=self.color_fg
        )
        self._image = img
        return self._image
        
        
class _Captcha__Img:
    def __init__( self, text="Error! No Text Supplied" , width=captcha__img_width , height=captcha__img_height , font_size = random.randint(captcha__font_range[0],captcha__font_range[1]) , color_fg="#000000" , color_bg="#FFFFFF"):
        self.text = text
        self.width = width
        self.height = height
        self.font_size = font_size
        self.color_fg = color_fg
        self.color_bg = color_bg
        self._layers = [
            _Captcha__bg( color=self.color_bg ),
            _Captcha__Img__text( text=self.text , font_size=self.font_size, color=self.color_fg , canvas_width=width , canvas_height=height),
            _Captcha__Img__lines(color=self.color_fg , canvas_width=width , canvas_height=height),
            _PyCaptcha_SineWarp(amplitudeRange = (4, 8) , periodRange=(0.65,0.73) ),
        ]
        
    def getImg(self):
        """Get a PIL image representing this CAPTCHA test, creating it if necessary"""
        if not self._image:
            self._image = self.render()
        return self._image

    def render(self):
        """Render this CAPTCHA, returning a PIL image"""
        size = (self.width,self.height)
        img = Image.new("RGB", size )
        for layer in self._layers:
            img = layer.render( img ) or img
        self._image = img
        return self._image
        


class _Captcha__bg( _Captcha__Img ):
    """BG class for image CAPTCHA tests."""
    def __init__(self, color="#ffffff"):
        self.color = color

    def render(self, image ):
        # lt grey bg - just a design choice
        image.paste( self.color )

class _Captcha__Img__text( _Captcha__Img ):
    """Text class for image CAPTCHA tests."""
    def __init__( self , text="Error! No Text Supplied" , font_size=10, color="#000000" , canvas_width=captcha__img_width , canvas_height=captcha__img_height):
        self.text = text
        self.font_size = font_size
        self.color = color
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

    def render( self , img ):
        if captcha__text__render_mode == 'by_letter':
            self.render__by_letter( img )
        else:
            self.render__whole_word( img )

    def render__by_letter(self, img):
        """Renders text onto the img"""
        # pick a random font and size it, then x1.5 in case its small
        font = ImageFont.truetype(  *_PyCaptcha_FontFactory().pick() )
        text_dimensions = [ int(1.2 * i) for i in font.getsize(self.text) ]
        letter_width = text_dimensions[0] / len(self.text)
        
        startX = int( random.randint(5,(self.canvas_width - text_dimensions[0]-5)) )
        startY = int( random.randint(5,(self.canvas_height - text_dimensions[1]-5)) )

        draw = ImageDraw.Draw(img)
        for letter_index in range( 0 , len(self.text)):
            draw.text( 
                (
                    (startX + (letter_index * letter_width )),
                    (startY + ( random.randint(-10,10) )),
                ),
                self.text[letter_index],
                font = ImageFont.truetype(  *_PyCaptcha_FontFactory().pick() ),
                fill = self.color
            )
        
        
    def render__whole_word(self, img):
        """Renders text onto the img"""
        font = ImageFont.truetype(  *_PyCaptcha_FontFactory().pick() )
        text_dimensions = font.getsize(self.text)

        draw = ImageDraw.Draw(img)

        r = random.randint
        draw.text( 
            (
                r(5,(self.canvas_width - text_dimensions[0]-5)) , 
                r(5,(self.canvas_height - text_dimensions[1]-5)) 
            ), 
            self.text, font=font, fill=self.color
        )

class _Captcha__Img__lines( _Captcha__Img ):
    def __init__( self , color="#000000" , canvas_width=captcha__img_width , canvas_height=captcha__img_height):
        self.color = color
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

    def render(self, img):
        """Renders lines onto the img"""

        draw = ImageDraw.Draw(img)

        # some sweeping arcs
        for i in range( 1 , random.randint(1,4) ):
            ( a1 , a2 ) = ( random.randint(0,360) , random.randint(0,360) )
            ( bbox1 , bbox2 , bbox3 , bbox4 ) = (
                random.randint((2*-self.canvas_width),self.canvas_width),
                random.randint((2*-self.canvas_height),self.canvas_height),
                random.randint((.5*self.canvas_width),(2*self.canvas_width)),
                random.randint((.5*self.canvas_height),(2*self.canvas_height))
            )
            draw.arc( ( bbox1 , bbox2 , bbox3 , bbox4 ) , a1 , a2,fill=self.color) 
            #randomly we'll draw some lines thicker.  this is accomplished by shifting the bounding box a bit in each direction
            if random.randint(0,100) > 50:
                #draw.arc( ( bbox1+1 , bbox2+1 , bbox3 , bbox4 ) , a1 , a2,fill=self.color) 
                #draw.arc( ( bbox1 , bbox2 , bbox3-1 , bbox4-1 ) , a1 , a2,fill=self.color) 
                # random.randint is out thickness
                for i in range (1 , random.randint(2,3) ):
                    draw.arc( ( bbox1+i , bbox2+i , bbox3 , bbox4 ) , a1 , a2,fill=self.color) 
                    draw.arc( ( bbox1 , bbox2 , bbox3+i , bbox4+i ) , a1 , a2,fill=self.color) 
                
        # little arcs
        for i in range( 1 , random.randint(5,15) ):
            ( a1 , a2 ) = ( random.randint(0,360) , random.randint(0,360) )
            ( bbox1 , bbox2 ) = (
                random.randint(-20,(1.25*self.canvas_width)),
                random.randint(-20,(1.25*self.canvas_height)),
            )
            ( bbox3 , bbox4 ) = (
                bbox1 + random.randint(0,40),
                bbox2 + random.randint(0,40)
            )
            draw.arc( ( bbox1 , bbox2 , bbox3 , bbox4 ) , a1 , a2,fill=self.color) 
            #randomly we'll draw some lines thicker.  this is accomplished by shifting the bounding box a bit in each direction
            if random.randint(0,100) > 50:
                #draw.arc( ( bbox1+1 , bbox2+1 , bbox3 , bbox4 ) , a1 , a2,fill=self.color) 
                #draw.arc( ( bbox1 , bbox2 , bbox3-1 , bbox4-1 ) , a1 , a2,fill=self.color) 
                # random.randint is out thickness
                for i in range (1 , random.randint(2,3) ):
                    draw.arc( ( bbox1+i , bbox2 , bbox3+i , bbox4 ) , a1 , a2,fill=self.color) 
                    draw.arc( ( bbox1-i , bbox2 , bbox3-i , bbox4 ) , a1 , a2,fill=self.color) 
         
        # and a few lines
        for i in range( 1 , random.randint(5,15) ):
            ( bbox1 , bbox2 ) = (
                random.randint(-20,(1.25*self.canvas_width)),
                random.randint(-20,(1.25*self.canvas_height)),
            )
            ( bbox3 , bbox4 ) = (
                bbox1 + random.randint(0,40),
                bbox2 + random.randint(0,40)
            )
            draw.line( ( bbox1 , bbox2 , bbox3 , bbox4 ) ,fill=self.color) 
            #randomly we'll draw some lines thicker.  this is accomplished by shifting the bounding box a bit in each direction
            if random.randint(0,100) > 50:
                for i in range (1 , random.randint(3,6) ):
                    draw.line( ( bbox1+i , bbox2+i , bbox3 , bbox4 ) , fill=self.color) 
                    draw.line( ( bbox1 , bbox2 , bbox3+i , bbox4+i ) , fill=self.color) 


class _PyCaptcha_WarpBase(object):
    """Abstract base class for image warping. Subclasses define a
       function that maps points in the output image to points in the input image.
       This warping engine runs a grid of points through this transform and uses
       PIL's mesh transform to warp the image.
       """
    filtering = Image.BILINEAR
    resolution = 10

    def get_transform(self, image):
        """Return a transformation function, subclasses should override this"""
        return lambda x, y: (x, y)

    def render(self, image):
        r = self.resolution
        xPoints = image.size[0] / r + 2
        yPoints = image.size[1] / r + 2
        f = self.get_transform(image)

        # Create a list of arrays with transformed points
        xRows = []
        yRows = []
        for j in xrange(yPoints):
            xRow = []
            yRow = []
            for i in xrange(xPoints):
                x, y = f(i*r, j*r)

                # Clamp the edges so we don't get black undefined areas
                x = max(0, min(image.size[0]-1, x))
                y = max(0, min(image.size[1]-1, y))

                xRow.append(x)
                yRow.append(y)
            xRows.append(xRow)
            yRows.append(yRow)

        # Create the mesh list, with a transformation for
        # each square between points on the grid
        mesh = []
        for j in xrange(yPoints-1):
            for i in xrange(xPoints-1):
                mesh.append((
                    # Destination rectangle
                    (i*r, j*r,
                     (i+1)*r, (j+1)*r),
                    # Source quadrilateral
                    (xRows[j  ][i  ], yRows[j  ][i  ],
                     xRows[j+1][i  ], yRows[j+1][i  ],
                     xRows[j+1][i+1], yRows[j+1][i+1],
                     xRows[j  ][i+1], yRows[j  ][i+1]),
                    ))

        return image.transform(image.size, Image.MESH, mesh, self.filtering)


class _PyCaptcha_SineWarp(_PyCaptcha_WarpBase):
    """Warp the image using a random composition of sine waves"""

    def __init__(self,
                 amplitudeRange = (4, 20),
                 periodRange    = (0.65, 0.74),
                 ):
        self.amplitude = random.uniform(*amplitudeRange)
        self.period = random.uniform(*periodRange)
        self.offset = (random.uniform(0, math.pi * 2 / self.period),
                       random.uniform(0, math.pi * 2 / self.period))
                       
    def get_transform(self, image):
        return (lambda x, y,
                a = self.amplitude,
                p = self.period,
                o = self.offset:
                (math.sin( (y+o[0])*p )*a + x,
                 math.sin( (x+o[1])*p )*a + y))    

class _PyCaptcha_FontFactory(object):
    """Picks random fonts and/or sizes from a given list.
       'sizes' can be a single size or a (min,max) tuple.
       If any of the given files are directories, all *.ttf found
       in that directory will be added.
       """

    def _pick_file(self):
        try:
            return random.choice(font__paths)
        except:
            return captcha__img_expired__font

    def pick(self):
        """Returns a (fileName, size) tuple that can be passed to ImageFont.truetype()"""
        fileName = self._pick_file()
        size = int(random.uniform(captcha__font_range[0], captcha__font_range[1]) + 0.5)
        return (fileName, size)
