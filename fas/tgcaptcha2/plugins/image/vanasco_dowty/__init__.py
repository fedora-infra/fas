import captcha
from turbogears import config
import random
import os.path
from pkg_resources import resource_filename

plugin_name = 'fas.tgcaptcha2.plugin.vanasco_dowty.'

width = int(config.get(plugin_name + 'width', 300))
height = int(config.get(plugin_name + 'height', 100))
bg_color = config.get(plugin_name + 'bg_color', '#DDDDDD')
fg_color = config.get(plugin_name + 'fg_color',
            ["#330000","#660000","#003300","#006600","#000033","#000066"])
font_size_min = int(config.get(plugin_name + 'font_size_min', 30))
font_size_max = int(config.get(plugin_name + 'font_size_max', 45))
font_paths = config.get(plugin_name + 'font_paths',
        [os.path.normpath('/usr/share/fonts/tulrich-tuffy/Tuffy.ttf')])

captcha.font__paths = font_paths
captcha.captcha__text__render_mode = config.get(plugin_name +
        'text_render_mode', 'by_letter')
captcha.captcha__font_range = (font_size_min, font_size_max)


def generate_jpeg(text, file_):
    font_size = random.randint(font_size_min, font_size_max)
    fg = random.choice(fg_color)
    ci = captcha._Captcha__Img(text, width, height, font_size, fg, bg_color)
    image = ci.render()
    image.save(file_, format='JPEG')
