# -*- coding: UTF-8 -*-

import sys, os
import json
import webbrowser
import time

import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox
from tkinter.colorchooser import askcolor

### GLOBALS

TITLE		= "QPY - Animáció Szerkesztő"
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
		"stage"				: "#d0d0d0",
		"layer"				: "#dddddd",
		"layer-active"		: "#bbccdd",
		"layer-color"		: "#222222",
	}
}

### 

class Application(tk.Frame):
	def __init__(self, master=None):
		self.root			= master
		super().__init__(self.root)
		self.version		= [int(v) for v in VERSION.split()[0].split(".")]
		
		self.changes_made	= False
		self.is_playing		= False
		self.is_loading		= False
		self.file			= ""
		self.animation		= self.new_animation() # animation data
					
		# generate editor window
		self.root.title(TITLE+" ("+VERSION+")")
		self.root.minsize(800,600)
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
		try:
			self.render_layers()
			self.render_frames()
		except Exception as e:
			self.error("Sikertelen az elemek kirajzolása!",e)
		
		self.root.bind("<Configure>", self.on_resize)
	
	def new_animation(self):
		data	= {
			"version"			: self.version,
			"stage"				: PROFILES["SCH"],
			"properties"		: {
				"title"				: "Ischmeretlen",
				"team"				: "Schapatnév",
				"year"				: time.strftime("%Y"),
				"music"				: "",
				"selected_layer"	: 0,
				"selected_frame"	: 0
			},
			"timeline"			: []
		}
		# TODO: allow the manual addition of multiple layers later
		for layer in ["Felső réteg","Középső réteg","Hátsó réteg"]:
			frames			= []
			for w in range(data["stage"]["width"]):
				line			= []
				for h in range(data["stage"]["height"]):
					line.append(0)
				frames.append(line)
			data["timeline"].append({
				"name"				: layer,
				"type"				: "normal",
				"visibility"		: True,
				"render"			: True,
				"frames"			: [{
					"type"				: "empty",
					"data"				: frames
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
		self.edit_menu.add_command(label = "Üres képkocka beszúrása", command = self.edit_insert_empty, underline=1,accelerator="Ctrl+E")
		self.root.bind_all("<Control-e>", self.edit_insert_empty)
		self.edit_menu.add_separator()
		self.edit_menu.add_command(label = "Képkocka hosszabbítása", command = self.edit_extend, underline=1,accelerator="+")
		self.root.bind_all("<Key-plus>", self.edit_extend)
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
		self.help_menu.add_command(label = "Névjegy", command = self.other_about,underline=1,accelerator="Ctrl+H")
		self.root.bind_all("<Control-h>", self.other_about)
		
		self.menubar.add_cascade(label = "Fájl", menu=self.file_menu)
		self.menubar.add_cascade(label = "Szerkesztés", menu=self.edit_menu)
		self.menubar.add_cascade(label = "Tulajdonságok", menu = self.properties_menu)
		self.menubar.add_cascade(label = "Transzformáció", menu = self.transform_menu)
		self.menubar.add_cascade(label = "Lejátszó", menu = self.playback_menu)
		self.menubar.add_cascade(label = "Segítség", menu = self.help_menu)
		self.root.config(menu=self.menubar)
		
	def create_timeline(self):
		self.timeline 		= tk.Frame(self.root, bg=LAYOUT["DEFAULT"]["root"], bd=0, highlightthickness=0)
		tk.Grid.columnconfigure(self.timeline, 1, weight=1)
		self.timeline_layers= tk.Canvas(self.timeline, width=200, height=180, bg=LAYOUT["DEFAULT"]["root"], bd=0, highlightthickness=0)
		self.timeline_layers.grid(row=0,column=0,sticky="w")
		self.timeline_frames= tk.Canvas(self.timeline,height=180)
		self.timeline_frames.grid(row=0,column=1,sticky="wen")
		self.timeline_scrollbar_h= tk.Scrollbar(self.timeline,orient='horizontal',command=self.timeline_frames.xview)
		self.timeline_scrollbar_h.grid(row=1,column=1,sticky="wen")
		self.timeline.pack(fill=tk.X)
		self.timeline_layers.bind("<Button-1>",self.mouse_click_layers)
		self.timeline_frames.bind("<Button-1>",self.mouse_click_frames)
		self.timeline_layers.bind("<Button-3>",self.mouse_popup_layers)
		self.timeline_frames.bind("<Button-3>",self.mouse_popup_frames)
		self.timeline_layers.bind('<Enter>',self.mouse_to_hand)
		self.timeline_layers.bind('<Leave>',self.mouse_to_default)

	def create_stage(self):
		self.stage 		= tk.Frame(self.root, bg=LAYOUT["DEFAULT"]["stage"], bd=0)
		tk.Grid.columnconfigure(self.stage, 1, weight=1)
		tk.Grid.rowconfigure(self.stage, 0, weight=1)
		self.stage_tools= tk.Frame(self.stage,width=100, bg=LAYOUT["DEFAULT"]["stage"], bd=0, highlightthickness=0)
		self.stage_tools.grid(row=0,column=0,sticky="nswe")
		self.stage_tools_test=tk.Button(self.stage_tools,width=2,height=1,text="test",bg="red")
		self.stage_tools_test.grid(row=0,column=0,sticky="w")
		self.stage_tools_test2=tk.Button(self.stage_tools,width=3,height=1,text="test2",bg="green")
		self.stage_tools_test2.grid(row=1,column=1,sticky="w")

		
		self.stage_editor= tk.Canvas(self.stage, bg=self.animation["stage"]["border-color"],bd=0,highlightthickness=0)
		self.stage_editor.grid(row=0,column=1,sticky="nswe")
		self.stage_scrollbar_h= tk.Scrollbar(self.stage,orient='vertical',command=self.stage_editor.xview)
		self.stage_scrollbar_h.grid(row=0,column=2,sticky="ns")
		self.stage_preview= tk.Canvas(self.stage,width=300, bg="#000000",bd=0,highlightthickness=0)
		self.stage_preview.grid(row=0,column=3,sticky="nswe")
		self.stage_scrollbar_w= tk.Scrollbar(self.stage,orient='horizontal',command=self.stage_editor.xview)
		self.stage_scrollbar_w.grid(row=1,column=1,sticky="we")	
		self.stage.pack(fill=tk.BOTH,expand=True)
		
		self.stage_editor.bind('<Enter>',self.mouse_to_hand)
		self.stage_preview.bind('<Enter>',self.mouse_to_hand)
		self.stage_editor.bind('<Leave>',self.mouse_to_default)
		self.stage_preview.bind('<Leave>',self.mouse_to_default)
	
	### RENDER ELEMENTS
	def render_layers(self):
		offset 			= 30
		height 			= 49
		width			= 199
		self.timeline_layers.delete("all")
		for i, layer in enumerate(self.animation["timeline"]):
			color	= LAYOUT["DEFAULT"]["layer"]
			if self.animation["properties"]["selected_layer"]==i:
				color	= LAYOUT["DEFAULT"]["layer-active"]
			self.timeline_layers.create_rectangle(0, offset+i*height, width, offset+(i+1)*height, fill=color, outline="#444444")
			self.timeline_layers.create_line(0, offset+i*height, width, offset+i*height, fill="#ffffff")
			self.timeline_layers.create_line(0, offset+i*height, 0, offset+(i+1)*height, fill="#ffffff")
			self.timeline_layers.create_text(10,offset+i*height+25,fill=LAYOUT["DEFAULT"]["layer-color"],font="system 10", text=layer["name"],anchor="w")
	
	def render_frames(self):
		offset 			= 30
		self.timeline_frames.delete("all")
		self.timeline_frames.create_rectangle(0, 0, self.root.winfo_width(), offset, fill="red", outline=LAYOUT["DEFAULT"]["root"])
		
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
		self.animation		= self.new_animation() 
		self.log("New")
		
	def file_open(self,event=None):
		self.playback_pause()
		file				= askopenfilename(initialdir="C:/Documents/",filetypes =(("Szerkesztő fájl", "*.qpy"),),title = "Megnyitás")
		if file:
			self.file			= file
			self.changes_made	= False
			#messagebox.showwarning("Warning","Warning message")
			self.log(self.file)
		
	def file_save(self,event=None):
		if self.file:
			self.log("Save")
			self.changes_made	= False
		else:
			self.file_save_as(event)
	
	def file_save_as(self,event=None):
		self.playback_pause()
		file				= asksaveasfilename(defaultextension=".qpy")
		if file:
			self.file			= file
			self.changes_made	= False
			self.log(self.file)
	
	def file_export(self,event=None):
		self.playback_pause()
		file				= asksaveasfilename(defaultextension=".qp4")
		if file:
			messagebox.showinfo("Exportálás sikeres" , "Az animáció konvertálása sikeres volt.")
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
	
	def mouse_to_default(self, event):
		self.cursor("")
	
	def mouse_click_layers(self,event):
		self.log("Click")
		
	def mouse_click_frames(self,event):
		self.log("Click")
	
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
	
	### OTHER 
	
	def on_resize(self,event):
		return
	
	def loading(self,update=True):
		self.is_loading		= update
		if self.is_loading:
			self.root.config(cursor="wait")
		else:
			self.root.config(cursor="")
			
	def error(self,message="Ismeretlen hiba",e=None):					
		messagebox.showerror(message, str(e))
		self.log(message+":"+str(e))
		if e:
			raise e
	
	def log(self,message=""):
		print(time.strftime("%H:%M:%S")+" > "+message)
	
if __name__ == "__main__":
	print("Ha ezt az ablakot bezárod, az alkalmazás is bezáródik!")
	app		= Application(master=tk.Tk())
	app.mainloop()
	print("Szerkesztő ablak bezárva.")