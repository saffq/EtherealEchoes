import pygame
from game.player import Player
from game.timeline import TimelineManager

TIMELINES = [(0, 0, 255), (255, 0, 0)]

class Game:
    def __init__(self, width, height):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.running = True
        self.timeline_manager = TimelineManager(TIMELINES)
        self.player = Player(width // 2, height // 2)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.timeline_manager.switch_timeline()

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.move(keys)

    def draw(self):
        self.screen.fill(self.timeline_manager.get_current_color())
        self.player.draw(self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()
