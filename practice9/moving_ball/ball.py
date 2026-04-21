import pygame

class Ball:
    def __init__(self, x, y, radius=25):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = 20

    def move(self, dx, dy, width, height):
        new_x = self.x + dx
        new_y = self.y + dy

        if self.radius <= new_x <= width - self.radius:
            self.x = new_x

        if self.radius <= new_y <= height - self.radius:
            self.y = new_y

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 0, 0), (self.x, self.y), self.radius)