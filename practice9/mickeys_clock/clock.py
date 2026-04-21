import pygame
import datetime

class Clock:
    def __init__(self):
        self.face = pygame.image.load('images/mainclock.png')
        self.face = pygame.transform.scale(self.face, (600, 600))

        self.minute_arrow = pygame.image.load('images/rightarm.png')
        self.minute_arrow = pygame.transform.scale(self.minute_arrow, (800, 700))

        self.second_arrow = pygame.image.load('images/leftarm.png')
        self.second_arrow = pygame.transform.scale(self.second_arrow, (40, 500))

    def draw(self, screen):
        my_time = datetime.datetime.now()
        minuteINT = int(my_time.strftime("%M"))
        secondINT = int(my_time.strftime("%S"))

        angleMINUTE = minuteINT * -6 - 25
        angleSECOND = secondINT * -6

        minute = pygame.transform.rotate(self.minute_arrow, angleMINUTE)
        second = pygame.transform.rotate(self.second_arrow, angleSECOND)

        screen.blit(self.face, (100, 40))

        screen.blit(second, (400 - second.get_width() // 2, 340 - second.get_height() // 2))
        screen.blit(minute, (400 - minute.get_width() // 2, 340 - minute.get_height() // 2))