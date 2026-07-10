import random
import string
from captcha.image import ImageCaptcha
from app import configs


def generate_captcha_text():
    return "".join(
        random.choice(string.ascii_uppercase + string.digits)
        for _ in range(configs.CAPTCHA_LENGTH)
    )


def create_captcha_image(text, path="app/static/captcha.png"):
    image = ImageCaptcha()
    image.write(text, path)

    
