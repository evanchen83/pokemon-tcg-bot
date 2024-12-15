import pathlib
import random

import cv2
import pydash


def overlay_transparent(background, overlay, x, y):
    # Extract dimensions
    bg_h, bg_w, _ = background.shape
    ol_h, ol_w, ol_channels = overlay.shape

    # Ensure overlay has an alpha channel
    if ol_channels < 4:
        raise ValueError("Overlay image must have an alpha channel")

    # Calculate regions of interest (ROI)
    x1, x2 = max(0, x), min(bg_w, x + ol_w)
    y1, y2 = max(0, y), min(bg_h, y + ol_h)

    ol_x1, ol_x2 = max(0, -x), min(ol_w, bg_w - x)
    ol_y1, ol_y2 = max(0, -y), min(ol_h, bg_h - y)

    # Extract alpha channel and normalize it
    alpha = overlay[ol_y1:ol_y2, ol_x1:ol_x2, 3] / 255.0

    # Blend the overlay into the background
    for c in range(3):  # Blend each color channel
        background[y1:y2, x1:x2, c] = (
            alpha * overlay[ol_y1:ol_y2, ol_x1:ol_x2, c]
            + (1 - alpha) * background[y1:y2, x1:x2, c]
        )

    return background


def _overlay_box_index(box_index: int, box: cv2.typing.MatLike) -> cv2.typing.MatLike:
    # Define the text and properties
    text = f"Box: {box_index}"
    position = (90, 20)  # Bottom-left corner of the text
    font = cv2.FONT_HERSHEY_SIMPLEX  # Font type
    font_scale = 0.4  # Font scale (size)
    color = (255, 255, 255)  # White color in BGR
    thickness = 1  # Thickness of the text

    # Add text to the image
    cv2.putText(box, text, position, font, font_scale, color, thickness, cv2.LINE_AA)
    return box


def make_pokemon_box(pokemon_names: list[str], box_index: int) -> cv2.typing.MatLike:
    box = cv2.imread(
        "/Users/evan/Downloads/workspace/pokemon-tcg-bot/.data/storage-bg.png",
        cv2.IMREAD_UNCHANGED,
    )
    box = _overlay_box_index(box_index, box)

    sprite_width = 36
    x, y = int(-sprite_width * 0.25), sprite_width // 2
    i = 0
    for pokemon_name in pokemon_names:
        overlay = cv2.imread(
            f"/Users/evan/Downloads/workspace/pokemon-tcg-bot/.data/pokemon-sprites/regular/{pokemon_name}.png",
            cv2.IMREAD_UNCHANGED,
        )

        box = overlay_transparent(box, overlay, x, y)
        x += sprite_width
        if x >= sprite_width * 5:
            x = int(-sprite_width * 0.25)
            y += int(sprite_width * 0.9)
            i += 1

    return box


pokemon_names = []
for p in pathlib.Path(
    "/Users/evan/Downloads/workspace/pokemon-tcg-bot/.data/pokemon-sprites/regular"
).rglob("*.png"):
    pokemon_names.append(p.stem)


pokemon_name_chunks = pydash.chunk(random.choices(pokemon_names, k=200), 30)

for box_index, pokemon_names in enumerate(pokemon_name_chunks):
    box = make_pokemon_box(pokemon_names, box_index)
    cv2.imwrite(f"box_{box_index}.jpeg", box)
