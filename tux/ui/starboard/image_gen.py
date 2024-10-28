from datetime import datetime
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from loguru import logger
from PIL import Image, ImageDraw, ImageFont


def generate_discord_message_image(
    nickname: str,
    pfp_url: str,
    role_color: str,
    message_content: str,
    image_attachment_url: str | None = None,
) -> Image.Image:
    # 1. Fetch profile picture (if needed) using pfp_url
    pfp_image = fetch_profile_picture(pfp_url)

    # 2. Create background image with dynamic height
    background_image = create_background_image(message_content)

    # 3. Place profile picture, nickname, and timestamp on the background
    # Add a thin border around the profile picture
    background_image.paste(pfp_image, (20, 20), pfp_image)

    draw: ImageDraw.ImageDraw = ImageDraw.Draw(background_image)
    name_font = get_font(30)
    timestamp_font = get_font(20)

    # Calculate vertical position to center nickname with profile picture
    nickname_bbox = draw.textbbox((0, 0), nickname, font=name_font)  # type: ignore
    nickname_height = nickname_bbox[3] - nickname_bbox[1]
    nickname_y = 20 + (64 - nickname_height) // 2 - 5

    draw.text((100, nickname_y), nickname, font=name_font, fill=role_color)  # type: ignore

    # Add timestamp with more specific format
    timestamp = datetime.now(ZoneInfo("America/New_York")).strftime("Today at %I:%M %p")  # Format: Today at HH:MM AM/PM
    timestamp_x = 100 + nickname_bbox[2] - nickname_bbox[0] + 10  # 10 pixels space after the name
    draw.text(  # type: ignore
        (timestamp_x, nickname_y + 8),
        timestamp,
        font=timestamp_font,
        fill="#72767d",
    )  # Discord's timestamp color

    # 4. Add message content, handling formatting
    return add_message_content(background_image, message_content)


def add_message_content(background_image: Image.Image, message_content: str) -> Image.Image:
    font = get_font(24)
    bold_font = get_font(24, bold=True)

    x, y = 20, 100  # Starting position with some padding
    padding = 20  # Padding for all sides
    max_width = background_image.width - 2 * padding

    # Create a new image with the correct size to fit the text
    new_height = y + calculate_text_height(message_content, font, max_width) + padding
    new_image = Image.new("RGB", (background_image.width, new_height), "#424549")

    # Paste the original background onto the new image
    new_image.paste(background_image, (0, 0))

    # Draw the text on the new image
    new_draw = ImageDraw.Draw(new_image)
    draw_formatted_text(new_draw, message_content, (x, y), font, bold_font, max_width)

    return new_image


def calculate_text_height(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> int:
    lines: list[str] = []
    current_line: list[str] = []
    current_width = 0
    for word in text.split():
        word_width, _ = font.getbbox(word)[2:4]
        if current_width + word_width <= max_width:
            current_line.append(word)
            current_width += word_width + font.getbbox(" ")[2]
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_width

    if current_line:
        lines.append(" ".join(current_line))

    return len(lines) * (40)


def draw_formatted_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    position: tuple[int, int],
    font: ImageFont.FreeTypeFont,
    bold_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> None:
    x, y = position
    current_x = x
    current_y = y
    bold = False

    words = text.split()
    i = 0
    while i < len(words):
        word = words[i]
        if word == "**":
            bold = not bold
            i += 1
            continue
        current_font = bold_font if bold else font
        word_bbox = current_font.getbbox(word)
        word_width, word_height = word_bbox[2] - word_bbox[0], word_bbox[3] - word_bbox[1]

        if current_x + word_width > x + max_width:
            current_x = x
            current_y += word_height + 4  # Add a small gap between lines
        draw.text((current_x, current_y), word, font=current_font, fill="white")  # type: ignore
        space_width = current_font.getbbox(" ")[2] - current_font.getbbox(" ")[0]
        current_x += word_width + space_width
        i += 1


def fetch_profile_picture(pfp_url: str) -> Image.Image:
    """
    Fetches the profile picture from the provided URL and returns it as a PIL Image object.
    The image is resized to a smaller, consistent size and made circular like a Discord avatar.

    Args:
        pfp_url (str): The URL of the profile picture.

    Returns:
        PIL.Image: The profile picture as a circular PIL Image object.
    """

    try:
        response = httpx.get(pfp_url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
    except httpx.HTTPError as e:
        logger.error(f"Error fetching profile picture: {e}")
        img = Image.open(Path(__file__).parent / "assets" / "default_pfp.png")

    img = img.resize((64, 64), Image.Resampling.LANCZOS)

    mask = Image.new("L", (64, 64), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, 64, 64), fill=255)

    output = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)

    return output


def create_background_image(message_content: str) -> Image.Image:
    """
    Creates a background image with the Discord color and dynamic height based on content.

    Args:
        message_content (str): The message content to determine the height.

    Returns:
        PIL.Image: The background image.
    """
    font = get_font(24)
    width = 1000
    padding = 20
    max_width = width - 2 * padding
    estimated_height = 100 + calculate_text_height(message_content, font, max_width) + 40
    return Image.new("RGB", (width, int(estimated_height)), "#282b30")


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """
    Attempts to load a font suitable for Discord-like messages.
    Falls back to default font if specific fonts are not available.

    Args:
        size (int): The font size to use.
        bold (bool): Whether to use a bold font.

    Returns:
        ImageFont.FreeTypeFont: The loaded font.
    """
    try:
        return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
        except OSError:  # noqa: TRY203
            raise
