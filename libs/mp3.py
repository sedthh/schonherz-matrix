from ffpyplayer.player import MediaPlayer
from time import sleep
import subprocess


class FFMP3:

    def __init__(self, file, autoplay=True):
        self.file = file
        self.metadata = {}
        self.is_playing = True
        self.player = MediaPlayer(file)
        if not autoplay:
            self.stop()

    def waveform(self, output, design):
        terminal = f'ffmpeg -y -i "{self.file}" ' \
            f'-hide_banner -loglevel panic ' \
            f'-filter_complex "aformat=channel_layouts=mono, compand=gain=-5, ' \
            f'showwavespic=s={int(design["width"])}x{int(design["height"])}:'\
            f'colors={design["foreground"]}|{design["background"]}" -vframes 1 {output}'
        pipe = subprocess.Popen(terminal, stdout=subprocess.PIPE)
        return pipe.communicate()  # out, err

    def destroy(self):
        self.player.close_player()
        self.player = None
        del self

    def command(self, function=None, args=[]):
        while True:
            self.metadata = self.player.get_metadata()
            if "duration" in self.metadata and self.metadata["duration"]:
                if function == "play":
                    self.player.set_pause(False)
                    self.is_playing = True
                elif function == "pause":
                    self.player.set_pause(True)
                    self.is_playing = False
                elif function == "toggle":
                    self.player.toggle_pause()
                    self.is_playing = not self.is_playing
                elif function == "current":
                    return self.player.get_pts()
                elif function == "duration":
                    return self.metadata["duration"]
                elif function == "seek":
                    if args:
                        self.player.seek(args[0], False)
                elif function == "get_volume":
                    return self.player.get_volume()
                elif function == "set_volume":
                    self.player.set_volume(args[0])
                elif function == "stop":
                    self.player.seek(0, False)
                    self.player.set_pause(True)
                    self.is_playing = False
                else:
                    raise ValueError("Unknown command")
                return True
            else:
                sleep(0.05)

    def play(self):
        return self.command("play")

    def pause(self):
        return self.command("pause")

    def toggle(self):
        return self.command("toggle")

    def current(self):
        return self.command("current")

    def duration(self):
        return self.command("duration")

    def seek(self, time):
        return self.command("seek", [time])

    def volume(self, value=None):
        if value is None:
            return self.command("get_volume")
        else:
            return self.command("set_volume", [min(1, max(0, value))])

    def stop(self):
        return self.command("stop")
