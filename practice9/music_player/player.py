import pygame

class MusicPlayer:
    def __init__(self, tracks):
        self.tracks = tracks
        self.index = 0
        self.playing = False

        pygame.mixer.init()

    def load(self):
        pygame.mixer.music.load(self.tracks[self.index])

    def play(self):
        self.load()
        pygame.mixer.music.play()
        self.playing = True

    def stop(self):
        pygame.mixer.music.stop()
        self.playing = False

    def next(self):
        self.index = (self.index + 1) % len(self.tracks)
        self.play()

    def prev(self):
        self.index = (self.index - 1) % len(self.tracks)
        self.play()

    def get_current_track(self):
        return self.tracks[self.index]