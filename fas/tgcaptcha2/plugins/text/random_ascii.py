import random
from turbogears import config

plugin_name = 'tgcaptcha2.plugin.random_ascii.'
valid_chars = config.get(plugin_name + 'valid_chars',
    'BCDEFGHJKLMNPQRTUVWXYacdefhijkmnprstuvwxyz378')
num_chars = int(config.get(plugin_name + 'num_chars', 5))

def generate_text():
    "Generate a random string to display as the captcha text."
    s = []
    for i in range(num_chars):
        s.append(random.choice(valid_chars))
    return ''.join(s)
