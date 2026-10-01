import random
import pygame
from game.text_box import TextBox

HINT_PENALTY = 0.5    # points deducted per revealed letter


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

        self.revealed = 0

        self.input_box = TextBox(width // 2 - 175, 220, 160, 46)
        self.submit_btn = pygame.Rect(width // 2 - 5, 220, 95, 46)
        self.hint_btn = pygame.Rect(width // 2 + 100, 220, 80, 46)

        self.font_title = pygame.font.SysFont(None, 40)
        self.font_word = pygame.font.SysFont(None, 52)
        self.font_msg = pygame.font.SysFont(None, 26)
        self.font_btn = pygame.font.SysFont(None, 24)

        self.next_round()

    def scramble_string(self, word):
        letters = list(word)
        while True:
            random.shuffle(letters)
            shuffled = "".join(letters)
            if shuffled != word or len(word) <= 1:
                return shuffled

    def next_round(self):
        self.secret_word = random.choice(self.words)
        self.scrambled_word = self.scramble_string(self.secret_word)
        self.input_box.clear()
        self.revealed = 0

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

    # ------------------------------------------------------------------ loop
    def handle_event(self, event):
        self.input_box.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.submit_guess()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.submit_btn.collidepoint(event.pos):
                self.submit_guess()
            elif self.hint_btn.collidepoint(event.pos):
                self.use_hint()
            # The text box is the only input, so clicks elsewhere shouldn't steal its focus.
            self.input_box.active = True

    def update(self):
        pass

    def draw_button(self, screen, rect, label, color):
        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, (220, 220, 220), rect, width=2, border_radius=6)
        text = self.font_btn.render(label, True, (255, 255, 255))
        screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))

    def render(self, screen):
        screen.fill((26, 30, 38))

        title_surf = self.font_title.render("Word Scramble Arena", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 25))

        score_surf = self.font_msg.render(f"Score: {self.score:g}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 70))

        spaced_letters = "  ".join(self.scrambled_word)
        scramble_surf = self.font_word.render(spaced_letters, True, (100, 200, 255))
        screen.blit(scramble_surf, (self.width // 2 - scramble_surf.get_width() // 2, 120))

        hint_surf = self.font_msg.render(f"Hint:  {self.hint_pattern()}", True, (100, 200, 255))
        screen.blit(hint_surf, (self.width // 2 - hint_surf.get_width() // 2, 178))

        self.input_box.render(screen)
        self.draw_button(screen, self.submit_btn, "SUBMIT", (50, 150, 85))
        self.draw_button(screen, self.hint_btn, "HINT", (180, 120, 40))

        feedback_surf = self.font_msg.render(self.feedback_msg, True, self.feedback_color)
        screen.blit(feedback_surf, (self.width // 2 - feedback_surf.get_width() // 2, 290))
