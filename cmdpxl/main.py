import sys
from pathlib import Path
from typing import Tuple, Union, Callable, Iterable

import click
import pygame as pg
import pygame.font

black, white, red = pg.Color(20, 20, 20), pg.Color(255, 255, 255), pg.Color(150, 0, 0)


def resize_surface_by_percentage(surface: pg.Surface, percentage: int) -> pg.Surface:
    new_image_resolution = [xy * percentage // 100 for xy in (surface.get_width(), surface.get_height())]
    return pg.transform.scale(surface, new_image_resolution)


def new_text_surface(text: str, size: int = 12, color: pg.color.Color = black):
    default_font = (Path(__file__).parent / ".." / "assets" / "fonts" / "PressStart2P-Regular.ttf").resolve()
    font = pygame.font.Font(default_font, size)
    return font.render(text, False, color, None)


def blit_text(draw: Union[str, pg.Surface], coord: Tuple[int, int]):
    surface = draw if isinstance(draw, pg.Surface) else new_text_surface(str(draw))
    pg.display.get_surface().blit(surface, coord)


def rect_screen_center(rect: pg.Rect, center_x=False, center_y=False) -> Tuple[int, int]:
    screen = pygame.display.get_surface()
    rect = rect.copy()

    if center_x:
        rect.x = screen.get_rect().centerx - rect.w // 2

    if center_y:
        rect.y = screen.get_rect().centery - rect.h // 2

    return rect.x, rect.y


def draw_welcome_msg(func):
    def wrapper():
        click.clear()
        click.echo(click.style("CMDPXL - A TOTALLY PRACTICAL IMAGE EDITOR", fg='red'))
        func()

    return wrapper


class KeyBinding:
    def __init__(self, keycode: int, description: str, func: Callable, on_pressed=False):
        self.keycode = keycode
        self.description = description
        self.func = func
        self.on_pressed = on_pressed

    def __str__(self):
        return f"(keycode={pg.key.name(self.keycode)}, description={self.description})"


def handle_input(keybindings: Iterable[KeyBinding]):
    on_pressed_bindings = set(filter(lambda k: k.on_pressed, keybindings))
    for binding in on_pressed_bindings:
        if pg.key.get_pressed()[binding.keycode]:
            binding.func()

    not_on_pressed_keybindings = set(keybindings).difference(on_pressed_bindings)
    for event in pg.event.get():
        if event.type == pg.QUIT:
            sys.exit()

        for binding in not_on_pressed_keybindings:
            if event.type == pg.KEYDOWN and event.key == binding.keycode:
                binding.func()


@draw_welcome_msg
@click.command(name="cmdpxl")
@click.option(
    "--filepath",
    "-f",
    prompt="File path",
    help="Path for the file you want to open",
    type=click.Path(),
)
@click.option(
    "--resolution",
    "-res",
    help="Image height and width separated by a comma, e.g. 20,10 for a 20x10 image. Note that no spaces can be used.",
)
def main(filepath, resolution):
    pg.init()
    screen = pg.display.set_mode((600, 600), pg.RESIZABLE)
    app_name = click.get_current_context().command.name
    pg.display.set_caption(app_name)

    path = Path(filepath)
    if path.exists() and path.is_file():
        image = pg.image.load(path)
    else:
        img_size = list(
            map(int, resolution.split(","))
            if resolution
            else map(int, (input(f"Image {x}: ") for x in ("width", "height")))
        )
        image = pg.Surface(img_size)

    cursor_rect = pg.Rect((0, 0), (0, 0))

    line_width = 6
    cursor_line_width = line_width // 4

    clock = pg.time.Clock()

    zoom = {
        "percent": 100,
        "step": 100,
        "changed": False,
    }

    def change_zoom(is_positive: bool):
        zoom["changed"] = True
        zoom["percent"] += zoom["step"] if is_positive else -zoom["step"]

    keybindings = (
        KeyBinding(pg.K_KP_PLUS, "Zoom in", lambda: change_zoom(True), on_pressed=True),
        KeyBinding(pg.K_KP_MINUS, "Zoom out", lambda: change_zoom(False), on_pressed=True),
        KeyBinding(pg.K_UP, "Move cursor up", lambda: cursor_rect.move_ip(0, -cursor_rect.w)),
        KeyBinding(pg.K_DOWN, "Move cursor down", lambda: cursor_rect.move_ip(0, cursor_rect.w)),
        KeyBinding(pg.K_RIGHT, "Move cursor right", lambda: cursor_rect.move_ip(cursor_rect.h, 0)),
        KeyBinding(pg.K_LEFT, "Move cursor left", lambda: cursor_rect.move_ip(-cursor_rect.h, 0)),
    )

    while True:
        screen.fill(black)

        # Draws header text
        header_text = f"{app_name}: {path.name} ({image.get_width()}x{image.get_height()}) {zoom['percent']}%"
        text_surface = new_text_surface(header_text, color=red)
        text_rect = rect_screen_center(text_surface.get_rect().move(0, 10), center_x=True)
        blit_text(text_surface, text_rect)

        # Draws the selected image
        resized_img = resize_surface_by_percentage(image, zoom["percent"])
        img_screen_pos = rect_screen_center(resized_img.get_rect(), center_x=True, center_y=True)
        screen.blit(resized_img, img_screen_pos)

        # Draws the rectangle around the image
        rectangle_x, rectangle_y = img_screen_pos[0] - line_width, img_screen_pos[1] - line_width
        rectangle_w, rectangle_h = resized_img.get_rect().w + line_width, resized_img.get_rect().h + line_width
        rectangle_rect = pg.Rect((rectangle_x, rectangle_y), (rectangle_w, rectangle_h))
        pg.draw.rect(screen, white, rectangle_rect, width=line_width)

        # Initializes cursor_rect value
        if cursor_rect is None or zoom["changed"]:
            zoom["changed"] = False
            cursor_rect.x, cursor_rect.y = img_screen_pos[0], img_screen_pos[1]
            cursor_rect.w, cursor_rect.h = resized_img.get_width() // image.get_width(), resized_img.get_height() // image.get_height()

        # Draws the rectangle that corresponds to the cursor
        pg.draw.rect(screen, white, cursor_rect, width=cursor_line_width)

        handle_input(keybindings)

        pg.display.flip()

        clock.tick(60)


if __name__ == "__main__":
    main()
