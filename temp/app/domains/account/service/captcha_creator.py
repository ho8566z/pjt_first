# ===========================================================================
# ===========================================================================
# 캡차 보안 크리에이터 모듈(captcha_creator)
# ===========================================================================
# ===========================================================================



from app.utils.captcha_util import generate_captcha_text, create_captcha_image
from flask import session


def make_captcha():
    text = generate_captcha_text()

    session["captcha"] = text   # ← 여기서만 session 사용

    create_captcha_image(text)