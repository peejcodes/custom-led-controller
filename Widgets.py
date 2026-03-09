# -------------------
# Library Imports
# -------------------
import pygame                # main pygame library (init, display, fonts, time, etc.)
import math                  # trig functions for circle/arc math
from pygame import gfxdraw   # higher-quality antialiased filled polygons
from collections import deque  # efficient FIFO queue for rolling-average timestamps

# -------------------
# Class Imports
# -------------------
from Variables import SCALE

# -----------------------------
# Base Widget Class
# -----------------------------
class Widget:
    def __init__(self, rect, visible=True, enabled=True):
        self.rect = pygame.Rect(rect)
        self.visible = visible
        self.enabled = enabled
        self.is_hovered = False
        self.is_pressed = False

    def draw(self, screen):
        pass

    def handle_event(self, event):
        pass

    def update_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos) if self.enabled and self.visible else False

    def update(self, dt):
        pass


# -----------------------------
# Label Widget
# -----------------------------
class Label(Widget):
    def __init__(self, rect, text, font,
                 text_color=(255, 255, 255),
                 bg_color=None,
                 opacity=180,  # <--- add opacity (0-255)
                 border_radius=0,
                 border_color=(0, 0, 0),
                 border_width=2):
        super().__init__(rect)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.bg_color = bg_color
        self.opacity = opacity
        self.border_radius = int(border_radius*SCALE)
        self.border_color = border_color
        self.border_width = int(border_width*SCALE)

    def set_text(self, text):
        self.text = text

    def draw(self, screen):
        if not self.visible:
            return

        # Create transparent surface
        label_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        # Draw border if enabled
        if self.border_width > 0:
            # border is fully opaque
            pygame.draw.rect(label_surf, self.border_color,
                             label_surf.get_rect(), border_radius=self.border_radius)

            # inner background (with opacity if bg_color is set)
            if self.bg_color:
                inner_rect = label_surf.get_rect().inflate(-2*self.border_width, -2*self.border_width)
                pygame.draw.rect(label_surf, (*self.bg_color, self.opacity),
                                 inner_rect, border_radius=max(0, self.border_radius - self.border_width))
        else:
            # no border, just background fill if provided
            if self.bg_color:
                pygame.draw.rect(label_surf, (*self.bg_color, self.opacity),
                                 label_surf.get_rect(), border_radius=self.border_radius)

        # Render text
        if self.text:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
            label_surf.blit(text_surf, text_rect)

        # Blit label surface to screen
        screen.blit(label_surf, self.rect.topleft)


# -----------------------------
# Button Widget
# -----------------------------
class Button(Widget):
    def __init__(self, rect, text, font, command=None,
                 text_color=(255, 255, 255),
                 color_normal=(0, 0, 0),
                 color_hover=(30, 30, 30),
                 color_pressed=(0, 0, 0),
                 border_radius=8,
                 border_color=(0, 0, 0),
                 border_width=2):  # set > 0 to enable border
        super().__init__(rect)
        self.text = text
        self.font = font
        self.command = command
        self.text_color = text_color
        self.colors = {"normal": color_normal, "hover": color_hover, "pressed": color_pressed}
        self.border_radius = int(border_radius*SCALE)
        self.border_color = border_color
        self.border_width = int(border_width*SCALE)
        self.text_surf = font.render(text, True, text_color)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self, screen):
        if not self.visible:
            return

        # choose button color depending on state
        color = self.colors["normal"]
        opacity = 180  # default opacity (0=transparent, 255=opaque)
        if self.is_pressed:
            color = self.colors["pressed"]
            opacity = 255  # fully opaque when pressed
        elif self.is_hovered:
            color = self.colors["hover"]
            opacity = 220  # more opaque on hover

        # Create a temporary surface with per-pixel alpha
        button_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        # Draw border if enabled
        if self.border_width > 0:
            # Draw border fully opaque
            pygame.draw.rect(button_surf, self.border_color, button_surf.get_rect(), border_radius=self.border_radius)

            # Draw inner rectangle with alpha
            inner_rect = button_surf.get_rect().inflate(-2 * self.border_width, -2 * self.border_width)
            pygame.draw.rect(button_surf, (*color, opacity), inner_rect,
                             border_radius=max(0, self.border_radius - self.border_width))
        else:
            # No border, draw normal button with alpha
            pygame.draw.rect(button_surf, (*color, opacity), button_surf.get_rect(), border_radius=self.border_radius)

        # Draw text
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        button_surf.blit(text_surf, text_rect)

        # Blit the button surface to the main screen
        screen.blit(button_surf, self.rect.topleft)

    # def draw(self, screen):
    #     if not self.visible:
    #         return
    #
    #     # choose button color depending on state
    #     color = self.colors["normal"]
    #     if self.is_pressed:
    #         color = self.colors["pressed"]
    #     elif self.is_hovered:
    #         color = self.colors["hover"]
    #
    #     # Draw border if enabled
    #     if self.border_width > 0:
    #         pygame.draw.rect(screen, self.border_color, self.rect, border_radius=self.border_radius)
    #
    #         # Inner rect (shrink by border_width to fit inside border)
    #         inner_rect = self.rect.inflate(-2*self.border_width, -2*self.border_width)
    #         pygame.draw.rect(screen, color, inner_rect, border_radius=max(0, self.border_radius - self.border_width))
    #     else:
    #         # No border, draw normal button
    #         pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
    #
    #     # Draw text
    #     screen.blit(self.text_surf, self.text_rect)

    def handle_event(self, event):
        if not (self.visible and self.enabled):
            return
        if event.type == pygame.MOUSEMOTION:
            self.update_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.is_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed and self.is_hovered and self.command:
                self.command()
            self.is_pressed = False


# -----------------------------
# CircleButton (slot button)
# -----------------------------
class CircleButton(Widget):
    def __init__(self, center, radius, color, font, slot_index, command=None):
        # rect used for events: bounding box of the circle
        rect = (center[0]-radius, center[1]-radius, radius*2, radius*2)
        super().__init__(rect)
        self.center = center
        self.radius = radius
        self.color = tuple(color)
        self.font = font
        self.slot_index = slot_index
        self.command = command  # will be a function to open the picker
        self.border_color = (0, 0, 0)
        self.border_width = int(2*SCALE)

    def draw(self, screen):
        if not self.visible:
            return
        # circle fill
        pygame.draw.circle(screen, self.color, self.center, self.radius)
        # border
        pygame.draw.circle(screen, self.border_color, self.center, self.radius, self.border_width)
        # small index label
        label_surf = self.font.render(str(self.slot_index + 1), True, (255,255,255))
        label_rect = label_surf.get_rect(center=self.center)
        screen.blit(label_surf, label_rect)

    def handle_event(self, event):
        if not (self.visible and self.enabled):
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # check distance from center
            mx, my = event.pos
            dx = mx - self.center[0]
            dy = my - self.center[1]
            if dx*dx + dy*dy <= self.radius*self.radius:
                if self.command:
                    self.command(self)  # pass self as owner


# -----------------------------
# Entry Widget
# -----------------------------
class Entry(Widget):
    def __init__(self, rect, font, placeholder="",
                 text_color=(255, 255, 255),
                 bg_color=(50, 50, 50),
                 border_color=(200, 200, 200),
                 border_radius=6,
                 active_color=(100, 100, 100)):
        super().__init__(rect)
        self.font = font
        self.text = ""
        self.placeholder = placeholder
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_color = border_color
        self.active_color = active_color
        self.border_radius = int(border_radius*SCALE)
        self.has_focus = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def draw(self, screen):
        if not self.visible:
            return
        color = self.active_color if self.has_focus else self.bg_color
        pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(screen, self.border_color, self.rect, 2, border_radius=self.border_radius)
        display_text = self.text if self.text else self.placeholder
        display_color = self.text_color if self.text else (150, 150, 150)
        text_surf = self.font.render(display_text, True, display_color)
        text_rect = text_surf.get_rect(midleft=(self.rect.x + 8, self.rect.centery))
        screen.blit(text_surf, text_rect)
        if self.has_focus and self.cursor_visible:
            cursor_x = text_rect.left + self.font.size(self.text)[0] if self.text else text_rect.left
            cursor_y = text_rect.top
            cursor_h = text_rect.height
            pygame.draw.line(screen, self.text_color, (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_h), 2)

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.has_focus = self.rect.collidepoint(event.pos)
        if self.has_focus and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.has_focus = False
            elif event.unicode.isprintable():
                self.text += event.unicode

    def update(self, dt):
        if self.has_focus:
            self.cursor_timer += dt
            if self.cursor_timer >= 500:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
        else:
            self.cursor_visible = False


# -----------------------------
# Gauge Widget
# -----------------------------
class Gauge(Widget):
    def __init__(self, center, radius, min_value, max_value,
                 label="RPM", num_segments=16, average_window=0.5,
                 visible=True, enabled=True):
        rect = pygame.Rect(0, 0, radius*2, radius*2)
        rect.center = center
        super().__init__(rect, visible, enabled)

        self.x, self.y = center
        self.radius = radius
        self.bg_color = (10, 10, 10)
        self.text_color = (255, 0, 0)

        self.min_value = min_value
        self.max_value = max_value
        self.value = min_value
        self.display_value = min_value
        self.label = label

        self.num_segments = num_segments
        self.segment_levels = [0.0 for _ in range(num_segments)]
        self.animation_speed = 6.0

        self.average_window = average_window
        self.recent_values = deque()
        self.average_value = min_value

        self.font = pygame.font.SysFont("consolas", max(12, int(radius*0.35)))
        self.label_font = pygame.font.SysFont("consolas", max(9, int(radius*0.17)))

    def set_value(self, value):
        self.value = max(self.min_value, min(self.max_value, value))

    def update(self, dt):
        if not self.enabled or not self.visible:
            return

        current_time = pygame.time.get_ticks() / 1000.0
        self.recent_values.append((self.value, current_time))
        while self.recent_values and (current_time - self.recent_values[0][1] > self.average_window):
            self.recent_values.popleft()

        if self.recent_values:
            self.average_value = sum(v for v,_ in self.recent_values) / len(self.recent_values)

        interp = min(1.0, dt * self.animation_speed)
        self.display_value += (self.average_value - self.display_value) * interp

        ratio = (self.display_value - self.min_value) / max(self.max_value - self.min_value, 1)
        ratio = max(0.0, min(1.0, ratio))
        target_lit = int(ratio * self.num_segments)

        for i in range(self.num_segments):
            target = 1.0 if i < target_lit else 0.0
            self.segment_levels[i] += (target - self.segment_levels[i]) * interp

    def draw_arc_segment(self, surface, start_angle, end_angle, inner_r, outer_r, color):
        line_color = self.bg_color
        points = []
        subdivisions = 12
        step = (end_angle - start_angle) / subdivisions
        for i in range(subdivisions + 1):
            angle = start_angle + i * step
            ox = self.x + outer_r * math.cos(angle)
            oy = self.y + outer_r * math.sin(angle)
            points.append((ox, oy))
        for i in range(subdivisions + 1):
            angle = end_angle - i * step
            ix = self.x + inner_r * math.cos(angle)
            iy = self.y + inner_r * math.sin(angle)
            points.append((ix, iy))
        gfxdraw.filled_polygon(surface, points, color)
        gfxdraw.aapolygon(surface, points, color)

        # Draw separation lines at start and end
        sx_inner = self.x + inner_r * math.cos(start_angle)
        sy_inner = self.y + inner_r * math.sin(start_angle)
        sx_outer = self.x + outer_r * math.cos(start_angle)
        sy_outer = self.y + outer_r * math.sin(start_angle)
        pygame.draw.line(surface, line_color, (sx_inner, sy_inner), (sx_outer, sy_outer), 2)

        ex_inner = self.x + inner_r * math.cos(end_angle)
        ey_inner = self.y + inner_r * math.sin(end_angle)
        ex_outer = self.x + outer_r * math.cos(end_angle)
        ey_outer = self.y + outer_r * math.sin(end_angle)
        pygame.draw.line(surface, line_color, (ex_inner, ey_inner), (ex_outer, ey_outer), 2)

    def draw(self, surface):
        if not self.visible:
            return

        pygame.draw.circle(surface, self.bg_color, (self.x, self.y), self.radius)
        inner_r = self.radius * 0.65
        outer_r = self.radius * 0.9

        for i, level in enumerate(self.segment_levels):
            angle_start = math.pi + (i / self.num_segments) * math.pi
            angle_end = math.pi + ((i + 1) / self.num_segments) * math.pi
            intensity = int(50 + 205*level)
            intensity = max(0, min(255, intensity))
            color = (intensity, 0, 0)
            self.draw_arc_segment(surface, angle_start, angle_end, inner_r, outer_r, color)

        value_text = self.font.render(f"{int(self.display_value)}", True, self.text_color)
        surface.blit(value_text, value_text.get_rect(center=(self.x, self.y)))

        label_text = self.label_font.render(self.label, True, self.text_color)
        surface.blit(label_text, label_text.get_rect(center=(self.x, self.y + self.radius*0.4)))


# -----------------------------
# StatusLight Widget
# -----------------------------
class StatusLight(Widget):
    """
    A glowing circular light widget with smooth fade-out edges.
    """
    def __init__(self, pos, radius=100, color=(255, 200, 60), falloff=2.0, scale=1.0, visible=True, enabled=True):
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = pos
        super().__init__(rect, visible, enabled)

        self.base_radius = radius
        self.color = color
        self.falloff = falloff
        self.scale = scale

        self._base_gradient = None
        self._scaled_cache = {}
        self._make_base_gradient()

    # --- internal generation ---
    def _make_base_gradient(self):
        """Create the base radial gradient surface."""
        r = self.base_radius
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        cx = cy = r

        for rad in range(r, -1, -1):
            alpha = int(255 * (1 - (rad / r)) ** self.falloff)
            alpha = max(0, min(255, alpha))
            pygame.draw.circle(surf, (*self.color, alpha), (cx, cy), rad)

        self._base_gradient = surf
        self._scaled_cache.clear()

    def _get_scaled_gradient(self):
        """Return the correct gradient surface for the current scale (cached)."""
        scaled_radius = max(1, int(round(self.base_radius * self.scale)))

        if scaled_radius == self.base_radius:
            return self._base_gradient

        if scaled_radius not in self._scaled_cache:
            new_surf = pygame.transform.smoothscale(
                self._base_gradient, (scaled_radius * 2, scaled_radius * 2)
            )
            self._scaled_cache[scaled_radius] = new_surf

        return self._scaled_cache[scaled_radius]

    # --- property setters ---
    def set_color(self, color):
        self.color = color
        self._make_base_gradient()

    def set_falloff(self, falloff):
        self.falloff = falloff
        self._make_base_gradient()

    def set_scale(self, scale):
        self.scale = max(0.1, float(scale))
        # scaling handled at draw time; no regen needed

    def set_position(self, pos):
        self.rect.center = pos

    # --- widget overrides ---
    def draw(self, screen, blend_add=False):
        if not self.visible:
            return

        gradient = self._get_scaled_gradient()
        rect = gradient.get_rect(center=self.rect.center)

        if blend_add:
            screen.blit(gradient, rect, special_flags=pygame.BLEND_ADD)
        else:
            screen.blit(gradient, rect)

    def update(self, dt):
        """Optional: could be used for animation or pulsing."""
        pass

    def handle_event(self, event):
        """Optional: handle clicks or hover interactions."""
        if not self.enabled or not self.visible:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and self.is_hovered:
            self.is_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.is_pressed = False
