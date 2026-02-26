"""
Docstring for backend.gateway.util.captcha
@Description: Generate and verify CAPTCHA images 
"""

from PIL import Image, ImageDraw, ImageFont
from random import randint, choices
from time import time

# Constants
CAPTCHA_LENGTH = 5
CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
IMAGE_WIDTH, IMAGE_HEIGHT = 150, 40
FONT_SIZE = 25
COLOR_MIN, COLOR_MAX = 150, 235
INTERFERENCE_LINES = 10
NOISE_POINTS = 150
NOISE_CIRCLES = 10
CIRCLE_RADIUS_RANGE = (2, 4)
TEXT_Y_OFFSET = 5


def _random_color():
    """Generate a random RGB color tuple."""
    return (
        randint(COLOR_MIN, COLOR_MAX),
        randint(COLOR_MIN, COLOR_MAX),
        randint(COLOR_MIN, COLOR_MAX),
    )


def _generate_captcha_text(length=CAPTCHA_LENGTH):
    """Generate random CAPTCHA text."""
    return ''.join(choices(CHARSET, k=length))


def generate_captcha():
    """Generate a CAPTCHA with unique ID, text, and image."""
    captcha_id = f"{int(time() * 1000)}{randint(1000, 9999)}"
    captcha_text = _generate_captcha_text()
    captcha_image = _generate_captcha_image(captcha_text)
    return captcha_id, captcha_text, captcha_image


def _generate_captcha_image(captcha_text):
    """Generate CAPTCHA image with text and noise."""
    # Create image
    image = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=FONT_SIZE)
    
    character_length = len(captcha_text)
    char_spacing = (IMAGE_WIDTH - 5) / character_length

    # Draw captcha text
    for i, char in enumerate(captcha_text):
        x = 5 + i * char_spacing
        y = randint(-TEXT_Y_OFFSET, TEXT_Y_OFFSET)
        draw.text((x, y), text=char, font=font, fill=_random_color())

    # Add interference lines
    for _ in range(INTERFERENCE_LINES):
        start = (randint(0, IMAGE_WIDTH), randint(0, IMAGE_HEIGHT))
        end = (randint(0, IMAGE_WIDTH), randint(0, IMAGE_HEIGHT))
        draw.line([start, end], fill=_random_color(), width=1)

    # Draw noise points
    for _ in range(NOISE_POINTS):
        draw.point(
            (randint(0, IMAGE_WIDTH), randint(0, IMAGE_HEIGHT)),
            fill=_random_color(),
        )

    # Draw noise circles
    for _ in range(NOISE_CIRCLES):
        x = randint(0, IMAGE_WIDTH)
        y = randint(0, IMAGE_HEIGHT)
        radius = randint(*CIRCLE_RADIUS_RANGE)
        draw.arc(
            (x - radius, y - radius, x + radius, y + radius),
            0,
            360,
            fill=_random_color(),
        )

    return image


if __name__ == "__main__":
    captcha_id, captcha_text, captcha_image = generate_captcha()
    print(captcha_id, captcha_text)

