# -*- coding: UTF-8 -*-

import sys, os
import json
import webbrowser
import time
import codecs

import numpy as np
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
		"offset_x"			: [1,1,0],
		"offset_y"			: [0,1,1,0],
		"padding_x"			: 1,
		"padding_y"			: 1,
		"border_x"			: 2,
		"border_y"			: 1,
		"background-color"	: "#000000",
		"foreground-color"	: "#d0d0d0",
		"border-color"		: "#444444",
		"mode"				: "12-bit RGB",
		"palette"			: ["#FFFFFF","#AAAAAA","#FF0000","#AA0000","#00FF00","#00AA00","#0000FF","#0000AA","#FFFF00","#AA00AA"]
	}
}
LAYOUT		= {
	"DEFAULT"	: { # default color scheme
		"root"				: "#f0f0f0",
		"stage"				: "#b0b0b0",
		"toolbar"			: "#d0d0d0",
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
		"playback-height"	: 30,
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
		self.tool			= 0
		self.color			= 0
		self.animation		= self.new_animation() # animation data
					
		# generate editor window
		self.root.minsize(self.width,self.height)
		self.root.configure(background=LAYOUT["DEFAULT"]["root"])
		self.root.protocol("WM_DELETE_WINDOW", self.file_quit)
		
		try:
			self.create_menubar()
			self.create_timeline()
			self.create_stage()
			self.pack()
			#color	= askcolor(initialcolor="#FF00FF")
		except Exception as e:
			self.error("Nem sikerült létrehozni a menüelemeket!",e)
		
		self.render(True)
		self.root.bind("<Configure>", self.on_resize)
		self.log("Alkalmazás készen áll")
	
	def new_animation(self):
		data				= {
			"header"			: "QPY",
			"version"			: self.version,
			"stage"				: PROFILES["SCH"],
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
		# TODO: allow the manual addition of multiple layers later
		for layer in ["Felső réteg","Középső réteg","Hátsó réteg"]:
			data["timeline"].append({
				"name"					: layer,
				"type"					: "normal",
				"visibility"			: True,
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
		self.transform_menu.add_command(label = "Elforgatás jobbra 90 fokkal", command = self.transform_rotate_right)
		self.transform_menu.add_command(label = "Elforgatás balra 90 fokkal", command = self.transform_rotate_left)
		self.transform_menu.add_command(label = "Vízszintes tükrözés", command = self.transform_flip_horizontal)
		self.transform_menu.add_command(label = "Függőleges tükrözés", command = self.transform_flip_vertical)
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
		#self.playback		= tk.Frame(self.root, bd=0, highlightthickness=0, bg="red", height=10)
		#self.playback.pack(fill=tk.X)
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
		self.stage_tools_test=tk.Button(self.stage_tools,width=2,height=1,text="test",bg="red")
		self.stage_tools_test.grid(row=0,column=0,sticky="w")
		self.stage_tools_test2=tk.Button(self.stage_tools,width=3,height=1,text="test2",bg="green")
		self.stage_tools_test2.grid(row=1,column=1,sticky="w")
		
		self.stage_editor= tk.Canvas(self.stage, bg=LAYOUT["DEFAULT"]["stage"], width=428, height=411, bd=0,highlightthickness=0) #(0,0,428,411)
		self.stage_editor.grid(row=0,column=1,sticky="nswe")
		self.stage_scrollbar_h= tk.Scrollbar(self.stage,orient='vertical',command=self.stage_editor.yview)
		self.stage_scrollbar_h.grid(row=0,column=2,sticky="ns")
		self.stage_scrollbar_w= tk.Scrollbar(self.stage,orient='horizontal',command=self.stage_editor.xview)
		self.stage_scrollbar_w.grid(row=1,column=1,sticky="we")	
		self.stage_preview= tk.Canvas(self.stage,width=300, bg=LAYOUT["DEFAULT"]["toolbar"],bd=0,highlightthickness=0)
		self.stage_preview.grid(row=0,column=3,sticky="nswe")
		self.stage.pack(fill=tk.BOTH,expand=True)
		self.stage_editor.configure(yscrollcommand = self.stage_scrollbar_h.set)
		self.stage_editor.configure(xscrollcommand = self.stage_scrollbar_w.set)
		
		self.stage_editor.bind('<Enter>',self.mouse_to_hand)
		self.stage_preview.bind('<Enter>',self.mouse_to_hand)
		self.stage_editor.bind('<Leave>',self.mouse_to_default)
		self.stage_preview.bind('<Leave>',self.mouse_to_default)
		self.stage_editor.bind("<Button-1>",self.mouse_click_stage)
		self.stage_editor.bind("<ButtonRelease-1>",self.mouse_release_stage)
		self.stage_editor.bind("<Button-3>",self.mouse_popup_stage)
		self.stage_editor.bind("<ButtonRelease-3>",self.mouse_release_stage)
		self.stage_editor.bind("<Motion>",self.mouse_move_stage)
	
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
						if self.animation["timeline"][j]["frames"][i]["type"]=="empty":
							color	= LAYOUT["DEFAULT"]["frame-empty"]
						elif self.animation["timeline"][j]["frames"][i]["type"]=="matrix":
							color	= LAYOUT["DEFAULT"]["frame-matrix"]
						else:
							color	= last
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

			min_x, min_y, max_x, max_y = 0, 0, p_width, p_height
			for i, layer in enumerate(reversed(self.animation["timeline"])):
				if layer["visibility"]:
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
							pos_x	= int(x)
							pos_y	= int(y)
							min_x	= min(min_x,pos_x)
							min_y	= min(min_y,pos_y)
							max_x	= max(max_x,pos_x)
							max_y	= max(max_y,pos_y)
							self.stage_editor.create_rectangle(left+pos_x*size, top+pos_y*size, left+(pos_x+1)*size, top+(pos_y+1)*size, fill=frame[x][y], outline="", stipple=stipple)		
					if is_empty:
						layer["frames"][select]["type"]="empty"
					else:
						layer["frames"][select]["type"]="matrix"		
			self.stage_editor.configure(scrollregion=((min_x+1)*size,(min_y+1)*size,(max(p_width,max_x-min_x)+1)*size,(max(p_height,max_y-min_y)+1)*size))
		self.stage_editor.update()
	
	def render_preview(self,redraw=False):
		if redraw:
			self.stage_preview.delete("all")
			width	= self.stage_preview.winfo_width()
			height	= self.stage_preview.winfo_height()-LAYOUT["DEFAULT"]["playback-height"]
			prew_w	= self.animation["stage"]["padding_x"]*2+self.animation["stage"]["border_x"]*2
			tmp		= self.animation["stage"]["width"]
			while tmp>0:
				for i in self.animation["stage"]["offset_x"]:
					if i:
						tmp		-= 1
					prew_w	+= 1
			prew_h	= self.animation["stage"]["padding_y"]*2+self.animation["stage"]["border_y"]
			tmp		= self.animation["stage"]["height"]
			while tmp>0:
				for i in self.animation["stage"]["offset_y"]:
					if i:
						tmp		-= 1
					prew_h	+= 1
			self.prew_matrix= []
			for p in range(self.animation["stage"]["border_y"]):
				row		= ["b" for i in range(prew_w)]
				self.prew_matrix.append(row)
			for p in range(self.animation["stage"]["padding_y"]):
				row		= []
				row		+=["b" for i in range(self.animation["stage"]["border_x"])]
				row		+=["p" for i in range(prew_w-self.animation["stage"]["border_x"]*2)]
				row		+=["b" for i in range(self.animation["stage"]["border_x"])]
				self.prew_matrix.append(row)
			step_x	= 0
			step_y	= 0
			for p in range(prew_h-self.animation["stage"]["border_y"]):
				row		= []
				row		+=["b" for i in range(self.animation["stage"]["border_x"])]
				row		+=["p" for i in range(self.animation["stage"]["padding_x"])]
				row		+=["x" for i in range(prew_w-self.animation["stage"]["border_x"]*2-self.animation["stage"]["padding_x"]*2)]
				row		+=["p" for i in range(self.animation["stage"]["padding_x"])]
				row		+=["b" for i in range(self.animation["stage"]["border_x"])]
				self.prew_matrix.append(row)
			for p in range(self.animation["stage"]["padding_y"]):
				row		= []
				row		+=["b" for i in range(self.animation["stage"]["border_x"])]
				row		+=["p" for i in range(prew_w-self.animation["stage"]["border_x"]*2)]
				row		+=["b" for i in range(self.animation["stage"]["border_x"])]
				self.prew_matrix.append(row)
			size_w	= int(np.floor(width/prew_w))
			size_h	= int(np.floor(height/prew_h))
			offset_y= height-size_h*len(self.prew_matrix)
			offset_x= int(np.floor((width-size_w*len(self.prew_matrix[0]))/2))
			self.stage_preview.create_rectangle(0,0,width,height,fill=self.animation["stage"]["border-color"])
			for y,row in enumerate(self.prew_matrix):
				for x,type in enumerate(row):	
					if type=="b":
						color	= self.animation["stage"]["border-color"]
					elif type=="p":
						color	= self.animation["stage"]["foreground-color"]
					else:
						color	= self.animation["stage"]["background-color"]
					self.stage_preview.create_rectangle(x*size_w+offset_x,y*size_h+offset_y,(x+1)*size_w+offset_x,(y+1)*size_h+offset_y,fill=color,outline="")			
		self.stage_preview.update()
	
	def render_helper(self,x,y,color):
		size	= max(1,self.animation["properties"]["zoom"])
		width	= self.stage_editor.winfo_width()
		height	= self.stage_editor.winfo_height()
		p_width	= self.animation["stage"]["width"]
		p_height= self.animation["stage"]["height"]
		left	= int((width-p_width*size)/2)
		top		= int((height-p_height*size)/2)
		self.stage_editor.create_rectangle(left+x*size, top+y*size, left+(x+1)*size, top+(y+1)*size, fill=color, outline="")		
	
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
					self.animation		= data
					self.changes_made	= False
					self.changes_draw	= False
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
		self.root.destroy()
	
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
		self.is_playing		= True
	
	def playback_pause(self,event=None):
		self.log("Pause")
		self.is_playing		= False
		
	def playback_stop(self,event=None):
		self.playback_pause()
		self.playback_rewind()
	
	def playback_rewind(self,event=None):
		self.log("Rewind")
	
	def playback_end(self,event=None):
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
		self.is_m1_down	= False
		self.is_m3_down	= False
		self.render_frames(self.changes_draw)
		self.render_editor(self.changes_draw)
		self.render_preview(self.changes_draw)
		self.changes_draw = False
	
	def mouse_click_layers(self,event):
		y					= max(-1,int(np.floor(self.timeline_layers.canvasy(event.y-LAYOUT["DEFAULT"]["layer-offset"])/LAYOUT["DEFAULT"]["layer-height"])))
		if y>=len(self.animation["timeline"]):
			y					= -1
		if y>-1:
			self.animation["properties"]["selected_layer"] = y
			self.render()
		
	def mouse_click_frames(self,event):
		x					= max(0,int(np.floor(self.timeline_frames.canvasx(event.x)/LAYOUT["DEFAULT"]["frame-width"])))
		y					= max(-1,int(np.floor(self.timeline_frames.canvasy(event.y-LAYOUT["DEFAULT"]["layer-offset"])/LAYOUT["DEFAULT"]["layer-height"])))
		if y>=len(self.animation["timeline"]):
			y					= -1
		if y>-1:
			self.animation["properties"]["selected_layer"] = y
		if x!=self.animation["properties"]["selected_frame"]:
			self.animation["properties"]["selected_frame"] = x
			self.render(True)
		else:
			self.animation["properties"]["selected_frame"] = x
			self.render()
	
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
	
	def mouse_click_stage(self,event,add=True):
		self.is_m1_down	= True
		self.mouse_move_stage(event)
	
	def mouse_popup_stage(self,event):
		self.is_m3_down	= True
		self.mouse_move_stage(event)
	
	def mouse_release_stage(self,event,add=True):
		self.is_m1_down	= False
		self.is_m3_down	= False
		self.render_frames(self.changes_draw)
		self.render_editor(self.changes_draw)
		self.render_preview(self.changes_draw)
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
			x		= self.stage_editor.canvasx(event.x)-left
			y		= self.stage_editor.canvasy(event.y)-top
			x		= int(np.floor(x/size))
			y		= int(np.floor(y/size))
			self.draw(x,y,self.is_m1_down)
		
	### DRAWING
	def draw(self,x,y,add=True):
		self.changes_draw = True
		_x,_y	= str(x),str(y)
		color	= self.animation["stage"]["palette"][self.color]
		layer	= self.animation["timeline"][self.animation["properties"]["selected_layer"]]
		select	= min(self.animation["properties"]["selected_frame"],len(layer["frames"])-1)
		if layer["frames"][select]["type"]=="link":
			select	= layer["frames"][select]["data"]
		frame	= layer["frames"][select]["data"]
		if self.tool==0:
			if add:
				if _x not in frame:
					frame[_x]	= {}
				frame[_x][_y]	= color
				self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["type"] = "matrix"
				self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["data"] = frame
				self.render_helper(x,y,color)
			else:
				if _x in frame:
					if _y in frame[_x]:
						del frame[_x][_y]
					if not frame[_x]:
						del frame[_x]
				if not frame:
					self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["type"] = "empty"
				self.animation["timeline"][self.animation["properties"]["selected_layer"]]["frames"][select]["data"] = frame
				self.render_helper(x,y,self.animation["stage"]["background-color"])

	### OTHER 
	
	def on_resize(self,event):
		self.root.update()
		update	= False
		if self.width!=self.root.winfo_width():
			self.width	= self.root.winfo_width()
			update		= True
		if self.height!=self.root.winfo_height():
			self.height	= self.root.winfo_height()
			update		= True
		if self.root.wm_state()!="normal":
			update=True
		if update:
			self.render(True)
		
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
		self.log(message+":"+str(e))
		try:
			raise e
		except:
			pass
		return
	
	def log(self,message=""):
		print(time.strftime("%H:%M:%S")+" > "+message,flush=True)
	
	def async(self,func):
		threading.Thread(target=lambda:self.loop.run_until_complete(func)).start()
	
	async def async_test(self,event):
		while True:
			await asyncio.sleep(1)
			print(event)

if __name__ == "__main__":
	print("Ha ezt az ablakot bezárod, az alkalmazás is bezáródik!")
	app		= Application(master=tk.Tk())
	app.mainloop()
	print("Szerkesztő ablak bezárva.")