import vlc
import subprocess


class FFMP3:

    def __init__(self, file, autoplay=True):
        self.file = file
        self.metadata = {}
        self.is_playing = autoplay
        self.audio = vlc.MediaPlayer(file)
        self.play()
        self.length = 0.
        self.duration()
        if not autoplay:
            self.stop()

    def waveform(self, output, design):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        terminal = f'ffmpeg -y -i "{self.file}" ' \
            f'-hide_banner -loglevel panic ' \
            f'-filter_complex "aformat=channel_layouts=mono, compand=gain=-5, ' \
            f'showwavespic=s={int(design["width"])}x{int(design["height"])}:'\
            f'colors={design["foreground"]}|{design["background"]}" -vframes 1 {output}'
        pipe = subprocess.Popen(terminal, stdout=subprocess.PIPE, shell=False, creationflags=subprocess.CREATE_NO_WINDOW, startupinfo=si)
        return pipe.communicate()  # out, err

    def destroy(self):
        self.audio = None

    def play(self):
        self.is_playing = True
        self.audio.play()

    def stop(self):
        self.is_playing = False
        self.audio.stop()

    def duration(self):
        while self.length == 0:
            self.length = max(self.length, self.audio.get_length() / 1000.)
        return self.length

    def current(self):
        return self.duration() * self.audio.get_position()

    def seek(self, time):
        time /= self.duration()
        self.audio.set_position(time)
