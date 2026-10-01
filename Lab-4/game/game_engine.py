import random
import pygame
from game.text_box import TextBox

ROUND_TIME = 20.0     # seconds allowed per word
HINT_PENALTY = 0.5    # points deducted per revealed letter
TILE_SIZE = 52
TILE_GAP = 8


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.words = ["PYTHON", "PYGAME", "PLANET", "ROCKET", "GALAXY", "STREAM", "PUZZLE", "ALGORITHM"]
        self.secret_word = ""
        self.scrambled_word = ""

        self.score = 0
        self.feedback_msg = "Unscramble the letters above!"
        self.feedback_color = (210, 215, 225)

        self.round_time = ROUND_TIME
        self.time_left = ROUND_TIME
        self.last_ticks = None
        self.revealed = 0

        # Letter tiles: `pool` holds the scrambled tiles at their home positions,
        # `rack` holds the player's arrangement. Each list has one slot per letter.
        self.pool = []
        self.rack = []
        self.drag = None

        self.input_box = TextBox(width // 2 - 175, 295, 160, 46)
        self.submit_btn = pygame.Rect(width // 2 - 5, 295, 95, 46)
        self.hint_btn = pygame.Rect(width // 2 + 100, 295, 80, 46)

        self.font_title = pygame.font.SysFont(None, 40)
        self.font_word = pygame.font.SysFont(None, 52)
        self.font_tile = pygame.font.SysFont(None, 44)
        self.font_msg = pygame.font.SysFont(None, 26)
        self.font_btn = pygame.font.SysFont(None, 24)
        self.font_small = pygame.font.SysFont(None, 21)

        self.next_round()

    def scramble_string(self, word):
        letters = list(word)
        while True:
            random.shuffle(letters)
            shuffled = "".join(letters)
            if shuffled != word or len(word) <= 1:
                return shuffled

    def next_round(self):
        # Don't serve the same word twice in a row.
        self.secret_word = random.choice([w for w in self.words if w != self.secret_word])
        self.scrambled_word = self.scramble_string(self.secret_word)
        self.input_box.clear()
        self.time_left = self.round_time
        self.revealed = 0
        self.pool = [{"letter": ch, "home": i} for i, ch in enumerate(self.scrambled_word)]
        self.rack = [None] * len(self.secret_word)
        self.drag = None

    def submit_guess(self):
        guess = self.input_box.text.strip().upper()
        if not guess:
            self.feedback_msg = "Type a word before submitting!"
            self.feedback_color = (240, 170, 50)
            return

        # Validate against the original (unscrambled) solution, not the jumbled letters.
        is_correct = (guess == self.secret_word)

        if is_correct:
            self.score += 1
            self.feedback_msg = f"CORRECT! '{self.secret_word}' is right."
            self.feedback_color = (80, 230, 110)
            self.next_round()
        else:
            self.feedback_msg = "WRONG GUESS! Try again."
            self.feedback_color = (240, 80, 80)
            self.input_box.clear()
            self.return_all_tiles()

    # ------------------------------------------------------------------ hints
    def use_hint(self):
        # Never reveal the whole word; the last letter is left for the player.
        if self.revealed >= len(self.secret_word) - 1:
            self.feedback_msg = "No more hints for this word!"
            self.feedback_color = (240, 170, 50)
            return
        self.revealed += 1
        self.score -= HINT_PENALTY
        self.feedback_msg = f"Hint used: -{HINT_PENALTY:g} points"
        self.feedback_color = (240, 170, 50)

    def hint_pattern(self):
        return " ".join(ch if i < self.revealed else "_" for i, ch in enumerate(self.secret_word))

    # ------------------------------------------------------------------ tiles
    def _row_rect(self, i, count, y):
        row_w = count * TILE_SIZE + (count - 1) * TILE_GAP
        x = self.width // 2 - row_w // 2 + i * (TILE_SIZE + TILE_GAP)
        return pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

    def pool_rect(self, i):
        return self._row_rect(i, len(self.pool), 118)

    def rack_rect(self, i):
        return self._row_rect(i, len(self.rack), 192)

    def sync_rack_to_input(self):
        self.input_box.text = "".join(t["letter"] for t in self.rack if t is not None)

    def return_all_tiles(self):
        for i, tile in enumerate(self.rack):
            if tile is not None:
                self.pool[tile["home"]] = tile
                self.rack[i] = None

    def tile_at(self, pos):
        for i, tile in enumerate(self.rack):
            if tile is not None and self.rack_rect(i).collidepoint(pos):
                return "rack", i
        for i, tile in enumerate(self.pool):
            if tile is not None and self.pool_rect(i).collidepoint(pos):
                return "pool", i
        return None

    def take_tile(self, src):
        where, i = src
        row = self.pool if where == "pool" else self.rack
        tile, row[i] = row[i], None
        return tile

    def click_tile(self, src, tile):
        """Pool tile -> first free rack slot; rack tile -> back to its home in the pool."""
        if src[0] == "pool" and None in self.rack:
            self.rack[self.rack.index(None)] = tile
        else:
            self.pool[tile["home"]] = tile

    def drop_tile(self, src, tile, pos):
        for j in range(len(self.rack)):
            if self.rack_rect(j).collidepoint(pos):
                occupant = self.rack[j]
                self.rack[j] = tile
                if occupant is not None:
                    if src[0] == "rack":
                        self.rack[src[1]] = occupant      # swap within the rack
                    else:
                        self.pool[occupant["home"]] = occupant
                return
        self.pool[tile["home"]] = tile

    def handle_tile_mouse(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            src = self.tile_at(event.pos)
            if src is not None:
                self.drag = {"src": src, "tile": self.take_tile(src),
                             "start": event.pos, "pos": event.pos, "moved": False}
        elif event.type == pygame.MOUSEMOTION and self.drag:
            self.drag["pos"] = event.pos
            sx, sy = self.drag["start"]
            if abs(event.pos[0] - sx) + abs(event.pos[1] - sy) > 6:
                self.drag["moved"] = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag:
            drag, self.drag = self.drag, None
            if drag["moved"]:
                self.drop_tile(drag["src"], drag["tile"], event.pos)
            else:
                self.click_tile(drag["src"], drag["tile"])
            self.sync_rack_to_input()

    # ------------------------------------------------------------------ loop
    def handle_event(self, event):
        self.input_box.handle_event(event)
        self.handle_tile_mouse(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.submit_guess()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.submit_btn.collidepoint(event.pos):
                self.submit_guess()
            elif self.hint_btn.collidepoint(event.pos):
                self.use_hint()
            # The text box is the only input, so clicks elsewhere shouldn't steal its focus.
            self.input_box.active = True

    def update(self, dt=None):
        if dt is None:
            now = pygame.time.get_ticks()
            dt = 0 if self.last_ticks is None else (now - self.last_ticks) / 1000
            self.last_ticks = now

        self.time_left -= dt
        if self.time_left <= 0:
            self.feedback_msg = f"TIME'S UP! The word was '{self.secret_word}'."
            self.feedback_color = (240, 80, 80)
            self.next_round()

    def draw_button(self, screen, rect, label, color):
        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, (220, 220, 220), rect, width=2, border_radius=6)
        text = self.font_btn.render(label, True, (255, 255, 255))
        screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))

    def draw_tile(self, screen, rect, letter, lifted=False):
        if lifted:
            pygame.draw.rect(screen, (10, 12, 16), rect.move(4, 5), border_radius=8)
        pygame.draw.rect(screen, (245, 225, 170), rect, border_radius=8)
        pygame.draw.rect(screen, (190, 150, 80), rect, width=3, border_radius=8)
        text = self.font_tile.render(letter, True, (40, 35, 30))
        screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2 + 2))

    def render_timer(self, screen):
        frac = max(0.0, self.time_left / self.round_time)
        bar = pygame.Rect(self.width // 2 - 220, 92, 440, 12)
        if frac > 0.5:
            color = (80, 210, 110)
        elif frac > 0.25:
            color = (240, 190, 60)
        else:
            color = (240, 80, 80)
        pygame.draw.rect(screen, (55, 60, 72), bar, border_radius=6)
        pygame.draw.rect(screen, color, (bar.x, bar.y, int(bar.w * frac), bar.h), border_radius=6)
        secs = self.font_small.render(f"{max(0, self.time_left):4.1f}s", True, color)
        screen.blit(secs, (bar.right + 10, bar.centery - secs.get_height() // 2))

    def render(self, screen):
        screen.fill((26, 30, 38))

        title_surf = self.font_title.render("Word Scramble Arena", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 20))

        score_surf = self.font_msg.render(f"Score: {self.score:g}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 60))

        self.render_timer(screen)

        # Scrambled letter tiles (empty outlines where a tile has been moved to the rack).
        for i, tile in enumerate(self.pool):
            rect = self.pool_rect(i)
            if tile is None:
                pygame.draw.rect(screen, (55, 60, 72), rect, width=2, border_radius=8)
            else:
                self.draw_tile(screen, rect, tile["letter"])

        # Rearrangement rack.
        for i, tile in enumerate(self.rack):
            rect = self.rack_rect(i)
            pygame.draw.rect(screen, (38, 44, 56), rect, border_radius=8)
            pygame.draw.rect(screen, (90, 140, 210), rect, width=2, border_radius=8)
            if tile is not None:
                self.draw_tile(screen, rect, tile["letter"])

        hint_surf = self.font_msg.render(f"Hint:  {self.hint_pattern()}", True, (100, 200, 255))
        screen.blit(hint_surf, (self.width // 2 - hint_surf.get_width() // 2, 262))

        self.input_box.render(screen)
        self.draw_button(screen, self.submit_btn, "SUBMIT", (50, 150, 85))
        self.draw_button(screen, self.hint_btn, "HINT", (180, 120, 40))

        feedback_surf = self.font_msg.render(self.feedback_msg, True, self.feedback_color)
        screen.blit(feedback_surf, (self.width // 2 - feedback_surf.get_width() // 2, 362))

        help_lines = [
            "Click or drag tiles into the rack to try arrangements, or just type.",
            f"HINT reveals the next letter (-{HINT_PENALTY:g} pts).  {int(self.round_time)} seconds per word.",
        ]
        for n, line in enumerate(help_lines):
            surf = self.font_small.render(line, True, (130, 136, 150))
            screen.blit(surf, (self.width // 2 - surf.get_width() // 2, 420 + n * 22))

        if self.drag:
            rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
            rect.center = self.drag["pos"]
            self.draw_tile(screen, rect, self.drag["tile"]["letter"], lifted=True)
