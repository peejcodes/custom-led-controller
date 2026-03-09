# -------------------
# Library Imports
# -------------------
import pygame
import sys


# -------------------
# Class Imports
# -------------------
from Managers import PageManager
from Widgets import Button
from Pages import PageHome, PageModules, PageSettings, PagePalette, PagePattern, PagePresets
from Visualizer import VisualizerControls, LedVisualizer
from Leds import Controller
from Variables import SCALE, SCREEN_WIDTH, SCREEN_HEIGHT, BASE_WIDTH, BASE_HEIGHT, background_image




# -------------------
# CONFIG
# -------------------
SCALE = 1# <-- Global scale multiplier; increase/decrease to resize the entire UI
BASE_WIDTH = 1024  # Base resolution width before scaling
BASE_HEIGHT = 600  # Base resolution height before scaling

# Apply scaling to get the actual screen resolution
SCREEN_WIDTH = int(BASE_WIDTH*SCALE)
SCREEN_HEIGHT = int(BASE_HEIGHT*SCALE)

# Background ["black_fade", "carbon_fiber", "metal", "pattern1", "pattern2", "pattern4", "pattern5",
# "pattern7", "pattern9","pattern10", "pattern11", "pattern12", "pattern13", "pattern15", "pattern16"
background_image =  "pattern15"

# -----------------------------
# Helper: create shared sidebar
# -----------------------------
def create_sidebar_buttons(manager, font):
    # Create buttons that change the manager's current page
    btns = []
    names = [("home", "Home"), ("palette", "Palette"), ("pattern", "Pattern"),
             ("modules", "Modules"), ("presets", "Presets"), ("settings", "Settings")]
    for i, (page_name, label) in enumerate(names):
        rect = (0, (i * 0.166666*BASE_HEIGHT)*SCALE, 0.15*BASE_WIDTH*SCALE, 0.166666*BASE_HEIGHT*SCALE)
        # Use lambda with default arg to capture page_name
        btn = Button(rect=rect, text=label, font=font,
                     command=(lambda name=page_name: manager.set_page(name)), border_radius=0)
        btns.append(btn)
    return btns


# -----------------------------
# MAIN UI
# -----------------------------
def main_ui():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("UI + LED Visualizer")

    font = pygame.font.SysFont("Arial", 24)

    manager = PageManager()
    sidebar = create_sidebar_buttons(manager, font)

    # Add pages
    pages = [
        PageHome(manager, font),
        PagePalette(manager, font),
        PagePattern(manager, font),
        PageModules(manager, font),
        PagePresets(manager, font),
        PageSettings(manager, font),
    ]

    for p in pages:
        p.sidebar = sidebar
        manager.add_page(p)

    # Global LED visualizer + controls
    visualizer = LedVisualizer(screen)
    visualizer_controls = VisualizerControls(font, visualizer, manager)
    main_controller()
    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Modal: if a color picker is open, it gets exclusive input
            if manager.active_color_picker:
                manager.active_color_picker.handle_event(event)
            else:
                manager.handle_event(event)
                visualizer_controls.handle_event(event)

        # Update
        if manager.active_color_picker:
            manager.active_color_picker.update()
        else:
            manager.update(dt)
            visualizer_controls.update(dt)

            elapsed_time = pygame.time.get_ticks() / 1000.0
            pattern_func = getattr(visualizer, f"pattern_{visualizer.pattern}", None)
            if pattern_func:
                pattern_func(elapsed_time)

        # Draw
        screen.fill((30, 30, 30))
        manager.draw(screen)
        visualizer.draw_leds()
        visualizer_controls.draw(screen)

        # Draw modal picker last (on top of everything else)
        if manager.active_color_picker:
            # Optional dimming layer behind picker
            dim_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dim_surface.fill((0, 0, 0, 120))  # translucent black
            screen.blit(dim_surface, (0, 0))
            manager.active_color_picker.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# -----------------------------
# MAIN UI
# -----------------------------
def main_controller():

    controller = Controller()

    # Add two strips
    strip1 = controller.add_strip(15, 1000)
    strip2 = controller.add_strip(10, 500)

    print()
    controller.print_status()
    print()

    # Set global brightness to 50%
    controller.set_global_brightness(0.5)

    print()
    controller.print_status()
    print()

    # Set all LEDs to blue
    controller.set_all_color(0, 0, 255)

    # Change just one LED to red
    controller.set_led(strip_index=0, led_index=2, r=255, g=0, b=0)

    # Print current status
    controller.print_status()




if __name__ == "__main__":
    main_ui()
    main_controller()
