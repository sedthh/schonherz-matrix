# -*- coding: UTF-8 -*-

import sys, os
import json
import webbrowser

import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter import messagebox

### GLOBALS

TITLE	= "Mátrix Animációt Szépen Szerkesztő Alkalmazás"
VERSION	= "0.1 alfa teszt verzió"
URL		= "https://github.com/sedthh/schonherz-matrix"

### 

class Application(tk.Frame):
	def __init__(self, master=None):
		self.root			= master
		super().__init__(self.root)
		self.root.title(TITLE+" ("+VERSION+")")
		self.root.minsize(800,600)
		self.root.protocol("WM_DELETE_WINDOW", self.file_quit)
		self.pack()
		self.create_menu()
		#self.create_layout()
		
		self.changes_made	= False
		self.is_playing		= False
		self.file			= ""
		self.stage			= {
			
		}
		
	def create_menu(self):		
		self.menubar		= tk.Menu(self)
		
		self.file_menu		= tk.Menu(self.menubar, tearoff=0)
		self.file_menu.add_command(label = "Új", command = self.file_new, underline=1,accelerator="Ctrl+N")
		self.bind_all("<Control-n>", self.file_new)
		self.file_menu.add_command(label = "Megnyitás", command = self.file_open, underline=1,accelerator="Ctrl+O")
		self.bind_all("<Control-o>", self.file_open)
		self.file_menu.add_command(label = "Mentés", command = self.file_save, underline=1,accelerator="Ctrl+S")
		self.bind_all("<Control-s>", self.file_save)
		self.file_menu.add_command(label = "Mentés másként", command = self.file_save_as, underline=1,accelerator="Ctrl+Shift+S")
		self.bind_all("<Control-S>", self.file_save_as)
		self.file_menu.add_separator()
		self.file_menu.add_command(label = "Importálás", command = self.file_import, underline=1,accelerator="Ctrl+I", state=tk.DISABLED)
		self.bind_all("<Control-i>", self.file_import)
		self.file_menu.add_command(label = "Exportálás", command = self.file_export, underline=1,accelerator="Ctrl+Enter")
		self.bind_all("<Control-Return>", self.file_export)
		self.file_menu.add_separator()
		self.file_menu.add_command(label = "Kilépés", command = self.file_quit, underline=1,accelerator="Ctrl+Q")
		self.bind_all("<Control-q>", self.file_quit)
		
		self.edit_menu		= tk.Menu(self.menubar, tearoff=0)
		self.edit_menu.add_command(label = "Visszavonás", command = self.edit_undo, underline=1,accelerator="Ctrl+Z", state=tk.DISABLED)
		self.bind_all("<Control-z>", self.edit_undo)
		self.edit_menu.add_separator()
		self.edit_menu.add_command(label = "Képkocka kivágása", command = self.edit_cut, underline=1,accelerator="Ctrl+X")
		self.bind_all("<Control-x>", self.edit_cut)
		self.edit_menu.add_command(label = "Képkocka másolása", command = self.edit_copy, underline=1,accelerator="Ctrl+C")
		self.bind_all("<Control-c>", self.edit_copy)
		self.edit_menu.add_command(label = "Képkocka felülírása", command = self.edit_paste, underline=1,accelerator="Ctrl+V")
		self.bind_all("<Control-v>", self.edit_paste)
		self.edit_menu.add_command(label = "Képkocka beszúrása", command = self.edit_insert, underline=1,accelerator="Ctrl+B")
		self.bind_all("<Control-b>", self.edit_insert)
		self.edit_menu.add_separator()
		self.edit_menu.add_command(label = "Képkocka törlése", command = self.edit_delete, underline=1,accelerator="Del")
		self.bind_all("<Delete>", self.edit_delete)
		self.edit_menu.add_command(label = "Képkocka tartalmának letörlése", command = self.edit_empty, underline=1,accelerator="Ctrl+R")
		self.bind_all("<Control-r>", self.edit_empty)
		self.edit_menu.add_command(label = "Képkocka duplikálása", command = self.edit_duplicate, underline=1,accelerator="Ctrl+D")
		self.bind_all("<Control-d>", self.edit_duplicate)
		self.edit_menu.add_command(label = "Üres képkocka beszúrása", command = self.edit_insert_empty, underline=1,accelerator="Ctrl+E")
		self.bind_all("<Control-e>", self.edit_insert_empty)
		self.edit_menu.add_separator()
		self.edit_menu.add_command(label = "Képkocka hosszabbítása", command = self.edit_extend, underline=1,accelerator="+")
		self.bind_all("<Key-plus>", self.edit_extend)
		self.edit_menu.add_command(label = "Képkocka rövidítése", command = self.edit_reduce, underline=1,accelerator="-")
		self.bind_all("<Key-minus>", self.edit_reduce)
		
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
		self.bind_all("<Up>", self.transform_move_up)
		self.transform_menu.add_command(label = "Elmozgatás lefelé", command = self.transform_move_down,underline=1,accelerator="Down")
		self.bind_all("<Down>", self.transform_move_down)
		self.transform_menu.add_command(label = "Elmozgatás balra", command = self.transform_move_left,underline=1,accelerator="Left")
		self.bind_all("<Left>", self.transform_move_left)
		self.transform_menu.add_command(label = "Elmozgatás jobbra", command = self.transform_move_right,underline=1,accelerator="Right")
		self.bind_all("<Right>", self.transform_move_right)
		
		self.playback_menu	= tk.Menu(self.menubar, tearoff=0)
		self.playback_menu.add_command(label = "Lejátszás", command = self.playback_play, underline=1,accelerator="Space")
		self.bind_all("<space>", self.playback_play)
		self.playback_menu.add_command(label = "Elejére", command = self.playback_rewind, underline=1,accelerator="Home")
		self.bind_all("<Home>", self.playback_rewind)
		self.playback_menu.add_command(label = "Végére", command = self.playback_end, underline=1,accelerator="End")
		self.bind_all("<End>", self.playback_end)
		self.playback_menu.add_command(label = "Egy kockát vissza", command = self.playback_back, underline=1,accelerator="PgDn")
		self.bind_all("<Next>", self.playback_back)
		self.playback_menu.add_command(label = "Egy kockát előre", command = self.playback_next, underline=1,accelerator="PgUp")
		self.bind_all("<Prior>", self.playback_next)

		self.help_menu		= tk.Menu(self.menubar, tearoff=0)
		self.help_menu.add_command(label = "Névjegy", command = self.other_about,underline=1,accelerator="Ctrl+H")
		self.bind_all("<Control-h>", self.other_about)
		
		self.menubar.add_cascade(label = "Fájl", menu=self.file_menu)
		self.menubar.add_cascade(label = "Szerkesztés", menu=self.edit_menu)
		self.menubar.add_cascade(label = "Tulajdonságok", menu = self.properties_menu)
		self.menubar.add_cascade(label = "Transzformáció", menu = self.transform_menu)
		self.menubar.add_cascade(label = "Lejátszó", menu = self.playback_menu)
		self.menubar.add_cascade(label = "Segítség", menu = self.help_menu)
		self.root.config(menu=self.menubar)
				
	'''
		messagebox.showinfo("test" , "hoi, dit is een test als je dit leest is het gelukt")
		messagebox.showerror("Error", "Error message")
		messagebox.showwarning("Warning","Warning message")
		messagebox.askyesno("hurr","durr")
	'''
	'''
	def create_widgets(self):
		self.hi_there 	= tk.Button(self)
		self.hi_there["text"] = "Hello World\n(click me)"
		self.hi_there["command"] = self.say_hi
		self.hi_there.pack(side="top")
		self.quit = tk.Button(self, text="QUIT", fg="red",command=self.quit)
		self.quit.pack(side="bottom")
	'''
	
	### FUNCTIONS
	
	def file_new(self,event=None):
		if self.changes_made:
			response			= messagebox.askyesnocancel(title="Új animáció létrehozása", message="Új animáció létrehozása előtt szeretnéd menteni a változtatásokat?", default=messagebox.YES)
			if response:
				self.file_save()
			elif response is None:
				return
		self.file			= ""
		print("New")
		
	def file_open(self,event=None):
		file				= askopenfilename(initialdir="C:/Documents/",filetypes =(("Szerkesztő fájl", "*.json"),),title = "Megnyitás")
		if file:
			self.file			= file
			print(self.file)
		
	def file_save(self,event=None):
		if self.file:
			print("Save")
		else:
			self.file_save_as(event)
	
	def file_save_as(self,event=None):
		file				= asksaveasfilename(defaultextension=".json")
		if file:
			self.file			= file
			print(self.file)
	
	def file_export(self,event=None):
		print("Export")
		
	def file_import(self,event=None):
		print("Export")
	
	def file_quit(self,event=None):
		if self.changes_made:
			response			= messagebox.askyesnocancel(title="Kilépés a szerkesztőből", message="Kilépés előtt szeretnéd menteni a változtatásokat?", default=messagebox.YES)
			if response:
				self.file_save()
			elif response is None:
				return
			
		self.root.destroy()
		#sys.exit(0)
	
	def edit_undo(self,event=None):
		print("Undo/Redo")
		
	def edit_cut(self,event=None):
		print("Cut")
	
	def edit_copy(self,event=None):
		print("Copy")
	
	def edit_paste(self,event=None):
		print("Paste")
		
	def edit_insert(self,event=None):
		print("Insert")
	
	def edit_delete(self,event=None):
		print("Delete")	
	
	def edit_empty(self,event=None):
		print("Empty")	
		
	def edit_duplicate(self,event=None):
		print("Duplicate")	

	def edit_insert_empty(self,event=None):
		print("Insert empty")	
		
	def edit_extend(self,event=None):
		print("Extend")
		
	def edit_reduce(self,event=None):
		print("Reduce")
	
	def properties_animation(self,event=None):
		print("Animation properties")
		
	def properties_stage(self,event=None):
		print("Stage properties")
		
	def properties_music(self,event=None):
		print("Music properties")
	
	def transform_rotate_right(self,event=None):
		print("Transform rotate right")
	
	def transform_rotate_left(self,event=None):
		print("Transform rotate left")
		
	def transform_flip_horizontal(self,event=None):
		print("Transform flip horizontal")
	
	def transform_flip_vertical(self,event=None):
		print("Transform flip vertical")	
			
	def transform_move_up(self,event=None):
		print("Transform move up")	
	
	def transform_move_down(self,event=None):
		print("Transform move down")	
		
	def transform_move_left(self,event=None):
		print("Transform move left")	
		
	def transform_move_right(self,event=None):
		print("Transform move right")	

	def playback_play(self,event=None):
		print("Play")
		
	def playback_rewind(self,event=None):
		print("Rewind")
	
	def playback_end(self,event=None):
		print("End")
		
	def playback_back(self,event=None):
		print("Back")
	
	def playback_next(self,event=None):
		print("Next")
	
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
    
if __name__ == "__main__":
	app		= Application(master=tk.Tk())
	app.mainloop()