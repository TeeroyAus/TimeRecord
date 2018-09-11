#-------------------------------------------------------------------------------
# Name:        Time Record
# Purpose:     Journal for time recording
#
# Author:      Troy Scott
#
# Created:     10/07/2018
# Copyright:   (c) teero_000 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import Tkinter as tk
import tkMessageBox
import tkFileDialog
import json
import ttk
import itertools
from datetime import datetime
from os.path import splitext, exists, join
from PIL import Image, ImageTk

class Settings(object):
    def __init__(self, caller=None): # get rid of caller?
        super(Settings, self).__init__()
        #read JSON file for defaults?
        try:
            with open("settings.json") as read_file:
                mysettings = json.load(read_file)
                self.interval = int(mysettings['interval'])*1000*60
                self.filename = mysettings['filename']
                self.settingsfile = True
                self.default_to_last = True
        except IOError:
            print "File not found"
            self.interval = 1 * 1000 * 60
            self.filename = ""
            self.settingsfile = False

class SettingsWindow(tk.Toplevel):
    '''This object holds the application level settings for the data file
    filename and the interval for automatic log requests.
    '''
    global settings
    def __init__(self, parent, filename=None, interval=None):
        #super(Settings, self).__init__(self,parent)#(*args, **kwargs)
        tk.Toplevel.__init__(self, parent)
        self.update_settings()

    def update_settings(self):
        self.minsize(300, 200)
        self.grid()
        #Filename Label
        filename_label = tk.Label(self, text="Log Filename:")
        filename_label.grid(row=1, column=0, sticky=tk.W)
        filename_label.bind("<Button-1>", self.open_file_dialog)
        #Filename Data
        filename_data_label = tk.Label(self, text=settings.filename)
        filename_data_label.grid(row=1, column=1, sticky=tk.W)
        #Interval Label
        interval_label = tk.Label(self, text="Timer Interval (minutes):")
        interval_label.grid(row=2, column=0, sticky=tk.W)
        #Interval Entry
        self.interval = tk.StringVar()
        self.interval.set(str(settings.interval/1000/60))
        interval_entry = tk.Entry(self, textvariable=self.interval)
        interval_entry.grid(row=2, column=1)

        #Button clear
        button_clear = tk.Button(self, text="Clear")
        button_clear.grid(row=4, column=0)
        #Button Save
        button_save = tk.Button(self, text="Save and Exit", command=self.save)
        button_save.grid(row=4, column=1)

    def save(self):
        settings.interval = int(self.interval.get())*1000*60
        self.open_file_dialog()
        self.destroy()

    def open_file_dialog(self, *args, **kwargs):
        print "I've Run"
        if settings.settingsfile == False:
            filename = tkFileDialog.asksaveasfilename(filetypes= \
                [("JSON files", ".json")])
            file_name, extension = splitext(filename)
            if extension != ".json":
                filename = file_name+".json"
                print "altered"
        else:
            filename = "settings.json"
        mysettings = {"filename":filename, "interval":self.interval.get()}
        with open(filename, 'w') as file:
            json.dump(mysettings, file)

class App(tk.Frame):

    global settings

    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        #Comment out next line for testing only; easier quitting the app
        #parent.protocol("WM_DELETE_WINDOW", self.on_delete)

        #image
        image = Image.open("time-1020373_960_720.jpg")
        photo = ImageTk.PhotoImage(image)
        image_canvas = tk.Canvas(self, width=720, height=720)
        image_canvas.grid(column=0, row=0, rowspan=8, columnspan=8)
        image_canvas.create_image(0, 0, image=photo, anchor=tk.NW)
        # String literal anchors are in lower case.  Can also use  tk.NW
        self.canvas_image = photo # keep a reference to prevent image garbage collection
        # if you don't keep an image reference then the image is empty after the class is
        # instantiated.
        self.grid_rowconfigure(0, weight=0)

        #Start Button
        # this starts a threaded timer to launch a new log window at predetermined intervals
        self.button_start = tk.Button(self, text="START", fg="green", \
            font=("helvetica", 10, 'bold'), command=self.timer_start) #replace quit
        self.button_start.grid(column=0, row=7)
        # Can use sticky in the grid e.g. sticky=tk.N
        self.timer_repeat = False

        #Stop Button
        #this kills the next threaded timer set.
        #ask whether a final time log is required?
        self.button_stop = tk.Button(self, fg="red", font=("helvetica", 10, 'bold'), \
            text="STOP", command=self.timer_stop)
        self.button_stop.grid(column=2, row=7)
        self.button_stop['state'] = tk.DISABLED

        # Manual Entry
        #this launches a manual entry log window independent of any set by the timer
        button_manual = tk.Button(self, fg="orange", font=("helvetica", 10, 'bold'), \
            text="LOG", command=self.manual_entry)
        button_manual.grid(column=1, row=7)

        #Quit Button
        #ask whether a final time log is required?
        button_quit = tk.Button(self, text="QUIT", font=("helvetica", 10, 'bold'), \
            command=self.on_delete)
        button_quit.grid(column=3, row=7)

        #menu
        menubar = tk.Menu(self.master)

        #File menu
        #Open, Save, Save As, Options, Quit
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open log...", command=self.open_file)
        filemenu.add_command(label="Close log...", command=self.close_file)
        filemenu.add_command(label="Save", command=self.save_log)
        filemenu.add_command(label="Save As...", command=self.save_as)
        filemenu.add_separator()
        filemenu.add_command(label="Options", command=self.app_settings)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.on_delete)
        menubar.add_cascade(label="File", menu=filemenu)

        #View Menu
        viewmenu = tk.Menu(menubar, tearoff=0)
        viewmenu.add_command(label="Active Log", command=log_open)
        viewmenu.add_command(label="Past Log File", command=log_open)
        menubar.add_cascade(label="View", menu=viewmenu)

        #display the menu
        self.master.config(menu=menubar)
        self.grid()

        # Add Icon toolbar row???

    def timer_start(self):
        '''Set timer start and start repeat log windows.
        '''
        self.button_stop['state'] = tk.NORMAL
        self.button_start['state'] = tk.DISABLED
        self.timer_time = settings.interval
        self.timer_repeat = True
        self.timer_repeat_function()

    def timer_repeat_function(self):
        '''Sets the next timer delayed log window.
        '''
        self.next = self.after(self.timer_time, self.manual_entry)

    def timer_stop(self):
        '''Cancel any future timer and set log state to accept a new timer
        or manual log entries.
        '''
        self.button_stop['state'] = tk.DISABLED
        self.button_start['state'] = tk.NORMAL
        self.timer_repeat = False
        self.after_cancel(self.next)

    def manual_entry(self):
        '''Log entry window.
        Even though it's called a manual entry this is wahat is used to
        set future timer log entries.
        '''
        if self.timer_repeat:
            self.timer_repeat_function()
        time_entry = TimeRecordWindow(self, editable=True)

    def app_settings(self):
        if str(self.button_stop['state']) == "normal":
            msg = "The settings can't be changed while a timer is running."+ \
                "\nDo you want to cancel the timer?"
            if tkMessageBox.askyesno("Settings", msg):
                self.timer_stop()
                self.app_settings()
        else:
            App.settings = SettingsWindow(self)

    def save_as(self):
        ''' Get save as filename and write out log record dictionary as
        a JSON file.
        '''
        file_name = self.get_file()
        if not bool(file_name):
            return
        with open(file_name, 'w') as outfile:
            write_string = encode_log(TimeRecord.TimeRecords)
            json.dump(write_string, outfile)

    def get_file(self):
        '''get the file name for storing the log entries.
        This is a JSON file.
        '''
        filename = tkFileDialog.asksaveasfilename(defaultextension='.json', \
                filetypes=[("JSON files", ".json")])
        if not bool(filename):
            return
        file_name, extension = splitext(filename)
        # print file_name, extension
        if not bool(extension):
            extension = ".json"
        filename = file_name + extension
        # print "filename = ", filename
        return filename

    def open_file(self):
        ''' The file opened becomes the active log file.
        '''
        # if the current log has any entries then check whether to save it or merge
        # with the log to be opened.
        if TimeRecord.TimeRecords:
            answer = tkMessageBox.askyesno('Open Log File', \
'The current log has entries.  Do you want this data to be \
appended to the opened file?')
            if answer:
                #open file and append data
                pass
            else:
                self.close_file()

        filename = tkFileDialog.askopenfilename( \
                filetypes=[("JSON files", ".json")])
        tkMessageBox.askyesno('Open Log File', \
            'This file becomes the current Log and new data is appended to it.')
        time_entry = TimeRecordWindow(self)

    def close_file(self):
        if TimeRecord.TimeRecords:
            answer = tkMessageBox.askyesno('Open Log File', \
            'The current log has entries.  Do you want to save this data before closing the file?')
            if answer:
                #save the file
                pass
            else:
                TimeRecord.TimeRecords.clear()
    def on_delete(self):
        if tkMessageBox.askokcancel("Quit", "Do you really wish to quit?"):
            self.master.quit()

    def save_log(self):
        '''Save the active log dictionary to a JSON file.'''
        with open('active_log.json', 'w') as outfile:
            write_string = encode_log(TimeRecord.TimeRecords)
            json.dump(write_string, outfile)

class TimeRecordWindow(tk.Toplevel):
    global settings

    def __init__(self, parent, **kwargs):
        COLUMN_PADDING = 5
        ROW_PADDING = 50
        tk.Toplevel.__init__(self, parent)
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        self.minsize(400, 300)
        self.maxsize(600, self.winfo_screenheight())
        self.kwargs = kwargs
        print "my keywords are: ", self.kwargs

        #set static labels and entry / text boxes

        #log_label = tk.Label(self, text="Log Details", anchor=tk.W)
        #log_label.grid(row=6, column=0, sticky=tk.EW)
        #date
        date_label = tk.Label(self, text="Date:", anchor=tk.W)
        date_label.grid(row=1, column=0, sticky=tk.EW)

        #time
        time_label = tk.Label(self, text="Time:", anchor=tk.W)
        time_label.grid(row=2, column=0, sticky=tk.EW)

        #project
        #Label
        project_label = tk.Label(self, text="Project:", anchor=tk.W)
        project_label.grid(row=3, column=0, sticky=tk.W, pady=COLUMN_PADDING)
        #Entry
        #How about a dropdown for all projects in the last week?
        self.project_entry = tk.Entry(self) #, textvariable=project)
        self.project_entry.focus()
        self.project_entry.bind("<Return>", lambda e: self.job_entry.focus())
        self.project_entry.grid(row=3, column=1, columnspan=2, sticky=tk.EW, \
            padx=(0, ROW_PADDING))

        #job
        #Label
        job_label = tk.Label(self, text="Job:", anchor=tk.W)
        job_label.grid(row=4, column=0, sticky=tk.W)
        #Entry? Single Line Entry Widget
        self.job_entry = tk.Entry(self) #, textvariable=job)
        self.job_entry.bind("<Return>", lambda e: self.note_text.focus_set())
        self.job_entry.grid(row=4, column=1, columnspan=2, sticky=tk.EW, \
            pady=COLUMN_PADDING, padx=(0, ROW_PADDING))

        #Note
        #Label
        note_label = tk.Label(self, text="Note:", anchor=tk.W)
        note_label.grid(row=5, column=0, sticky=tk.NW)
        #Text (entry not used as it is single line only)
        self.note_text = tk.Text(self)
        self.note_text.grid(row=5, column=1, columnspan=2, sticky=tk.NSEW, \
            pady=COLUMN_PADDING, padx=(0, ROW_PADDING))

        #Clear Button
        clear_button = tk.Button(self, text="Clear", command=self.clear_entries)
        clear_button.grid(row=7, column=2, sticky=tk.EW, \
            padx=(0, ROW_PADDING), pady=COLUMN_PADDING)

        # Quit Button
        quit_button = tk.Button(self, text="Cancel", command=self.destroy)
        quit_button.grid(row=8, column=2, sticky=tk.EW, \
            padx=(0, ROW_PADDING), pady=COLUMN_PADDING)

        #Save Button
        save_button = tk.Button(self, text="Save and Exit", command=self.on_save)
        save_button.grid(row=6, column=2, sticky=tk.EW, \
            padx=(0, ROW_PADDING), pady=COLUMN_PADDING)

        # Check if editable = False and remove save and clear options
        if not self.kwargs.pop('editable', False):
            clear_button['state'] = tk.DISABLED
            save_button['state'] = tk.DISABLED

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=0)
        self.rowconfigure(4, weight=0)
        self.rowconfigure(5, weight=1)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

        self.log_time = datetime.now()
        self.time = format_time(self.log_time)

        if  self.kwargs:
            self.log_time_reference = self.kwargs['log_time_reference']
            self.time = self.kwargs['time']
            self.log_time = self.master.reference[self.log_time_reference]
            self.project_entry.insert(0, self.kwargs['project'])
            self.job_entry.insert(0, self.kwargs['job'])
            self.note_text.insert("1.0", self.kwargs['note'])
            #self.show_log_details()

        elif settings.default_to_last:
            print"Fill me in!"
            # If a log exists and default_to_last==True
            if TimeRecord.TimeRecords and settings.default_to_last:
                most_recent = None
                for k in TimeRecord.TimeRecords.keys():
                    if most_recent == None:
                        most_recent = k
                    elif k > most_recent:
                        most_recent = k
                self.project_entry.insert(0, TimeRecord.TimeRecords[most_recent][0])
                self.job_entry.insert(0, TimeRecord.TimeRecords[most_recent][1])
                #self.show_log_details()

        #set dynamic text
        log_date_label = tk.Label(self, text=format_date(self.log_time) \
            , anchor=tk.W)
        log_date_label.grid(row=1, column=1, sticky=tk.EW)

        log_time_label = tk.Label(self, text=self.time, anchor=tk.W)
        log_time_label.grid(row=2, column=1, sticky=tk.EW)

    def show_log_details(self):
        ''' Show Log Details
            Will not display when a new log is created.
        '''
        log_label = tk.Label(self, text="Log Details", anchor=tk.W)
        log_label.grid(row=6, column=0, sticky=tk.EW)
        time_label = tk.Label(self, text="Date:", anchor=tk.W)
        time_label.grid(row=7, column=0, sticky=tk.EW)
        log_time_label = tk.Label(self, text=format_date(self.log_time) \
            , anchor=tk.W)
        log_time_label.grid(row=7, column=1, sticky=tk.EW)

        time_label = tk.Label(self, text="Time:", anchor=tk.W)
        time_label.grid(row=8, column=0, sticky=tk.EW)
        log_time_label = tk.Label(self, text=self.time, anchor=tk.W)
        log_time_label.grid(row=8, column=1, sticky=tk.EW)

    def on_save(self):
        if self.kwargs:
            TimeRecord.TimeRecords[self.log_time] = list(self.get_text())
            # Update the treeview in the parent
            tree_item = self.kwargs['tree_item']
            values_list = list(itertools.chain(self.log_time_reference, \
                [self.time], TimeRecord.TimeRecords[self.log_time]))
            self.master.tree.item(tree_item, values=values_list)
        else:
            x = TimeRecord(self.get_text())
        self.destroy()

    def clear_entries(self):
        self.project_entry.delete(0, "end")
        self.job_entry.delete(0, "end")
        self.note_text.delete("1.0", "end")

    def on_quit(self):
        if tkMessageBox.askyesno("Quit", "Do you want to save the record prior to exit?"):
            self.on_save()
        else:
            self.destroy()
    def get_text(self):
        return (self.project_entry.get(), self.job_entry.get(), \
            self.note_text.get("1.0", "end-1c"), self.log_time)

def format_date(log_date):
    format_string = '%A %d/%m/%Y'
    return log_date.strftime(format_string)

def format_time(log_date):
    format_string = '%H:%M'
    return log_date.strftime(format_string)


class TimeRecord(object):
    TimeRecords = {}

    def __init__(self, (project, job, note, log_time)):
        TimeRecord.TimeRecords[log_time] = [project, job, note]
        #print (TimeRecord.TimeRecords)
##        with open("data_file.json", "w") as write_file:
##            json.dump(encode_log(TimeRecord.TimeRecords), write_file)

def import_log(*ignore):
    global settings

    if settings.filename == "" or settings.filename == None:
        print "No Log File has been set"
    else:
        print settings.filename

def encode_log(log_dict):
    '''return json string from dictionary'''
    #dumps to create a string json object first then dump to write it?
    print type(log_dict), "now"
    str_log_dict = {str(key):value for (key, value) in log_dict.items()}

    return json.dumps(str_log_dict)

def decode_log(log_str):
    '''return dictionary from json string'''
    str_log_dict = json.loads(log_str)
    log_dict = {datetime.strptime(key, '%Y-%m-%d %H:%M:%S.%f'):value for \
        (key, value) in str_log_dict.items()}
    return log_dict

def open_log_file(*ignore):
    '''
    This function opens an existing log file and passes the contents
    to a LogViewer window.
    '''
    filename = "data_file.json"
    print exists(filename) #os.path.exists
    try:
        with open(filename, 'r') as file:
            log_dict = json.load(file)
            log_dict = decode_log(log_dict)
    except ValueError:
        tkMessageBox.showerror("FileError", "The selected Log file could not be opened.")
    LogViewer(log_dict)

def log_open(*ignore):
    if not TimeRecord.TimeRecords:
        print "no entries"
        msg = "The Log Viewer is not available as there are no log entries. "
        msg += "\nOpen an existing log or make one or more log "
        msg += "entries before opening the Log Viewer."
        tkMessageBox.showinfo("Information", msg)
    else:
        LogViewer(TimeRecord.TimeRecords, editable=True)

class LogViewer(tk.Toplevel):
    global root

    def __init__(self, log_dict, **kwargs): # send TimeRecord.TimeRecords dictionary
        tk.Toplevel.__init__(self)
        self.counter = 0
        self.reference = {}
        self.minsize(550, 300)
        self.editable = kwargs.pop('editable', False)
        key_list = log_dict.keys()
        key_list.sort()
        key_list = [(x, x.strftime('%A %d/%m/%Y')) for x in key_list]
        # key_list is tuple of (datetime object, datetime sring)
        print key_list
        #Page Title
        title_label = tk.Label(self, text="Log Viewer")
        title_label.grid(row=0, column=0, sticky=tk.EW)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        frame = tk.Frame(self)
        frame.grid(row=1, column=0, sticky=tk.NSEW)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        style = ttk.Style(frame)
        style.configure('Treeview', rowheight=50)
        self.tree = ttk.Treeview(frame)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.tree.column("#0", width=150, anchor=tk.NW, stretch=tk.NO)
        self.tree["columns"] = ("key", "time", 1, 2, 3)
        self.tree.column("key")
        self.tree.column("time", width=100, anchor=tk.NW, stretch=tk.NO)
        self.tree.column(1, width=100, anchor=tk.NW, stretch=tk.NO)
        self.tree.column(2, width=100, anchor=tk.NW, stretch=tk.NO)
        self.tree.column(3, minwidth=200, anchor=tk.NW)
        self.tree.heading("key", text="Log Dictionary Key")
        self.tree.heading("time", text="Time")
        self.tree.heading(1, text="Project")
        self.tree.heading(2, text="Job")
        self.tree.heading(3, text="Notes")
        self.tree["displaycolumns"] = ["time", 1, 2, 3]
        count = 0
        for key in key_list:
            if count == 0:
                print "key is ", key
                current_date = key[1]
            elif current_date != key[1]:
                current_date = key[1]
                count = 0
            if count == 0:
                my_date = self.tree.insert("", 0, text=key[1], tag="date")
                self.tree.item(my_date, open=True)

            if count%2 == 1:
                row_tag = 'oddrow'
            else:
                row_tag = 'evenrow'
            value_list = log_dict[key[0]][:]
            #add time to values List
            value_list.insert(0, key[0].strftime("%H:%M"))
            #or value_list.insert(0, key[0].strftime("%I:%M %p")) for 12 hr time
            #value_list.insert(0,"test") #test is same value for every row
            # nees to insert the datetime object instead.
            self.reference[str(self.counter)] = key[0]
            value_list.insert(0, self.counter)
            self.counter += 1
            self.tree.insert(my_date, 'end', values=(value_list), tags=(row_tag,))
            count += 1
        self.tree.tag_configure('oddrow', background='#cce6ff')#'orange')
        self.tree.tag_configure('date', background='#ffd699')
        self.tree.bind("<Double-1>", self.OnDoubleClick)

    def OnDoubleClick(self, event):
        item = self.tree.identify('item', event.x, event.y)
        item_content = self.tree.item(item, "values")
        if item_content != "":
            print("you clicked on", item_content)
            # If item is a log entry open that log entry....
            #send reference instead of log_time?
            kwargs = {k:v for k, v in zip(["log_time_reference", "time", \
            "project", "job", "note"], item_content)}
            TimeRecordWindow(self, editable=self.editable, tree_item=item, **kwargs)

def date_list(my_datetime):
    my_list = list(my_datetime.timetuple()[0:6])
    my_list.append(my_datetime.microsecond)
    return my_list

def test(*ignore):
    print "F1 pressed"
    Settings(root)
    print TimeRecord.TimeRecords

root = tk.Tk()
root.iconbitmap(default="flat-clock-small.ico") #This works for the tkMessageBox
root.title("Journal Time Recorder")
root.minsize(300, 60)
#root.bind("<F1>", test)
#root.bind("<F1>", lambda e: LogViewer(TimeRecord.TimeRecords))
root.bind("<F1>", log_open)
root.bind("<F2>", open_log_file)
settings = Settings()
print settings.filename
app = App(root)#.pack()
root.mainloop()
