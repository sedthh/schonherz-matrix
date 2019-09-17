# -*- coding: UTF-8 -*-

import os
import json
import time
import codecs
import re
from copy import deepcopy
from webbrowser import open as webbrowser_open
from math import floor, sqrt
from sys import modules

import asyncio
import threading

import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox
from tkinter.colorchooser import askcolor
from tkinter.ttk import Progressbar

from libs.profiles import *
from libs.layouts import *
from libs.mp3 import *

##### GLOBALS

TITLE = "QPY"  # name for window title
HEADER = "QPY"  # file headers
NAME = "QPY Animáció Szerkesztő 2019"  # software name
VERSION = "1.0.2"  # version number
URL = "https://github.com/sedthh/schonherz-matrix"  # GitHub URL
WAVEFORM = os.path.join(os.path.dirname(os.path.realpath(__file__)), "wave.png")   # waveform generated

##### EDITOR WINDOW

class Application(tk.Frame):
    def __init__(self, master=None):
        self.root = master
        super().__init__(self.root)
        self.skin = "DEFAULT"
        self.version = [int(v) for v in VERSION.split()[0].split(".")]
        self.loop = asyncio.get_event_loop()
        self.state = self.root.wm_state()
        self.width = LAYOUTS[self.skin]["width"]
        self.height = LAYOUTS[self.skin]["height"]

        self.changes_made = False
        self.changes_draw = False
        self.is_playing = False
        self.is_loading = False
        self.is_m1_down = False
        self.is_m3_down = False
        self.is_shift_down = False
        self.resize = False
        self.file = ""
        self.tool = ""
        self.color = 0
        self.start_x = None  # workarounds for drawing lines and rectangles
        self.end_x = 0
        self.start_y = None
        self.end_y = 0
        self.animation = self.new_animation()  # animation data
        self.render_cache = {}
        self.pixel_cache = {}
        self.building = None
        self.timer = None
        self.duration = 0
        self.history = []
        self.history_index = 0
        self.history_events = 0
        self.audio = None
        self.block_hotkeys = False
        self.progress_window = False
        self.progress_bar = False
        self.frame_marker = None
        self.timeline_layer_list = []
        self.timeline_frames_select = None
        self.timeline_frames_select_line = None
        self.timeline_frames_select_frame = None
        self.mouse_pos = {"type": "stage", "event": None}  # workaround for drawing with shift

        # images
        self.path = os.path.dirname(os.path.realpath(__file__))
        self.images = {}
        self.waveform = None
        notfound = []

        for img in self.animation["stage"]["images"]:
            try:
                self.images[img] = tk.PhotoImage(
                    file=os.path.join(self.path, "images", self.animation["stage"]["images"][img]["src"]),
                    width=self.animation["stage"]["images"][img]["width"],
                    height=self.animation["stage"]["images"][img]["height"])
            except tk.TclError:
                notfound.append(self.animation["stage"]["images"][img]["src"])
                self.images[img] = tk.PhotoImage(width=self.animation["stage"]["images"][img]["width"],
                                                 height=self.animation["stage"]["images"][img]["height"])

        for img in LAYOUTS[self.skin]["images"]:
            try:
                self.images[img] = tk.PhotoImage(
                    file=os.path.join(self.path, "images", LAYOUTS[self.skin]["images"][img]["src"]),
                    width=LAYOUTS[self.skin]["images"][img]["width"],
                    height=LAYOUTS[self.skin]["images"][img]["height"])
            except tk.TclError:
                notfound.append(LAYOUTS[self.skin]["images"][img]["src"])
                self.images[img] = tk.PhotoImage(width=LAYOUTS[self.skin]["images"][img]["width"],
                                                 height=LAYOUTS[self.skin]["images"][img]["height"])
        if notfound:
            self.error("A keresett fájl nem található!", "Nem található(k): " + ",".join(notfound))

        # generate editor window
        self.root.minsize(self.width, self.height)
        self.root.configure(background=LAYOUTS[self.skin]["root"])
        self.root.protocol("WM_DELETE_WINDOW", self.file_quit)
        try:
            self.create_menubar()
            self.create_timeline()
            self.create_stage()
        except Exception as e:
            self.error("Nem sikerült létrehozni a menüelemeket!", e)
        self.render(True)

        # finishing window configuration
        self.edit_history_clear()
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<FocusIn>", self.on_focus)
        self.root.call('wm', 'iconphoto', self.root._w, self.images["icon"])
        self.on_focus()
        self.music_load()

    # generate required object for animation data
    def new_animation(self):
        data = {
            "header": HEADER,
            "version": self.version,
            "stage": deepcopy(PROFILES["SCH"]),
            "properties": {
                "title": "Ischmeretlen",
                "team": "Schapatnév",
                "year": time.strftime("%Y"),
                "music": "",
                "selected_layer": 0,
                "selected_frame": 0,
                "zoom": 10
            },
            "timeline": []
        }
        while len(data["stage"]["palette"]) < LAYOUTS[self.skin]["palette-length"]:
            data["stage"]["palette"].append("#ffffff")
        # TODO: allow the manual addition of multiple layers later
        for layer in ["Előtér", "Közép", "Háttér"]:
            data["timeline"].append({
                "name": layer,
                "type": "normal",
                "visible": True,
                "render": True,
                "frames": [{
                    "type": "empty",  # empty, matrix, link
                    "data": {}
                }]
            })
        return data

    # create menu for main window and for some right click popups
    def create_menubar(self):
        self.menubar = tk.Menu(self.root)

        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Új", command=self.file_new, underline=1, accelerator="Ctrl+N")
        self.root.bind_all("<Control-n>", self.file_new)
        self.file_menu.add_command(label="Megnyitás", command=self.file_open, underline=1, accelerator="Ctrl+O")
        self.root.bind_all("<Control-o>", self.file_open)
        self.file_menu.add_command(label="Mentés", command=self.file_save, underline=1, accelerator="Ctrl+S")
        self.root.bind_all("<Control-s>", self.file_save)
        self.file_menu.add_command(label="Mentés másként", command=self.file_save_as, underline=1,
                                   accelerator="Ctrl+Shift+S")
        self.root.bind_all("<Control-S>", self.file_save_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Importálás", command=self.file_import, underline=1, accelerator="Ctrl+I")
        self.root.bind_all("<Control-i>", self.file_import)
        self.file_menu.add_command(label="Exportálás", command=self.file_export, underline=1, accelerator="Ctrl+Enter")
        self.root.bind_all("<Control-Return>", self.file_export)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Kilépés", command=self.file_quit, underline=1, accelerator="Ctrl+Q")
        self.root.bind_all("<Control-q>", self.file_quit)

        self.edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.edit_menu.add_command(label="Visszavonás", command=self.edit_history_back, underline=1,
                                   accelerator="Ctrl+Z", state=tk.DISABLED)
        self.root.bind_all("<Control-z>", self.edit_history_back)
        self.edit_menu.add_command(label="Újra", command=self.edit_history_forward, underline=1, accelerator="Ctrl+Y",
                                   state=tk.DISABLED)
        self.root.bind_all("<Control-y>", self.edit_history_forward)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Képkocka kivágása", command=self.edit_cut, underline=1, accelerator="Ctrl+X")
        self.root.bind_all("<Control-x>", self.edit_cut)
        self.edit_menu.add_command(label="Képkocka másolása", command=self.edit_copy, underline=1, accelerator="Ctrl+C")
        self.root.bind_all("<Control-c>", self.edit_copy)
        self.edit_menu.add_command(label="Képkocka felülírása", command=self.edit_paste, underline=1,
                                   accelerator="Ctrl+V", state=tk.DISABLED)
        self.root.bind_all("<Control-v>", self.edit_paste)
        self.edit_menu.add_command(label="Képkocka beszúrása", command=self.edit_insert, underline=1,
                                   accelerator="Ctrl+B", state=tk.DISABLED)
        self.root.bind_all("<Control-b>", self.edit_insert)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Képkocka törlése", command=self.edit_remove, underline=1,
                                   accelerator="Backspace")
        self.root.bind_all("<BackSpace>", self.edit_remove)
        self.edit_menu.add_command(label="Képkocka tartalmának kiürítése", command=self.edit_empty, underline=1,
                                   accelerator="Del")
        self.root.bind_all("<Delete>", self.edit_empty)
        self.edit_menu.add_command(label="Képkocka duplikálása", command=self.edit_duplicate, underline=1,
                                   accelerator="Ctrl+D")
        self.root.bind_all("<Control-d>", self.edit_duplicate)
        self.root.bind_all("<F6>", self.edit_duplicate)
        self.edit_menu.add_command(label="Üres képkocka beszúrása", command=self.edit_insert_empty, underline=1,
                                   accelerator="Ctrl+E")
        self.root.bind_all("<Control-e>", self.edit_insert_empty)
        self.root.bind_all("<F7>", self.edit_insert_empty)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Képkocka hosszabbítása", command=self.edit_extend, underline=1,
                                   accelerator="+")
        self.root.bind_all("<Key-plus>", self.edit_extend)
        self.root.bind_all("<F5>", self.edit_extend)
        self.edit_menu.add_command(label="Képkocka rövidítése", command=self.edit_reduce, underline=1, accelerator="-")
        self.root.bind_all("<Key-minus>", self.edit_reduce)

        self.properties_menu = tk.Menu(self.menubar, tearoff=0)
        self.properties_menu.add_command(label="Animáció tulajdonságai", command=self.properties_animation)
        self.properties_menu.add_command(label="Színpad tulajdonságai", command=self.properties_stage,
                                         state=tk.DISABLED)
        self.properties_menu.add_command(label="Színpad nyújtása", command=self.properties_ratio, underline=1,
                                         accelerator="0")
        self.root.bind_all("<Key-0>", self.properties_ratio)
        self.properties_menu.add_command(label="Zene betöltése", command=self.properties_music)

        self.transform_menu = tk.Menu(self.menubar, tearoff=0)
        self.transform_menu.add_command(label="Elforgatás jobbra 90 fokkal", command=self.transform_rotate_right)
        self.transform_menu.add_command(label="Elforgatás balra 90 fokkal", command=self.transform_rotate_left)
        self.transform_menu.add_command(label="Vízszintes tükrözés", command=self.transform_flip_horizontal)
        self.transform_menu.add_command(label="Függőleges tükrözés", command=self.transform_flip_vertical)
        self.transform_menu.add_command(label="Elmozgatás felfelé", command=self.transform_move_up, underline=1,
                                        accelerator="(Shift) Up")
        self.root.bind_all("<Up>", self.transform_move_up)
        self.root.bind_all("<Shift-Up>", lambda event: self.transform_move_up(event, True))
        self.transform_menu.add_command(label="Elmozgatás lefelé", command=self.transform_move_down, underline=1,
                                        accelerator="(Shift) Down")
        self.root.bind_all("<Down>", self.transform_move_down)
        self.root.bind_all("<Shift-Down>", lambda event: self.transform_move_down(event, True))
        self.transform_menu.add_command(label="Elmozgatás balra", command=self.transform_move_left, underline=1,
                                        accelerator="(Shift) Left")
        self.root.bind_all("<Left>", self.transform_move_left)
        self.root.bind_all("<Shift-Left>", lambda event: self.transform_move_left(event, True))
        self.transform_menu.add_command(label="Elmozgatás jobbra", command=self.transform_move_right, underline=1,
                                        accelerator="(Shift) Right")
        self.root.bind_all("<Right>", self.transform_move_right)
        self.root.bind_all("<Shift-Right>", lambda event: self.transform_move_right(event, True))

        self.playback_menu = tk.Menu(self.menubar, tearoff=0)
        self.playback_menu.add_command(label="Lejátszás innen", command=self.playback_toggle, underline=1,
                                       accelerator="Space")
        self.root.bind_all("<space>", self.playback_toggle)
        self.playback_menu.add_command(label="Lejátszás az elejéről", command=self.playback_start, underline=1,
                                       accelerator="Enter")
        self.root.bind_all("<Return>", self.playback_start)
        self.playback_menu.add_command(label="Elejére", command=self.playback_rewind, underline=1, accelerator="Home")
        self.root.bind_all("<Home>", self.playback_rewind)
        self.playback_menu.add_command(label="Végére", command=self.playback_end, underline=1, accelerator="End")
        self.root.bind_all("<End>", self.playback_end)
        self.playback_menu.add_command(label="Egy kockát vissza", command=self.playback_back, underline=1,
                                       accelerator="PgDn")
        self.root.bind_all("<Next>", self.playback_back)
        self.playback_menu.add_command(label="Egy kockát előre", command=self.playback_next, underline=1,
                                       accelerator="PgUp")
        self.root.bind_all("<Prior>", self.playback_next)

        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label="Hiba bejelentés", command=self.other_issue, underline=1)
        self.help_menu.add_command(label="Névjegy", command=self.other_about, underline=1, accelerator="F1")
        self.root.bind_all("<F1>", self.other_about)

        self.menubar.add_cascade(label="Fájl", menu=self.file_menu)
        self.menubar.add_cascade(label="Szerkesztés", menu=self.edit_menu)
        self.menubar.add_cascade(label="Tulajdonságok", menu=self.properties_menu)
        self.menubar.add_cascade(label="Transzformáció", menu=self.transform_menu)
        self.menubar.add_cascade(label="Lejátszó", menu=self.playback_menu)
        self.menubar.add_cascade(label="Segítség", menu=self.help_menu)
        self.root.config(menu=self.menubar)

        self.root.bind_all("<Tab>", self.change_layer)
        self.root.bind_all("<Shift-Tab>", self.change_layer)
        self.root.bind_all("<Shift_L>", lambda event: self.press_shift(event, True))
        self.root.bind_all("<Shift_R>", lambda event: self.press_shift(event, True))
        self.root.bind_all("<KeyRelease>", lambda event: self.press_shift(event, False))

    # create tkinter widgets for timeline (layers & frame holder)
    def create_timeline(self):
        height = LAYOUTS[self.skin]["layer-height"] * 3 + LAYOUTS[self.skin]["layer-offset"]

        self.timeline = tk.Frame(self.root, bg=LAYOUTS[self.skin]["root"], bd=0, highlightthickness=0)
        tk.Grid.columnconfigure(self.timeline, 1, weight=1)
        self.timeline_layers = tk.Canvas(self.timeline, width=LAYOUTS[self.skin]["layer-width"], height=height,
                                         bg=LAYOUTS[self.skin]["root"], bd=0, highlightthickness=0)
        self.timeline_layers.grid(row=0, column=0, sticky="w")
        self.timeline_pos = tk.Label(self.timeline, font="fixedsys 10", text="x:-100 y: -100 ")
        self.timeline_pos.grid(row=1, column=0, sticky="en")
        self.timeline_frames = tk.Canvas(self.timeline, height=height)
        self.timeline_frames.grid(row=0, column=1, sticky="wen")
        self.timeline_scrollbar_h = tk.Scrollbar(self.timeline, orient='horizontal',
                                                 command=lambda a, b, c=None: [self.timeline_frames.xview(a, b, c),
                                                                               self.render_frames(True)])
        self.timeline_scrollbar_h.grid(row=1, column=1, sticky="wen")
        self.timeline_frames.config(xscrollcommand=self.timeline_scrollbar_h.set)
        self.timeline.pack(fill=tk.X)
        self.timeline_layers.bind("<Button-1>", self.mouse_click_layers)
        self.timeline_frames.bind("<Button-1>", self.mouse_click_frames)
        self.timeline_layers.bind("<Button-3>", self.mouse_popup_layers)
        self.timeline_frames.bind("<Button-3>", self.mouse_popup_frames)
        self.timeline_layers.bind('<Enter>', self.mouse_to_hand)
        self.timeline_layers.bind('<Leave>', self.mouse_to_default)
        self.timeline_frames.bind("<MouseWheel>", self.mouse_wheel_frames)

    # create tkitner widgets for stage (toolbar, stage, preview, color palette, playback)
    def create_stage(self):
        self.stage = tk.Frame(self.root, bg=LAYOUTS[self.skin]["toolbar"], bd=0)
        tk.Grid.columnconfigure(self.stage, 1, weight=1)
        tk.Grid.rowconfigure(self.stage, 0, weight=1)
        self.stage_tools = tk.Frame(self.stage, width=100, bg=LAYOUTS[self.skin]["toolbar"], bd=0, highlightthickness=0)
        self.stage_tools.grid(row=0, column=0, sticky="nswe")
        self.stage_tools_buttons = {}
        for i, button in enumerate(LAYOUTS[self.skin]["tools"]):
            self.stage_tools_buttons[button] = tk.Button(self.stage_tools, width=LAYOUTS[self.skin]["button-width"],
                                                         height=LAYOUTS[self.skin]["button-height"],
                                                         image=self.images[button], bg=LAYOUTS[self.skin]["button"],
                                                         bd=1)
            self.stage_tools_buttons[button]["command"] = lambda workaround=button: self.button_tool(workaround)
            self.stage_tools_buttons[button].grid(row=int(i / (LAYOUTS[self.skin]["toolbar-column"])),
                                                  column=int(i % LAYOUTS[self.skin]["toolbar-column"]), sticky="w")

        self.stage_editor = tk.Canvas(self.stage, bg=LAYOUTS[self.skin]["stage"], width=428, height=411, bd=0,
                                      highlightthickness=0)
        self.stage_editor.grid(row=0, column=1, sticky="nswe")
        self.stage_scrollbar_h = tk.Scrollbar(self.stage, orient='vertical', command=self.stage_editor.yview)
        self.stage_scrollbar_h.grid(row=0, column=2, sticky="ns")
        self.stage_scrollbar_w = tk.Scrollbar(self.stage, orient='horizontal', command=self.stage_editor.xview)
        self.stage_scrollbar_w.grid(row=1, column=1, sticky="we")
        self.stage_preview = tk.Canvas(self.stage, width=300, bg=self.animation["stage"]["skybox-color"], bd=0,
                                       highlightthickness=0)
        self.stage_preview.grid(row=0, column=3, sticky="nswe")
        self.stage.pack(fill=tk.BOTH, expand=True)
        self.stage_editor.configure(yscrollcommand=self.stage_scrollbar_h.set)
        self.stage_editor.configure(xscrollcommand=self.stage_scrollbar_w.set)

        self.stage_colorpicker_padding = tk.Frame(self.stage, bd=0, highlightthickness=0,
                                                  bg=LAYOUTS[self.skin]["toolbar"], width=428,
                                                  height=LAYOUTS[self.skin]["toolbar-padding"])
        self.stage_colorpicker_padding.grid(row=2, column=1, sticky="nswe")
        self.stage_colorpicker = tk.Frame(self.stage, bd=0, highlightthickness=0, bg=LAYOUTS[self.skin]["toolbar"],
                                          width=428, height=LAYOUTS[self.skin]["toolbar-height"] - LAYOUTS[self.skin][
                "toolbar-padding"])
        self.stage_colorpicker.grid(row=3, column=1, sticky="nswe")
        self.stage_colorpicker_buttons = []

        color = self.animation["stage"]["palette"][self.color]
        self.stage_colorpicker_buttons.append(
            tk.Button(self.stage_colorpicker, width=LAYOUTS[self.skin]["palette-select-width"],
                      height=LAYOUTS[self.skin]["palette-select-height"], image=self.images["palette-select"], bg=color,
                      highlightcolor=color, relief="flat", bd=0, highlightthickness=0, highlightbackground=color,
                      fg=color, activebackground=color, activeforeground=color, cursor="hand2"))
        self.stage_colorpicker_buttons[-1]["command"] = lambda: self.button_colorpicker(-1)
        self.stage_colorpicker_buttons[-1].grid(row=0, column=0, sticky="w")
        tk.Frame(self.stage_colorpicker, bg=LAYOUTS[self.skin]["toolbar"], width=LAYOUTS[self.skin]["palette-width"],
                 height=LAYOUTS[self.skin]["palette-height"]).grid(row=0, column=1, sticky="nswe")
        for i, color in enumerate(self.animation["stage"]["palette"]):
            self.stage_colorpicker_buttons.append(
                tk.Button(self.stage_colorpicker, width=LAYOUTS[self.skin]["palette-width"],
                          height=LAYOUTS[self.skin]["palette-height"], image=self.images["palette"], bg=color,
                          highlightcolor=color, relief="flat", bd=0, highlightthickness=0, highlightbackground=color,
                          fg=color, activebackground=color, activeforeground=color, cursor="hand2"))
            self.stage_colorpicker_buttons[-1]["command"] = lambda workaround=i: self.button_colorpicker(workaround)
            self.stage_colorpicker_buttons[-1].grid(row=0, column=i + 2, sticky="nswe")
            self.stage_colorpicker_buttons[-1].bind("<Button-3>",
                                                    lambda event, workaround=i: [self.button_colorpicker(workaround),
                                                                                 self.button_colorpicker(-1)])
        self.stage_colorpicker_buttons[0].bind("<Button-3>", lambda event: self.button_colorpicker(-1))
        self.stage_colorpicker_buttons[1].configure(image=self.images["palette-active"])

        self.stage_playback = tk.Frame(self.stage, bd=0, highlightthickness=0, bg=LAYOUTS[self.skin]["toolbar"],
                                       width=300, height=LAYOUTS[self.skin]["toolbar-height"])
        self.stage_playback.grid(row=3, column=3)
        self.stage_playback_rewind = tk.Button(self.stage_playback, width=LAYOUTS[self.skin]["button-width"],
                                               height=LAYOUTS[self.skin]["button-height"], image=self.images["rewind"],
                                               bg=LAYOUTS[self.skin]["button"], command=self.playback_rewind)
        self.stage_playback_rewind.grid(row=0, column=0, sticky="nsw")
        self.stage_playback_back = tk.Button(self.stage_playback, width=LAYOUTS[self.skin]["button-width"],
                                             height=LAYOUTS[self.skin]["button-height"], image=self.images["back"],
                                             bg=LAYOUTS[self.skin]["button"], command=self.playback_back)
        self.stage_playback_back.grid(row=0, column=1, sticky="nsw")
        self.stage_playback_toggle = tk.Button(self.stage_playback, width=LAYOUTS[self.skin]["button-active-width"],
                                               height=LAYOUTS[self.skin]["button-height"], image=self.images["play"],
                                               bg=LAYOUTS[self.skin]["button"], command=self.playback_toggle)
        self.stage_playback_toggle.grid(row=0, column=2, sticky="nswe")
        self.stage_playback_next = tk.Button(self.stage_playback, width=LAYOUTS[self.skin]["button-width"],
                                             height=LAYOUTS[self.skin]["button-height"], image=self.images["next"],
                                             bg=LAYOUTS[self.skin]["button"], command=self.playback_next)
        self.stage_playback_next.grid(row=0, column=3, sticky="nsw")
        self.stage_playback_end = tk.Button(self.stage_playback, width=LAYOUTS[self.skin]["button-width"],
                                            height=LAYOUTS[self.skin]["button-height"], image=self.images["end"],
                                            bg=LAYOUTS[self.skin]["button"], command=self.playback_end)
        self.stage_playback_end.grid(row=0, column=4, sticky="nse")

        self.stage_editor.bind('<Enter>', self.mouse_to_hand)
        self.stage_preview.bind('<Enter>', self.mouse_to_hand)
        self.stage_editor.bind('<Leave>', self.mouse_to_default)
        self.stage_preview.bind('<Leave>', self.mouse_to_default)
        self.stage_editor.bind("<Button-1>", self.mouse_click_stage)
        self.stage_preview.bind("<Button-1>", self.mouse_click_preview)
        self.stage_editor.bind("<ButtonRelease-1>", self.mouse_release_stage)
        self.stage_preview.bind("<ButtonRelease-1>", self.mouse_release_preview)
        self.stage_editor.bind("<Button-3>", self.mouse_popup_stage)
        self.stage_preview.bind("<Button-3>", self.mouse_popup_preview)
        self.stage_editor.bind("<ButtonRelease-3>", self.mouse_release_stage)
        self.stage_preview.bind("<ButtonRelease-3>", self.mouse_release_preview)
        self.stage_editor.bind("<Motion>", self.mouse_move_stage)
        self.stage_preview.bind("<Motion>", self.mouse_move_preview)
        self.stage_editor.bind("<MouseWheel>", self.mouse_wheel_stage)
        self.stage_preview.bind("<MouseWheel>", self.mouse_wheel_stage)

        for i, tool in enumerate(LAYOUTS[self.skin]["tools"]):
            self.root.bind_all("<Key-" + str(i + 1) + ">", lambda event, workaround=tool: self.button_tool(
                workaround) if not self.block_hotkeys else None)
        self.button_tool(LAYOUTS[self.skin]["tools"][0])

    ### RENDER ELEMENTS
    # render layers & layer select
    def render_layers(self, redraw=False):
        offset = LAYOUTS[self.skin]["layer-offset"]
        height = LAYOUTS[self.skin]["layer-height"] - 1
        width = LAYOUTS[self.skin]["layer-width"] - 1
        if redraw:
            self.timeline_layers.delete("all")
            self.timeline_layers_list = []
            for i, layer in enumerate(self.animation["timeline"]):
                self.timeline_layers_list.append(
                    self.timeline_layers.create_rectangle(0, offset + i * height, width, offset + (i + 1) * height,
                                                          fill=LAYOUTS[self.skin]["layer"],
                                                          outline=LAYOUTS[self.skin]["layer-outline"]))
                self.timeline_layers.create_line(0, offset + i * height, width, offset + i * height,
                                                 fill=LAYOUTS[self.skin]["layer-outline-highlight"])
                self.timeline_layers.create_line(0, offset + i * height, 0, offset + (i + 1) * height,
                                                 fill=LAYOUTS[self.skin]["layer-outline-highlight"])
                self.timeline_layers.create_text(10, offset + i * height + (height / 2),
                                                 fill=LAYOUTS[self.skin]["layer-color"], font="Helvetica 10",
                                                 text=layer["name"], anchor="w")
            self.timeline_layers.create_line(width, offset, width + 1, offset, fill=LAYOUTS[self.skin]["layer-color"])
        for i, layer in enumerate(self.timeline_layers_list):
            if i == self.animation["properties"]["selected_layer"]:
                self.timeline_layers.itemconfig(layer, fill=LAYOUTS[self.skin]["layer-active"])
            else:
                self.timeline_layers.itemconfig(layer, fill=LAYOUTS[self.skin]["layer"])

    # render visible frames, frame timing & frame select
    def render_frames(self, redraw=False):
        offset = LAYOUTS[self.skin]["layer-offset"] - 1
        width = LAYOUTS[self.skin]["frame-width"]
        height = LAYOUTS[self.skin]["layer-height"]
        max_frames = self.animation_length() + 50  # extra 5 seconds visible in editor
        max_height = (len(self.animation["timeline"]) + 1) * height
        max_width = max(60, int(self.timeline_frames.winfo_width() / width) + 1)
        visible_min = self.timeline_frames.canvasx(0)
        visible_min_i = max(0, int(visible_min / width) - 1)
        visible_max = self.timeline_frames.canvasx(self.timeline_frames.winfo_width())
        visible_max_i = int(visible_max / width) + 1
        if redraw:
            self.timeline_frames.delete("all")
            if self.waveform:
                self.timeline_frames.create_image(int((LAYOUTS[self.skin]["frame-width"] * (1000 / self.animation["stage"]["speed"]) * self.audio.duration())/2), int(LAYOUTS[self.skin]["layer-offset"]/2), image=self.waveform)

            for j in range(len(self.animation["timeline"])):
                workaround = self.animation["timeline"][j]["frames"][
                    min(visible_min_i, len(self.animation["timeline"][j]["frames"]) - 1)]["type"]
                if workaround == "link":
                    workaround = self.animation["timeline"][j]["frames"][self.animation["timeline"][j]["frames"][
                        min(visible_min_i, len(self.animation["timeline"][j]["frames"]) - 1)]["data"]]["type"]
                if workaround == "empty":
                    color = LAYOUTS[self.skin]["frame-empty"]
                else:
                    color = LAYOUTS[self.skin]["frame-matrix"]
                last = color
                stipple = "gray50"
                outline = LAYOUTS[self.skin]["frame-color"]
                cache_frame = 0
                for i in range(visible_min_i, max(max_width, max_frames * width) + 1):
                    if i < len(self.animation["timeline"][j]["frames"]):
                        if self.animation["timeline"][j]["frames"][i]["type"] == "empty":
                            if cache_frame:
                                if i * width > visible_min and ((i - cache_frame) * width + 1) < visible_max:
                                    self.timeline_frames.create_rectangle(
                                        max(visible_min, (i - cache_frame) * width + 1), offset + j * height + 1,
                                        min(visible_max, i * width), offset + (j + 1) * height, fill=color,
                                        stipple=stipple, outline="")
                                    if i > visible_max_i:
                                        break
                                cache_frame = 0
                            color = LAYOUTS[self.skin]["frame-empty"]
                            stipple = ""
                            outline = LAYOUTS[self.skin]["frame-border"]
                        elif self.animation["timeline"][j]["frames"][i]["type"] == "matrix":
                            if cache_frame:
                                if i * width > visible_min and ((i - cache_frame) * width + 1) < visible_max:
                                    self.timeline_frames.create_rectangle(
                                        max(visible_min, (i - cache_frame) * width + 1), offset + j * height + 1,
                                        min(visible_max, i * width), offset + (j + 1) * height, fill=color,
                                        stipple=stipple, outline="")
                                    if i > visible_max_i:
                                        break
                                cache_frame = 0
                            color = LAYOUTS[self.skin]["frame-matrix"]
                            stipple = ""
                            outline = LAYOUTS[self.skin]["frame-border"]
                        else:
                            color = last
                            stipple = "gray50"
                            outline = LAYOUTS[self.skin]["frame-color"]
                            cache_frame += 1
                        last = color
                        if not cache_frame:
                            if (i + 1) * width > visible_min and i * width < visible_max:
                                self.timeline_frames.create_rectangle(i * width + 1, offset + j * height + 1,
                                                                      (i + 1) * width, offset + (j + 1) * height,
                                                                      fill=color, stipple=stipple, outline=color)
                                if i > visible_max_i:
                                    break
                    else:
                        stipple = "gray50"
                        if i == len(self.animation["timeline"][j]["frames"]):
                            self.timeline_frames.create_line(i * width + 1, offset + j * height + 1, i * width + 1,
                                                             offset + (j + 1) * height, fill=outline)
                            if i > visible_max_i:
                                break
                        outline = LAYOUTS[self.skin]["frame-color"]
                    # self.timeline_frames.create_line(i*width, offset+j*height+1, i*width, offset+(j+1)*height, fill=outline)
                    if j == 0:
                        if (i + 1) * width + 1 > visible_min and i * width - 1 < visible_max:
                            if i % 10 == 0:
                                self.timeline_frames.create_text(i * width + 6, offset - 12,
                                                                 fill=LAYOUTS[self.skin]["layer-color"],
                                                                 font="Helvetica 10", text=str(int(i / 10)))
                                self.timeline_frames.create_line(i * width + 1, offset - 10, i * width + 1, offset,
                                                                 fill=LAYOUTS[self.skin]["layer-color"])
                            elif i % 5 == 0:
                                self.timeline_frames.create_line(i * width + 1, offset - 10, i * width + 1, offset,
                                                                 fill=LAYOUTS[self.skin]["layer-color"])
                            else:
                                self.timeline_frames.create_line(i * width + 1, offset - 5, i * width + 1, offset,
                                                                 fill=LAYOUTS[self.skin]["layer-color"])
                if cache_frame:
                    if len(self.animation["timeline"][j]["frames"]) * width > visible_min and (
                            (len(self.animation["timeline"][j]["frames"]) - cache_frame) * width + 1) < visible_max:
                        self.timeline_frames.create_rectangle(
                            max(visible_min, (len(self.animation["timeline"][j]["frames"]) - cache_frame) * width + 1),
                            offset + j * height + 1,
                            min(visible_max, len(self.animation["timeline"][j]["frames"]) * width),
                            offset + (j + 1) * height, fill=color, stipple=stipple, outline="")
            self.timeline_frames.create_line(max(visible_min, 0), offset,
                                             min(visible_max, (max(max_width, max_frames * width) + 1) * width + 1),
                                             offset, fill=LAYOUTS[self.skin]["layer-color"])
            if self.frame_marker:
                self.timeline_frames.delete(self.frame_marker)
                self.frame_marker = None
        try:
            self.timeline_frames.delete(self.timeline_frames_select)
            self.timeline_frames.delete(self.timeline_frames_select_line)
            self.timeline_frames.delete(self.timeline_frames_select_frame)
        except AttributeError:
            pass

        self.timeline_frames_select = self.timeline_frames.create_rectangle(
            self.animation["properties"]["selected_frame"] * width + 1, 1,
            (self.animation["properties"]["selected_frame"] + 1) * width - 1, offset,
            outline=LAYOUTS[self.skin]["frame-active"], fill=LAYOUTS[self.skin]["frame-active"], stipple="gray50")
        self.timeline_frames_select_line = self.timeline_frames.create_line(
            int(self.animation["properties"]["selected_frame"] * width + width * .5), offset + 2,
            int(self.animation["properties"]["selected_frame"] * width + width * .5), max_height,
            fill=LAYOUTS[self.skin]["frame-active"], stipple="gray25")
        self.timeline_frames_select_frame = self.timeline_frames.create_rectangle(
            self.animation["properties"]["selected_frame"] * width + 1,
            offset + self.animation["properties"]["selected_layer"] * height,
            (self.animation["properties"]["selected_frame"] + 1) * width - 1,
            offset + (self.animation["properties"]["selected_layer"] + 1) * height,
            outline=LAYOUTS[self.skin]["frame-active"], fill="", stipple="gray50")
        self.timeline_frames.configure(scrollregion=(0, 0, (max(max_width, max_frames) + 10) * width, height))
        self.timeline_frames.update()

    # render stage & pixels visible at the current position (based on selected layer and frame)
    def render_stage(self, redraw=False, play=False):
        if redraw:
            size_x = max(1, self.animation["properties"]["zoom"])
            size_y = int(size_x * self.animation["stage"]["ratio"])
            width = self.stage_editor.winfo_width()
            height = self.stage_editor.winfo_height()
            p_width = self.animation["stage"]["width"]
            p_height = self.animation["stage"]["height"]
            left = int((width - p_width * size_x) / 2)
            top = int((height - p_height * size_y) / 2)

            if not play:
                self.stage_editor.delete("all")
                if size_x < 12:
                    self.stage_editor.create_rectangle(left, top, left + p_width * size_x, top + p_height * size_y,
                                                       fill=self.animation["stage"]["stage-color"],
                                                       outline=self.animation["stage"]["border-color"])
                else:
                    for x in range(p_width):
                        for y in range(p_height):
                            self.stage_editor.create_rectangle(left + size_x * x, top + size_y * y,
                                                               left + size_x * (x + 1), top + size_y * (y + 1),
                                                               fill=self.animation["stage"]["stage-color"],
                                                               outline=self.animation["stage"]["border-color"])
                self.stage_editor.create_line(left + int(p_width * size_x / 2), top, left + int(p_width * size_x / 2),
                                              top + p_height * size_y, fill=self.animation["stage"]["border-color"],
                                              width=2)
                self.stage_editor.create_line(left, top + int(p_height * size_y / 2), left + p_width * size_x,
                                              top + int(p_height * size_y / 2),
                                              fill=self.animation["stage"]["border-color"], width=2)

            min_x, min_y, max_x, max_y = 0, 0, p_width, p_height
            self.render_cache = {}
            for i, layer in enumerate(reversed(self.animation["timeline"])):
                if layer["visible"] or layer["render"]:
                    if self.animation["properties"]["selected_layer"] != len(self.animation["timeline"]) - 1 - i:
                        stipple = "gray50"
                    else:
                        stipple = ""
                    frame, select = self.get_frame(layer)
                    is_empty = True
                    for x in frame:
                        for y in frame[x]:
                            is_empty = False
                            if not play:
                                min_x = min(min_x, x)
                                min_y = min(min_y, y)
                                max_x = max(max_x, x)
                                max_y = max(max_y, y)
                                if layer["visible"]:
                                    self.stage_editor.create_rectangle(left + x * size_x, top + y * size_y,
                                                                       left + (x + 1) * size_x, top + (y + 1) * size_y,
                                                                       fill=frame[x][y], outline="", stipple=stipple)
                            if layer["render"]:
                                # create cache for preview
                                if x >= 0 and x < p_width and y >= 0 and y < p_height:
                                    if x not in self.render_cache:
                                        self.render_cache[x] = {}
                                    if play:
                                        if y in self.render_cache[x] and self.render_cache[x][y] == frame[x][y]:
                                            self.render_cache[x][y] = ""
                                        else:
                                            self.render_cache[x][y] = frame[x][y]
                                    else:
                                        self.render_cache[x][y] = frame[x][y]
                    if not play:
                        if is_empty:
                            layer["frames"][select]["type"] = "empty"
                        else:
                            layer["frames"][select]["type"] = "matrix"
            if not play:
                x_scroll = max(max((min_x + 1) * size_x, (max(p_width, max_x - min_x) + 1) * size_x),
                               width - p_width * size_x)
                y_scroll = max(max((min_y + 1) * size_y, (max(p_height, max_y - min_y) + 1) * size_y),
                               height - p_height * size_y)
                self.stage_editor.configure(scrollregion=(-x_scroll / 2, -y_scroll / 2, x_scroll * 2, y_scroll * 2))

    # render preview window, timer and currently visible pixels that were calculated in "render_stage" function (based on visible frames in all layers)
    def render_preview(self, redraw=False, play=False):
        height = self.stage_preview.winfo_height()
        offset_x = self.animation["stage"]["offset_x"]
        offset_y = height - self.animation["stage"]["images"]["preview"]["height"] + self.animation["stage"]["offset_y"]

        if redraw:
            self.stage_preview.delete("all")
            self.building = self.stage_preview.create_image(
                int(self.animation["stage"]["images"]["preview"]["width"] / 2),
                height - int(self.animation["stage"]["images"]["preview"]["height"] / 2), image=self.images["preview"])
            self.timer = self.stage_preview.create_text(self.animation["stage"]["font-x"],
                                                        self.animation["stage"]["font-y"],
                                                        fill=self.animation["stage"]["font-color"], font="fixedsys 10",
                                                        text="00:00 - 00:00")
            d = self.animation_length() * self.animation["stage"]["speed"] / 1000
            m = int(d / 60)
            s = int(d - m * 60)
            self.duration = str(m).zfill(2) + ":" + str(s).zfill(2)
        # self.stage_preview.create_rectangle(0, height, width, self.stage_preview.winfo_height(), fill=LAYOUTS[self.skin]["toolbar"], outline="")
        if not play:
            for x in range(self.animation["stage"]["width"]):
                for y in range(self.animation["stage"]["height"]):
                    px = int(
                        offset_x + x * self.animation["stage"]["size_x"] + int(x / self.animation["stage"]["skip_x"]) *
                        self.animation["stage"]["pad_x"])
                    py = int(
                        offset_y + y * self.animation["stage"]["size_y"] + int(y / self.animation["stage"]["skip_y"]) *
                        self.animation["stage"]["pad_y"])
                    if x in self.render_cache and y in self.render_cache[x]:
                        color = self.render_cache[x][y]
                    else:
                        color = self.animation["stage"]["background-color"]
                    if x not in self.pixel_cache:
                        self.pixel_cache[x] = {}
                    self.pixel_cache[x][y] = self.stage_preview.create_rectangle(px, py,
                                                                                 px + self.animation["stage"]["size_x"],
                                                                                 py + self.animation["stage"]["size_y"],
                                                                                 fill=color, outline="")
        else:
            for x in range(self.animation["stage"]["width"]):
                for y in range(self.animation["stage"]["height"]):
                    if x in self.render_cache and y in self.render_cache[x]:
                        color = self.render_cache[x][y]
                    else:
                        color = self.animation["stage"]["background-color"]
                    if color:
                        self.stage_preview.itemconfig(self.pixel_cache[x][y], fill=color)
        if self.timer:
            d = self.animation["properties"]["selected_frame"] * self.animation["stage"]["speed"] / 1000
            m = int(d / 60)
            s = int(d - m * 60)
            timestamp = str(m).zfill(2) + ":" + str(s).zfill(2)
            self.stage_preview.itemconfig(self.timer, text=timestamp + " - " + self.duration)

    # quickly draw pixels on editor without much overhead (please call "render_stage" after)
    def render_stage_helper(self, x, y, color):
        size_x = max(1, self.animation["properties"]["zoom"])
        size_y = size_x * self.animation["stage"]["ratio"]
        width = self.stage_editor.winfo_width()
        height = self.stage_editor.winfo_height()
        p_width = self.animation["stage"]["width"]
        p_height = self.animation["stage"]["height"]
        left = int((width - p_width * size_x) / 2)
        top = int((height - p_height * size_y) / 2)
        self.stage_editor.create_rectangle(left + x * size_x, top + y * size_y, left + (x + 1) * size_x,
                                           top + (y + 1) * size_y, fill=color, outline="")

    # quickly draw pixels on preview without much overhead (please call "render_preview" after)
    def render_preview_helper(self, x, y, color):
        height = self.stage_preview.winfo_height()
        offset_x = self.animation["stage"]["offset_x"]
        offset_y = height - self.animation["stage"]["images"]["preview"]["height"] + self.animation["stage"]["offset_y"]
        px = int(offset_x + x * self.animation["stage"]["size_x"] + int(x / self.animation["stage"]["skip_x"]) *
                 self.animation["stage"]["pad_x"])
        py = int(offset_y + y * self.animation["stage"]["size_y"] + int(y / self.animation["stage"]["skip_y"]) *
                 self.animation["stage"]["pad_y"])
        self.stage_preview.create_rectangle(px, py, px + self.animation["stage"]["size_x"],
                                            py + self.animation["stage"]["size_y"], fill=color, outline="")

    # mark a frame on timeline after copy/cut
    def render_frames_mark(self):
        if self.frame_marker:
            self.timeline_frames.delete(self.frame_marker)
        offset = LAYOUTS[self.skin]["layer-offset"] - 1
        width = LAYOUTS[self.skin]["frame-width"]
        height = LAYOUTS[self.skin]["layer-height"]
        top = self.animation["properties"]["selected_layer"] * height + offset
        self.frame_marker = self.timeline_frames.create_rectangle(
            self.animation["properties"]["selected_frame"] * width + 1, top,
            (self.animation["properties"]["selected_frame"] + 1) * width - 1, top + height, outline="",
            fill=LAYOUTS[self.skin]["frame-marker"], stipple="gray50")

    # call most common render functions at once
    def render(self, redraw=False):
        self.loading(True)
        try:
            self.title()
            self.render_layers(redraw)
            self.render_frames(redraw)
            self.render_stage(redraw)
            self.render_preview(redraw)
            self.changes_draw = False
        except Exception as e:
            self.error("Sikertelen az elemek kirajzolása!", e)
        self.loading(False)

    # change title of main window
    def title(self, name=""):
        if not name:
            name = self.animation["properties"]["title"]
        if not self.file:
            file = ""
        else:
            file = " (" + self.file + ")"
        self.root.title(TITLE + " " + VERSION + " - " + name + file)

    ##### MENU FUNCITONS #####
    ### FILE FUNCTIONS

    # new animation
    def file_new(self, event=None):
        self.playback_pause()
        if self.changes_made:
            response = messagebox.askyesnocancel(title="Új animáció létrehozása",
                                                 message="Új animáció létrehozása előtt szeretnéd menteni a változtatásokat?",
                                                 default=messagebox.YES)
            if response:
                self.file_save()
            elif response is None:
                return
        self.file = ""
        self.changes_made = False
        self.changes_draw = False
        self.animation = self.new_animation()
        self.edit_history_clear()
        self.refresh_colorpicker()
        self.music_load()
        self.timeline_frames.xview("moveto", 0.0, None)
        self.render(True)

    # open animation (check if it's an actual animation file & check it's verion)
    def file_open(self, event=None):
        self.playback_pause()
        if self.changes_made:
            response = messagebox.askyesnocancel(title="Másik animáció megnyitása",
                                                 message="Másik animáció megnyitása előtt szeretnéd menteni a változtatásokat?",
                                                 default=messagebox.YES)
            if response:
                self.file_save()
            elif response is None:
                return
        self.root.update()
        file = askopenfilename(defaultextension="*.qpy", initialdir="C:/Documents/",
                               filetypes=(("QPY animációs fájl", "*.qpy"),), title="Megnyitás")
        if file:
            self.file = file
            try:
                self.loading_progress(10)
                time.sleep(.25)
                self.loading(True)
                with codecs.open(self.file, "r", encoding="utf-8") as f:
                    data = f.read()
                self.loading_progress(20)
                if '"' + HEADER + '"' not in data and "'" + HEADER + "'" not in data:
                    self.loading_progress(100)
                    return self.error("Nem megfelelő formátum!", "A kiválasztott fájl nem Mátrix animáció!")
                try:
                    self.loading_progress(50)
                    data = json.loads(data)
                except Exception as e:
                    self.loading_progress(100)
                    return self.error("Hibás vagy sérült fájl!", e)
                if "header" not in data or data["header"] != HEADER:
                    self.loading_progress(100)
                    return self.error("Nem megfelelő formátum!", "A kiválasztott fájl nem Mátrix animáció!")
                if "version" in data and "stage" in data and "properties" in data and "timeline" in data:
                    if data["version"][0] > self.version[0] or data["version"][1] > self.version[1] or data["version"][
                        2] > self.version[2]:
                        # TODO: auto update
                        messagebox.showinfo("Eltérő verziók!",
                                            "Ez az animáció egy eltérő verziójú szerkesztőben lett létrehozva!\nElőfordulhat, hogy az animáció nem megfelelően fog megjelenni.")
                    self.loading_progress(75)
                    self.animation = self.json_fix(data)
                    ### add variables for backward compatiblity
                    if "ratio" not in self.animation["stage"]:
                        self.animation["stage"]["ratio"] = PROFILES["SCH"]["ratio"]
                    if "stage-color" not in self.animation["stage"]:
                        self.animation["stage"]["stage-color"] = PROFILES["SCH"]["stage-color"]
                    if "shift" not in self.animation["stage"]:
                        self.animation["stage"]["shift"] = PROFILES["SCH"]["shift"]
                    self.changes_made = False
                    self.changes_draw = False
                    self.loading_progress(90)
                    self.edit_history_clear()
                    self.refresh_colorpicker()
                    self.music_load()
                    self.timeline_frames.xview("moveto", self.animation["properties"]["selected_frame"] / (
                        self.animation_length()), None)
                    self.render_frames(True)
                else:
                    self.loading_progress(100)
                    return self.error("Hibás vagy sérült fájl!", "A fájl alapján nem hozható létre animáció.")
            except Exception as e:
                self.loading_progress(100)
                self.error("Nem sikerült megnyitni a fájlt!", e)
            self.render(True)
            self.loading(False)
            self.loading_progress(100)

    # save animation
    def file_save(self, event=None):
        if self.file:
            try:
                self.loading(True)
                f = codecs.open(self.file, "w+", encoding="utf-8")
                self.animation["version"] = self.version
                f.write(json.dumps(self.animation))
                f.close()
                self.changes_made = False
                self.changes_draw = False
                self.loading(False)
            except Exception as e:
                return self.error("Nem sikerült menteni!", e)
        else:
            self.file_save_as(event)

    # save animation as
    def file_save_as(self, event=None):
        self.playback_pause()
        self.root.update()
        file = asksaveasfilename(defaultextension="*.qpy", initialdir="C:/Documents/",
                                 filetypes=(("QPY animációs fájl", "*.qpy"),))
        if file:
            self.file = file
            try:
                self.loading(True)
                f = codecs.open(self.file, "w+", encoding="utf-8")
                self.animation["version"] = self.version
                f.write(json.dumps(self.animation))
                f.close()
                self.changes_made = False
                self.changes_draw = False
                self.loading(False)
                self.render(True)
            except Exception as e:
                return self.error("Nem sikerült menteni!", e)

    # export animation as *.qp4 (calls actual async export function)
    def file_export(self, event=None):
        if self.is_loading:
            return
        self.playback_pause()
        self.root.update()
        file = asksaveasfilename(defaultextension="*.qp4", initialdir="C:/Documents/",
                                 filetypes=(("AnimEditor2012 fájl", "*.qp4"),), title="Exportálás")
        if file:
            self.async_run(self.async_export(file))

    # import animation as *.qp4 (calls actual async import function)
    def file_import(self, event=None):
        self.root.update()
        file = askopenfilename(defaultextension="*.qp4", initialdir="C:/Documents/",
                               filetypes=(("AnimEditor2012 fájl", "*.qp4"),), title="Importálás")
        if file:
            self.async_run(self.async_import(file))

    # see if changes were made before closing window (automatically called when the X button is pressed)
    def file_quit(self, event=None):
        if self.changes_made:
            response = messagebox.askyesnocancel(title="Kilépés a szerkesztőből",
                                                 message="Kilépés előtt szeretnéd menteni a változtatásokat?",
                                                 default=messagebox.YES)
            if response:
                self.file_save()
            elif response is None:
                return
        try:
            self.root.destroy()
        except:
            pass

    ### EDIT FUNCTIONS

    # undo
    def edit_history_back(self, event=None):
        if self.history:
            if self.history_index > 0:
                self.history_index -= 1
                self.animation = self.copy_animation(self.history[self.history_index]["data"])
                self.edit_menu.entryconfigure(0, state=tk.NORMAL)
                if self.history[self.history_index]["type"]:
                    self.edit_menu.entryconfigure(0, label="Visszavonás: " + self.history[self.history_index]["type"])
                else:
                    self.edit_menu.entryconfigure(0, label="Visszavonás")
            if not self.history_index:
                self.edit_menu.entryconfigure(0, state=tk.DISABLED)
                self.edit_menu.entryconfigure(0, label="Visszavonás")
            if self.history_index < len(self.history) - 1:
                self.edit_menu.entryconfigure(1, state=tk.NORMAL)
                if self.history[(self.history_index + 1)]["type"]:
                    self.edit_menu.entryconfigure(1, label="Újra: " + self.history[(self.history_index + 1)]["type"])
                else:
                    self.edit_menu.entryconfigure(1, label="Újra")
            else:
                self.edit_menu.entryconfigure(1, state=tk.DISABLED)
            self.history_events += 1
            self.refresh_colorpicker()
            self.render(True)

    # redo
    def edit_history_forward(self, event=None):
        if self.history:
            if self.history_index < len(self.history) - 1:
                if self.history[self.history_index]["type"]:
                    self.edit_menu.entryconfigure(1, label="Újra: " + self.history[self.history_index]["type"])
                else:
                    self.edit_menu.entryconfigure(1, label="Újra")
                self.history_index += 1
                self.animation = self.copy_animation(self.history[self.history_index]["data"])
                self.edit_menu.entryconfigure(1, state=tk.NORMAL)
            if self.history_index >= len(self.history) - 1:
                self.edit_menu.entryconfigure(1, state=tk.DISABLED)
                self.edit_menu.entryconfigure(1, label="Újra")
            if self.history_index > 0:
                self.edit_menu.entryconfigure(0, state=tk.NORMAL)
                if self.history[(self.history_index)]["type"]:
                    self.edit_menu.entryconfigure(0, label="Visszavonás: " + self.history[(self.history_index)]["type"])
                else:
                    self.edit_menu.entryconfigure(0, label="Visszavonás")
            else:
                self.edit_menu.entryconfigure(0, state=tk.DISABLED)
            self.history_events += 1
            self.refresh_colorpicker()
            self.render(True)

    # add event to history
    def edit_history_add(self, type=""):
        if not LAYOUTS[self.skin]["history_size"]:
            self.history = []
        elif LAYOUTS[self.skin]["history_size"]:
            self.history = self.history[:self.history_index + 1]
            self.history.append({
                "type": type,
                "data": self.copy_animation(self.animation)
            })
            self.history = self.history[-(LAYOUTS[self.skin]["history_size"] + 1):]
        self.history_index = len(self.history) - 1
        if self.history:
            self.edit_menu.entryconfigure(0, state=tk.NORMAL)
            if type:
                self.edit_menu.entryconfigure(0, label="Visszavonás: " + type)
            else:
                self.edit_menu.entryconfigure(0, label="Visszavonás")
            self.edit_menu.entryconfigure(1, state=tk.DISABLED)
            self.edit_menu.entryconfigure(1, label="Újra")
            if len(self.history) > 1:
                self.changes_made = True
        self.history_events += 1

    # clear history	and add an empty event
    def edit_history_clear(self):
        self.history = []
        self.history_index = 0
        self.edit_history_add()
        self.edit_menu.entryconfigure(0, state=tk.DISABLED)
        self.edit_menu.entryconfigure(0, label="Visszavonás")
        self.edit_menu.entryconfigure(1, state=tk.DISABLED)
        self.edit_menu.entryconfigure(1, label="Újra")

    # cut frame
    def edit_cut(self, event=None):
        frame, select = self.get_frame(self.animation["timeline"][self.animation["properties"]["selected_layer"]])
        data = {
            "header": HEADER,
            "type": "cut",
            "layer": self.animation["properties"]["selected_layer"],
            "select": select,
            "events": self.history_events,
            "frame": deepcopy(frame)
        }
        self.root.clipboard_clear()
        self.root.clipboard_append(json.dumps(data))
        self.edit_menu.entryconfigure(5, state=tk.NORMAL)
        self.edit_menu.entryconfigure(6, state=tk.NORMAL)
        self.render_frames_mark()

    # copy frame
    def edit_copy(self, event=None):
        frame, select = self.get_frame(self.animation["timeline"][self.animation["properties"]["selected_layer"]])
        data = {
            "header": HEADER,
            "type": "copy",
            "layer": self.animation["properties"]["selected_layer"],
            "select": select,
            "events": self.history_events,
            "frame": deepcopy(frame)
        }
        self.root.clipboard_clear()
        self.root.clipboard_append(json.dumps(data))
        self.edit_menu.entryconfigure(5, state=tk.NORMAL)
        self.edit_menu.entryconfigure(6, state=tk.NORMAL)
        self.render_frames_mark()

    # paste frame (overwrite)
    def edit_paste(self, event=None):
        try:
            clipboard = json.loads(self.root.clipboard_get())
        except:
            return
        if "header" in clipboard and clipboard["header"] == HEADER:
            frame = {"type": "empty", "data": {}}
            is_empty = True
            for x in clipboard["frame"]:
                if int(x) not in frame:
                    frame["data"][int(x)] = {}
                for y in clipboard["frame"][x]:
                    frame["data"][int(x)][int(y)] = clipboard["frame"][x][y]
                    is_empty = False
            if not is_empty:
                frame["type"] = "matrix"
            if clipboard["type"] == "cut":
                if self.history_events == clipboard["events"]:
                    self.animation["timeline"][clipboard["layer"]]["frames"][clipboard["select"]] = {"type": "empty",
                                                                                                     "data": {}}
            self.overwrite_frame(self.animation["properties"]["selected_frame"], frame)
            if clipboard["type"] == "cut":
                self.edit_history_add("kivágás vágólapról")
            else:
                self.edit_history_add("másolás vágólapról")
        self.render(True)

    # paste frame (insert after selected)
    def edit_insert(self, event=None):
        try:
            clipboard = json.loads(self.root.clipboard_get())
        except:
            return
        if "header" in clipboard and clipboard["header"] == HEADER:
            frame = {"type": "empty", "data": {}}
            is_empty = True
            for x in clipboard["frame"]:
                if int(x) not in frame:
                    frame["data"][int(x)] = {}
                for y in clipboard["frame"][x]:
                    frame["data"][int(x)][int(y)] = clipboard["frame"][x][y]
                    is_empty = False
            if not is_empty:
                frame["type"] = "matrix"
            if clipboard["type"] == "cut":
                if self.history_events == clipboard["events"]:
                    self.animation["timeline"][clipboard["layer"]]["frames"][clipboard["select"]] = {"type": "empty",
                                                                                                     "data": {}}
            self.insert_frame_extra(self.animation["properties"]["selected_frame"], frame)
            if clipboard["type"] == "cut":
                self.edit_history_add("kivágás és beszúrás vágólapról")
            else:
                self.edit_history_add("másolás és beszúrás vágólapról")
        self.render(True)

    # remove frame
    def edit_remove(self, event=None):
        if self.block_hotkeys:
            return
        self.remove_frame(self.animation["properties"]["selected_frame"])
        self.edit_history_add("képkocka törlése")
        self.render(True)

    # delete contents of a frame
    def edit_empty(self, event=None):
        if self.block_hotkeys:
            return
        if self.animation["properties"]["selected_frame"] < len(
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"]):
            if self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][
                self.animation["properties"]["selected_frame"]]["type"] == "link":
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][
                    self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][
                        self.animation["properties"]["selected_frame"]]["data"]] = {"type": "empty", "data": {}}
            else:
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][
                    self.animation["properties"]["selected_frame"]] = {"type": "empty", "data": {}}
            self.edit_history_add("képkocka tartalmának kiürítése")
            self.render(True)

    # duplicate selected frame
    def edit_duplicate(self, event=None):
        frame, select = self.get_frame(self.animation["timeline"][self.animation["properties"]["selected_layer"]])
        if frame:
            self.insert_frame_extra(self.animation["properties"]["selected_frame"],
                                    {"type": "matrix", "data": deepcopy(frame)})
        else:
            self.insert_frame_extra(self.animation["properties"]["selected_frame"], {"type": "empty", "data": {}})
        self.edit_history_add("képkocka duplikálása utána")
        self.render_frames(True)

    # insert an empty frame
    def edit_insert_empty(self, event=None):
        self.insert_frame_extra(self.animation["properties"]["selected_frame"], {"type": "empty", "data": {}})
        self.edit_history_add("üres képkocka beszúrása utána")
        self.render(True)

    # extend duration of selected frame
    def edit_extend(self, event=None):
        self.extend_frame(self.animation["properties"]["selected_frame"])
        self.edit_history_add("képkocka hosszabbítása")
        self.render_frames(True)

    # reduce duration of selected frame
    def edit_reduce(self, event=None):
        self.reduce_frame(self.animation["properties"]["selected_frame"])
        self.edit_history_add("képkocka rövidítése")
        self.render_frames(True)

    ### SET ANIMATION PROPERTIES

    # set title, team for animation (blocks hotkeys while typing)
    def properties_animation(self, event=None):
        self.block_hotkeys = True
        self.properties_window = tk.Toplevel(self.root)
        self.properties_window.wm_title("Beállítások")
        l_title = tk.Label(self.properties_window, text="Animáció címe:")
        l_title.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=(10, 0))
        self.v_title = tk.StringVar(self.properties_window)
        self.v_title.set(self.animation["properties"]["title"])
        e_title = tk.Entry(self.properties_window, textvariable=self.v_title)
        e_title.grid(row=0, column=1, sticky="we", padx=(10, 20), pady=(10, 0))
        l_team = tk.Label(self.properties_window, text="Csapatnév:")
        l_team.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=(0, 10))
        self.v_team = tk.StringVar(self.properties_window)
        self.v_team.set(self.animation["properties"]["team"])
        e_team = tk.Entry(self.properties_window, textvariable=self.v_team)
        e_team.grid(row=1, column=1, sticky="we", padx=(10, 20), pady=(0, 0))
        save = tk.Button(self.properties_window, text="Mentés", command=lambda: [
            self.properties_update({"title": self.v_title.get(), "team": self.v_team.get()}), self.properties_quit()])
        save.grid(row=2, column=1, sticky="we", padx=(10, 20), pady=(10, 10))
        self.properties_window.protocol("WM_DELETE_WINDOW", self.properties_quit)

    # animation properties window is closed (reenables hotkeys as the user is no longer typing)
    def properties_quit(self, event=None):
        self.block_hotkeys = False
        self.properties_window.destroy()

    # update animation properties
    def properties_update(self, data):
        for key in data:
            self.animation["properties"][key] = data[key]
        self.edit_history_add("tulajdonságok szerkesztése")
        self.render(True)

    # set the properties used by rendering functions of the current animation profile (not yet implemented)
    def properties_stage(self, event=None):
        self.log("Stage properties disabled")

    # stretch the stage to resemble the pixel offsets in preview
    def properties_ratio(self, event=None):
        if self.is_playing:
            return
        if self.animation["stage"]["ratio"] == 1:
            self.animation["stage"]["ratio"] = PROFILES["SCH"]["ratio"]
        else:
            self.animation["stage"]["ratio"] = 1
        self.render(True)

    # load path to mp3 file (playback of selected mp3 is handled elsewhere)
    def properties_music(self, event=None):
        self.root.update()
        file = askopenfilename(defaultextension="*.mp3", initialdir="C:/Documents/",
                               filetypes=(("MP3 hangfájlok", "*.mp3"),), title="Hangfájl hozzáadása")
        if file:
            self.animation["properties"]["music"] = file
            self.music_load()

    ### TRANSFORM FUNCTIONS

    # rotate 90 deg right
    def transform_rotate_right(self, event=None):
        if self.is_playing or self.is_loading:
            return
        self.rotate(True)

    # rotate 90 deg left
    def transform_rotate_left(self, event=None):
        if self.is_playing or self.is_loading:
            return
        self.rotate(False)

    # flip horizontally
    def transform_flip_horizontal(self, event=None):
        if self.is_playing or self.is_loading:
            return
        self.flip(True)

    # flip vertically
    def transform_flip_vertical(self, event=None):
        if self.is_playing or self.is_loading:
            return
        self.flip(False)

    # move all selected pixels one pixel up
    def transform_move_up(self, event=None, double=None):
        if self.is_playing or self.is_loading:
            return
        self.move(0, -1 * self.animation["stage"]["shift"] if double else -1)

    # move all selected pixels one pixeldown
    def transform_move_down(self, event=None, double=None):
        if self.is_playing or self.is_loading:
            return
        self.move(0, self.animation["stage"]["shift"] if double else 1)

    # move all selected pixels one pixel left
    def transform_move_left(self, event=None, double=None):
        if self.is_playing or self.is_loading:
            return
        self.move(-1 * self.animation["stage"]["shift"] if double else -1, 0)

    # move all selected pixels one pixel right
    def transform_move_right(self, event=None, double=None):
        if self.is_playing or self.is_loading:
            return
        self.move(self.animation["stage"]["shift"] if double else 1, 0)

    ### PLAYBACK FUNCTIONS

    # toggle play/pause from/at actual position
    def playback_toggle(self, event=None):
        if self.is_playing:
            self.playback_pause()
        else:
            self.playback_play()

    # start palyback from the beggining of the animation (handles funcitons in toggle, as it was added later with workarounds)
    def playback_start(self, event=None):
        if self.block_hotkeys:
            return
        if self.is_playing:
            self.stage_playback_toggle.configure(image=self.images["play"])
            self.is_playing = False
            self.music(False)
            self.render(True)
        else:
            self.stage_playback_toggle.configure(image=self.images["pause"])
            self.is_playing = True
            self.music(True)
            self.async_play(True)

    # play animation from current position
    def playback_play(self, event=None):
        if self.block_hotkeys:
            return
        self.stage_playback_toggle.configure(image=self.images["pause"])
        self.is_playing = True
        self.music(True)
        # self.async_run(self.async_play())
        self.async_play()

    # pause animatino at current position
    def playback_pause(self, event=None):
        if self.block_hotkeys:
            return
        self.stage_playback_toggle.configure(image=self.images["play"])
        self.is_playing = False
        self.music(False)
        self.render(True)

    # stop = pause animation and rewind
    def playback_stop(self, event=None):
        if self.block_hotkeys:
            return
        self.playback_pause()
        self.playback_rewind()

    # jump to beginning of animation
    def playback_rewind(self, event=None):
        if self.is_playing or self.is_loading:
            return
        if self.block_hotkeys:
            return
        self.animation["properties"]["selected_frame"] = 0
        self.render(True)

    # jump to end of animation
    def playback_end(self, event=None):
        if self.is_playing or self.is_loading:
            return
        if self.block_hotkeys:
            return
        self.playback_pause()
        self.animation["properties"]["selected_frame"] = max(0, self.animation_length() - 1)
        self.render(True)

    # jump to next keyframe	in layer
    def playback_back(self, event=None):
        if self.is_playing or self.is_loading:
            return
        if self.block_hotkeys:
            return
        self.animation["properties"]["selected_frame"] = self.get_prev()
        self.render(True)

    # jump to previous keyframe in layer
    def playback_next(self, event=None):
        if self.is_playing or self.is_loading:
            return
        if self.block_hotkeys:
            return
        self.animation["properties"]["selected_frame"] = self.get_next()
        self.render(True)

    ### OTHER MENU ITEMS

    # open GitHub repo
    def other_about(self, event=None):
        return webbrowser_open(URL, new=0, autoraise=True)

    # open GitHub repo's issues with predefined message
    def other_issue(self, event=None):
        return webbrowser_open(f'{URL}/issues/new?body=Verzió:%20{VERSION}%0A%0AHiba%20leírása:', new=0, autoraise=True)

    ##### MOUSE EVENTS
    ### CURSORS
    # try to change cursor (exception can rise if cursor is unavailable in current system)
    def cursor(self, type=""):
        if not self.is_loading:
            try:
                self.root.config(cursor=type)
            except:
                pass

    # change to drawing cursor when entering drawing area (does not disturb line or rectangle drawing process)
    def mouse_to_hand(self, event):
        self.cursor("hand2")
        if self.is_playing or self.is_loading:
            return
        if (self.is_m1_down or self.is_m3_down) and self.start_x is not None and self.start_y is not None:
            if self.tool in ("line", "rectangle"):
                return
        self.is_m1_down = False
        self.is_m3_down = False
        self.changes_draw = False

    # change to default cursor after leaving drawing area (line, rectangle and pencil tools handle it as a key release)
    def mouse_to_default(self, event):
        self.cursor("")
        if self.is_playing or self.is_loading:
            return
        if (self.is_m1_down or self.is_m3_down) and self.start_x is not None and self.start_y is not None:
            if self.tool == "line":
                self.line(self.end_x, self.end_y, self.is_m1_down, True, True, self.is_shift_down)
                return
            elif self.tool == "rectangle":
                self.rectangle(self.end_x, self.end_y, self.is_m1_down, True, True, self.is_shift_down)
                return
        if self.tool == "pencil" and (self.is_m1_down or self.is_m3_down):
            self.edit_history_add("ceruza eszköz")
        self.is_m1_down = False
        self.is_m3_down = False
        self.render_frames(self.changes_draw)
        self.render_stage(self.changes_draw)
        self.render_preview(self.changes_draw)
        self.changes_made = self.changes_made or self.changes_draw
        self.changes_draw = False

    ### TOOLBAR
    # select layers
    def mouse_click_layers(self, event):
        if self.is_loading:
            return
        y = max(-1, int((self.timeline_layers.canvasy(event.y - LAYOUTS[self.skin]["layer-offset"]) /
                         LAYOUTS[self.skin]["layer-height"])))
        if y >= len(self.animation["timeline"]):
            y = -1
        if y > - 1:
            self.animation["properties"]["selected_layer"] = y
            self.render_layers(False)
            self.render_frames(False)
            if self.is_playing:
                return
            self.render_stage(True)
            self.render_preview(True)

    # select layers and current frame
    def mouse_click_frames(self, event):
        if self.is_loading:
            return
        x = max(0, int((self.timeline_frames.canvasx(event.x) / LAYOUTS[self.skin]["frame-width"])))
        y = max(-1, int((self.timeline_frames.canvasy(event.y - LAYOUTS[self.skin]["layer-offset"]) /
                         LAYOUTS[self.skin]["layer-height"])))
        if y >= len(self.animation["timeline"]):
            y = -1
        if y > - 1:
            self.animation["properties"]["selected_layer"] = y
        if self.is_playing:
            return
        self.animation["properties"]["selected_frame"] = x
        self.render_layers(False)
        self.render_frames(False)
        self.render_stage(True)
        self.render_preview(True)

    # right click on layers will select clicked layer and popup playback functions
    def mouse_popup_layers(self, event):
        if self.is_playing or self.is_loading:
            return
        self.mouse_click_layers(event)
        try:
            self.playback_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.playback_menu.grab_release()

    # right click on frames will select click layer and frame and popup edit functions
    def mouse_popup_frames(self, event):
        if self.is_playing or self.is_loading:
            return
        self.mouse_click_frames(event)
        try:
            self.edit_menu.tk_popup(event.x_root, event.y_root + 10, 0)
        finally:
            self.edit_menu.grab_release()

    # mouse wheel scrolls frames over frames (re-renders visible frames afterwards)
    def mouse_wheel_frames(self, event):
        value = int(event.delta / 120)  # Windows needs delta/120
        if self.timeline_scrollbar_h.get()[0] > 0 or value > 0:
            self.timeline_frames.xview_scroll(value, "units")
        else:
            self.timeline_frames.xview_moveto(0)
        self.render_frames(True)

    ### STAGE
    # click on stage (information required by tools)
    def mouse_click_stage(self, event):
        if self.is_playing or self.is_loading:
            return
        self.is_m1_down = True
        self.start_x = None
        self.start_y = None
        self.mouse_move_stage(event)

    # right click on stage (information required by tools)
    def mouse_popup_stage(self, event):
        if self.is_playing or self.is_loading:
            return
        self.is_m3_down = True
        self.start_x = None
        self.start_y = None
        self.mouse_move_stage(event)

    # mouse released over stage (line, rectangle are drawn, pencil tool adds drawing event to history)
    def mouse_release_stage(self, event):
        if self.is_playing or self.is_loading:
            return
        if self.tool == "line":
            self.line(self.end_x, self.end_y, self.is_m1_down, True, False, self.is_shift_down)
        elif self.tool == "rectangle":
            self.rectangle(self.end_x, self.end_y, self.is_m1_down, True, False, self.is_shift_down)
        elif self.tool == "pencil" and (self.is_m1_down or self.is_m3_down):
            self.edit_history_add("ceruza eszköz")
        self.is_m1_down = False
        self.is_m3_down = False
        self.render_frames(self.changes_draw)
        self.render_stage(self.changes_draw)
        self.render_preview(self.changes_draw)
        self.changes_made = self.changes_made or self.changes_draw
        self.changes_draw = False

    # mouse movement over stage (calculates x,y as pixel positions, handles most drawing processes)
    def mouse_move_stage(self, event):
        if self.is_playing or self.is_loading or not event:
            return
        self.mouse_pos = {"type": "stage", "event": event}

        size_x = max(1, self.animation["properties"]["zoom"])
        size_y = size_x * self.animation["stage"]["ratio"]
        width = self.stage_editor.winfo_width()
        height = self.stage_editor.winfo_height()
        p_width = self.animation["stage"]["width"]
        p_height = self.animation["stage"]["height"]
        left = int((width - p_width * size_x) / 2)
        top = int((height - p_height * size_y) / 2)
        x = floor((self.stage_editor.canvasx(event.x) - left) / size_x)
        y = floor((self.stage_editor.canvasy(event.y) - top) / size_y)
        self.timeline_pos.configure(text="x:" + str(x).ljust(4) + " y:" + str(y).ljust(4) + " ")

        if self.is_m1_down or self.is_m3_down:
            if self.start_x is None:
                self.start_x = x
            if self.start_y is None:
                self.start_y = y
            self.end_x = x
            self.end_y = y
            if self.tool == "pencil":
                self.pencil(x, y, self.is_m1_down, True, self.is_shift_down)
            elif self.tool == "line":
                self.line(x, y, self.is_m1_down, True, True, self.is_shift_down)
            elif self.tool == "rectangle":
                self.rectangle(x, y, self.is_m1_down, True, True, self.is_shift_down)
            elif self.tool == "fill":
                self.fill(x, y, self.is_m1_down, True)
            elif self.tool == "picker":
                self.picker(x, y, True)
            elif self.tool == "zoom":
                self.zoom(self.is_m1_down)

    # mouse wheel over stage & preview changes active color
    def mouse_wheel_stage(self, event):
        if event.delta > 0:
            self.color += 1
            if self.color >= len(self.animation["stage"]["palette"]):
                self.color = 0
        else:
            self.color -= 1
            if self.color < 0:
                self.color = len(self.animation["stage"]["palette"]) - 1
        self.button_colorpicker(self.color)

    ### PREVIEW
    # click on preview (information required by tools)
    def mouse_click_preview(self, event):
        if self.is_playing or self.is_loading:
            return
        self.is_m1_down = True
        self.start_x = None
        self.start_y = None
        self.mouse_move_preview(event)

    # right click on stage (information required by tools)
    def mouse_popup_preview(self, event):
        if self.is_playing or self.is_loading:
            return
        self.is_m3_down = True
        self.start_x = None
        self.start_y = None
        self.mouse_move_preview(event)

    # mouse released over preview (line, rectangle are drawn, pencil tool adds drawing event to history)
    def mouse_release_preview(self, event):
        if self.is_playing or self.is_loading:
            return
        if self.tool == "line":
            self.line(self.end_x, self.end_y, self.is_m1_down, False, False, self.is_shift_down)
        elif self.tool == "rectangle":
            self.rectangle(self.end_x, self.end_y, self.is_m1_down, True, False, self.is_shift_down)
        elif self.tool == "pencil" and (self.is_m1_down or self.is_m3_down):
            self.edit_history_add("ceruza eszköz")
        self.is_m1_down = False
        self.is_m3_down = False
        self.render_frames(self.changes_draw)
        self.render_stage(self.changes_draw)
        self.render_preview(self.changes_draw)
        self.changes_made = self.changes_made or self.changes_draw
        self.changes_draw = False

    # mouse movement over preview (calculates x,y as pixel positions, handles most drawing processes)
    def mouse_move_preview(self, event):
        if self.is_playing or self.is_loading or not event:
            return
        self.mouse_pos = {"type": "preview", "event": event}

        height = self.stage_preview.winfo_height()
        offset_x = self.animation["stage"]["offset_x"]
        offset_y = height - self.animation["stage"]["images"]["preview"]["height"] + self.animation["stage"]["offset_y"]
        px = int(self.stage_preview.canvasx(event.x))
        py = int(self.stage_preview.canvasy(event.y))
        x = round((px - offset_x) / (self.animation["stage"]["size_x"] + (
                self.animation["stage"]["pad_x"] / self.animation["stage"]["skip_x"])))
        y = round((py - offset_y) / (self.animation["stage"]["size_y"] + (
                self.animation["stage"]["pad_y"] / self.animation["stage"]["skip_y"])))
        self.timeline_pos.configure(text="x:" + str(x).ljust(4) + " y:" + str(y).ljust(4) + " ")

        if self.is_m1_down or self.is_m3_down:
            if self.start_x is None:
                self.start_x = x
            if self.start_y is None:
                self.start_y = y
            self.end_x = x
            self.end_y = y
            if self.tool == "pencil":
                if x >= 0 and x < self.animation["stage"]["width"] and y >= 0 and y < self.animation["stage"]["height"]:
                    self.pencil(x, y, self.is_m1_down, False, self.is_shift_down)
            elif self.tool == "line":
                self.line(x, y, self.is_m1_down, False, True, self.is_shift_down)
            elif self.tool == "rectangle":
                self.rectangle(x, y, self.is_m1_down, False, True, self.is_shift_down)
            elif self.tool == "fill":
                if x >= 0 and x < self.animation["stage"]["width"] and y >= 0 and y < self.animation["stage"]["height"]:
                    self.fill(x, y, self.is_m1_down, False)
            elif self.tool == "picker":
                if x >= 0 and x < self.animation["stage"]["width"] and y >= 0 and y < self.animation["stage"]["height"]:
                    self.picker(x, y, False)

    ##### DRAWING
    ### FRAME FUNCTIONS

    # insert a frame at position (extend preceding frame up to this point)
    def insert_frame(self, position):
        layer = self.animation["timeline"][self.animation["properties"]["selected_layer"]]
        if position < len(layer["frames"]):
            if layer["frames"][position]["type"] in ("empty", "matrix"):
                return
            else:
                layer["frames"][position] = deepcopy(layer["frames"][layer["frames"][position]["data"]])
                for f in range(position + 1, len(layer["frames"])):
                    if layer["frames"][f]["type"] == "link":
                        layer["frames"][f]["data"] = position
                    else:
                        break
        else:
            frame, select = self.get_frame(layer)
            for f in range(len(layer["frames"]) - 1, position - 1):
                layer["frames"].append({"type": "link", "data": select})
            # layer["frames"].append({"type":"empty","data":{}})
            if frame:
                layer["frames"].append({"type": "matrix", "data": deepcopy(frame)})
            else:
                layer["frames"].append({"type": "empty", "data": {}})

    # insert given frame after position
    def insert_frame_extra(self, position, extra):
        layer = self.animation["timeline"][self.animation["properties"]["selected_layer"]]
        self.extend_frame(position)
        if position < len(layer["frames"]):
            position += 1
        self.insert_frame(position)
        self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][position] = deepcopy(extra)

    # overwrite to given frame at position
    def overwrite_frame(self, position, extra):
        if position:
            self.insert_frame_extra(position, extra)
            if position < len(self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"]):
                self.remove_frame(position)
                self.animation["properties"]["selected_frame"] += 1
        else:
            self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][position] = deepcopy(
                extra)

    # remove frame at position
    def remove_frame(self, position):
        layer = self.animation["timeline"][self.animation["properties"]["selected_layer"]]
        if position < len(layer["frames"]):
            frames = layer["frames"]
            new_frames = frames[:position]
            change_frames = frames[position + 1:]
            extend = False
            for frame in change_frames:
                if frame["type"] == "link":
                    if frame["data"] == position:
                        if not extend:
                            extend = True
                            frame["type"] = "empty"
                            frame["data"] = {}
                        else:
                            frame["data"] = position
                    elif frame["data"] > position:
                        frame["data"] -= 1
                new_frames.append(frame)
            if not new_frames:
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"] = [
                    {"type": "empty", "data": {}}]
            else:
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"] = new_frames
            self.animation["properties"]["selected_frame"] = max(0, self.animation["properties"]["selected_frame"] - 1)

    # extend length of frame at position/until position if it's outside the curernt boundaries
    def extend_frame(self, position):
        layer = self.animation["timeline"][self.animation["properties"]["selected_layer"]]
        frames = layer["frames"]
        if position >= len(frames):
            frame, select = self.get_frame(layer)
            for f in range(len(frames) - 1, position):
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"].append(
                    {"type": "link", "data": select})
            return
        new_frames = frames[:position + 1]
        if frames[position]["type"] == "link":
            new_frames.append({"type": "link", "data": frames[position]["data"]})
        else:
            new_frames.append({"type": "link", "data": position})
        change_frames = frames[position + 1:]
        for frame in change_frames:
            if frame["type"] == "link":
                if frame["data"] > position:
                    frame["data"] += 1
            new_frames.append(frame)
        self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"] = new_frames

    # reduce length of frame if it's not just a single keyframe
    def reduce_frame(self, position):
        layer = self.animation["timeline"][self.animation["properties"]["selected_layer"]]
        frames = layer["frames"]
        if position >= len(frames):
            return
        new_frames = frames[:position + 1]
        if len(frames) > (position + 1) and frames[position + 1]["type"] == "link":
            change_frames = frames[position + 2:]
        else:
            if frames[position]["type"] == "link":
                new_frames.pop()
                change_frames = frames[position + 1:]
                position -= 1
            else:
                change_frames = frames[position + 1:]
        for frame in change_frames:
            if frame["type"] == "link":
                if frame["data"] > position:
                    frame["data"] -= 1
            new_frames.append(frame)
        self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"] = new_frames

    # get currently visible frame (for altering or just viewing)
    def get_frame(self, view=None):
        if view is None:
            # get a deep copy of the selected frame for editing
            self.changes_draw = True
            self.insert_frame(self.animation["properties"]["selected_frame"])
            layer = self.animation["timeline"][self.animation["properties"]["selected_layer"]]
            select = self.animation["properties"]["selected_frame"]
            if layer["frames"][self.animation["properties"]["selected_frame"]]["type"] == "link":
                select = layer["frames"][self.animation["properties"]["selected_frame"]]["data"]
                if layer["frames"][select]["type"] == "link":
                    return {}, select  # error
            return self.copy_frame_data(layer["frames"][select]["data"]), select
        else:
            # get the selected frame from the passed layer to view
            select = min(self.animation["properties"]["selected_frame"], len(view["frames"]) - 1)
            if view["frames"][select]["type"] == "link":
                select = view["frames"][select]["data"]
                if view["frames"][select]["type"] == "link":
                    return {}, select  # error
            return view["frames"][select]["data"], select

    # get next keyframe in layer
    def get_next(self):
        layer = self.animation["timeline"][self.animation["properties"]["selected_layer"]]
        for select in range(self.animation["properties"]["selected_frame"] + 1, len(layer["frames"])):
            if layer["frames"][select]["type"] != "link":
                return select
        return len(layer["frames"])

    # get previous keyframe in layer
    def get_prev(self):
        layer = self.animation["timeline"][self.animation["properties"]["selected_layer"]]
        select = max(0, min(self.animation["properties"]["selected_frame"] - 1, len(layer["frames"]) - 1))
        if layer["frames"][select]["type"] == "link":
            select = layer["frames"][select]["data"]
        return select

    ### TOOLS

    # change stage's zoom level
    def zoom(self, inc=True):
        self.is_m1_down = False
        self.is_m3_down = False
        step = LAYOUTS[self.skin]["zoom_step"]
        if inc:
            self.animation["properties"]["zoom"] = min(int(self.animation["properties"]["zoom"] / step) * step + step,
                                                       LAYOUTS[self.skin]["zoom_max"])
        else:
            self.animation["properties"]["zoom"] = max(int(self.animation["properties"]["zoom"] / step) * step - step,
                                                       LAYOUTS[self.skin]["zoom_min"])
        self.render_stage(True)
        self.cursor("hand2")

    # select color from selected layer's current frame on stage / visible pixel in window on preview
    def picker(self, x, y, is_editor=True):
        if is_editor:
            frame, select = self.get_frame(self.animation["timeline"][self.animation["properties"]["selected_layer"]])
            if x in frame and y in frame[x]:
                self.animation["stage"]["palette"][self.color] = frame[x][y]
        else:
            if x in self.render_cache and y in self.render_cache[x]:
                self.animation["stage"]["palette"][self.color] = self.render_cache[x][y]
        self.refresh_colorpicker()
        self.cursor("hand2")
        if self.is_m1_down:
            self.button_tool(LAYOUTS[self.skin]["tools"][0])
        self.is_m1_down = False
        self.is_m3_down = False
        self.changes_draw = False

    # pencil tool (uses helper function to quickly render scribbles without actually rerendering the stage)
    def pencil(self, x, y, add=True, is_editor=True, straight=False):
        if straight:  # straight is actually fills an entire window
            x = floor(x / self.animation["stage"]["shift"]) * self.animation["stage"]["shift"]
            y = floor(y / self.animation["stage"]["shift"]) * self.animation["stage"]["shift"]
            for x_plus in range(self.animation["stage"]["shift"]):
                for y_plus in range(self.animation["stage"]["shift"]):
                    self.pencil_pixel(x + x_plus, y + y_plus, add, is_editor)
        else:
            self.pencil_pixel(x, y, add, is_editor)

    # draw a single pixel (uses helper function to quickly render scribbles without actually rerendering the stage)
    def pencil_pixel(self, x, y, add=True, is_editor=True):
        if add:
            color = self.animation["stage"]["palette"][self.color]
        else:
            color = self.animation["stage"]["background-color"]
        frame, select = self.get_frame()
        if add:
            if x not in frame:
                frame[x] = {}
            frame[x][y] = color
            self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
                "type"] = "matrix"
            self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["data"] = frame
        else:
            if x in frame:
                if y in frame[x]:
                    del frame[x][y]
                if not frame[x]:
                    del frame[x]
            if not frame:
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
                    "type"] = "empty"
            self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["data"] = frame
        if is_editor:
            self.render_stage_helper(x, y, color)
        else:
            self.render_preview_helper(x, y, color)

    # draw line based on Bresenham’s algorithm (can render without actually altering the frame's contents)
    def line(self, x, y, add=True, is_editor=True, hint=True, straight=False):
        if hint:
            if self.start_x is None:
                self.start_x = x
            if self.start_y is None:
                self.start_y = y
        if x is None or self.start_x is None or y is None or self.start_y is None:
            return
        if add:
            color = self.animation["stage"]["palette"][self.color]
        else:
            color = self.animation["stage"]["background-color"]
        if hint:
            if is_editor:
                self.render_stage(True)
            else:
                self.render_preview(True)
        else:
            frame, select = self.get_frame()
        # based on http://floppsie.comp.glam.ac.uk/Glamorgan/gaius/gametools/6.html
        x0, x1, y0, y1 = x, self.start_x, y, self.start_y
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        if straight:
            if dy < dx:
                dy = 0
                y0 = self.start_y
            else:
                dx = 0
                x0 = self.start_x
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1
        err = dx - dy
        while True:
            if hint:
                if is_editor:
                    self.render_stage_helper(x0, y0, color)
                else:
                    self.render_preview_helper(x0, y0, color)
            else:
                if add:
                    if x0 not in frame:
                        frame[x0] = {}
                    frame[x0][y0] = color
                else:
                    if x0 in frame and y0 in frame[x0]:
                        del frame[x0][y0]
                        if not frame[x0]:
                            del frame[x0]
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err = err - dy
                x0 = x0 + sx
            if e2 < dx:
                err = err + dx
                y0 = y0 + sy

        if not hint:
            if not straight:
                if x not in frame:
                    frame[x] = {}
                if add:
                    frame[x][y] = self.animation["stage"]["palette"][self.color]
                else:
                    if x in frame and y in frame[x]:
                        del frame[x][y]
                        if not frame[x]:
                            del frame[x]
            self.start_x = None
            self.start_y = None
            if not frame:
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
                    "type"] = "empty"
            else:
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
                    "type"] = "matrix"
            self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["data"] = frame
            self.edit_history_add("vonal eszköz")

    # draw rectangle (can render without actually altering the frame's contents)
    def rectangle(self, x, y, add=True, is_editor=True, hint=True, straight=False):
        if hint:
            if self.start_x is None:
                self.start_x = x
            if self.start_y is None:
                self.start_y = y
        if x is None or self.start_x is None or y is None or self.start_y is None:
            return
        if add:
            color = self.animation["stage"]["palette"][self.color]
        else:
            color = self.animation["stage"]["background-color"]
        if hint:
            if is_editor:
                self.render_stage(True)
            else:
                self.render_preview(True)
        else:
            frame, select = self.get_frame()
        if straight:
            if (x - self.start_x) ** 2 < (y - self.start_y) ** 2:
                if self.start_y < y:
                    dif = (y - self.start_y)
                else:
                    dif = -(y - self.start_y)
                if self.start_x < x:
                    x = self.start_x + dif
                else:
                    x = self.start_x - dif
            else:
                if self.start_x < x:
                    dif = (x - self.start_x)
                else:
                    dif = -(x - self.start_x)
                if self.start_y < y:
                    y = self.start_y + dif
                else:
                    y = self.start_y - dif

        x0, x1, y0, y1 = x, self.start_x, y, self.start_y
        if x0 > x1:
            x0, x1 = x1, x0
        x1 += 1
        if y0 > y1:
            y0, y1 = y1, y0
        y1 += 1
        for _x in range(x0, x1):
            for _y in range(y0, y1):
                if hint:
                    if is_editor:
                        self.render_stage_helper(_x, _y, color)
                    else:
                        self.render_preview_helper(_x, _y, color)
                else:
                    if add:
                        if _x not in frame:
                            frame[_x] = {}
                        frame[_x][_y] = color
                    else:
                        if _x in frame and _y in frame[_x]:
                            del frame[_x][_y]
                            if not frame[_x]:
                                del frame[_x]
        if not hint:
            self.start_x = None
            self.start_y = None
            if not frame:
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
                    "type"] = "empty"
            else:
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
                    "type"] = "matrix"
            self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["data"] = frame
            self.edit_history_add("négyszög eszköz")

    # flood fill (uses helper first to determine if fill is possible, alters frame afterwards)
    def fill(self, x, y, add=True, is_editor=True):
        self.is_m1_down = False
        self.is_m3_down = False
        self.changes_made = True
        self.changes_draw = False
        frame, select = self.get_frame()
        min_x, min_y, max_x, max_y = 0, 0, self.animation["stage"]["width"], self.animation["stage"]["height"]
        for _x in frame:
            for _y in frame[_x]:
                min_x = min(min_x, _x)
                min_y = min(min_y, _y)
                max_x = max(max_x, _x)
                max_y = max(max_y, _y)
        min_x -= 1
        min_y -= 1
        max_x += 1
        max_y += 1
        if x in frame and y in frame[x]:
            original = frame[x][y]
        else:
            original = ""
        if add:
            replace = self.animation["stage"]["palette"][self.color]
        else:
            replace = ""
        if original != replace:
            self.fill_break = False
            self.loading(True)
            frame = self.fill_flood(self.copy_frame_data(frame), x, y, min_x, max_x, min_y, max_y, original, replace)
            if not self.fill_break:
                if frame:
                    self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
                        "type"] = "matrix"
                else:
                    self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
                        "type"] = "empty"
                self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
                    "data"] = self.copy_frame_data(frame)
                self.edit_history_add("festékes vödör")
            self.loading(False)
        self.cursor("hand2")

    # flood fill helper that checks if selected shape is not closed
    def fill_flood(self, frame, x, y, min_x, max_x, min_y, max_y, original, replace):
        if self.fill_break:
            return self.copy_frame_data(frame)
        # based on https://stackoverflow.com/questions/19839947/flood-fill-in-python
        if original == "":
            if x < min_x or x >= max_x or y < min_y or y >= max_y:
                self.fill_break = True
                return self.copy_frame_data(frame)
        if (original == "" and (x not in frame or (x in frame and y not in frame[x]))) or (
                x in frame and y in frame[x] and frame[x][y] == original):
            if x not in frame:
                frame[x] = {}
            if replace:
                frame[x][y] = replace
            else:
                del frame[x][y]
            if x >= min_x:
                frame = self.fill_flood(self.copy_frame_data(frame), x - 1, y, min_x, max_x, min_y, max_y, original,
                                        replace)
            if x < max_x:
                frame = self.fill_flood(self.copy_frame_data(frame), x + 1, y, min_x, max_x, min_y, max_y, original,
                                        replace)
            if y >= min_y:
                frame = self.fill_flood(self.copy_frame_data(frame), x, y - 1, min_x, max_x, min_y, max_y, original,
                                        replace)
            if y < max_y:
                frame = self.fill_flood(self.copy_frame_data(frame), x, y + 1, min_x, max_x, min_y, max_y, original,
                                        replace)
            if x in frame and not frame[x]:
                del frame[x]
        return self.copy_frame_data(frame)

    ### TRANSFORM PIXEL DRAWINGS

    # move all pixels in active frame
    def move(self, x_delta=0, y_delta=0):
        frame, select = self.get_frame()
        new_frame = {}
        for x in frame:
            new_frame[(x + x_delta)] = {}
            for y in frame[x]:
                new_frame[(x + x_delta)][(y + y_delta)] = frame[x][y]
        self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
            "data"] = self.copy_frame_data(new_frame)
        self.edit_history_add("elmozdítás")
        self.render(True)

    # flip all pixels in active frame
    def flip(self, horizontal=True, render_flip=True):
        frame, select = self.get_frame()
        if horizontal:
            x_offset = int(self.animation["stage"]["width"]) - 1
            x_delta = -1
            y_offset = 0
            y_delta = 1
        else:
            x_offset = 0
            x_delta = 1
            y_offset = int(self.animation["stage"]["height"]) - 1
            y_delta = -1
        new_frame = {}
        for x in frame:
            new_frame[(x * x_delta + x_offset)] = {}
            for y in frame[x]:
                new_frame[(x * x_delta + x_offset)][(y * y_delta + y_offset)] = frame[x][y]
        self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
            "data"] = self.copy_frame_data(new_frame)
        if render_flip:
            self.render(True)
            self.edit_history_add("tükrözés")

    # rotate all pixels in active frame (transpose, flip and move)
    def rotate(self, right=True):
        frame, select = self.get_frame()
        transpose = {}
        for x in frame:
            for y in frame[x]:
                if y not in transpose:
                    transpose[y] = {}
                transpose[y][x] = frame[x][y]
        self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select][
            "data"] = self.copy_frame_data(transpose)
        self.flip(right, False)
        if right:
            self.move(-self.animation["stage"]["width"], 0)
        else:
            self.move(0, -self.animation["stage"]["height"])

    ### TOOL BUTTONS

    # select tool
    def button_tool(self, parameter):
        if parameter in LAYOUTS[self.skin]["tools"]:
            self.tool = parameter
            for button in LAYOUTS[self.skin]["tools"]:
                self.stage_tools_buttons[button].configure(bg=LAYOUTS[self.skin]["button"])
                self.stage_tools_buttons[button].configure(image=self.images[button])
            self.stage_tools_buttons[parameter].configure(bg=LAYOUTS[self.skin]["button-active"])
            if parameter + "-active" in self.images:
                self.stage_tools_buttons[parameter].configure(image=self.images[parameter + "-active"])

    # select or change color (-1 is the selected color button, rest are palette indexes)
    def button_colorpicker(self, i):
        if i >= 0 and i < len(self.animation["stage"]["palette"]):
            self.color = i
        else:
            self.root.update()
            new_color = askcolor(initialcolor=self.animation["stage"]["palette"][self.color])
            self.animation["stage"]["palette"][self.color] = new_color[1]
            self.stage_colorpicker_buttons[self.color + 1].configure(bg=self.animation["stage"]["palette"][self.color],
                                                                     highlightcolor=self.animation["stage"]["palette"][
                                                                         self.color], highlightbackground=
                                                                     self.animation["stage"]["palette"][self.color],
                                                                     fg=self.animation["stage"]["palette"][self.color],
                                                                     activebackground=
                                                                     self.animation["stage"]["palette"][self.color],
                                                                     activeforeground=
                                                                     self.animation["stage"]["palette"][self.color])
        for i, palette in enumerate(self.animation["stage"]["palette"]):
            if i == self.color:
                self.stage_colorpicker_buttons[(i + 1)].configure(image=self.images["palette-active"])
            elif i != -1:
                self.stage_colorpicker_buttons[(i + 1)].configure(image=self.images["palette"])
        self.stage_colorpicker_buttons[0].configure(bg=self.animation["stage"]["palette"][self.color],
                                                    highlightcolor=self.animation["stage"]["palette"][self.color],
                                                    highlightbackground=self.animation["stage"]["palette"][self.color],
                                                    fg=self.animation["stage"]["palette"][self.color],
                                                    activebackground=self.animation["stage"]["palette"][self.color],
                                                    activeforeground=self.animation["stage"]["palette"][self.color])
        self.edit_history_add("színkeverés")

    ##### MISC FUNCITONS
    # deepcopy is slow, implemented animation dict copy instead
    def copy_animation(self, data):
        result = {
            "header": data["header"],
            "version": data["version"],
            "stage": {},
            "properties": {},
            "timeline": []
        }
        for item in data["stage"]:
            if isinstance(data["stage"][item], list):
                result["stage"][item] = []
                for element in data["stage"][item]:
                    result["stage"][item].append(element)
            elif isinstance(data["stage"][item], dict):
                result["stage"][item] = {}
                for element in data["stage"][item]:
                    if isinstance(data["stage"][item][element], dict):
                        result["stage"][item][element] = {}
                        for sub_element in data["stage"][item][element]:
                            result["stage"][item][element][sub_element] = data["stage"][item][element][sub_element]
                    else:
                        result["stage"][item]["element"] = element
            else:
                result["stage"][item] = data["stage"][item]
        for item in data["properties"]:
            result["properties"][item] = data["properties"][item]
        for layer in data["timeline"]:
            copylayer = {}
            for item in layer:
                if isinstance(layer[item], list):
                    copylayer[item] = []
                    for frame in layer[item]:
                        copylayer[item].append(self.copy_frame(frame))
                else:
                    copylayer[item] = layer[item]
            result["timeline"].append(copylayer)
        return result

    # deepcopy is slow, copy frames manually
    def copy_frame(self, data):
        result = {
            "type": data["type"],
            "data": {}
        }
        if isinstance(data["data"], dict):
            result["data"] = self.copy_frame_data(data["data"])
        else:
            result["data"] = data["data"]
        return result

    # deepcopy is slow, copy frame data manually
    def copy_frame_data(self, data):
        result = {}
        for x in data:
            if data[x]:
                result[x] = {}
                for y in data[x]:
                    if data[x][y] and data[x][y] != 0:
                        result[x][y] = data[x][y]
        return result

    # JSON objects can't have int keys --> turn str keys into ints
    def json_fix(self, data):
        newdata = deepcopy(data)
        newdata["timeline"] = []
        for layer in data["timeline"]:
            frames = []
            for frame in layer["frames"]:
                if frame["data"] and isinstance(frame["data"], dict):
                    fix = {}
                    for x in frame["data"]:
                        fix[int(x)] = {}
                        for y in frame["data"][x]:
                            fix[int(x)][int(y)] = frame["data"][x][y]
                    frame["data"] = fix
                frames.append(frame)
            layer["frames"] = frames
            newdata["timeline"].append(layer)
        return newdata

    # length of animation
    def animation_length(self):
        max_frames = 0
        for layer in self.animation["timeline"]:
            max_frames = max(max_frames, len(layer["frames"]))
        return max_frames

    # render color picker buttons based on updated palette
    def refresh_colorpicker(self):
        for i, color in enumerate(self.animation["stage"]["palette"]):
            self.stage_colorpicker_buttons[i + 1].configure(bg=color, highlightcolor=color, highlightbackground=color,
                                                            fg=color, activebackground=color, activeforeground=color)
            self.stage_colorpicker_buttons[0].configure(bg=self.animation["stage"]["palette"][self.color],
                                                        highlightcolor=self.animation["stage"]["palette"][self.color],
                                                        highlightbackground=self.animation["stage"]["palette"][
                                                            self.color],
                                                        fg=self.animation["stage"]["palette"][self.color],
                                                        activebackground=self.animation["stage"]["palette"][self.color],
                                                        activeforeground=self.animation["stage"]["palette"][self.color])
        self.stage_colorpicker_buttons[(self.color + 1)].configure(image=self.images["palette-active"])

    # change active layer with tab key
    def change_layer(self, event=None):
        if self.block_hotkeys:
            return
        if self.is_shift_down:
            self.animation["properties"]["selected_layer"] = (self.animation["properties"]["selected_layer"] - 1) % len(
                self.animation["timeline"])
        else:
            self.animation["properties"]["selected_layer"] = (self.animation["properties"]["selected_layer"] + 1) % len(
                self.animation["timeline"])
        self.render(True)

    # workaround to know if shift was pressed or released
    def press_shift(self, event=None, is_down=True):
        if event:
            if is_down:
                if not self.is_shift_down:
                    self.is_shift_down = True
                    if self.mouse_pos["type"] == "stage":
                        self.mouse_move_stage(self.mouse_pos["event"])
                    else:
                        self.mouse_move_preview(self.mouse_pos["event"])
                return
            elif self.is_shift_down:
                if event.keysym in ("Shift_L", "Shift_R"):
                    self.is_shift_down = False
                    if self.mouse_pos["type"] == "stage":
                        self.mouse_move_stage(self.mouse_pos["event"])
                    else:
                        self.mouse_move_preview(self.mouse_pos["event"])

    # window resize function that lags so information passed is usually inaccurate
    def on_resize(self, event):
        try:
            self.root.update()
            update = False
            if self.width != self.root.winfo_width() or self.height != self.root.winfo_height():
                update = True
            if self.state != self.root.wm_state():
                update = False
                self.state = self.root.wm_state()
                if not self.resize:
                    self.resize = True
                    self.async_run(self.async_render())
            if update:
                self.width = self.root.winfo_width()
                self.height = self.root.winfo_height()
                self.state = self.root.wm_state()
                if not self.resize:
                    self.resize = True
                    self.async_run(self.async_render())
        except:
            pass

    # window focus gained (check if clipboard contents have been altered since)
    def on_focus(self, event=None):
        clipboard = {}
        try:
            clipboard = json.loads(self.root.clipboard_get())
        except:
            pass
        if "header" in clipboard and clipboard["header"] == HEADER:
            self.edit_menu.entryconfigure(5, state=tk.NORMAL)
            self.edit_menu.entryconfigure(6, state=tk.NORMAL)
        else:
            self.edit_menu.entryconfigure(5, state=tk.DISABLED)
            self.edit_menu.entryconfigure(6, state=tk.DISABLED)

    # play or stop audio
    def music(self, play=True):
        if self.audio is not None:
            if play:
                self.audio.play()
            else:
                self.audio.stop()

    # load audio file, alert if file is not found
    def music_load(self):
        if self.audio:
            self.waveform = None
            self.audio.destroy()
            self.audio = None
        if self.animation["properties"]["music"]:
            if os.path.isfile(os.path.join(self.animation["properties"]["music"])):
                try:
                    self.audio = FFMP3(self.animation["properties"]["music"], False)
                    self.loading(True)
                    file = self.animation["properties"]["music"].replace("/", "\\").split("\\")[-1]
                    self.properties_menu.entryconfigure(3, label="Zene: " + file)
                    out, err = self.audio.waveform(WAVEFORM, {
                        "width": int(LAYOUTS[self.skin]["frame-width"] * (1000. / self.animation["stage"]["speed"]) * self.audio.duration()),
                        "height": int(LAYOUTS[self.skin]["layer-offset"] * 2),
                        "foreground": LAYOUTS[self.skin]["layer-waveform"],
                        "background": LAYOUTS[self.skin]["layer"]
                    })
                    try:
                        self.waveform = tk.PhotoImage(
                            file=WAVEFORM,
                            width=int(LAYOUTS[self.skin]["frame-width"] * (1000. / self.animation["stage"]["speed"]) * self.audio.duration()),
                            height=int(LAYOUTS[self.skin]["layer-offset"]))
                    except tk.TclError as ep:
                        pass
                    self.loading(False)
                except Exception as e:
                    self.error("VLC hiba!",
                               "Nem sikerült betölteni a hangfájlt, a VLC dll hiba miatt.")
                    file = self.animation["properties"]["music"].replace("/", "\\").split("\\")[-1]
                    self.properties_menu.entryconfigure(3, label="Zene nem található: " + file)
            else:
                self.error("Nem található az MP3 fájl.",
                           "A megadott mp3 nem található:\n" + self.animation["properties"]["music"])
                file = self.animation["properties"]["music"].replace("/", "\\").split("\\")[-1]
                self.properties_menu.entryconfigure(3, label="Zene nem található: " + file)
        else:
            self.properties_menu.entryconfigure(3, label="Zene betöltése")
        self.render_frames(True)

    # disable certain functions while loading, and change cursor if wait cursor is available in system
    def loading(self, update=True):
        self.is_loading = update
        if self.is_loading:
            try:
                self.root.config(cursor="wait")
                self.root.update()
            except:
                pass
        else:
            self.root.config(cursor="")
            self.root.update()

    # show progress bar window where percentage 0-99 updates the progress bar, percentage 100 will destroy the window
    def loading_progress(self, percentage=0):
        if not self.progress_window:
            self.progress_window = tk.Toplevel(self.root)
            self.progress_window.wm_geometry(
                f'{LAYOUTS[self.skin]["loading_width"]}x{LAYOUTS[self.skin]["loading_height"]}')
            self.progress_window.wm_title("Kis türelmet...")
            self.root.call('wm', 'iconphoto', self.progress_window._w, self.images["icon"])
            self.progress_bar = Progressbar(self.progress_window, orient="horizontal",
                                            length=LAYOUTS[self.skin]["loading_width"], mode="determinate")
            self.progress_bar["value"] = 0
            self.progress_bar["maximum"] = 100
            self.progress_bar.pack()
        if percentage >= 100:
            self.progress_window.destroy()
            self.progress_window = None
        else:
            self.progress_bar["value"] = min(99, max(0, percentage))

    # self.properties_window.protocol("WM_DELETE_WINDOW", lambda event:pass)

    # show error window and log error message and raise it again if it the error was raised by an exception
    def error(self, message="Ismeretlen hiba", e=None):
        self.loading(False)
        messagebox.showerror(message, str(e))
        self.log(message + " - " + str(e))
        try:
            raise e
        except TypeError:
            pass
        return

    # log message with timestamp
    def log(self, message=""):
        print(time.strftime("%H:%M:%S") + " > " + message, flush=True)

    # enable async running of async functions
    def async_run(self, func):
        try:
            threading.Thread(target=lambda: self.loop.run_until_complete(func)).start()
        except RuntimeError as e:
            pass

    # play animation
    # NOTE: THIS ISN'T ASYNC, IT WAS UPDATED TO BE SYNC TO IMPROVE PERFORMANCE
    def async_play(self, from_start=False):
        timestamp = time.time()
        length = self.animation_length()
        speed = self.animation["stage"]["speed"] / 1000
        start = 0 if from_start else self.animation["properties"]["selected_frame"]
        end = self.animation["properties"]["selected_frame"] if from_start else length
        start_time = start * speed
        try:
            # self.stage_preview.delete(self.building)
            self.timeline_frames.delete(self.timeline_frames_select)
            self.timeline_frames.delete(self.timeline_frames_select_line)
            self.timeline_frames.delete(self.timeline_frames_select_frame)
        except AttributeError:
            pass
        if from_start:
            self.animation["properties"]["selected_frame"] = 0
        while True:
            if not self.is_playing:
                if from_start:
                    self.animation["properties"]["selected_frame"] = end
                self.render(True)
                self.playback_pause()
                return
            current = time.time()
            if timestamp < (current - speed):
                lag = 0
                while timestamp + speed < current:
                    timestamp += speed
                    lag += 1
                self.animation["properties"]["selected_frame"] += lag
                if self.animation["properties"]["selected_frame"] >= length:
                    self.animation["properties"]["selected_frame"] = end
                    self.playback_pause()
                    return
                self.render_stage(True, True)
                self.render_preview(False, True)
                self.root.update()

                if self.audio is not None:
                    audio_current = self.audio.current() * 1000
                    audio_duration = self.audio.duration() * 1000
                    if audio_duration > self.animation["properties"]["selected_frame"] * self.animation["stage"]["speed"]:
                        if not self.audio.is_playing:
                            self.music(True)
                    else:
                        if self.audio.is_playing:
                            self.music(False)
                    if audio_current < (self.animation["properties"]["selected_frame"] - 3) * self.animation["stage"]["speed"] or audio_current > (self.animation["properties"]["selected_frame"] + 2) * self.animation["stage"]["speed"]:
                        fix = (self.animation["properties"]["selected_frame"]+.5) * self.animation["stage"]["speed"]
                        self.audio.seek(fix/1000)


            time.sleep(int(speed / 20))

    # await asyncio.sleep(int(speed/20))

    # async render resized window after window properties are most likely up to date
    async def async_render(self, event=None):
        try:
            await asyncio.sleep(.5)
            self.render(True)
        except:
            pass
        self.resize = False

    # import *.qp4 file (async but blocks altering most parts of the animation)
    async def async_import(self, file):
        self.loading(True)
        with codecs.open(file, "r", encoding="utf-8") as f:
            data = f.read()
        pattern = re.compile(r'frame\(\{[\r\n]*([0123456789abcdefx\,\r\n\s]+)[\r\n]*\}\s?\,\s?(\d+)\)',
                             flags=re.IGNORECASE)
        c_pattern = re.compile(r'([0123456789abcdefx]+)[\r\n\s\,]*', flags=re.IGNORECASE)
        frames = re.findall(pattern, data)
        if frames:
            step = 0
            for at, info in enumerate(frames):
                self.loading_progress(int(at / len(frames) * 100) - 1)
                length = max(1, int(int(info[1]) / self.animation["stage"]["speed"]))
                colors = re.findall(c_pattern, info[0])
                newframe = {}
                x = 0
                y = 0
                for i, color in enumerate(colors):
                    if color != '0':
                        x = i % self.animation["stage"]["width"]
                        y = int(i / self.animation["stage"]["width"])
                        if x not in newframe:
                            newframe[x] = {}
                        newcolor = "#" + color[-6:]
                        if len(newcolor) == 7:
                            newframe[x][y] = newcolor
                if newframe:
                    self.insert_frame_extra(self.animation["properties"]["selected_frame"] + step,
                                            {"type": "matrix", "data": self.copy_frame_data(newframe)})
                else:
                    self.insert_frame_extra(self.animation["properties"]["selected_frame"] + step,
                                            {"type": "empty", "data": {}})
                step += 1
                for i in range(length):
                    if i:
                        self.extend_frame(self.animation["properties"]["selected_frame"] + step)
                        step += 1
            self.edit_history_add("képkockák importálása")
            self.render(True)
        else:
            self.error("Ismeretlen fájl formátum!", "A fájl nem tartalmaz képkockákat.")
        self.loading_progress(100)
        self.loading(False)

    # export *.qp4 file (async but blocks altering most parts of the animation)
    async def async_export(self, file):
        if self.is_loading:
            return
        self.loading(True)
        if self.animation["stage"]["profile"] == "sch":  # only supported profile at the moment
            width = self.animation["stage"]["width"]
            height = self.animation["stage"]["height"]
            speed = self.animation["stage"]["speed"]
            default = str(self.animation["stage"]["default"])
            audio = json.dumps(self.animation["properties"]["music"], ensure_ascii=False)
            team = json.dumps(self.animation["properties"]["team"], ensure_ascii=False)
            title = json.dumps(self.animation["properties"]["title"], ensure_ascii=False)
            year = str(int(self.animation["properties"]["year"]))
            output = '-- __animeditor__\nmeta({\naudio=' + audio + ',\nteam=' + team + ',\ntitle=' + title + ',\nyear=' + year + '})\n\nbeginclip(32,26,"main")\n'
            length = self.animation_length()
            current = self.animation["properties"]["selected_frame"]
            try:
                last_frame = ''
                last_frame_times = 0
                for keyframe in range(length):
                    self.animation["properties"]["selected_frame"] = keyframe
                    if keyframe % 10 == 0:
                        percentage = int(keyframe / length * 100) - 1
                        self.loading_progress(percentage)
                    frame_text = 'frame({\n'
                    frame_cache = {}
                    for layer in reversed(self.animation["timeline"]):
                        if layer["render"]:
                            frame, _ = self.get_frame(layer)
                            xframe = self.copy_frame_data(frame)
                            for x in xframe:
                                for y in xframe[x]:
                                    if x >= 0 and x < width and y >= 0 and y < height:
                                        if x not in frame_cache:
                                            frame_cache[x] = {}
                                        frame_cache[x][y] = xframe[x][y]
                    for y in range(height):
                        for x in range(width):
                            if x in frame_cache and y in frame_cache[x]:
                                frame_text += frame_cache[x][y].upper().replace('#', '0xFF') + ','
                            else:
                                frame_text += default + ','
                        frame_text += '\n'
                    if frame_text == last_frame:
                        last_frame_times += 1
                    elif last_frame:
                        output += last_frame + '},' + str(speed * (last_frame_times + 1)) + ')\n'
                        last_frame_times = 0
                    last_frame = frame_text
                output += last_frame + '},' + str(speed * (last_frame_times + 1)) + ')\n'
                output += 'endclip()\n\nrootclip("main")\n'
                self.animation["properties"]["selected_frame"] = current
                try:
                    with codecs.open(file, "w", "utf-8-sig") as f:
                        f.write(output)
                except Exception as e:
                    return self.error("Nem sikerült menteni a fájlt!", e)
                messagebox.showinfo("Exportálás sikeres", "Az animáció konvertálása sikeres volt.")
            except Exception as e:
                return self.error("Hiba exportálás közben!", e)
        self.loading_progress(100)
        self.loading(False)


if __name__ == "__main__":
    # if editor is started from command line, notify the user not to close it
    print("Ha ezt az ablakot bezárod, az alkalmazás is bezáródik!")
    app = Application(master=tk.Tk())
    app.mainloop()
    print("Szerkesztő ablak bezárva.")
