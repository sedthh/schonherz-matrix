# -*- coding: UTF-8 -*-

import sys, os
import json
import webbrowser
import time
import codecs

import asyncio
import threading
from pygame import mixer

import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox
from tkinter.colorchooser import askcolor

### GLOBALS

TITLE		= "QPY"
NAME		= "QPY Animáció Szerkesztő"
VERSION		= "0.1.0 alfa"
URL			= "https://github.com/sedthh/schonherz-matrix"
PROFILES	= {	
	"SCH"		: {	# default display profile for Schönherz Matrix
		"width"				: 32,
		"height"			: 26,
		"background-color"	: "#000000",
		"border-color"		: "#d0d0d0",
		"skybox-color"		: "#0f1114",
		"offset_x"			: 29,
		"offset_y"			: 109,
		"size_x"			: 5,
		"size_y"			: 5,
		"pad_x"				: 4.75,
		"pad_y"				: 14.2,
		"skip_x"			: 2,
		"skip_y"			: 2,
		"mode"				: "12-bit RGB",
		"palette"			: ["#FFFFFF","#AAAAAA","#666666","#660000","#FF0000",
								"#FF00FF","#AA00AA","#AA00FF","#0000AA","#0000FF",
								"#00FFFF","#00FFAA","#00AAAA","#00AA00","#00FF00",
								"#AAFF00","#FFFF00","#AAAA00","#AA6600","#FFAA00"
							],
		"images"			: {
			"preview"				: {
				"src"					: "sch.png",
				"width"					: 300,
				"height"				: 420
			}
		}
	}
}
LAYOUT		= {
	"DEFAULT"	: { # default color scheme
		"root"				: "#f0f0f0",
		"stage"				: "#b0b0b0",
		"toolbar"			: "#d0d0d0",
		"toolbar-width"		: 30,
		"toolbar-height"	: 30,
		"toolbar-padding"	: 5,
		"toolbar-column"	: 1,
		"button"			: "#ffffff",
		"button-active"		: "#000000",
		"button-width"		: 30,
		"button-height"		: 20,
		"layer"				: "#d0d0d0",
		"layer-active"		: "#bbccdd",
		"layer-color"		: "#202020",
		"layer-offset"		: 30,
		"layer-height"		: 40,
		"layer-width"		: 200,
		"frame-width"		: 10,
		"frame-active"		: "#aa0000",
		"frame-color"		: "#e0e0e0",
		"frame-empty"		: "#f0f0f0",
		"frame-matrix"		: "#bbccdd",
		"frame-border"		: "#d0d0d0",
		"tools"				: ["pencil","line","rectangle","fill","picker","zoom"],
		"palette-length"	: 20,
		"palette-width"		: 20,
		"palette-height"	: 20,
		"palette-active-width"	: 40,
		"palette-active-height"	: 20,
		"images"			: {
			"pencil"			: {
				"src"					: "pencil.png",
				"width"					: 20,
				"height"				: 20
			},
			"pencil-active"		: {
				"src"					: "pencil-active.png",
				"width"					: 20,
				"height"				: 20
			},
			"line"				: {
				"src"					: "line.png",
				"width"					: 20,
				"height"				: 20
			},
			"line-active"		: {
				"src"					: "line-active.png",
				"width"					: 20,
				"height"				: 20
			},
			"rectangle"			: {
				"src"					: "rectangle.png",
				"width"					: 20,
				"height"				: 20
			},
			"rectangle-active"			: {
				"src"					: "rectangle-active.png",
				"width"					: 20,
				"height"				: 20
			},
			"fill"				: {
				"src"					: "fill.png",
				"width"					: 20,
				"height"				: 20
			},
			"fill-active"		: {
				"src"					: "fill-active.png",
				"width"					: 20,
				"height"				: 20
			},
			"picker"			: {
				"src"					: "picker.png",
				"width"					: 20,
				"height"				: 20
			},
			"picker-active"		: {
				"src"					: "picker-active.png",
				"width"					: 20,
				"height"				: 20
			},
			"zoom"				: {
				"src"					: "zoom.png",
				"width"					: 20,
				"height"				: 20
			},
			"zoom-active"		: {
				"src"					: "zoom-active.png",
				"width"					: 20,
				"height"				: 20
			},
			"palette"			: {
				"src"					: "palette.png",
				"width"					: 20,
				"height"				: 20
			},
			"palette-active"	: {
				"src"					: "palette-active.png",
				"width"					: 40,
				"height"				: 20
			},
			"rewind"			: {
				"src"					: "rewind.png",
				"width"					: 20,
				"height"				: 20
			},
			"play"			: {
				"src"					: "play.png",
				"width"					: 20,
				"height"				: 20
			},
			"pause"			: {
				"src"					: "pause.png",
				"width"					: 20,
				"height"				: 20
			},
			"end"			: {
				"src"					: "end.png",
				"width"					: 20,
				"height"				: 20
			},
		}
	}
}

### 

class Application(tk.Frame):
	def __init__(self, master=None):
		self.root			= master
		super().__init__(self.root)
		self.version		= [int(v) for v in VERSION.split()[0].split(".")]
		self.loop 			= asyncio.get_event_loop()
		self.width			= 800
		self.height			= 600
		self.state			= self.root.wm_state()
		
		self.changes_made	= False
		self.changes_draw	= False
		self.is_playing		= False
		self.is_loading		= False
		self.is_m1_down		= False
		self.is_m3_down		= False
		self.file			= ""
		self.tool			= ""
		self.color			= 0
		self.start_x		= None
		self.end_x			= 0
		self.start_y		= None
		self.end_y			= 0
		self.animation		= self.new_animation() # animation data
		self.render_cache	= {}

		# images
		self.path			= "\\".join(os.path.realpath(__file__).split("\\")[:-1])
		self.images			= {}
		for img in self.animation["stage"]["images"]:
			try:
				self.images[img]	= tk.PhotoImage(file=os.path.join(self.path,"images",self.animation["stage"]["images"][img]["src"]),width=self.animation["stage"]["images"][img]["width"],height=self.animation["stage"]["images"][img]["height"])
			except:
				self.error("A keresett fájl nem található!","Nem található a(z) "+self.animation["stage"]["images"][img]["src"]+" képfájl.")
				self.images[img]	= tk.PhotoImage(width=self.animation["stage"]["images"][img]["width"],height=self.animation["stage"]["images"][img]["height"])
		for img in LAYOUT["DEFAULT"]["images"]:
			try:
				self.images[img]	= tk.PhotoImage(file=os.path.join(self.path,"images",LAYOUT["DEFAULT"]["images"][img]["src"]),width=LAYOUT["DEFAULT"]["images"][img]["width"],height=LAYOUT["DEFAULT"]["images"][img]["height"])
			except:
				self.error("A keresett fájl nem található!","Nem található a(z) "+LAYOUT["DEFAULT"]["images"][img]["src"]+" képfájl.")
				self.images[img]	= tk.PhotoImage(width=LAYOUT["DEFAULT"]["images"][img]["width"],height=LAYOUT["DEFAULT"]["images"][img]["height"])
		
		# generate editor window
		self.root.minsize(self.width,self.height)
		self.root.configure(background=LAYOUT["DEFAULT"]["root"])
		self.root.protocol("WM_DELETE_WINDOW", self.file_quit)
		
		try:
			self.create_menubar()
			self.create_timeline()
			self.create_stage()
			self.pack()
		except Exception as e:
			self.error("Nem sikerült létrehozni a menüelemeket!",e)
		
		self.render(True)
		self.root.bind("<Configure>", self.on_resize)
		self.log("Alkalmazás készen áll")
	
	def new_animation(self):
		data				= {
			"header"			: "QPY",
			"version"			: self.version,
			"stage"				: PROFILES["SCH"].copy(),
			"properties"		: {
				"title"				: "Ischmeretlen",
				"team"				: "Schapatnév",
				"year"				: time.strftime("%Y"),
				"music"				: "",
				"selected_layer"	: 0,
				"selected_frame"	: 0,
				"zoom"				: 10
			},
			"timeline"			: []
		}
		while len(data["stage"]["palette"])<LAYOUT["DEFAULT"]["palette-length"]:
			data["stage"]["palette"].append("#ffffff")
		# TODO: allow the manual addition of multiple layers later
		for layer in ["Felső réteg","Középső réteg","Hátsó réteg"]:
			data["timeline"].append({
				"name"					: layer,
				"type"					: "normal",
				"visible"				: True,
				"render"				: True,
				"frames"				: [{
					"type"					: "empty",	# empty, matrix, link
					"data"					: {}
				}]
			})
		return data
	
	def int2hex(n):
		return str(hex(n)).format(16746513).replace("0x","#",1)
		
	def hex2int(n):
		return int(n.replace("#","0x",1),16)
	
	def create_menubar(self):		
		self.menubar		= tk.Menu(self.root)
		
		self.file_menu		= tk.Menu(self.menubar, tearoff=0)
		self.file_menu.add_command(label = "Új", command = self.file_new, underline=1,accelerator="Ctrl+N")
		self.root.bind_all("<Control-n>", self.file_new)
		self.file_menu.add_command(label = "Megnyitás", command = self.file_open, underline=1,accelerator="Ctrl+O")
		self.root.bind_all("<Control-o>", self.file_open)
		self.file_menu.add_command(label = "Mentés", command = self.file_save, underline=1,accelerator="Ctrl+S")
		self.root.bind_all("<Control-s>", self.file_save)
		self.file_menu.add_command(label = "Mentés másként", command = self.file_save_as, underline=1,accelerator="Ctrl+Shift+S")
		self.root.bind_all("<Control-S>", self.file_save_as)
		self.file_menu.add_separator()
		self.file_menu.add_command(label = "Importálás", command = self.file_import, underline=1,accelerator="Ctrl+I", state=tk.DISABLED)
		self.root.bind_all("<Control-i>", self.file_import)
		self.file_menu.add_command(label = "Exportálás", command = self.file_export, underline=1,accelerator="Ctrl+Enter")
		self.root.bind_all("<Control-Return>", self.file_export)
		self.file_menu.add_separator()
		self.file_menu.add_command(label = "Kilépés", command = self.file_quit, underline=1,accelerator="Ctrl+Q")
		self.root.bind_all("<Control-q>", self.file_quit)
		
		self.edit_menu		= tk.Menu(self.menubar, tearoff=0)
		self.edit_menu.add_command(label = "Visszavonás", command = self.edit_undo, underline=1,accelerator="Ctrl+Z", state=tk.DISABLED)
		self.root.bind_all("<Control-z>", self.edit_undo)
		self.edit_menu.add_separator()
		self.edit_menu.add_command(label = "Képkocka kivágása", command = self.edit_cut, underline=1,accelerator="Ctrl+X")
		self.root.bind_all("<Control-x>", self.edit_cut)
		self.edit_menu.add_command(label = "Képkocka másolása", command = self.edit_copy, underline=1,accelerator="Ctrl+C")
		self.root.bind_all("<Control-c>", self.edit_copy)
		self.edit_menu.add_command(label = "Képkocka felülírása", command = self.edit_paste, underline=1,accelerator="Ctrl+V")
		self.root.bind_all("<Control-v>", self.edit_paste)
		self.edit_menu.add_command(label = "Képkocka beszúrása", command = self.edit_insert, underline=1,accelerator="Ctrl+B")
		self.root.bind_all("<Control-b>", self.edit_insert)
		self.edit_menu.add_separator()
		self.edit_menu.add_command(label = "Képkocka törlése", command = self.edit_delete, underline=1,accelerator="Del")
		self.root.bind_all("<Delete>", self.edit_delete)
		self.edit_menu.add_command(label = "Képkocka tartalmának letörlése", command = self.edit_empty, underline=1,accelerator="Ctrl+R")
		self.root.bind_all("<Control-r>", self.edit_empty)
		self.edit_menu.add_command(label = "Képkocka duplikálása", command = self.edit_duplicate, underline=1,accelerator="Ctrl+D")
		self.root.bind_all("<Control-d>", self.edit_duplicate)
		self.root.bind_all("<F6>", self.edit_duplicate)
		self.edit_menu.add_command(label = "Üres képkocka beszúrása", command = self.edit_insert_empty, underline=1,accelerator="Ctrl+E")
		self.root.bind_all("<Control-e>", self.edit_insert_empty)
		self.root.bind_all("<F7>", self.edit_insert_empty)
		self.edit_menu.add_separator()
		self.edit_menu.add_command(label = "Képkocka hosszabbítása", command = self.edit_extend, underline=1,accelerator="+")
		self.root.bind_all("<Key-plus>", self.edit_extend)
		self.root.bind_all("<F5>", self.edit_extend)
		self.edit_menu.add_command(label = "Képkocka rövidítése", command = self.edit_reduce, underline=1,accelerator="-")
		self.root.bind_all("<Key-minus>", self.edit_reduce)
		
		self.properties_menu= tk.Menu(self.menubar, tearoff=0)
		self.properties_menu.add_command(label = "Animáció tulajdonságai", command = self.properties_animation)
		self.properties_menu.add_command(label = "Színpad tulajdonságai", command = self.properties_stage, state=tk.DISABLED)
		self.properties_menu.add_command(label = "Zene betöltése", command = self.properties_music)
		
		self.transform_menu	= tk.Menu(self.menubar, tearoff=0)
		self.transform_menu.add_command(label = "Elforgatás jobbra 90 fokkal", command = self.transform_rotate_right, state=tk.DISABLED)
		self.transform_menu.add_command(label = "Elforgatás balra 90 fokkal", command = self.transform_rotate_left, state=tk.DISABLED)
		self.transform_menu.add_command(label = "Vízszintes tükrözés", command = self.transform_flip_horizontal, state=tk.DISABLED)
		self.transform_menu.add_command(label = "Függőleges tükrözés", command = self.transform_flip_vertical, state=tk.DISABLED)
		self.transform_menu.add_command(label = "Elmozgatás felfelé", command = self.transform_move_up, underline=1,accelerator="Up")
		self.root.bind_all("<Up>", self.transform_move_up)
		self.transform_menu.add_command(label = "Elmozgatás lefelé", command = self.transform_move_down,underline=1,accelerator="Down")
		self.root.bind_all("<Down>", self.transform_move_down)
		self.transform_menu.add_command(label = "Elmozgatás balra", command = self.transform_move_left,underline=1,accelerator="Left")
		self.root.bind_all("<Left>", self.transform_move_left)
		self.transform_menu.add_command(label = "Elmozgatás jobbra", command = self.transform_move_right,underline=1,accelerator="Right")
		self.root.bind_all("<Right>", self.transform_move_right)
		
		self.playback_menu	= tk.Menu(self.menubar, tearoff=0)
		self.playback_menu.add_command(label = "Lejátszás", command = self.playback_toggle, underline=1,accelerator="Space")
		self.root.bind_all("<space>", self.playback_toggle)
		self.playback_menu.add_command(label = "Elejére", command = self.playback_rewind, underline=1,accelerator="Home")
		self.root.bind_all("<Home>", self.playback_rewind)
		self.playback_menu.add_command(label = "Végére", command = self.playback_end, underline=1,accelerator="End")
		self.root.bind_all("<End>", self.playback_end)
		self.playback_menu.add_command(label = "Egy kockát vissza", command = self.playback_back, underline=1,accelerator="PgDn")
		self.root.bind_all("<Next>", self.playback_back)
		self.playback_menu.add_command(label = "Egy kockát előre", command = self.playback_next, underline=1,accelerator="PgUp")
		self.root.bind_all("<Prior>", self.playback_next)

		self.help_menu		= tk.Menu(self.menubar, tearoff=0)
		self.help_menu.add_command(label = "Névjegy", command = self.other_about,underline=1,accelerator="F1")
		self.root.bind_all("<F1>", self.other_about)
		
		self.menubar.add_cascade(label = "Fájl", menu=self.file_menu)
		self.menubar.add_cascade(label = "Szerkesztés", menu=self.edit_menu)
		self.menubar.add_cascade(label = "Tulajdonságok", menu = self.properties_menu)
		self.menubar.add_cascade(label = "Transzformáció", menu = self.transform_menu)
		self.menubar.add_cascade(label = "Lejátszó", menu = self.playback_menu)
		self.menubar.add_cascade(label = "Segítség", menu = self.help_menu)
		self.root.config(menu=self.menubar)
		
		self.root.bind_all("<Tab>", self.change_layer)
		
	def create_timeline(self):
		height				= LAYOUT["DEFAULT"]["layer-height"]*3+LAYOUT["DEFAULT"]["layer-offset"]
		self.timeline 		= tk.Frame(self.root, bg=LAYOUT["DEFAULT"]["layer"], bd=0, highlightthickness=0)
		tk.Grid.columnconfigure(self.timeline, 1, weight=1)
		self.timeline_layers= tk.Canvas(self.timeline, width=LAYOUT["DEFAULT"]["layer-width"], height=height, bg=LAYOUT["DEFAULT"]["root"], bd=0, highlightthickness=0)
		self.timeline_layers.grid(row=0,column=0,sticky="w")
		self.timeline_frames= tk.Canvas(self.timeline,height=height)
		self.timeline_frames.grid(row=0,column=1,sticky="wen")
		self.timeline_scrollbar_h= tk.Scrollbar(self.timeline,orient='horizontal',command=self.timeline_frames.xview)
		self.timeline_scrollbar_h.grid(row=1,column=1,sticky="wen")
		self.timeline_frames.config(yscrollcommand = self.timeline_scrollbar_h.set)
		self.timeline.pack(fill=tk.X)
		self.timeline_layers.bind("<Button-1>",self.mouse_click_layers)
		self.timeline_frames.bind("<Button-1>",self.mouse_click_frames)
		self.timeline_layers.bind("<Button-3>",self.mouse_popup_layers)
		self.timeline_frames.bind("<Button-3>",self.mouse_popup_frames)
		self.timeline_layers.bind('<Enter>',self.mouse_to_hand)
		self.timeline_layers.bind('<Leave>',self.mouse_to_default)
		self.timeline_frames.bind("<MouseWheel>", self.mouse_wheel_frames)

	def create_stage(self):
		self.stage 		= tk.Frame(self.root, bg=LAYOUT["DEFAULT"]["toolbar"], bd=0)
		tk.Grid.columnconfigure(self.stage, 1, weight=1)
		tk.Grid.rowconfigure(self.stage, 0, weight=1)
		self.stage_tools= tk.Frame(self.stage,width=100, bg=LAYOUT["DEFAULT"]["toolbar"], bd=0, highlightthickness=0)
		self.stage_tools.grid(row=0,column=0,sticky="nswe")
		self.stage_tools_buttons={}
		for i,button in enumerate(LAYOUT["DEFAULT"]["tools"]):
			self.stage_tools_buttons[button]			= tk.Button(self.stage_tools,width=LAYOUT["DEFAULT"]["button-width"],height=LAYOUT["DEFAULT"]["button-height"],image=self.images[button],bg=LAYOUT["DEFAULT"]["button"],bd=1)
			self.stage_tools_buttons[button]["command"]	= lambda workaround=button: self.button_tool(workaround)
			self.stage_tools_buttons[button].grid(row=int(i/(LAYOUT["DEFAULT"]["toolbar-column"])),column=int(i%LAYOUT["DEFAULT"]["toolbar-column"]),sticky="w")
		
		self.stage_editor= tk.Canvas(self.stage, bg=LAYOUT["DEFAULT"]["stage"], width=428, height=411, bd=0,highlightthickness=0) #(0,0,428,411)
		self.stage_editor.grid(row=0,column=1,sticky="nswe")
		self.stage_scrollbar_h= tk.Scrollbar(self.stage,orient='vertical',command=self.stage_editor.yview)
		self.stage_scrollbar_h.grid(row=0,column=2,sticky="ns")
		self.stage_scrollbar_w= tk.Scrollbar(self.stage,orient='horizontal',command=self.stage_editor.xview)
		self.stage_scrollbar_w.grid(row=1,column=1,sticky="we")	
		self.stage_preview= tk.Canvas(self.stage,width=300, bg=self.animation["stage"]["skybox-color"],bd=0,highlightthickness=0)
		self.stage_preview.grid(row=0,column=3,sticky="nswe")
		self.stage.pack(fill=tk.BOTH,expand=True)
		self.stage_editor.configure(yscrollcommand = self.stage_scrollbar_h.set)
		self.stage_editor.configure(xscrollcommand = self.stage_scrollbar_w.set)
		
		self.stage_colorpicker_padding= tk.Frame(self.stage, bd=0, highlightthickness=0, bg=LAYOUT["DEFAULT"]["toolbar"], width=428, height=LAYOUT["DEFAULT"]["toolbar-padding"])
		self.stage_colorpicker_padding.grid(row=2,column=1,sticky="nswe")
		self.stage_colorpicker= tk.Frame(self.stage, bd=0, highlightthickness=0, bg=LAYOUT["DEFAULT"]["toolbar"], width=428, height=LAYOUT["DEFAULT"]["toolbar-height"]-LAYOUT["DEFAULT"]["toolbar-padding"])
		self.stage_colorpicker.grid(row=3,column=1,sticky="nswe")
		self.stage_colorpicker_buttons=[]
		color	= self.animation["stage"]["palette"][self.color]
		self.stage_colorpicker_buttons.append(tk.Button(self.stage_colorpicker,width=LAYOUT["DEFAULT"]["palette-active-width"],height=LAYOUT["DEFAULT"]["palette-active-height"],image=self.images["palette-active"],bg=color,highlightcolor=color,relief="flat",bd=0,highlightthickness=0,highlightbackground=color,fg=color,activebackground=color,activeforeground=color,cursor="hand2"))
		self.stage_colorpicker_buttons[-1]["command"]	= lambda: self.button_colorpicker(-1)
		self.stage_colorpicker_buttons[-1].grid(row=0,column=0,sticky="w")
		tk.Frame(self.stage_colorpicker, bg=LAYOUT["DEFAULT"]["toolbar"],width=LAYOUT["DEFAULT"]["palette-width"],height=LAYOUT["DEFAULT"]["palette-height"]).grid(row=0, column=1,sticky="nswe")
		for i,color in enumerate(self.animation["stage"]["palette"]):
			self.stage_colorpicker_buttons.append(tk.Button(self.stage_colorpicker,width=LAYOUT["DEFAULT"]["palette-width"],height=LAYOUT["DEFAULT"]["palette-height"],image=self.images["palette"],bg=color,highlightcolor=color,relief="flat",bd=0,highlightthickness=0,highlightbackground=color,fg=color,activebackground=color,activeforeground=color,cursor="hand2"))
			self.stage_colorpicker_buttons[-1]["command"]	= lambda workaround=i: self.button_colorpicker(workaround)
			self.stage_colorpicker_buttons[-1].grid(row=0,column=i+2,sticky="nswe")
		
		self.stage_playback		= tk.Frame(self.stage, bd=0, highlightthickness=0, bg=LAYOUT["DEFAULT"]["toolbar"], width=300, height=LAYOUT["DEFAULT"]["toolbar-height"])
		self.stage_playback.grid(row=3,column=3)
		self.stage_playback_rewind = tk.Button(self.stage_playback,width=LAYOUT["DEFAULT"]["button-width"],height=LAYOUT["DEFAULT"]["button-height"],image=self.images["rewind"],bg=LAYOUT["DEFAULT"]["button"],command=self.playback_rewind)
		self.stage_playback_rewind.grid(row=0,column=0,sticky="nsw")		
		self.stage_playback_toggle = tk.Button(self.stage_playback,width=LAYOUT["DEFAULT"]["button-width"],height=LAYOUT["DEFAULT"]["button-height"],image=self.images["play"],bg=LAYOUT["DEFAULT"]["button"],command=self.playback_toggle)
		self.stage_playback_toggle.grid(row=0,column=2,sticky="nswe")		
		self.stage_playback_end = tk.Button(self.stage_playback,width=LAYOUT["DEFAULT"]["button-width"],height=LAYOUT["DEFAULT"]["button-height"],image=self.images["end"],bg=LAYOUT["DEFAULT"]["button"],command=self.playback_end)
		self.stage_playback_end.grid(row=0,column=3,sticky="nse")		
		
		self.stage_editor.bind('<Enter>',self.mouse_to_hand)
		self.stage_preview.bind('<Enter>',self.mouse_to_hand)
		self.stage_editor.bind('<Leave>',self.mouse_to_default)
		self.stage_preview.bind('<Leave>',self.mouse_to_default)
		self.stage_editor.bind("<Button-1>",self.mouse_click_stage)
		self.stage_preview.bind("<Button-1>",self.mouse_click_preview)
		self.stage_editor.bind("<ButtonRelease-1>",self.mouse_release_stage)
		self.stage_preview.bind("<ButtonRelease-1>",self.mouse_release_preview)
		self.stage_editor.bind("<Button-3>",self.mouse_popup_stage)
		self.stage_preview.bind("<Button-3>",self.mouse_popup_preview)
		self.stage_editor.bind("<ButtonRelease-3>",self.mouse_release_stage)
		self.stage_preview.bind("<ButtonRelease-3>",self.mouse_release_preview)
		self.stage_editor.bind("<Motion>",self.mouse_move_stage)
		self.stage_preview.bind("<Motion>",self.mouse_move_preview)
		self.stage_editor.bind("<MouseWheel>", self.mouse_wheel_stage)
		self.stage_preview.bind("<MouseWheel>", self.mouse_wheel_stage)
		
		self.button_tool(LAYOUT["DEFAULT"]["tools"][0])
	
	### RENDER ELEMENTS
	def render_layers(self,redraw=False):
		offset 			= LAYOUT["DEFAULT"]["layer-offset"]
		height 			= LAYOUT["DEFAULT"]["layer-height"]-1
		width			= LAYOUT["DEFAULT"]["layer-width"]-1
		if redraw:
			self.timeline_layers.delete("all")			
			for i, layer in enumerate(self.animation["timeline"]):
				self.timeline_layers.create_rectangle(0, offset+i*height, width, offset+(i+1)*height, fill=LAYOUT["DEFAULT"]["layer"], outline="#444444")
				self.timeline_layers.create_line(0, offset+i*height, width, offset+i*height, fill="#ffffff")
				self.timeline_layers.create_line(0, offset+i*height, 0, offset+(i+1)*height, fill="#ffffff")
				self.timeline_layers.create_text(10,offset+i*height+(height/2),fill=LAYOUT["DEFAULT"]["layer-color"],font="system 10", text=layer["name"],anchor="w")
		try:
			self.timeline_layers.delete(self.timeline_layers_select)
		except:
			pass
		self.timeline_layers_select	= self.timeline_layers.create_rectangle(1, offset+self.animation["properties"]["selected_layer"]*height+1, width-1, offset+(self.animation["properties"]["selected_layer"]+1)*height-1, fill=LAYOUT["DEFAULT"]["layer-active"], outline="", stipple="gray50")

	def render_frames(self,redraw=False):
		offset 			= LAYOUT["DEFAULT"]["layer-offset"]-1
		width			= LAYOUT["DEFAULT"]["frame-width"]
		height			= LAYOUT["DEFAULT"]["layer-height"]
		max_frames		= 0
		max_height		= (len(self.animation["timeline"])+1)*height
		for layer in self.animation["timeline"]:
			max_frames		= max(max_frames,len(layer["frames"]))
		max_frames		+=10 # extra second visible in editor
		max_width		= max(60,int(self.timeline_frames.winfo_width()/width)+1)
		if redraw:
			self.timeline_frames.delete("all")
			for i in range(max(max_width,max_frames)+1):
				last		= ""
				color		= ""
				for j in range(len(self.animation["timeline"])):
					if i<len(self.animation["timeline"][j]["frames"]):
						try:
							if self.animation["timeline"][j]["frames"][i]["type"]=="empty":
								color	= LAYOUT["DEFAULT"]["frame-empty"]
							elif self.animation["timeline"][j]["frames"][i]["type"]=="matrix":
								color	= LAYOUT["DEFAULT"]["frame-matrix"]
							else:
								color	= last
						except Exception as e:
							raise e
					else:
						color		= ""
					last		= color
					if color:
						outline		= LAYOUT["DEFAULT"]["frame-border"]
					else:
						outline		= LAYOUT["DEFAULT"]["frame-color"]	
					self.timeline_frames.create_rectangle(i*width+1, offset+j*height+1, (i+1)*width, offset+(j+1)*height, fill=color, outline=outline)
				if i%10==0:
					self.timeline_frames.create_text(i*width+6,offset-12,fill=LAYOUT["DEFAULT"]["layer-color"],font="system 10", text=str(int(i/10)))
					self.timeline_frames.create_line(i*width+1, offset-10, i*width+1, offset, fill=LAYOUT["DEFAULT"]["layer-color"])
				elif i%5==0:
					self.timeline_frames.create_line(i*width+1, offset-10, i*width+1, offset, fill=LAYOUT["DEFAULT"]["layer-color"])
				else:
					self.timeline_frames.create_line(i*width+1, offset-5, i*width+1, offset, fill=LAYOUT["DEFAULT"]["layer-color"])
			self.timeline_frames.create_line(0, offset, (max(max_width,max_frames)+1)*width+1, offset, fill=LAYOUT["DEFAULT"]["layer-color"])
		try:
			self.timeline_frames.delete(self.timeline_frames_select)
			self.timeline_frames.delete(self.timeline_frames_select_line)
			self.timeline_frames.delete(self.timeline_frames_select_frame)
		except:
			pass
		self.timeline_frames_select	= self.timeline_frames.create_rectangle(self.animation["properties"]["selected_frame"]*width+1, 1, (self.animation["properties"]["selected_frame"]+1)*width-1, offset, outline=LAYOUT["DEFAULT"]["frame-active"], fill=LAYOUT["DEFAULT"]["frame-active"], stipple="gray50")
		self.timeline_frames_select_line= self.timeline_frames.create_line(int(self.animation["properties"]["selected_frame"]*width+width*.5), offset+2, int(self.animation["properties"]["selected_frame"]*width+width*.5), max_height, fill=LAYOUT["DEFAULT"]["frame-active"],stipple="gray25")
		self.timeline_frames_select_frame= self.timeline_frames.create_rectangle(self.animation["properties"]["selected_frame"]*width+1, offset+self.animation["properties"]["selected_layer"]*height, (self.animation["properties"]["selected_frame"]+1)*width-1, offset+(self.animation["properties"]["selected_layer"]+1)*height, outline=LAYOUT["DEFAULT"]["frame-active"], fill="", stipple="gray50")
		self.timeline_frames.configure(scrollregion=(0,0,(max(max_width,max_frames)+10)*width,height))
		self.timeline_frames.update()
	
	def render_editor(self,redraw=False):
		if redraw:
			size	= max(1,self.animation["properties"]["zoom"])
			width	= self.stage_editor.winfo_width()
			height	= self.stage_editor.winfo_height()
			p_width	= self.animation["stage"]["width"]
			p_height= self.animation["stage"]["height"]
			left	= int((width-p_width*size)/2)
			top		= int((height-p_height*size)/2)
				
			self.stage_editor.delete("all")
			self.stage_editor.create_rectangle(left, top, left+p_width*size, top+p_height*size, fill=self.animation["stage"]["background-color"], outline=self.animation["stage"]["border-color"])		

			min_x, min_y, max_x, max_y 	= 0, 0, p_width, p_height
			self.render_cache			= {}
			for i, layer in enumerate(reversed(self.animation["timeline"])):
				if layer["visible"] or layer["render"]:
					if self.animation["properties"]["selected_layer"]!=len(self.animation["timeline"])-1-i:
						stipple	= "gray50"	
					else:
						stipple	= ""
					select	= min(self.animation["properties"]["selected_frame"],len(layer["frames"])-1)
					if layer["frames"][select]["type"]=="link":
						select	= layer["frames"][select]["data"]
					frame	= layer["frames"][select]["data"]
					is_empty= True
					for x in frame:
						for y in frame[x]:
							is_empty= False
							min_x	= min(min_x,x)
							min_y	= min(min_y,y)
							max_x	= max(max_x,x)
							max_y	= max(max_y,y)
							if layer["visible"]:
								self.stage_editor.create_rectangle(left+x*size, top+y*size, left+(x+1)*size, top+(y+1)*size, fill=frame[x][y], outline="", stipple=stipple)										
							if layer["render"]:
								if x>=0 and x<p_width and y>=0 and y<p_height:
									if x not in self.render_cache:
										self.render_cache[x]	= {}
									self.render_cache[x][y]	= frame[x][y]
					if is_empty:
						layer["frames"][select]["type"]="empty"
					else:
						layer["frames"][select]["type"]="matrix"		
			self.stage_editor.configure(scrollregion=((min_x+1)*size,(min_y+1)*size,(max(p_width,max_x-min_x)+1)*size,(max(p_height,max_y-min_y)+1)*size))
		#self.stage_editor.update()
	
	def render_preview(self,redraw=False):
		width	= self.stage_preview.winfo_width()
		height	= self.stage_preview.winfo_height()
		offset_x= self.animation["stage"]["offset_x"]
		offset_y= height-self.animation["stage"]["images"]["preview"]["height"]+self.animation["stage"]["offset_y"]	
		
		if redraw:
			self.stage_preview.delete("all")
			self.stage_preview.create_image(int(self.animation["stage"]["images"]["preview"]["width"]/2),height-int(self.animation["stage"]["images"]["preview"]["height"]/2),image=self.images["preview"])
			self.stage_preview.create_rectangle(0, height, width, self.stage_preview.winfo_height(), fill=LAYOUT["DEFAULT"]["toolbar"], outline="")		
			#self.stage_preview.update()
		for x in range(self.animation["stage"]["width"]):
			for y in range(self.animation["stage"]["height"]):
				px		= int(offset_x+x*self.animation["stage"]["size_x"]+int(x/self.animation["stage"]["skip_x"])*self.animation["stage"]["pad_x"])
				py		= int(offset_y+y*self.animation["stage"]["size_y"]+int(y/self.animation["stage"]["skip_y"])*self.animation["stage"]["pad_y"])
				if x in self.render_cache and y in self.render_cache[x]:
					color	= self.render_cache[x][y]
				else:
					color	= self.animation["stage"]["background-color"]				
				self.stage_preview.create_rectangle(px,py,px+self.animation["stage"]["size_x"],py+self.animation["stage"]["size_y"],fill=color,outline="")

	def render_editor_helper(self,x,y,color):
		size	= max(1,self.animation["properties"]["zoom"])
		width	= self.stage_editor.winfo_width()
		height	= self.stage_editor.winfo_height()
		p_width	= self.animation["stage"]["width"]
		p_height= self.animation["stage"]["height"]
		left	= int((width-p_width*size)/2)
		top		= int((height-p_height*size)/2)
		self.stage_editor.create_rectangle(left+x*size, top+y*size, left+(x+1)*size, top+(y+1)*size, fill=color, outline="")
	
	def render_preview_helper(self,x,y,color):
		width	= self.stage_preview.winfo_width()
		height	= self.stage_preview.winfo_height()
		offset_x= self.animation["stage"]["offset_x"]
		offset_y= height-self.animation["stage"]["images"]["preview"]["height"]+self.animation["stage"]["offset_y"]		
		px		= int(offset_x+x*self.animation["stage"]["size_x"]+int(x/self.animation["stage"]["skip_x"])*self.animation["stage"]["pad_x"])
		py		= int(offset_y+y*self.animation["stage"]["size_y"]+int(y/self.animation["stage"]["skip_y"])*self.animation["stage"]["pad_y"])
		self.stage_preview.create_rectangle(px,py,px+self.animation["stage"]["size_x"],py+self.animation["stage"]["size_y"],fill=color,outline="")
	
	def render(self,redraw=False):
		self.loading(True)
		try:
			self.title()
			self.render_layers(redraw)
			self.render_frames(redraw)
			self.render_editor(redraw)
			self.render_preview(redraw)
		except Exception as e:
			self.error("Sikertelen az elemek kirajzolása!",e)
		self.loading(False)
	
	def title(self,name=""):
		if not name:
			name				= self.animation["properties"]["title"]
		self.root.title(TITLE+" "+VERSION+" - "+name)
		
	### FUNCTIONS
	
	def file_new(self,event=None):
		self.playback_pause()
		if self.changes_made:
			response			= messagebox.askyesnocancel(title="Új animáció létrehozása", message="Új animáció létrehozása előtt szeretnéd menteni a változtatásokat?", default=messagebox.YES)
			if response:
				self.file_save()
			elif response is None:
				return
		self.file			= ""
		self.changes_made	= False
		self.changes_draw	= False
		self.animation		= self.new_animation() 
		self.refresh_colorpicker()
		self.render(True)
		
	def file_open(self,event=None):
		self.playback_pause()
		if self.changes_made:
			response			= messagebox.askyesnocancel(title="Másik animáció megnyitása", message="Másik animáció megnyitása előtt szeretnéd menteni a változtatásokat?", default=messagebox.YES)
			if response:
				self.file_save()
			elif response is None:
				return
		file				= askopenfilename(defaultextension="*.qpy",initialdir="C:/Documents/",filetypes =(("QPY animációs fájl", "*.qpy"),),title = "Megnyitás")
		if file:
			self.file			= file
			try:
				self.loading(True)
				with codecs.open(self.file,"r",encoding="utf-8") as f:
					data				= f.read()
				if '"QPY"' not in data:
					return self.error("Nem megfelelő formátum!","A kiválasztott fájl nem Mátrix animáció!")
				try:
					data				= json.loads(data)
				except Exception as e:
					return self.error("Hibás vagy sérült fájl!",e)
				if "version" in data and "stage" in data and "properties" in data and "timeline" in data:
					if data["version"][0]>self.version[0] or data["version"][1]>self.version[1] or data["version"][2]>self.version[2]:
						# TODO: auto update
						messagebox.showinfo("Eltérő verziók!", "Ez az animáció egy újabb verziójú szerkesztőben lett létrehozva!\nElőfordulhat, hogy az animáció nem megfelelően fog megjelenni.")
					newdata				= data.copy()
					newdata["timeline"]	= []
					for layer in data["timeline"]:
						frames				= []
						for frame in layer["frames"]:
							if frame["data"] and isinstance(frame["data"],dict):
								fix		= {}
								for x in frame["data"]:
									fix[int(x)]	= {}
									for y in frame["data"][x]:
										fix[int(x)][int(y)]	= frame["data"][x][y]
								frame["data"]	= fix
							frames.append(frame)
						layer["frames"]	= frames
						newdata["timeline"].append(layer)
					self.animation		= newdata
					self.changes_made	= False
					self.changes_draw	= False
					self.refresh_colorpicker()
					self.render(True)
				else:
					return self.error("Hibás vagy sérült fájl!","A fájl alapján nem hozható létre animáció.")				
			except Exception as e:
				self.error("Nem sikerült megnyitni a fájlt!",e)
			self.render(True)
			self.loading(False)
		
	def file_save(self,event=None):
		if self.file:
			try:
				self.loading(True)
				f					= codecs.open(self.file,"w+",encoding="utf-8")
				f.write(json.dumps(self.animation))
				f.close()
				self.changes_made	= False
				self.changes_draw	= False
				self.loading(False)
			except Exception as e:
				return self.error("Nem sikerült menteni!",e)
		else:
			self.file_save_as(event)
	
	def file_save_as(self,event=None):
		self.playback_pause()
		file				= asksaveasfilename(defaultextension="*.qpy",initialdir="C:/Documents/",filetypes =(("QPY animációs fájl", "*.qpy"),))
		if file:
			self.file			= file
			try:
				self.loading(True)
				f					= codecs.open(self.file,"w+",encoding="utf-8")
				f.write(json.dumps(self.animation))
				f.close()
				self.changes_made	= False
				self.changes_draw	= False
				self.loading(False)
			except Exception as e:
				return self.error("Nem sikerült menteni!",e)
	
	def file_export(self,event=None):
		self.playback_pause()
		file				= asksaveasfilename(defaultextension="*.qp4",initialdir="C:/Documents/",filetypes =(("AnimEditor2012 fájl", "*.qp4"),))
		if file:
			self.loading(True)
			messagebox.showinfo("Exportálás sikeres" , "Az animáció konvertálása sikeres volt.")
			self.loading(False)
			self.log("Export")
		
	def file_import(self,event=None):
		self.log("Import")
	
	def file_quit(self,event=None):
		if self.changes_made:
			response			= messagebox.askyesnocancel(title="Kilépés a szerkesztőből", message="Kilépés előtt szeretnéd menteni a változtatásokat?", default=messagebox.YES)
			if response:
				self.file_save()
			elif response is None:
				return	
		try:
			self.root.destroy()
		except:
			pass
	
	def edit_undo(self,event=None):
		self.log("Undo/Redo")
		
	def edit_cut(self,event=None):
		self.log("Cut")
	
	def edit_copy(self,event=None):
		self.log("Copy")
	
	def edit_paste(self,event=None):
		self.log("Paste")
		
	def edit_insert(self,event=None):
		self.log("Insert")
	
	def edit_delete(self,event=None):
		self.log("Delete")	
	
	def edit_empty(self,event=None):
		self.log("Empty")	
		
	def edit_duplicate(self,event=None):
		self.log("Duplicate")	

	def edit_insert_empty(self,event=None):
		self.log("Insert empty")	
		
	def edit_extend(self,event=None):
		self.log("Extend")
		
	def edit_reduce(self,event=None):
		self.log("Reduce")
	
	def properties_animation(self,event=None):
		self.log("Animation properties")
		
	def properties_stage(self,event=None):
		self.log("Stage properties")
		
	def properties_music(self,event=None):
		self.log("Music properties")
	
	def transform_rotate_right(self,event=None):
		self.log("Transform rotate right")
	
	def transform_rotate_left(self,event=None):
		self.log("Transform rotate left")
		
	def transform_flip_horizontal(self,event=None):
		self.log("Transform flip horizontal")
	
	def transform_flip_vertical(self,event=None):
		self.log("Transform flip vertical")	
			
	def transform_move_up(self,event=None):
		self.log("Transform move up")	
	
	def transform_move_down(self,event=None):
		self.log("Transform move down")	
		
	def transform_move_left(self,event=None):
		self.log("Transform move left")	
		
	def transform_move_right(self,event=None):
		self.log("Transform move right")	

	def playback_toggle(self,event=None):
		if self.is_playing:
			self.playback_pause()
		else:
			self.playback_play()
	
	def playback_play(self,event=None):
		self.log("Play")
		self.stage_playback_toggle.configure(image=self.images["pause"])
		self.is_playing		= True
	
	def playback_pause(self,event=None):
		self.log("Pause")
		self.stage_playback_toggle.configure(image=self.images["play"])
		self.is_playing		= False
		
	def playback_stop(self,event=None):
		self.playback_pause()
		self.playback_rewind()
	
	def playback_rewind(self,event=None):
		self.log("Rewind")
	
	def playback_end(self,event=None):
		self.playback_pause()
		self.log("End")
		
	def playback_back(self,event=None):
		self.log("Back")
	
	def playback_next(self,event=None):
		self.log("Next")
	
	def other_about(self,event=None):
		toplevel			= tk.Toplevel(self)
		toplevel.geometry('480x130')
		label1 				= tk.Label(toplevel, text=TITLE,font=("Helvetica", 16),pady=3)
		label2 				= tk.Label(toplevel, text=VERSION.title(),font=("Helvetica", 12))
		label3 				= tk.Label(toplevel, text=URL,font=("Helvetica", 14),pady=5,fg="blue")
		label1.pack()
		label2.pack()
		label3.pack()
		button1				= tk.Button(toplevel, text='Dokumentáció',command=lambda: webbrowser.open(URL, new=0, autoraise=True))
		button1.pack()
	
	### MOUSE EVENTS
	def cursor(self,type=""):
		if not self.is_loading:
			self.root.config(cursor=type)
		
	def mouse_to_hand(self, event):
		self.cursor("hand2")
		self.is_m1_down	= False
		self.is_m3_down	= False
		self.changes_draw = False
	
	def mouse_to_default(self, event):
		self.cursor("")
		if self.tool=="line":
			self.line(self.end_x,self.end_y,self.is_m1_down,True,False)
		self.is_m1_down	= False
		self.is_m3_down	= False
		self.render_frames(self.changes_draw)
		self.render_editor(self.changes_draw)
		self.render_preview(self.changes_draw)
		self.changes_made=self.changes_made or self.changes_draw
		self.changes_draw = False
	
	def mouse_click_layers(self,event):
		y					= max(-1,int((self.timeline_layers.canvasy(event.y-LAYOUT["DEFAULT"]["layer-offset"])/LAYOUT["DEFAULT"]["layer-height"])))
		if y>=len(self.animation["timeline"]):
			y					= -1
		if y>-1:
			self.animation["properties"]["selected_layer"] = y
			self.render(True)
		
	def mouse_click_frames(self,event):
		x					= max(0,int((self.timeline_frames.canvasx(event.x)/LAYOUT["DEFAULT"]["frame-width"])))
		y					= max(-1,int((self.timeline_frames.canvasy(event.y-LAYOUT["DEFAULT"]["layer-offset"])/LAYOUT["DEFAULT"]["layer-height"])))
		if y>=len(self.animation["timeline"]):
			y					= -1
		if y>-1:
			self.animation["properties"]["selected_layer"] = y
		self.animation["properties"]["selected_frame"] = x
		self.render(True)
		
	def mouse_popup_layers(self, event):
		self.mouse_click_layers(event)
		try:
			self.playback_menu.tk_popup(event.x_root, event.y_root, 0)
		finally:
			self.playback_menu.grab_release()
	
	def mouse_popup_frames(self, event):
		self.mouse_click_frames(event)
		try:
			self.edit_menu.tk_popup(event.x_root, event.y_root, 0)
		finally:
			self.edit_menu.grab_release()
	
	def mouse_wheel_frames(self,event):
		value		= int(event.delta/120) # Windows needs /120
		if self.timeline_scrollbar_h.get()[0]>0 or value>0:
			self.timeline_frames.xview_scroll(value, "units")
		else:
			self.timeline_frames.xview_moveto(0)
	
	def mouse_click_stage(self,event):
		self.is_m1_down	= True
		self.start_x	= None
		self.start_y	= None
		self.mouse_move_stage(event)
	
	def mouse_popup_stage(self,event):
		self.is_m3_down	= True
		self.start_x	= None
		self.start_y	= None
		self.mouse_move_stage(event)
	
	def mouse_release_stage(self,event):
		if self.tool=="line":
			self.line(self.end_x,self.end_y,self.is_m1_down,True,False)
		self.is_m1_down	= False
		self.is_m3_down	= False
		self.render_frames(self.changes_draw)
		self.render_editor(self.changes_draw)
		self.render_preview(self.changes_draw)
		self.changes_made=self.changes_made or self.changes_draw
		self.changes_draw = False
	
	def mouse_move_stage(self,event):
		if self.is_m1_down or self.is_m3_down:
			size	= max(1,self.animation["properties"]["zoom"])
			width	= self.stage_editor.winfo_width()
			height	= self.stage_editor.winfo_height()
			p_width	= self.animation["stage"]["width"]
			p_height= self.animation["stage"]["height"]
			left	= int((width-p_width*size)/2)
			top		= int((height-p_height*size)/2)
			x		= int((self.stage_editor.canvasx(event.x)-left)/size)
			y		= int((self.stage_editor.canvasy(event.y)-top)/size)
			if self.start_x is None:
				self.start_x	= x
			if self.start_y is None:
				self.start_y	= y
			self.end_x	= x
			self.end_y	= y
			if self.tool=="pencil":
				self.pencil(x,y,self.is_m1_down,True)
			elif self.tool=="line":
				self.line(x,y,self.is_m1_down,True,True)
			elif self.tool=="fill":
				self.fill(x,y,self.is_m1_down,True)
			elif self.tool=="picker":
				self.picker(x,y,True)
			elif self.tool=="zoom":
				self.zoom(self.is_m1_down)
	
	def mouse_click_preview(self,event):
		self.is_m1_down	= True
		self.start_x	= None
		self.start_y	= None
		self.mouse_move_preview(event)
	
	def mouse_popup_preview(self,event):
		self.is_m3_down	= True
		self.start_x	= None
		self.start_y	= None
		self.mouse_move_preview(event)
	
	def mouse_release_preview(self,event):
		if self.tool=="line":
			self.line(self.end_x,self.end_y,self.is_m1_down,False,False)
		self.is_m1_down	= False
		self.is_m3_down	= False
		self.render_frames(self.changes_draw)
		self.render_editor(self.changes_draw)
		self.render_preview(self.changes_draw)
		self.changes_made=self.changes_made or self.changes_draw
		self.changes_draw = False
		
	def mouse_move_preview(self,event):
		if self.is_m1_down or self.is_m3_down:
			width	= self.stage_preview.winfo_width()
			height	= self.stage_preview.winfo_height()
			offset_x= self.animation["stage"]["offset_x"]
			offset_y= height-self.animation["stage"]["images"]["preview"]["height"]+self.animation["stage"]["offset_y"]		
			px		= int(self.stage_preview.canvasx(event.x))
			py		= int(self.stage_preview.canvasy(event.y))
			x		= int((px-offset_x)/(self.animation["stage"]["size_x"]+int(self.animation["stage"]["pad_x"]/self.animation["stage"]["skip_x"])))
			y		= int((py-offset_y)/(self.animation["stage"]["size_y"]+int(self.animation["stage"]["pad_y"]/self.animation["stage"]["skip_y"])))
			if self.start_x is None:
				self.start_x	= x
			if self.start_y is None:
				self.start_y	= y
			self.end_x	= x
			self.end_y	= y
			if self.tool=="pencil":
				if x>=0 and x<self.animation["stage"]["width"] and y>=0 and y<self.animation["stage"]["height"]:
					self.pencil(x,y,self.is_m1_down,False)
			elif self.tool=="line":
				self.line(x,y,self.is_m1_down,False,True)
			elif self.tool=="fill":
				if x>=0 and x<self.animation["stage"]["width"] and y>=0 and y<self.animation["stage"]["height"]:
					self.fill(x,y,self.is_m1_down,False)
			elif self.tool=="picker":
				if x>=0 and x<self.animation["stage"]["width"] and y>=0 and y<self.animation["stage"]["height"]:
					self.picker(x,y,False)
	
	def mouse_wheel_stage(self,event):
		if event.delta>0:
			self.color+=1
			if self.color>=len(self.animation["stage"]["palette"]):
				self.color=0
		else:
			self.color-=1
			if self.color<0:
				self.color	= len(self.animation["stage"]["palette"])-1
		self.button_colorpicker(self.color)
	
	### DRAWING
	def get_frame(self):
		self.changes_draw = True
		layer	= self.animation["timeline"][self.animation["properties"]["selected_layer"]]
		select	= min(self.animation["properties"]["selected_frame"],len(layer["frames"])-1)
		if layer["frames"][select]["type"]=="link":
			select	= layer["frames"][select]["data"]
		frame	= layer["frames"][select]["data"].copy()
		return frame, select
		
	def zoom(self,inc=True):
		self.is_m1_down	= False
		self.is_m3_down	= False
		if inc:
			self.animation["properties"]["zoom"] = min(int(self.animation["properties"]["zoom"]/5)*5+5,35)
		else:
			self.animation["properties"]["zoom"] = max(int(self.animation["properties"]["zoom"]/5)*5-5,1)
		self.render_editor(True)
		self.cursor("hand2")
	
	def picker(self,x,y,is_editor=True):
		self.is_m1_down	= False
		self.is_m3_down	= False
		self.changes_draw= False
		frame, select= self.get_frame()
		if is_editor:
			if x in frame and y in frame[x]:
				self.animation["stage"]["palette"][self.color]	= frame[x][y]
		else:
			if x in self.render_cache and y in self.render_cache[x]:
				self.animation["stage"]["palette"][self.color]	= self.render_cache[x][y]
		self.refresh_colorpicker()
		self.cursor("hand2")
	
	def pencil(self,x,y,add=True,is_editor=True):
		if add:
			color		= self.animation["stage"]["palette"][self.color]
		else:
			color		= self.animation["stage"]["background-color"]
		frame, select= self.get_frame()
		if add:
			if x not in frame:
				frame[x]	= {}
			frame[x][y]	= color
			self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["type"] = "matrix"
			self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["data"] = frame
		else:
			if x in frame:
				if y in frame[x]:
					del frame[x][y]
				if not frame[x]:
					del frame[x]
			if not frame:
				self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["type"] = "empty"
			self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["data"] = frame
		if is_editor:
			self.render_editor_helper(x,y,color)
		else:
			self.render_preview_helper(x,y,color)			
	
	def line(self,x,y,add=True,is_editor=True,hint=True):
		if self.start_x is None:
			self.start_x	= x
		if self.start_y is None:
			self.start_y	= y
		if add:
			color		= self.animation["stage"]["palette"][self.color]
		else:
			color		= self.animation["stage"]["background-color"]
		if hint:
			if is_editor:
				self.render_editor(True)
			else:
				self.render_preview(True)
		else:
			frame, select= self.get_frame()
		# based on http://floppsie.comp.glam.ac.uk/Glamorgan/gaius/gametools/6.html

		x0,x1,y0,y1		= x,self.start_x,y,self.start_y
		dx = abs(x1 - x0)
		dy = abs(y1 - y0)
		sx = -1 if x0 > x1 else 1
		sy = -1 if y0 > y1 else 1
		err = dx-dy
		while True:
			if hint:
				if is_editor:
					self.render_editor_helper(x0,y0,color)
				else:
					self.render_preview_helper(x0,y0,color)
			else:
				if add:
					if x0 not in frame:
						frame[x0]		= {}
					frame[x0][y0]	= color
				else:
					if x0 in frame and y0 in frame[x0]:
						del frame[x0][y0]
						if not frame[x0]:
							del frame[x0]
			if x0 == x1 and y0 == y1:
				break
			e2 = 2*err
			if e2 > -dy:
				err = err - dy
				x0 = x0 + sx
			if e2 < dx:
				err = err + dx
				y0 = y0 + sy

		if not hint:
			if x not in frame:
				frame[x]		= {}
			frame[x][y]		= color
			self.start_x	= None
			self.start_y	= None
			if not frame:
				self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["type"] = "empty"
			self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["data"] = frame
		
	def fill(self,x,y,add=True,is_editor=True):
		self.is_m1_down = False
		self.is_m3_down = False
		self.changes_made = True
		self.changes_draw= False
		frame, select= self.get_frame()
		min_x, min_y, max_x, max_y 	= 0, 0, self.animation["stage"]["width"], self.animation["stage"]["height"]
		strange_bug	= {}
		for _x in frame:
			if _x not in strange_bug:
				strange_bug[_x]={}
			for _y in frame[_x]:
				min_x	= min(min_x,_x)
				min_y	= min(min_y,_y)
				max_x	= max(max_x,_x)
				max_y	= max(max_y,_y)
				strange_bug[_x][_y]=frame[_x][_y]
		if x in frame and y in frame[x]:
			original= frame[x][y]
		else:
			original= ""
		if add:
			replace	= self.animation["stage"]["palette"][self.color]
		else:
			replace	= ""
		if original!=replace:
			self.fill_break=False
			strange_bug	= self.fill_flood(strange_bug,x,y,min_x,max_x,min_y,max_y,original,replace)
			if not self.fill_break:
				if strange_bug:
					self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["type"] = "matrix"
				else:
					self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["type"] = "empty"
				self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["data"] = strange_bug.copy()
		self.cursor("hand2")
	
	# based on https://stackoverflow.com/questions/19839947/flood-fill-in-python
	def fill_flood(self,frame,x,y,min_x,max_x,min_y,max_y,original,replace):
		if frame is False or self.fill_break:
			self.fill_break=True
			return frame
		if x<min_x or x>=max_x or y<min_y or y>=max_y:
			if original=="":
				self.fill_break=True
				return frame
		if (original=="" and (x not in frame or (x in frame and y not in frame[x]))) or (x in frame and y in frame[x] and frame[x][y] == original):
			if x not in frame:
				frame[x]={}
			if replace:
				frame[x][y] = replace 
			else:
				del frame[x][y]			
			if x >= min_x:
				frame	= self.fill_flood(frame.copy(),x-1,y,min_x,max_x,min_y,max_y,original,replace)
			if x < max_x:
				frame	= self.fill_flood(frame.copy(),x+1,y,min_x,max_x,min_y,max_y,original,replace)
			if y >= min_y:
				frame 	= self.fill_flood(frame.copy(),x,y-1,min_x,max_x,min_y,max_y,original,replace)
			if y < max_y:
				frame	= self.fill_flood(frame.copy(),x,y+1,min_x,max_x,min_y,max_y,original,replace)
			if x in frame and not frame[x]:
				del frame[x]
		return frame.copy()
	
	def button_tool(self,parameter):
		if parameter in LAYOUT["DEFAULT"]["tools"]:
			self.tool	= parameter
			for button in LAYOUT["DEFAULT"]["tools"]:
				self.stage_tools_buttons[button].configure(bg=LAYOUT["DEFAULT"]["button"])
				self.stage_tools_buttons[button].configure(image=self.images[button])
			self.stage_tools_buttons[parameter].configure(bg=LAYOUT["DEFAULT"]["button-active"])
			if parameter+"-active" in self.images:
				self.stage_tools_buttons[parameter].configure(image=self.images[parameter+"-active"])
	
	def button_colorpicker(self,i):
		if i>=0 and i<len(self.animation["stage"]["palette"]):
			self.color	= i
		else:
			new_color	= askcolor(initialcolor=self.animation["stage"]["palette"][self.color])
			self.animation["stage"]["palette"][self.color]	= new_color[1]
			self.stage_colorpicker_buttons[self.color+1].configure(bg=self.animation["stage"]["palette"][self.color],highlightcolor=self.animation["stage"]["palette"][self.color],highlightbackground=self.animation["stage"]["palette"][self.color],fg=self.animation["stage"]["palette"][self.color],activebackground=self.animation["stage"]["palette"][self.color],activeforeground=self.animation["stage"]["palette"][self.color])
		self.stage_colorpicker_buttons[0].configure(bg=self.animation["stage"]["palette"][self.color],highlightcolor=self.animation["stage"]["palette"][self.color],highlightbackground=self.animation["stage"]["palette"][self.color],fg=self.animation["stage"]["palette"][self.color],activebackground=self.animation["stage"]["palette"][self.color],activeforeground=self.animation["stage"]["palette"][self.color])

	### OTHER 
	
	def refresh_colorpicker(self):
		for i, color in enumerate(self.animation["stage"]["palette"]):
			self.stage_colorpicker_buttons[i+1].configure(bg=color,highlightcolor=color,highlightbackground=color,fg=color,activebackground=color,activeforeground=color)
		color		= self.animation["stage"]["palette"][0]
		self.stage_colorpicker_buttons[0].configure(bg=color,highlightcolor=color,highlightbackground=color,fg=color,activebackground=color,activeforeground=color)
		self.color	= 0
	
	def change_layer(self,event=None):
		self.animation["properties"]["selected_layer"] = (self.animation["properties"]["selected_layer"]+1)%len(self.animation["timeline"])
		self.render(True)
	
	def on_resize(self,event):
		try:
			self.root.update()
			update	= False
			if self.width!=self.root.winfo_width() or self.height!=self.root.winfo_height():
				update		= True
			if self.state!=self.root.wm_state():
				update		= True
				self.async_run(self.async_render())
			if update:
				self.stage_editor.update()
				self.stage_preview.update()
				self.stage.update()
				self.root.update()
				self.width	= self.root.winfo_width()
				self.height	= self.root.winfo_height()		
				self.state	= self.root.wm_state()
				self.render(True)
		except:
			pass
		
	def music():
		mixer.init()
		mixer.music.load("toto.mp3")
		mixer.music.play()
		mixer.music.rewind()
		mixer.music.set_pos(10)
	
	def loading(self,update=True):
		self.is_loading		= update
		if self.is_loading:
			self.root.config(cursor="wait")
		else:
			self.root.config(cursor="")
			
	def error(self,message="Ismeretlen hiba",e=None):					
		self.loading(False)
		messagebox.showerror(message, str(e))
		self.log(message+" - "+str(e))
		try:
			raise e
		except:
			pass
		return
	
	def log(self,message=""):
		print(time.strftime("%H:%M:%S")+" > "+message,flush=True)
	
	def async_run(self,func):
		threading.Thread(target=lambda:self.loop.run_until_complete(func)).start()
	
	async def async_render(self,event=None):
		try:
			await asyncio.sleep(.5)
			self.render(True)
		except:
			pass

if __name__ == "__main__":
	print("Ha ezt az ablakot bezárod, az alkalmazás is bezáródik!")
	app		= Application(master=tk.Tk())
	app.mainloop()
	print("Szerkesztő ablak bezárva.")