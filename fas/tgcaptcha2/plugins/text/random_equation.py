
import random
from turbogears import config

plugin_name = 'tgcaptcha2.plugin.random_equation.'
range_start = int(config.get(plugin_name + 'range_start', 0))
range_end = int(config.get(plugin_name + 'range_end', 100))

def generate_text():
    "Generate two random numbers to display as the captcha text."
    first = random.randint(range_start, range_end)
    second = random.randint(range_start, range_end)
    return (first, second)
