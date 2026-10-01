import pygame
from game.game_engine import GameEngine

WIDTH, HEIGHT = 700, 500
FPS = 60


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Word Scramble Arena")
    clock = pygame.time.Clock()

    engine = GameEngine(WIDTH, HEIGHT)

    running = True
    dt = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            engine.handle_event(event)

        engine.update(dt)
        engine.render(screen)

        pygame.display.flip()
        dt = clock.tick(FPS) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()