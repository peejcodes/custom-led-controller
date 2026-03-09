# -------------------
# Library Imports
# -------------------
import pygame

# -------------------
# Class Imports
# -------------------
from Variables import SCALE, SCREEN_WIDTH, SCREEN_HEIGHT
from Widgets import Widget


# -----------------------------
# ColorPicker (modal floating panel)
# -----------------------------
class ColorPicker(Widget):
    def __init__(self, font, initial_color=(255,255,255), swatches=None):
        w = int(300*SCALE)
        h = int(320*SCALE)
        cx = SCREEN_WIDTH // 2 + int(150*SCALE)
        cy = SCREEN_HEIGHT // 2
        rect = (cx - w//2, cy - h//2, w, h)
        super().__init__(rect)
        self.font = font
        self.bg_color = (70, 70, 70)
        self.bg_opacity = 180
        self.border_color = (0,0,0)
        self.border_width = int(2*SCALE)
        self.active = False
        self.owner = None        # CircleButton being edited
        self.original_color = None  # store original RGB tuple
        self.color = pygame.Color(*initial_color)
        self._sync_hsva_from_color()
        # default swatches
        default_swatches = [
            (255,0,0), (255,128,0), (255,255,0), (0,255,0),
            (0,255,255), (0,0,255), (128,0,255), (255,0,255)
        ]
        self.swatches = swatches if swatches else default_swatches
        self.padding = int(12*SCALE)
        self.preview_rect = pygame.Rect(self.rect.left + self.padding,
                                        self.rect.top + self.padding,
                                        self.rect.width - 2*self.padding,
                                        int(60*SCALE))
        self.swatch_area = pygame.Rect(self.rect.left + self.padding,
                                       self.preview_rect.bottom + int(8*SCALE),
                                       self.rect.width - 2*self.padding,
                                       int(80*SCALE))
        self.slider_area = pygame.Rect(self.rect.left + self.padding,
                                       self.swatch_area.bottom + int(8*SCALE),
                                       self.rect.width - 2*self.padding,
                                       int(110*SCALE))
        self.buttons_rect = pygame.Rect(self.rect.left + self.padding,
                                        self.rect.bottom - self.padding - int(36*SCALE),
                                        self.rect.width - 2*self.padding,
                                        int(36*SCALE))
        self.dragging = None
        self._compute_elements()

    def _compute_elements(self):
        cols, rows, spacing = 4, 2, int(8*SCALE)
        sw_w = (self.swatch_area.width - (cols-1)*spacing) // cols
        sw_h = (self.swatch_area.height - (rows-1)*spacing) // rows
        self.swatch_rects = []
        for i in range(min(len(self.swatches), cols*rows)):
            col = i % cols
            row = i // cols
            rx = self.swatch_area.left + col*(sw_w + spacing)
            ry = self.swatch_area.top + row*(sw_h + spacing)
            self.swatch_rects.append(pygame.Rect(rx, ry, sw_w, sw_h))
        slider_h = int(24*SCALE)
        gap = int(12*SCALE)
        self.slider_rects = {}
        top = self.slider_area.top
        for name in ('h','s','v'):
            self.slider_rects[name] = pygame.Rect(self.slider_area.left, top, self.slider_area.width, slider_h)
            top += slider_h + gap
        btn_w = (self.buttons_rect.width - int(12*SCALE))//2
        btn_h = self.buttons_rect.height
        self.ok_rect = pygame.Rect(self.buttons_rect.left, self.buttons_rect.top, btn_w, btn_h)
        self.cancel_rect = pygame.Rect(self.ok_rect.right + int(12*SCALE), self.buttons_rect.top, btn_w, btn_h)

    def _sync_hsva_from_color(self):
        self.hsva = list(self.color.hsva)
        self.h, self.s, self.v = self.hsva[0], self.hsva[1], self.hsva[2]

    def _sync_color_from_hsv(self):
        self.color.hsva = (self.h, self.s, self.v, 100)

    def open(self, owner_button):
        """Open modal for a CircleButton."""
        self.owner = owner_button
        self.original_color = tuple(owner_button.color)  # save original
        self.color = pygame.Color(*self.original_color)
        self._sync_hsva_from_color()
        self.active = True
        self.dragging = None

    def close(self, accept=False):
        """Close picker; commit color if accept=True."""
        if accept and self.owner:
            self.owner.color = (self.color.r, self.color.g, self.color.b)
        elif self.owner and not accept:
            self.owner.color = self.original_color
        self.active = False
        self.owner = None
        self.original_color = None

    def handle_event(self, event):
        if not self.active:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                self.close(accept=False)
                return
            lx, ly = event.pos[0] - self.rect.left, event.pos[1] - self.rect.top
            for idx, r in enumerate(self.swatch_rects):
                if r.collidepoint(event.pos):
                    rcol = self.swatches[idx]
                    self.color = pygame.Color(*rcol)
                    self._sync_hsva_from_color()
                    return
            for name, r in self.slider_rects.items():
                if r.collidepoint(event.pos):
                    self.dragging = name
                    self._update_slider_from_pos(name, event.pos[0])
                    return
            if self.ok_rect.collidepoint(event.pos):
                self._sync_color_from_hsv()
                self.close(accept=True)
                return
            if self.cancel_rect.collidepoint(event.pos):
                self.close(accept=False)
                return
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = None
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_slider_from_pos(self.dragging, event.pos[0])

    def _update_slider_from_pos(self, name, global_x):
        r = self.slider_rects[name]
        rel_x = max(r.left, min(global_x, r.right)) - r.left
        frac = rel_x / float(r.width)
        if name == 'h':
            self.h = max(0.0, min(360.0, frac*360.0))
        elif name == 's':
            self.s = max(0.0, min(100.0, frac*100.0))
        else:
            self.v = max(0.0, min(100.0, frac*100.0))
        self._sync_color_from_hsv()
        # do NOT update owner's color live — only on OK

    def draw(self, screen):
        if not self.active:
            return
        panel_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel_surf.fill((*self.bg_color, self.bg_opacity))
        pygame.draw.rect(panel_surf, self.border_color, panel_surf.get_rect(), self.border_width)
        # preview
        preview_local = self.preview_rect.move(-self.rect.left, -self.rect.top)
        pygame.draw.rect(panel_surf, (0,0,0), preview_local, 2)
        pygame.draw.rect(panel_surf, (self.color.r, self.color.g, self.color.b), preview_local.inflate(-4,-4))
        # swatches
        for idx, r in enumerate(self.swatch_rects):
            local_r = r.move(-self.rect.left, -self.rect.top)
            pygame.draw.rect(panel_surf, self.swatches[idx], local_r)
            pygame.draw.rect(panel_surf, (0,0,0), local_r, 2)
        # sliders
        for name in ('h','s','v'):
            r = self.slider_rects[name]
            local_r = r.move(-self.rect.left, -self.rect.top)
            grad_surf = pygame.Surface((local_r.width, local_r.height))
            for x in range(local_r.width):
                frac = x / local_r.width
                c = pygame.Color(0)
                if name=='h': c.hsva = (frac*360, 100, 100, 100)
                elif name=='s': c.hsva = (self.h, frac*100, self.v, 100)
                else: c.hsva = (self.h, self.s, frac*100, 100)
                pygame.draw.line(grad_surf, c, (x,0), (x,local_r.height))
            panel_surf.blit(grad_surf, local_r)
            pygame.draw.rect(panel_surf, (0,0,0), local_r, 2, border_radius=4)
            # handle
            if name=='h': pos=int((self.h/360)*local_r.width)
            elif name=='s': pos=int((self.s/100)*local_r.width)
            else: pos=int((self.v/100)*local_r.width)
            handle_rect = pygame.Rect(local_r.left+pos-4, local_r.top, 8, local_r.height)
            pygame.draw.rect(panel_surf, (255,255,255), handle_rect)
            pygame.draw.rect(panel_surf, (0,0,0), handle_rect, 1)
        # buttons
        ok_local = self.ok_rect.move(-self.rect.left, -self.rect.top)
        cancel_local = self.cancel_rect.move(-self.rect.left, -self.rect.top)
        pygame.draw.rect(panel_surf, (80,80,80), ok_local, border_radius=6)
        pygame.draw.rect(panel_surf, (0,0,0), ok_local, 2, border_radius=6)
        pygame.draw.rect(panel_surf, (80,80,80), cancel_local, border_radius=6)
        pygame.draw.rect(panel_surf, (0,0,0), cancel_local, 2, border_radius=6)
        ok_surf = self.font.render("OK", True, (255,255,255))
        ok_rect = ok_surf.get_rect(center=ok_local.center)
        cancel_surf = self.font.render("Cancel", True, (255,255,255))
        cancel_rect = cancel_surf.get_rect(center=cancel_local.center)
        panel_surf.blit(ok_surf, ok_rect)
        panel_surf.blit(cancel_surf, cancel_rect)
        screen.blit(panel_surf, self.rect.topleft)