# -------------------
# Library Imports
# -------------------
import os
import pygame
import json

# -------------------
# Class Imports
# -------------------
from Variables import SCALE, SCREEN_WIDTH, SCREEN_HEIGHT, background_image
from Widgets import Button, Label, CircleButton, Gauge
from UI import ColorPicker



# -----------------------------
# Page
# -----------------------------
class Page:
    def __init__(self, name, manager, font, background=None):
        self.name = name
        self.manager = manager
        self.font = font
        self.widgets = []
        self.sidebar = []

        self.background_image = None

        if isinstance(background, str) and os.path.exists(background):
            img = pygame.image.load(background).convert()
            self.background_image = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            self.background_color = background if isinstance(background, tuple) else (30, 30, 30)


    def add(self, widget):
        self.widgets.append(widget)

    def draw_sidebar_background(self, screen):
        # Sidebar background
        pygame.draw.rect(screen, (40, 40, 40), (0, 0, 200, screen.get_height()))

    def draw(self, screen):
        # Draw background
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
        elif hasattr(self, "background_color"):
            screen.fill(self.background_color)
        else:
            screen.fill((30, 30, 30))  # default background

        # Draw sidebar
        for s in self.sidebar:
            s.draw(screen)

        # Draw widgets
        for w in self.widgets:
            w.draw(screen)

        # Optional border
        pygame.draw.rect(screen, (200, 200, 200), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), width=2)


    def handle_event(self, event):
        # Send events to sidebar buttons first (so they always receive clicks)
        for s in self.sidebar:
            s.handle_event(event)
        for w in self.widgets:
            w.handle_event(event)

    def update(self, dt):
        for w in self.widgets:
            if hasattr(w, "update"):
                w.update(dt)


# -----------------------------
# Helper: create shared sidebar
# -----------------------------
def create_sidebar_buttons(manager, font):
    # Create buttons that change the manager's current page
    btns = []
    pad = 0
    names = [("home", "Home"), ("palette", "Palette"), ("pattern", "Pattern"),
             ("modules", "Modules"), ("presets", "Presets"), ("settings", "Settings")]
    for i, (page_name, label) in enumerate(names):
        rect = (0, (i * 80)*SCALE, 150*SCALE, 80*SCALE)
        # Use lambda with default arg to capture page_name
        btn = Button(rect=rect, text=label, font=font,
                     command=(lambda name=page_name: manager.set_page(name)), border_radius=0)
        btns.append(btn)
    return btns


# -----------------------------
# Page Subclasses
# -----------------------------
class PageHome(Page):
    def __init__(self, manager, font):
        super().__init__("home", manager, font, background=f"assets/backgrounds/{background_image}.png")
        # add a label to show page identity
        label = Label(rect=(int(175*SCALE), int(0*SCALE), int(150*SCALE), int(80*SCALE))
, text="Home Page", bg_color=None, border_width=0, font=font)
        self.add(label)

        # Buttons
        self.buttons = [
            Button(rect=(int((175 + 55)*SCALE), int(300*SCALE), int(50*SCALE), int(40*SCALE)),
                   text="/", font=font,
                   command=None, border_radius=2),
            Button(rect=(int(670*SCALE), int(300*SCALE), int(50*SCALE), int(40*SCALE)),
                   text="+", font=font,
                   command=None, border_radius=2),
            Button(rect=(int(175*SCALE), int(300*SCALE), int(50*SCALE), int(40*SCALE)),
                   text="<", font=font,
                   command=None, border_radius=2),
            Button(rect=(int((725)*SCALE), int(300*SCALE), int(50*SCALE), int(40*SCALE)),
                   text=">", font=font,
                   command=None, border_radius=2),
        ]
        for i in range(len(self.buttons)):
            self.widgets.append(self.buttons[i])


# -----------------------------
# Page_Palette (replacement)
# -----------------------------
class PagePalette(Page):
    def __init__(self, manager, font):
        super().__init__("palette", manager, font, background=f"assets/backgrounds/{background_image}.png")
        # Label at top-left same as others
        label = Label(rect=(int(175*SCALE), int(0*SCALE), int(150*SCALE), int(80*SCALE)), text="Palette Page", bg_color=None, border_width=0, font=font)
        self.add(label)

        # load persisted slot colors
        self.palette_file = "palette.json"
        self.slots = [(200, 120), (280, 120), (360, 120)]  # centers for circle buttons (x,y)
        # adjust y to be appropriate scaled
        self.slots = [(int(x*SCALE), int(y*SCALE)) for (x,y) in self.slots]
        self.slot_radius = int(30*SCALE)

        colors = self._load_palette()

        # create slot buttons
        self.color_buttons = []
        for i in range(3):
            col = tuple(colors.get(f"slot{i+1}", [200,200,200]))
            btn = CircleButton(center=self.slots[i], radius=self.slot_radius, color=col, font=font, slot_index=i,
                               command=self.open_picker_for)
            self.color_buttons.append(btn)
            self.add(btn)

        # create a single ColorPicker instance used modally
        self.picker = ColorPicker(font, initial_color=(255,255,255))
        # Note: do NOT add picker to self.widgets; we manage it separately to ensure modal behavior

    def draw(self, screen):
        # draw page background as usual
        super().draw(screen)
        # if modal picker active, draw it last (on top)
        if self.picker.active:
            # also draw a translucent full-screen block to indicate modal
            modal = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            modal.fill((0,0,0,100))
            screen.blit(modal, (0,0))
            self.picker.draw(screen)

    def handle_event(self, event):
        # If picker is active, it gets all events exclusively
        if self.picker.active:
            self.picker.handle_event(event)
            # while active, block events to other widgets
            return
        # otherwise pass events to sidebar first and widgets (already handled by Page.handle_event)
        # but since base Page.handle_event sends events to self.sidebar and self.widgets, we can reuse
        # however we want to ensure circle buttons get the event -- they are in self.widgets already
        for s in self.sidebar:
            s.handle_event(event)
        for w in self.widgets:
            w.handle_event(event)

    def update(self, dt):
        # do not update other widgets while picker active
        if self.picker.active:
            return
        for w in self.widgets:
            if hasattr(w, "update"):
                w.update(dt)

    # open picker callback
    def open_picker_for(self, circle_button):
        # open centered (picker.open will copy owner color)
        self.picker.open(circle_button)

    # persistence
    def _load_palette(self):
        if os.path.exists(self.palette_file):
            try:
                with open(self.palette_file, "r") as f:
                    data = json.load(f)
                    # ensure tuples
                    clean = {}
                    for k, v in data.items():
                        if isinstance(v, list) and len(v) == 3:
                            clean[k] = v
                    return clean
            except Exception:
                return {}
        else:
            # defaults
            return {
                "slot1": [200, 50, 50],
                "slot2": [50, 200, 50],
                "slot3": [50, 50, 200]
            }

    def save_palette(self):
        data = {}
        for i, btn in enumerate(self.color_buttons):
            data[f"slot{i+1}"] = list(btn.color)
        try:
            with open(self.palette_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("Failed to save palette:", e)


class PagePattern(Page):
    def __init__(self, manager, font):
        super().__init__("pattern", manager, font, background=f"assets/backgrounds/{background_image}.png")
        label = Label(rect=(int(175*SCALE), int(0*SCALE), int(150*SCALE), int(80*SCALE)), text="Pattern Page", bg_color=None, border_width=0, font=font)
        self.add(label)


class PageModules(Page):
    def __init__(self, manager, font):
        super().__init__("modules", manager, font, background=f"assets/backgrounds/{background_image}.png")
        label = Label(rect=(int(175*SCALE), int(0*SCALE), int(150*SCALE), int(80*SCALE)), text="Modules Page", bg_color=None, border_width=0, font=font)
        self.add(label)
        gauge = Gauge((500,200),100,0,200,"Speed", 16,0.5,True, True)
        self.add(gauge)

class PagePresets(Page):
    def __init__(self, manager, font):
        super().__init__("presets", manager, font, background=f"assets/backgrounds/{background_image}.png")
        label = Label(rect=(int(175*SCALE), int(0*SCALE), int(150*SCALE), int(80*SCALE)), text="Presets Page", bg_color=None,  border_width=0,font=font)
        self.add(label)


class PageSettings(Page):
    def __init__(self, manager, font):
        super().__init__("settings", manager, font, background=f"assets/backgrounds/{background_image}.png")
        label = Label(rect=(int(175*SCALE), int(0*SCALE), int(150*SCALE), int(80*SCALE)), text="Settings Page", bg_color=None, border_width=0, font=font)
        self.add(label)


