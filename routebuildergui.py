from tkinter import *
import tkinter.messagebox
import tkinter.simpledialog
import csv
import math
import glob
import os
from vehicleparameters import *
from busroute import *
from simconfig import *
from streetmap import *
from ttputils import *
from bikepath import *


class Dialog(Toplevel):

    def __init__(self, parent, title = None):
        Toplevel.__init__(self, parent)
        
        self.withdraw() # remain invisible for now
        # If the master is not viewable, don't
        # make the child transient, or else it
        # would be opened withdrawn
        if parent.winfo_viewable():
            self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()


        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        if self.parent is not None:
            self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                      parent.winfo_rooty()+50))

        self.deiconify() # become visibile now

        self.initial_focus.focus_set()

        # wait for window to appear on screen before calling grab_set
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)

    def destroy(self):
        self.initial_focus = None
        Toplevel.destroy(self)

    #
    # construction hooks
    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        box = Frame(self)

        
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    #
    # standard button semantics
    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        try:
            self.apply()
        finally:
            self.cancel()

    def cancel(self, event=None):
        # put focus back to the parent window
        if self.parent is not None:
            self.parent.focus_set()
        self.destroy()

    #
    # command hooks
    def validate(self):
        return 1 # override

    def apply(self):
        pass # override


class SingleEntryDialog(Dialog):
    def __init__(self, parent, title=None, labeltext="Data:", entryinit="", validatefun=None):
        self.LabelText = labeltext
        self.EntryText = StringVar()
        self.EntryText.set(entryinit)
        self.ValidateFunction = validatefun
        Dialog.__init__(self, parent, title)
        
        
    def body(self, master):
        self.MainLabel = Label(master, text=self.LabelText).grid(row=0)
        self.MainEntry = Entry(master, textvariable=self.EntryText).grid(row=0, column=1)

        #self.MainEntry.grid(row=0, column=1)
        return self.MainEntry # initial focus

    def apply(self):
        self.result = self.EntryText.get()
        
    def validate(self):
        return self.ValidateFunction(self.EntryText.get())

class MultipleInputDialog(Dialog):
    def __init__(self, parent, title=None, labeltexts=["Data:"], valueinits=[""], validatefun=None):
        if len(labeltexts) != len(valueinits):
            return
        self.LabelTexts = labeltexts
        self.ValueInits = valueinits
        self.ValidateFunction = validatefun
        Dialog.__init__(self, parent, title)
        
        
    def body(self, master):
        self.MainLabels = []
        self.MainInputs = []
        self.MainTextValues = []
        for Index in range(0, len(self.LabelTexts)):
            TempLabel = Label(master, text=self.LabelTexts[Index])
            TempLabel.grid(row=Index, sticky=E)
            self.MainLabels.append(TempLabel)
            if isinstance(self.ValueInits[Index], str):
                TextVariable = StringVar()
                TextVariable.set(self.ValueInits[Index])
                TempEntry = Entry(master, textvariable=TextVariable)
                TempEntry.grid(row=Index, column=1, sticky=W)
                self.MainInputs.append(TempEntry)
            else:
                TextVariable = StringVar()
                TempSpinbox = Spinbox(master, values=tuple(self.ValueInits[Index][1:]), textvariable=TextVariable, state="readonly")
                TempSpinbox.grid(row=Index, column=1, sticky=W)
                TextVariable.set(self.ValueInits[Index][0])
                self.MainInputs.append(TempSpinbox)
            self.MainTextValues.append(TextVariable)

        #self.MainEntry.grid(row=0, column=1)
        return self.MainInputs[0] # initial focus

    def apply(self):
        AllValues = []
        for Value in self.MainTextValues:
            AllValues.append(Value.get())
        self.result = AllValues
        
    def validate(self):
        if self.ValidateFunction:
            AllValues = []
            for Value in self.MainTextValues:
                AllValues.append(Value.get())
                
            return self.ValidateFunction(AllValues)
        return 1

class AddRemoveGridDialog(Dialog):
    def __init__(self, parent, title=None, headings=["Data"], valueinits=[[""]], validatefun=None, removefun=None, addfun=None, removeimage=None, addimage=None):
        self.HeadingTexts = headings
        self.ValueInits = valueinits
        self.ValidateFunction = validatefun
        self.RemoveFunction = removefun
        self.AddFunction = addfun
        self.RemoveImage = removeimage
        self.AddImage = addimage
        Dialog.__init__(self, parent, title)

    def body(self, master):
        self.MainFrame = master
        self.MainHeadingLabels = []
        self.MainRowData = []
        self.MainButtonRowLookup = {}
        for Index in range(0, len(self.HeadingTexts)):
            TempLabel = Label(master, text=self.HeadingTexts[Index])
            TempLabel.grid(row=0,column=Index+1)
            self.MainHeadingLabels.append(TempLabel)

        for RowIndex in range(0, len(self.ValueInits)):
            self.InsertRow(-1, self.ValueInits[RowIndex])
        TempButton = Button(master, image=self.AddImage, highlightthickness=0, borderwidth=0, relief=FLAT)
        TempButton.grid(row=len(self.ValueInits)+2,column=0)
        def AddCallback():
            if self.AddFunction:
                self.AddFunction(dialog=self)
        
        TempButton.configure(command=AddCallback)
        self.MainAddButton = TempButton
        

        #self.MainEntry.grid(row=0, column=1)
        return None #self.MainInputs[0] # initial focus
                                     
    def InsertRow(self, index=-1, values=[]):   
        if 0 > index:
            index = len(self.MainRowData)
        if index < len(self.MainRowData):
            if hasattr(self, 'MainAddButton'):
                self.MainAddButton.grid(row=len(self.MainButtonRowLookup)+3, column=0)
            NewRow = index + 2
            for RowData in self.MainRowData[index:]:
                RowData[0].grid(row=NewRow,column=0)
                for LabelIndex, Item in enumerate(RowData[1]):
                    Item.grid(row=NewRow,column=LabelIndex+1)
                NewRow += 1
            for Key in self.MainButtonRowLookup:
                if index <= self.MainButtonRowLookup[Key]:
                    self.MainButtonRowLookup[Key] = self.MainButtonRowLookup[Key] + 1
        else:
            if hasattr(self, 'MainAddButton'):
                self.MainAddButton.grid(row=len(self.MainButtonRowLookup)+3, column=0)
        TextLabels = []
        for ColIndex in range(0, len(values)):  
            TempLabel = Label(self.MainFrame, text=values[ColIndex])
            TempLabel.grid(row=index+1,column=ColIndex+1)
            TextLabels.append(TempLabel)
            
        TempButton = Button(self.MainFrame, image=self.RemoveImage, highlightthickness=0, borderwidth=0, relief=FLAT)
        TempButton.grid(row=index+1,column=0)
        self.MainButtonRowLookup[str(TempButton)] = index
        self.MainRowData.insert(index, (TempButton, TextLabels, values) )
        def RemoveCallback(buttonstr=str(TempButton)):
            RowToRemove = self.MainButtonRowLookup[buttonstr]
            RowData = self.MainRowData[RowToRemove]
            RowButton = RowData[0]             
            RowLabels = RowData[1]
            RowText = RowData[2]
            RowButton.destroy()
            for Label in RowLabels:
                Label.destroy()
            NewRowIndex = RowToRemove+1                            
            for OtherRowData in self.MainRowData[RowToRemove+1:]:
                OtherRowData[0].grid(row=NewRowIndex,column=0)
                for Index, Item in enumerate(OtherRowData[1]):
                    Item.grid(row=NewRowIndex,column=Index+1)
                NewRowIndex += 1
            self.MainAddButton.grid(row=len(self.MainRowData)+1,column=0)
            del self.MainButtonRowLookup[buttonstr]
            for Key in self.MainButtonRowLookup:
                if RowToRemove < self.MainButtonRowLookup[Key]:
                    self.MainButtonRowLookup[Key] = self.MainButtonRowLookup[Key] - 1
            del self.MainRowData[RowToRemove]
            if self.RemoveFunction:
                self.RemoveFunction(dialog=self,values=RowText)
        TempButton.configure(command=RemoveCallback)
        
    def apply(self):
        self.result = True
        
    def validate(self):
        if self.ValidateFunction:
                
            return 1 #self.ValidateFunction(AllValues)
        return 1

class RouteBuilderApp:

    BusStopImageData = """R0lGODlhIAAgAOMKAAAAAAEBAAEBAQICAQICAgMDAgMDAwQEBAUFBAUFBf///////////////////////yH+GkNyZWF0ZWQgd2l0aCBHSU1QIG9uIGEgTWFjACH5BAEKAA8ALAAAAAAgACAAAATa8MlJJxAXgMp7JVhxhRfhnc8IGOWqEhtKqYfnCoIsqfoQyiMdRZSz4YQVXIyjnGBYRShmAjN0mpLBrahiTaDMmGkbU7IGKcmRUpWYDl31zZSQI2bedDdGTqfyEiwmD3UgN4E0D4MJFzNFTls7Zktqjw9rSB5TkBUIe5MCgxZWo5SfTzylFGBUXKEuOzVfjRSYD1qVAHBRpgKkkHU7UmSCFrbCvaigtZsVQU6azJRsGLJ+TK0AwR2HQmZAWCjfOlUlHIxK1kKnfZl4p+4nWoDxJ8X1KOb4JwABmREAOw=="""
    EraserImageData = """R0lGODlhIAAgAOfcAEREQAAAAEREQEREQAAAAEREQEREQAAAAEREQAAAAEREQEREQAAAAAUFBUREQAAAAEREQAAAAEREQAAAAAQEBAgICC4uK0REQAgIBwAAAEREQAAAAEREQAAAAAAAAAAAAAEBAQAAAAEBAQAAAAUFBQAAAAAAAAUFBB8fHgcHBxwcGx8fHgcHBiEhHxwcGyAgHiMjIR8fHSIiIB4eHSEhHyAgHgAAAAAAAAUFBQQEBAUFBAAAAAAAAAEBAQAAAAEBAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAEBAQAAAAAAAAAAAAAAAAEBAQEBAQkJCQEBAQAAAAEBAQAAAAAAAAEBAQAAAAkJCAAAAAAAAAAAAAAAAAAAAAAAAAEBAQAAAAgICAAAAAICAgAAAAAAAAAAAAEBAQAAAAAAAAAAAAAAAAICAQcHBgEBAQICAgcHBggIBwAAAAcHBggIBwcHBggIBwAAAAAAAAEBAQEBAQAAAAAAAAEBAQAAAAAAAAEBAQAAAAAAAAAAAAEBAAAAAAAAAAAAAAEBAAEBAQEBAQAAAAAAAAAAAAEBAQAAAAAAAAAAAAEBAQAAAAEBAQQEBAAAAAEBAQAAAAEBAQEBAQAAAAAAAAAAAAAAAAEBAQAAAAEBAQAAAAEBAQUFBQUFBQAAAAEBAQQEBAUFBQAAAAEBAQUFBQAAAAEBAQUFBQUFBQAAAAUFBQAAAAAAAAAAAAAAAAAAAAAAAAICAgICAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEBAQAAAAEBAQAAAAAAAAAAAAEBAQAAAAEBAQAAAAEBAQAAAAAAAAAAAAAAAAICAgAAAAICAgAAAAAAAAEBAAEBAQICAgMDAgMDAwQEAwQEBP///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////yH+GkNyZWF0ZWQgd2l0aCBHSU1QIG9uIGEgTWFjACH5BAEKAP8ALAAAAAAgACAAAAjAAP8JHEiwIMFk1Kg5M8iwocFtCa1R2+aw4sOIExNa3AiRmsSOEjc6BJnRY0aRF02SBIly4EqMK1u+VAlTI8eaNHOGrDjzI06fI3+W9JmzYc+hSDtSY3i0KcaURKMmfVqQpVOdS6tGHIj1KNSCU7F+NSiU5FiGUs0WPLaVp1CGbS2KhbtzI1KHzk6KpBrU40YxJvd+rDgmMMqSDckYbsl3oJnFLf8BHXgGcuR/LP+lsXz5n0pbnDt7ViuabMKslwMCADs="""
    StopWatchImageData = """R0lGODlhIAAgAIABAAAAAP///yH+GkNyZWF0ZWQgd2l0aCBHSU1QIG9uIGEgTWFjACH5BAEKAAEALAAAAAAgACAAAAJmjI8IC+kPA1uxwtmsVmx7Q31eKIKZiXVjh3GqlZ7PW02rfOGwnpCf3wNuaJzSQShBmiLEZI131CmXTCmUmnNMnVXtlZsNGoviMTZqPqPHyu2zW9o2n99kPXq3a+a5ZiseY5MWqFEAADs="""
    BikeImageData = """R0lGODlhIAAgAIABAAAAAP///yH+GkNyZWF0ZWQgd2l0aCBHSU1QIG9uIGEgTWFjACH5BAEKAAEALAAAAAAgACAAAAJrjI+py+0Po5y02ovzA5zT3jXAFzqjdYrpBLYtuiYlO8tBvLgGfu+g4vLcYp7QzycTroqj5YnYjCKVNuEh9Rzurk4od/hcJpNBrBhhzeHSQDZ6zZuKGPGetk3nWWe1thnepxKoQVhoeIj4UAAAOw=="""
    SelectImageData = """R0lGODlhIAAgAMIFAAAAAAQEBAYGBgcHBwgICP///////////yH+GkNyZWF0ZWQgd2l0aCBHSU1QIG9uIGEgTWFjACH5BAEKAAcALAAAAAAgACAAAANmeLrc/jDKSau9FASALfhcJ4HbJz5fmYbnomogILRH/Konae+sd/Mry09HNGVWRRhxgmwqP7PKc4rrAGG0ZFXkvLWGyJyuNuWGD17udtnZKsqYWIOwswIGjrE1AMHmIj1WNIOEhYUJADs="""
    RemoveImageData = """R0lGODlhEAAQAKUxAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP8AAP///////////////////////////////////////////////////////////yH+GkNyZWF0ZWQgd2l0aCBHSU1QIG9uIGEgTWFjACH5BAEKAD8ALAAAAAAQABAAAAY2wN8PJiwah0WY8phcKp/Mp1NqlBKFViy1at0eu0um1ivuisfZKDjchA69aTQx3p5e1fd7WRgEADs="""
    PlusImageData = """R0lGODlhEAAQAKECAAD+AAD/AP///////yH+GkNyZWF0ZWQgd2l0aCBHSU1QIG9uIGEgTWFjACH5BAEKAAIALAAAAAAQABAAAAIjlB8Ace25nBSQzVYvVlZTLiniSJbmiaaplHlf5LaerNGXLRQAOw=="""
    def __init__(self, master):
        self.TkMaster = master
        self.MapCircleRadiusScaling = -6
        self.MapBorderWidth = 40
        self.MapLineWidth = 2
        self.MapStreetColor = 'black'
        self.MapPathColor = 'green'
        self.MapOffColor = ''
        self.MapPointSearchDelta = 4
        self.RouteColor = 'green'
        self.SelectedButtonOutlineColor = 'green'
        self.CurrentMode = StringVar()
        self.CurrentSubMode = 'select'
        self.CurrentRoute = IntVar()
        self.CurrentRoute.set(-1)
        self.CurrentStatusText = StringVar()
        self.BikePathAnchor = None
        master.title('Route Builder')
        MainMenuBar = Menu(master)
        
        master.protocol("WM_DELETE_WINDOW", self.ExitProgram)

        # create pulldown file menu
        self.FileMenu = Menu(MainMenuBar, tearoff=0)
        self.FileMenu.add_command(label="Reopen", command=self.ReopenData)
        self.FileMenu.add_command(label="Save", command=self.SaveData)
        self.FileMenu.add_separator()
        self.FileMenu.add_command(label="Exit", command=self.ExitProgram)
        MainMenuBar.add_cascade(label="File", menu=self.FileMenu)
        
        # create pulldown mode menu
        self.ModeMenu = Menu(MainMenuBar, tearoff=0)
        self.ModeMenu.add_radiobutton(label="Bus Stops", variable =self.CurrentMode, value='Bus Stop', command=self.ModeBusStops)
        self.ModeMenu.add_radiobutton(label="Bus Routes", variable =self.CurrentMode, value='Bus Route',command=self.ModeBusRoutes)
        self.ModeMenu.add_radiobutton(label="Bike Paths", variable =self.CurrentMode, value='Bike Path',command=self.ModeBikePaths)
        MainMenuBar.add_cascade(label="Mode", menu=self.ModeMenu)
        self.CurrentMode.set('Bus Stop')
        
        # create pulldown routes menu
        self.RouteMenu = Menu(MainMenuBar, tearoff=0)
        self.RouteMenu.add_command(label="Add Route", command=self.RouteAddRoute)
        self.RouteMenu.add_command(label="Remove Route", command=self.RouteRemoveRoute)
        self.RouteMenu.add_command(label="Copy Route", command=self.RouteCopyRoute)
        self.RouteMenu.add_command(label="Reverse Route", command=self.RouteReverseRoute)
        self.RouteMenu.add_command(label="Rename Route", command=self.RouteRenameRoute)
        self.RouteMenu.add_command(label="Change Bus", command=self.RouteChangeBus)
        self.RouteMenu.add_separator()
        self.RouteMenuFirstRouteIndex = self.RouteMenu.index("end") + 1
        MainMenuBar.add_cascade(label="Route", menu=self.RouteMenu)        
                
        # display the menu
        master.config(menu=MainMenuBar)
        
        MainFrame = Frame(master, bd=0,relief=RIDGE)  
        MainFrame.pack(fill=BOTH, expand=YES)

        self.MainCanvas = Canvas(MainFrame, width=600, height=400, bd=0, relief=RIDGE)
        self.MainCanvas.pack(fill=BOTH, expand=YES)

        #self.line = self.MainCanvas.create_line(0, 0, 200, 100, fill="black")
        
        self.MainEntry = Entry(MainFrame, textvariable=self.CurrentStatusText, state="readonly")
        self.MainEntry.pack(fill=X, side=LEFT,expand=YES)
        self.CurrentStatusText.set("")
        
        self.BusStopPhoto = PhotoImage(data=RouteBuilderApp.BusStopImageData)
        self.EraserPhoto = PhotoImage(data=RouteBuilderApp.EraserImageData)
        self.StopWatchPhoto = PhotoImage(data=RouteBuilderApp.StopWatchImageData)
        self.BikePhoto = PhotoImage(data=RouteBuilderApp.BikeImageData)
        self.SelectPhoto = PhotoImage(data=RouteBuilderApp.SelectImageData)
        self.RemovePhoto = PhotoImage(data=RouteBuilderApp.RemoveImageData)
        self.PlusPhoto = PhotoImage(data=RouteBuilderApp.PlusImageData)
        
        self.ModeLeftMousePress = self.BusStopModeLeftMousePress              
        self.ModeLeftMouseRelease = self.BusStopModeLeftMouseRelease
        self.ModeMouseEnter = self.BusStopModeMouseEnter
        self.ModeMouseMotion = self.BusStopModeMouseMotion
        self.ModeMouseLeave = self.BusStopModeMouseLeave
        self.ModeLeftMouseDrag = self.BusStopModeMouseDrag

        
        self.MapBorderWidth = self.BusStopPhoto.width() + 4 * self.MapLineWidth
        master.update()
        master.minsize(master.winfo_width(), master.winfo_height())
        self.MainCanvasHeight = self.MainCanvas.winfo_reqheight()
        self.MainCanvasWidth = self.MainCanvas.winfo_reqwidth()
        self.ReopenData()
                
        self.MainCanvas.bind("<Configure>", self.CanvasResize) #bind to resize event
        self.MainCanvas.bind("<Button-1>",self.CanvasLeftMousePress)
        self.MainCanvas.bind("<Enter>",self.CanvasMouseEnter)
        self.MainCanvas.bind("<Motion>",self.CanvasMouseMotion)
        self.MainCanvas.bind("<Leave>",self.CanvasMouseLeave)
        self.MainCanvas.bind("<B1-Motion>",self.CanvasLeftMouseDrag)
        self.MainCanvas.bind("<ButtonRelease-1>",self.CanvasLeftMouseRelease)

    @staticmethod
    def TypeNameToTag(typename, name):
        return typename + "_" + name.replace("_","__").replace(" ", "_")
        
    @staticmethod
    def TagToTypeName(tag):
        FirstUnderscore = tag.find("_")
        Type = tag[:FirstUnderscore]
        Name = ''
        LastWasUnderscore = False
        for Letter in tag[FirstUnderscore+1:]:
            if LastWasUnderscore:
                if Letter == '_':
                    Name += '_'
                else:
                    Name += ' ' + Letter
                LastWasUnderscore = False
            elif Letter == '_':
                LastWasUnderscore = True
            else:
                Name += Letter
                
        return (Type, Name)

    def ExitProgram(self):
        if self.ChangesMade:
            WantToSave = tkinter.messagebox.askyesnocancel("Unsaved Changes", "Do you want to save before closing?")
            if WantToSave is None:
                return
            if WantToSave:
                self.SaveData()
        self.TkMaster.destroy()

    def ReopenData(self):
        self.SimConfig = SimulationConfiguration()
        if len(glob.glob("data/config.csv")):
            self.SimConfig.Load("data/config.csv")
        self.LocalStreetMap = StreetMap('data/streetmap.csv')
        self.LocalBusStops = BusStops(self.LocalStreetMap)
        self.LocalBikePaths = BikePaths(self.LocalStreetMap)
        if len(glob.glob("data/busstops.csv")):
            self.LocalBusStops.Load("data/busstops.csv")
        if len(glob.glob("data/bikepath.csv")):
            self.LocalBikePaths.Load("data/bikepath.csv")
        self.LocalBusRoutes = {}
        for RouteFile in glob.glob("data/route*.csv"):
            NewBusRoute = BusRoute(self.LocalStreetMap, self.SimConfig.BusStation())
            if NewBusRoute.Load(RouteFile):
                self.LocalBusRoutes[NewBusRoute.RouteName] = NewBusRoute
        self.AllVehicles = VehicleParameters("data/vehicleparameters.csv")
        self.DefaultVehicle = ''
        self.AllVehicleNames = self.AllVehicles.GetVehicleNames()
        for Vehicle in self.AllVehicleNames:
            Capacity = self.AllVehicles.GetParameter(Vehicle,'Capacity')
            if Capacity:
                if int(Capacity) >  10:
                    if 0 == len(self.DefaultVehicle):
                        self.DefaultVehicle = Vehicle
                    elif int(self.AllVehicles.GetParameter(self.DefaultVehicle,'Capacity')) > int(Capacity):
                        self.DefaultVehicle = Vehicle
        self.RefreshMap()
        self.RedrawButtons()
        self.UpdateRouteMenu()
        self.ChangesMade = False
        
    def SaveData(self):
        self.SimConfig.Save("data/config.csv")
        self.LocalBusStops.Save("data/busstops.csv")
        self.LocalBikePaths.Save("data/bikepath.csv")
        for RouteFile in glob.glob("data/route*.csv"):
            os.remove(RouteFile)
        Index = 0
        for RouteName in self.LocalBusRoutes:
            RouteFileName = "data/route"+str(Index)+".csv"
            self.LocalBusRoutes[RouteName].Save(RouteFileName)
            Index = Index + 1
        self.OutputRoutesAsHTML("routes.html")
        self.CurrentStatusText.set('Data Saved')
        self.ChangesMade = False
        
    def OutputRoutesAsHTML(self,filename):
        OutputFile = open("results/"+filename, 'w')
        OutputHTMLHead(OutputFile,'Bus Routes')
        RouteIndex = 1
        for RouteName in self.LocalBusRoutes:
            RouteInfo = self.LocalBusRoutes[RouteName]
            OutputHTMLHeader1(OutputFile,'Route: '+RouteName)
            
            FullPath = RouteInfo.CalculateFullPath()
            PathEdges = []
            if 0 != len(FullPath):
                LastNode = FullPath[0]
                for CurNode in FullPath[1:]:
                    if LastNode < CurNode:
                        PathEdges.append((LastNode,CurNode))
                    else:
                        PathEdges.append((CurNode,LastNode))
                    LastNode = CurNode
            
            CircleRadius = 5
            DesiredWidth = 600
            BorderWidth = 40
            
            Scaling = float(DesiredWidth) / RouteInfo.StreetMap.MaxX
            DesiredHeight = int(math.ceil(RouteInfo.StreetMap.MaxY * Scaling))
            WidthCenter = (BorderWidth * 2 + DesiredWidth) / 2
            HeightCenter = (BorderWidth * 2 + DesiredHeight) / 2
            
            OutputImageFileName = "Route"+str(RouteIndex)+".svg"
            RouteIndex = RouteIndex + 1
            OutputImageFile = open("results/"+OutputImageFileName, 'w')
            OutputHTMLIndent(OutputFile,2)
            OutputHTMLImage(OutputFile, OutputImageFileName, DesiredWidth + 2 * BorderWidth, DesiredHeight + 2 * BorderWidth)
            
            OutputSVGDocType(OutputImageFile)
            OutputSVGHead(OutputImageFile, DesiredWidth + 2 * BorderWidth, DesiredHeight + 2 * BorderWidth, True)
            RGBBlack = (0,0,0)
            RGBRed = (255,0,0)
            for Edge in RouteInfo.StreetMap.EdgeList:
                if not Edge in PathEdges:
                    Source = RouteInfo.StreetMap.PointDB[Edge[0]]
                    Source = (BorderWidth + int(Source[0] * Scaling), DesiredHeight + BorderWidth - int(Source[1] * Scaling))
                    Dest = RouteInfo.StreetMap.PointDB[Edge[1]]
                    Dest = (BorderWidth + int(Dest[0] * Scaling), DesiredHeight + BorderWidth - int(Dest[1] * Scaling))
                    OutputHTMLIndent(OutputImageFile,2)
                    OutputSVGLine(OutputImageFile, Source, Dest, RGBBlack, 2)
            
            for Edge in PathEdges:
                Source = RouteInfo.StreetMap.PointDB[Edge[0]]
                Source = (BorderWidth + int(Source[0] * Scaling), DesiredHeight + BorderWidth - int(Source[1] * Scaling))
                Dest = RouteInfo.StreetMap.PointDB[Edge[1]]
                Dest = (BorderWidth + int(Dest[0] * Scaling), DesiredHeight + BorderWidth - int(Dest[1] * Scaling))
                OutputHTMLIndent(OutputImageFile,2)
                OutputSVGLine(OutputImageFile, Source, Dest, RGBRed, 2)
            
            for Point in RouteInfo.RoutePath:
                Center = RouteInfo.StreetMap.PointDB[Point]
                Center = (BorderWidth + int(Center[0] * Scaling), DesiredHeight + BorderWidth - int(Center[1] * Scaling))
    
                OutputHTMLIndent(OutputImageFile,2)
                OutputSVGCircle(OutputImageFile,Center,CircleRadius,RGBRed)
                OtherPoints = RouteInfo.StreetMap.ConnectivityDB[Point]
                StreetAngle = StreetMap.CalculateAngle(RouteInfo.StreetMap.PointDB[OtherPoints[0]], RouteInfo.StreetMap.PointDB[OtherPoints[1]])
                if math.pi < StreetAngle:
                    StreetAngle = StreetAngle - math.pi
                ClosestTB = RouteInfo.StreetMap.FindNearestTopBottom(Point)
                ClosestLR = RouteInfo.StreetMap.FindNearestLeftRight(Point)
                MinDist = min(ClosestTB[0],ClosestTB[1],ClosestLR[0],ClosestLR[1])
                PointText = 'S'+str(RouteInfo.RoutePath.index(Point)+1)
                OutputHTMLIndent(OutputImageFile,2)
                if (math.pi * 7.0/8.0 < StreetAngle) or (StreetAngle < math.pi / 8.0):
                    if ClosestTB[1] < ClosestTB[0]:
                        OutputSVGText(OutputImageFile,Center[0],Center[1]+CircleRadius+2,RGBRed,'bottom','center', PointText)
                    else:
                        OutputSVGText(OutputImageFile,Center[0],Center[1]-(CircleRadius+2),RGBRed,'top','center', PointText)
                elif (math.pi * 3.0/8.0 < StreetAngle) and (StreetAngle < math.pi * 5.0/ 8.0):
                    if ClosestLR[0] < ClosestLR[1]:
                        OutputSVGText(OutputImageFile,Center[0]+CircleRadius+2,Center[1],RGBRed,'middle','right', PointText)
                    else:
                        OutputSVGText(OutputImageFile,Center[0]-(CircleRadius+2),Center[1],RGBRed,'middle','left', PointText)
                elif (math.pi * 3.0/8.0 > StreetAngle):
                    DistFromPoint = (CircleRadius + 2)/2
                    if (MinDist != ClosestTB[1]) and (MinDist != ClosestLR[1]):
                        OutputSVGText(OutputImageFile,Center[0]+DistFromPoint,Center[1]+DistFromPoint,RGBRed,'bottom','right', PointText)
                    else:
                        OutputSVGText(OutputImageFile,Center[0]-DistFromPoint,Center[1]-DistFromPoint,RGBRed,'top','left', PointText)
                else:
                    DistFromPoint = (CircleRadius + 2)/2
                    if (MinDist != ClosestTB[1]) and (MinDist != ClosestLR[0]):
                        OutputSVGText(OutputImageFile,Center[0]+DistFromPoint,Center[1]-DistFromPoint,RGBRed,'top','right', PointText)
                    else:
                        OutputSVGText(OutputImageFile,Center[0]-DistFromPoint,Center[1]+DistFromPoint,RGBRed,'bottom','left', PointText)
            Center = RouteInfo.StreetMap.PointDB[RouteInfo.RouteAnchor]
            Center = (BorderWidth + int(Center[0] * Scaling), DesiredHeight + BorderWidth - int(Center[1] * Scaling))
            OutputHTMLIndent(OutputImageFile,2)
            OutputSVGSquare(OutputImageFile,Center,CircleRadius,RGBRed)
            OutputHTMLIndent(OutputImageFile,2)
            OutputSVGText(OutputImageFile,Center[0],Center[1]+CircleRadius+2,RGBRed,'bottom','center', 'Campus')    
                
            #OutputHTMLIndent(OutputImageFile,2)
            OutputSVGTail(OutputImageFile)
            OutputImageFile.close()
                    
            OutputHTMLHeader2(OutputFile,'Bus Type: ')
            OutputHTMLText(OutputFile, RouteInfo.BusType + '\n')
            OutputHTMLHeader2(OutputFile,'Times:')
            OutputHTMLTableBegin(OutputFile, 1)
            
            StopNames = [' ','Campus']
            for Point in RouteInfo.RoutePath:
                StopNames.append(Point + ' (S'+str(RouteInfo.RoutePath.index(Point)+1)+')')
            StopNames.append('Campus')
            OutputHTMLTableRow(OutputFile,StopNames)
            Index = 1
            for LoopTimes in RouteInfo.RouteTimes:
                LoopRow = ['Loop '+str(Index)]
                StopTimes = list(LoopTimes)
                for StopTime in StopTimes:
                    LoopRow.append(ConvertSecondsToTime(StopTime))
                OutputHTMLTableRow(OutputFile,LoopRow)
                Index = Index + 1
            OutputHTMLTableEnd(OutputFile)
    
    
        OutputHTMLTail(OutputFile)
        OutputFile.close()
    
    
    def UpdateRouteMenu(self):
        AllRouteNames = list(self.LocalBusRoutes.keys())
        AllRouteNames.sort()
        SelectedName = ''
        SelectedIndex = -1
        if 0 <= self.CurrentRoute.get():
            SelectedName = self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label')
        LastIndex = self.RouteMenu.index("end")
        if self.RouteMenuFirstRouteIndex <= LastIndex:
            self.RouteMenu.delete(self.RouteMenuFirstRouteIndex, LastIndex)
        CurrentIndex = 0
        for RouteName in AllRouteNames:
            self.RouteMenu.add_radiobutton(label=RouteName, variable=self.CurrentRoute, value=CurrentIndex, command=self.RouteSelectRoute)
            if RouteName == SelectedName:
                SelectedIndex = CurrentIndex
            CurrentIndex += 1
        self.CurrentRoute.set(SelectedIndex)
    
    def CanvasToMapXY(self, x, y):
        x = (x - self.MapBorderWidth) / self.MapScaling
        y = (self.MapRenderedHeight + self.MapBorderWidth - y) / self.MapScaling
        return (x, y)
    
    def MapToCanvasXY(self, x, y, offx=0.0, offy=0.0):
        return (self.MapBorderWidth + int(x * self.MapScaling + offx), self.MapRenderedHeight + self.MapBorderWidth - int(y * self.MapScaling + offy))
        
    def DrawBikePathDrag(self, x, y):
        for MapPart in self.MainCanvas.find_withtag('drag_path'):
            self.MainCanvas.delete(MapPart)
            
        if self.BikePathAnchor:
            if isinstance(self.BikePathAnchor, str):
                Source = self.LocalBikePaths.StreetMap.PointDB[self.BikePathAnchor]
            elif 3 == len(self.BikePathAnchor):
                Source = self.LocalBikePaths.GetLocationBetweenPoints(self.BikePathAnchor[0], self.BikePathAnchor[1], self.BikePathAnchor[2])
            else:
                Source = self.BikePathAnchor
            Source = self.MapToCanvasXY(Source[0], Source[1])
            Coords = (Source[0], Source[1], x, y)
            NewLine = self.MainCanvas.create_line(Coords, fill=self.MapPathColor, width=self.MapLineWidth )
            self.MainCanvas.itemconfig(NewLine, tags=("all", "map", "drag_path"))
        self.MainCanvas.update_idletasks()
    
    def RemoveBikePathDrag(self):
        for MapPart in self.MainCanvas.find_withtag('drag_path'):
            self.MainCanvas.delete(MapPart)

        self.MainCanvas.update_idletasks()
    
    def RefreshMap(self):
        self.RedrawMap(self.MainCanvasWidth, self.MainCanvasHeight)
        self.TkMaster.focus()
        
    def RedrawMap(self, width, height):
        for MapPart in self.MainCanvas.find_withtag('map'):
            self.MainCanvas.delete(MapPart)
        self.MainCanvasHeight = height
        self.MainCanvasWidth = width
    
        MapDrawingWidth = self.MainCanvasWidth - 2 * self.MapBorderWidth
        MapDrawingHeight = self.MainCanvasHeight - 2 * self.MapBorderWidth
        CurrentWHRatio = MapDrawingWidth / MapDrawingHeight
        MapWHRatio = self.LocalStreetMap.MaxX / self.LocalStreetMap.MaxY
        if CurrentWHRatio <= MapWHRatio:
            self.MapScaling = float(MapDrawingWidth) / self.LocalStreetMap.MaxX
            DesiredWidth = MapDrawingWidth
            DesiredHeight = int(math.ceil(self.LocalStreetMap.MaxY * self.MapScaling))
        else:
            self.MapScaling = float(MapDrawingHeight) / self.LocalStreetMap.MaxY   
            DesiredWidth = int(math.ceil(self.LocalStreetMap.MaxX * self.MapScaling))
            DesiredHeight = MapDrawingHeight
        if 0 > self.MapCircleRadiusScaling:
            # first call setup scaling
            self.MapCircleRadiusScaling = -self.MapCircleRadiusScaling / self.MapScaling
        self.MapCircleRadius = int(round(self.MapCircleRadiusScaling * self.MapScaling))
        self.MapRenderedHeight = DesiredHeight
        self.MapRenderedWidth = DesiredWidth
        WidthCenter = (self.MapBorderWidth * 2 + DesiredWidth) / 2
        HeightCenter = (self.MapBorderWidth * 2 + DesiredHeight) / 2
                                                           
        for Edge in self.LocalStreetMap.EdgeList:   
            Source = self.LocalStreetMap.PointDB[Edge[0]]      
            Source = self.MapToCanvasXY(Source[0], Source[1])
            Dest = self.LocalStreetMap.PointDB[Edge[1]]
            Dest = self.MapToCanvasXY(Dest[0], Dest[1])
            Coords = (Source[0], Source[1], Dest[0], Dest[1])
            NewLine = self.MainCanvas.create_line(Coords, fill=self.MapStreetColor, width=self.MapLineWidth )
            self.MainCanvas.itemconfig(NewLine, tags=("all", "map", "street", RouteBuilderApp.TypeNameToTag('street', Edge[0]+'_'+Edge[1]), RouteBuilderApp.TypeNameToTag('street', Edge[1]+'_'+Edge[0])))    

        for EdgeName, EdgeValue in self.LocalBikePaths.AddedEdges.items():
            Source = self.LocalBikePaths.StreetMap.PointDB[EdgeValue[0]]      
            Source = self.MapToCanvasXY(Source[0], Source[1])
            Dest = self.LocalBikePaths.StreetMap.PointDB[EdgeValue[1]]
            Dest = self.MapToCanvasXY(Dest[0], Dest[1])
            Coords = (Source[0], Source[1], Dest[0], Dest[1])
            NewLine = self.MainCanvas.create_line(Coords, fill=self.MapPathColor if self.CurrentMode.get() == 'Bike Path' else self.MapOffColor, width=self.MapLineWidth )
            self.MainCanvas.itemconfig(NewLine, tags=("all", "map", "path", RouteBuilderApp.TypeNameToTag('path', EdgeName)))    

        for StopName in self.LocalBusStops.StopNames:
            Location = self.LocalStreetMap.PointDB[StopName]
            Location = self.MapToCanvasXY(Location[0], Location[1], - self.MapCircleRadius*0.5, - self.MapCircleRadius*0.5)
            Coords = (Location[0], Location[1], Location[0] + self.MapCircleRadius, Location[1] - self.MapCircleRadius)
            NewCircle = self.MainCanvas.create_oval(Coords, fill=self.MapStreetColor, width=0)
            self.MainCanvas.itemconfig(NewCircle, tags=("all", "map", "stop", RouteBuilderApp.TypeNameToTag('stop', StopName)))    
            
        Location = self.LocalStreetMap.PointDB[self.SimConfig.BusStation()]
        Location = self.MapToCanvasXY(Location[0], Location[1], - self.MapCircleRadius*0.5, - self.MapCircleRadius*0.5)
        Coords = (Location[0], Location[1], Location[0] + self.MapCircleRadius, Location[1] - self.MapCircleRadius)
        NewCircle = self.MainCanvas.create_rectangle(Coords, fill=self.MapStreetColor, width=0) 
        self.MainCanvas.itemconfig(NewCircle, tags=("all", "map", "busstation", "stop", RouteBuilderApp.TypeNameToTag('stop', self.SimConfig.BusStation())))    
        
        for RouteName in self.LocalBusRoutes:
            RouteInfo = self.LocalBusRoutes[RouteName]
            FullPath = RouteInfo.CalculateFullPath()
            PathEdges = []
            if 0 != len(FullPath):
                LastNode = FullPath[0]
                for CurNode in FullPath[1:]:
                    if LastNode < CurNode:
                        PathEdges.append((LastNode,CurNode))
                    else:
                        PathEdges.append((CurNode,LastNode))
                    LastNode = CurNode
                    
            for Edge in PathEdges:
                self.MainCanvas.addtag_withtag(RouteBuilderApp.TypeNameToTag('route', RouteName), RouteBuilderApp.TypeNameToTag('street', Edge[0]+'_'+Edge[1]))
            for Point in RouteInfo.RoutePath:
                self.MainCanvas.addtag_withtag(RouteBuilderApp.TypeNameToTag('route', RouteName), RouteBuilderApp.TypeNameToTag('stop', Point))
            self.MainCanvas.addtag_withtag(RouteBuilderApp.TypeNameToTag('route', RouteName), RouteBuilderApp.TypeNameToTag('stop', self.SimConfig.BusStation()))  
        
        self.MainCanvas.update_idletasks()                                            
    
    def RedrawButtons(self):
        self.ButtonLeftOffset = LeftOffset = int(self.MainCanvasWidth - self.MapBorderWidth + self.MapLineWidth)
        self.ButtonTopOffset = TopOffset = self.MapLineWidth * 2
        for Icon in self.MainCanvas.find_withtag('icon'):
            self.MainCanvas.delete(Icon)
        
        if self.CurrentMode.get() == 'Bus Stop' or self.CurrentMode.get() == 'Bus Route':
            NewImage = self.MainCanvas.create_image((LeftOffset, TopOffset), anchor = NW, image=self.SelectPhoto)
            self.MainCanvas.itemconfig(NewImage, tags=("all", "icon", "selectstop"))    
            Coords = (LeftOffset, TopOffset, LeftOffset + self.SelectPhoto.width(), TopOffset + self.SelectPhoto.height())
            NewRectangle = self.MainCanvas.create_rectangle(Coords, fill='', outline=self.SelectedButtonOutlineColor if self.CurrentSubMode=='select' else '', width=self.MapLineWidth)
            self.MainCanvas.itemconfig(NewRectangle, tags=("all", "icon", "buttonborder", "selectborder"))
            
            TopOffset += self.SelectPhoto.height()
            NewImage = self.MainCanvas.create_image((LeftOffset, TopOffset), anchor = NW, image=self.BusStopPhoto)
            self.MainCanvas.itemconfig(NewImage, tags=("all", "icon", "addstop"))    
            Coords = (LeftOffset, TopOffset, LeftOffset + self.BusStopPhoto.width(), TopOffset + self.BusStopPhoto.height())
            NewRectangle = self.MainCanvas.create_rectangle(Coords, fill='', outline=self.SelectedButtonOutlineColor if self.CurrentSubMode=='add' else '', width=self.MapLineWidth)
            self.MainCanvas.itemconfig(NewRectangle, tags=("all", "icon", "buttonborder", "addborder"))
            
            TopOffset += self.BusStopPhoto.height()
            NewImage = self.MainCanvas.create_image((LeftOffset, TopOffset), anchor = NW, image=self.EraserPhoto)
            self.MainCanvas.itemconfig(NewImage, tags=("all", "icon", "removestop"))    
            Coords = (LeftOffset, TopOffset, LeftOffset + self.EraserPhoto.width(), TopOffset + self.EraserPhoto.height())
            NewRectangle = self.MainCanvas.create_rectangle(Coords, fill='', outline=self.SelectedButtonOutlineColor if self.CurrentSubMode=='remove' else '', width=self.MapLineWidth)
            self.MainCanvas.itemconfig(NewRectangle, tags=("all", "icon", "buttonborder", "removeborder"))
            
            TopOffset += self.EraserPhoto.height()
            
            if self.CurrentMode.get() == 'Bus Route':
                NewImage = self.MainCanvas.create_image((LeftOffset, TopOffset), anchor = NW, image=self.StopWatchPhoto)
                self.MainCanvas.itemconfig(NewImage, tags=("all", "icon", "stoptimes"))
                TopOffset += self.StopWatchPhoto.height()
        else:
            NewImage = self.MainCanvas.create_image((LeftOffset, TopOffset), anchor = NW, image=self.SelectPhoto)
            self.MainCanvas.itemconfig(NewImage, tags=("all", "icon", "selectpath"))    
            Coords = (LeftOffset, TopOffset, LeftOffset + self.SelectPhoto.width(), TopOffset + self.SelectPhoto.height())
            NewRectangle = self.MainCanvas.create_rectangle(Coords, fill='', outline=self.SelectedButtonOutlineColor if self.CurrentSubMode=='select' else '', width=self.MapLineWidth)
            self.MainCanvas.itemconfig(NewRectangle, tags=("all", "icon", "buttonborder", "selectborder"))
            
            TopOffset += self.SelectPhoto.height()
            NewImage = self.MainCanvas.create_image((LeftOffset, TopOffset), anchor = NW, image=self.BikePhoto)
            self.MainCanvas.itemconfig(NewImage, tags=("all", "icon", "addstop"))    
            Coords = (LeftOffset, TopOffset, LeftOffset + self.BikePhoto.width(), TopOffset + self.BikePhoto.height())
            NewRectangle = self.MainCanvas.create_rectangle(Coords, fill='', outline=self.SelectedButtonOutlineColor if self.CurrentSubMode=='add' else '', width=self.MapLineWidth)
            self.MainCanvas.itemconfig(NewRectangle, tags=("all", "icon", "buttonborder", "addborder"))
            
            TopOffset += self.BikePhoto.height()
            NewImage = self.MainCanvas.create_image((LeftOffset, TopOffset), anchor = NW, image=self.EraserPhoto)
            self.MainCanvas.itemconfig(NewImage, tags=("all", "icon", "removestop"))    
            Coords = (LeftOffset, TopOffset, LeftOffset + self.EraserPhoto.width(), TopOffset + self.EraserPhoto.height())
            NewRectangle = self.MainCanvas.create_rectangle(Coords, fill='', outline=self.SelectedButtonOutlineColor if self.CurrentSubMode=='remove' else '', width=self.MapLineWidth)
            self.MainCanvas.itemconfig(NewRectangle, tags=("all", "icon", "buttonborder", "removeborder"))
            
            TopOffset += self.EraserPhoto.height()
        self.ButtonBottomOffset = TopOffset
        self.MainCanvas.update_idletasks()
        
    def HighlightRoute(self):
        for Edge in self.MainCanvas.find_withtag('street'):
            self.MainCanvas.itemconfig(Edge, fill=self.MapStreetColor)
        for Stop in self.MainCanvas.find_withtag('stop'):
            self.MainCanvas.itemconfig(Stop, fill=self.MapStreetColor)
        if 0 <= self.CurrentRoute.get():    
            RouteName = self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label')
            for Item in self.MainCanvas.find_withtag(RouteBuilderApp.TypeNameToTag('route', RouteName)):
                self.MainCanvas.itemconfig(Item, fill=self.RouteColor)
        self.MainCanvas.update_idletasks()
    
    def HighlightBikePath(self):
        for Edge in self.MainCanvas.find_withtag('path'):
            self.MainCanvas.itemconfig(Edge, fill=self.MapPathColor)
            
    def UnhighlightBikePath(self):
        for Edge in self.MainCanvas.find_withtag('path'):
            self.MainCanvas.itemconfig(Edge, fill=self.MapOffColor)
    
    def RemoveTagFromItems(self, tag):
        AllItems = self.MainCanvas.find_withtag(tag)
        for Item in AllItems:
            self.MainCanvas.dtag(Item, tag)
    
    def FindClosestItemWithTag(self, tag, x, y):
        DeltaDistance = 2
        NearItems = self.MainCanvas.find_overlapping(x - DeltaDistance, y - DeltaDistance, x + DeltaDistance, y + DeltaDistance)
        BestItem = None
        for Item in NearItems:
            if tag in self.MainCanvas.gettags(Item):
                BestItem = Item
        return BestItem
    
    def GetItemTypeAndName(self, item):
        AllTags = self.MainCanvas.gettags(item)
        for Tag in AllTags:
            if Tag.find('stop_') == 0 or Tag.find('street_') == 0 or Tag.find('path_') == 0:
                return RouteBuilderApp.TagToTypeName(Tag)
        return ('unknown', '')
    
    def ModeBusStops(self):
        if self.CurrentMode.get() != 'Bus Stop':
            self.CurrentMode.set('Bus Stop')
        self.ModeLeftMousePress = self.BusStopModeLeftMousePress              
        self.ModeLeftMouseRelease = self.BusStopModeLeftMouseRelease
        self.ModeMouseEnter = self.BusStopModeMouseEnter
        self.ModeMouseMotion = self.BusStopModeMouseMotion
        self.ModeMouseLeave = self.BusStopModeMouseLeave
        self.ModeLeftMouseDrag = self.BusStopModeMouseDrag
        self.CurrentRoute.set(-1)
        self.CurrentStatusText.set('')
        self.HighlightRoute()
        self.UnhighlightBikePath()
        self.RedrawButtons()
        
    def ModeBikePaths(self):
        if self.CurrentMode.get() != 'Bike Path':
            self.CurrentMode.set('Bike Path')
        self.ModeLeftMousePress = self.BikePathModeLeftMousePress              
        self.ModeLeftMouseRelease = self.BikePathModeLeftMouseRelease
        self.ModeMouseEnter = self.BikePathModeMouseEnter
        self.ModeMouseMotion = self.BikePathModeMouseMotion
        self.ModeMouseLeave = self.BikePathModeMouseLeave
        self.ModeLeftMouseDrag = self.BikePathModeMouseDrag
        self.CurrentRoute.set(-1)
        self.CurrentStatusText.set('')
        self.HighlightRoute()
        self.HighlightBikePath()
        self.RedrawButtons()
    
    def ModeBusRoutes(self):
        if 0 == len(list(self.LocalBusRoutes.keys())):
            tkinter.messagebox.showerror("Bus Route Error", "No routes to modify, add a route first!")
            self.ModeBusStops()
            return
        if self.CurrentMode.get() != 'Bus Route':
            self.CurrentMode.set('Bus Route')
        self.ModeLeftMousePress = self.BusRouteModeLeftMousePress              
        self.ModeLeftMouseRelease = self.BusRouteModeLeftMouseRelease
        self.ModeMouseEnter = self.BusRouteModeMouseEnter
        self.ModeMouseMotion = self.BusRouteModeMouseMotion
        self.ModeMouseLeave = self.BusRouteModeMouseLeave
        self.ModeLeftMouseDrag = self.BusRouteModeMouseDrag
        self.CurrentStatusText.set('')
        self.RedrawButtons()
        self.UnhighlightBikePath()
        if 0 > self.CurrentRoute.get():
            self.CurrentRoute.set(0)
            self.HighlightRoute()
    
    def RouteAddRoute(self):
        NewRouteNumber = 1
        while "R" + str(NewRouteNumber) in self.LocalBusRoutes:
            NewRouteNumber += 1
        def RouteNameValidate(name):
            return 0 if name in self.LocalBusRoutes else 1
            
        TempDialog = SingleEntryDialog(self.TkMaster, title = "Add Route", labeltext="Route Name:", entryinit="R" + str(NewRouteNumber), validatefun=RouteNameValidate)
        if TempDialog.result:
            self.LocalBusRoutes[TempDialog.result] = BusRoute(self.LocalStreetMap, self.SimConfig.BusStation())
            self.LocalBusRoutes[TempDialog.result].RouteName = TempDialog.result
            self.LocalBusRoutes[TempDialog.result].BusType = self.DefaultVehicle
            self.UpdateRouteMenu()
            self.ChangesMade = True
        
    def RouteRemoveRoute(self):
        RouteValues = []
        for RouteName in self.LocalBusRoutes:
            RouteValues.append(RouteName)
        if 0 == len(RouteValues):
            tkinter.messagebox.showerror("Remove Route Error", "No routes to remove!")
            return
        if 0 <= self.CurrentRoute.get():
            RouteValues.insert(0, self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label'))
        else:
            RouteValues.insert(0, RouteValues[-1])
            
        TempDialog = MultipleInputDialog(self.TkMaster, title="Remove Route", labeltexts=["Route Name:"], valueinits=[RouteValues])
        if TempDialog.result:
            if 0 <= self.CurrentRoute.get():
                if self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label') == TempDialog.result[0]:
                    self.CurrentRoute.set(-1)
            del self.LocalBusRoutes[TempDialog.result[0]]
            self.RemoveTagFromItems(RouteBuilderApp.TypeNameToTag('route', TempDialog.result[0]) )
            self.UpdateRouteMenu()
            self.HighlightRoute()
            self.ChangesMade = True
        
    def RouteCopyRoute(self):
        RouteValues = []
        for RouteName in self.LocalBusRoutes:
            RouteValues.append(RouteName)
        if 0 == len(RouteValues):
            tkinter.messagebox.showerror("Remove Route Error", "No routes to copy!")
            return
        if 0 <= self.CurrentRoute.get():
            RouteValues.insert(0, self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label'))
        else:
            RouteValues.insert(0, RouteValues[-1])
        
        NewRouteNumber = 1
        while "R" + str(NewRouteNumber) in self.LocalBusRoutes:
            NewRouteNumber += 1
            
        def RouteNameValidate(values):
            return 0 if values[1] in self.LocalBusRoutes else 1
        NewRouteName = "R"+str(NewRouteNumber)
        TempDialog = MultipleInputDialog(self.TkMaster, title="Copy Route", labeltexts=["Route To Copy:","Route Name:"], valueinits=[RouteValues,NewRouteName], validatefun=RouteNameValidate )
        if TempDialog.result:
            OldRoute = TempDialog.result[0]
            NewRoute = TempDialog.result[1]
            self.MainCanvas.addtag_withtag(RouteBuilderApp.TypeNameToTag('route', NewRoute), RouteBuilderApp.TypeNameToTag('route', OldRoute))
            self.LocalBusRoutes[NewRoute] = BusRoute(self.LocalStreetMap, self.SimConfig.BusStation())
            self.LocalBusRoutes[NewRoute].RouteName = NewRoute
            self.LocalBusRoutes[NewRoute].BusType = self.DefaultVehicle
            self.LocalBusRoutes[NewRoute].CopyRoute(self.LocalBusRoutes[OldRoute])
            self.UpdateRouteMenu()
            self.ChangesMade = True
        
    def RouteReverseRoute(self):
        RouteValues = []
        for RouteName in self.LocalBusRoutes:
            RouteValues.append(RouteName)
        if 0 == len(RouteValues):
            tkinter.messagebox.showerror("Reverse Route Error", "No routes to reverse!")
            return
        if 0 <= self.CurrentRoute.get():
            RouteValues.insert(0, self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label'))
        else:
            RouteValues.insert(0, RouteValues[-1])
            
        TempDialog = MultipleInputDialog(self.TkMaster, title="Reverse Route", labeltexts=["Route Name:"], valueinits=[RouteValues])
        if TempDialog.result:
            self.LocalBusRoutes[TempDialog.result[0]].ReverseStops()
            self.ChangesMade = True
        
    def RouteRenameRoute(self):
        RouteValues = []
        for RouteName in self.LocalBusRoutes:
            RouteValues.append(RouteName)
        if 0 == len(RouteValues):
            tkinter.messagebox.showerror("Rename Route Error", "No routes to rename!")
            return
        if 0 <= self.CurrentRoute.get():
            RouteValues.insert(0, self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label'))
        else:
            RouteValues.insert(0, RouteValues[-1])
            
        TempDialog = MultipleInputDialog(self.TkMaster, title="Rename Route", labeltexts=["Route Name:"], valueinits=[RouteValues])
        if TempDialog.result:
            OldName = TempDialog.result[0]

            def RouteNameValidate(name):
                if name == OldName:
                    return 1
                return 0 if name in self.LocalBusRoutes else 1
                
            TempDialog = SingleEntryDialog(self.TkMaster, title = "Rename Route "+OldName, labeltext="Route Name:", entryinit=OldName, validatefun=RouteNameValidate)
            if TempDialog.result:
                NewName = TempDialog.result
                self.LocalBusRoutes[OldName].RouteName = NewName
                self.LocalBusRoutes[NewName] = self.LocalBusRoutes[OldName]
                del self.LocalBusRoutes[OldName]
                if 0 <= self.CurrentRoute.get():
                    if OldName == self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label'):
                        self.RouteMenu.entryconfig(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), label=NewName)
                self.MainCanvas.addtag_withtag(RouteBuilderApp.TypeNameToTag('route', NewName), RouteBuilderApp.TypeNameToTag('route', OldName))    
                self.RemoveTagFromItems(RouteBuilderApp.TypeNameToTag('route', OldName) )
                self.UpdateRouteMenu()
                self.ChangesMade = True
            
        
    def RouteChangeBus(self):
        RouteValues = []
        for RouteName in self.LocalBusRoutes:
            RouteValues.append(RouteName)
        if 0 == len(RouteValues):
            tkinter.messagebox.showerror("Change Bus Error", "No routes to change bus for!")
            return
        if 0 <= self.CurrentRoute.get():
            RouteValues.insert(0, self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label'))
        else:
            RouteValues.insert(0, RouteValues[-1])
            
        TempDialog = MultipleInputDialog(self.TkMaster, title="Change Bus", labeltexts=["Route Name:"], valueinits=[RouteValues])
        if TempDialog.result:
            RouteName = TempDialog.result[0]
            BusValues = []
            for Vehicle in self.AllVehicleNames:
                Capacity = self.AllVehicles.GetParameter(Vehicle,'Capacity')
                if Capacity:
                    if int(Capacity) >  10:
                        BusValues.append(Vehicle)   
            BusValues.insert(0, self.LocalBusRoutes[RouteName].BusType)
            TempDialog = MultipleInputDialog(self.TkMaster, title="Change Bus for " + RouteName, labeltexts=["Bus Type:"], valueinits=[BusValues])
            if TempDialog.result:
                self.LocalBusRoutes[RouteName].BusType = TempDialog.result[0]
                self.ChangesMade = True
            
    def RouteSelectRoute(self):
        self.ModeBusRoutes()
        self.HighlightRoute()
            
    def CanvasResize(self, event):                
        self.RedrawMap(event.width, event.height)
        self.RedrawButtons()
        self.HighlightRoute()
            
    def CanvasLeftMousePress(self, event):
        if event.x >= self.ButtonLeftOffset and event.y >= self.ButtonTopOffset and event.y < self.ButtonBottomOffset:
            ButtonIndex = int((event.y -self.ButtonTopOffset)/self.SelectPhoto.height())
            if ButtonIndex < 3:
                for Borders in self.MainCanvas.find_withtag('buttonborder'):
                    self.MainCanvas.itemconfig(Borders, outline='')  
            if ButtonIndex == 0:
                self.CurrentSubMode = 'select'
                for Borders in self.MainCanvas.find_withtag('selectborder'):
                    self.MainCanvas.itemconfig(Borders, outline=self.SelectedButtonOutlineColor)
            elif ButtonIndex == 1:
                self.CurrentSubMode = 'add'
                for Borders in self.MainCanvas.find_withtag('addborder'):
                    self.MainCanvas.itemconfig(Borders, outline=self.SelectedButtonOutlineColor)
            elif ButtonIndex == 2:
                self.CurrentSubMode = 'remove'
                for Borders in self.MainCanvas.find_withtag('removeborder'):
                    self.MainCanvas.itemconfig(Borders, outline=self.SelectedButtonOutlineColor)
            elif ButtonIndex == 3:
                RouteName = self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label')
                RouteStartTimeCopy = self.LocalBusRoutes[RouteName].RouteStartTimes[:]
                StopNames = ['Station']
                for Name in self.LocalBusRoutes[RouteName].RoutePath:
                    StopNames.append(Name)
                StopNames.append('Station')
                StopTimes = []
                ChangesMadeCopy = self.ChangesMade
                for CurRouteTimes in self.LocalBusRoutes[RouteName].RouteTimes:
                    StopTimes.append([])
                    for StopTime in CurRouteTimes:
                        StopTimes[-1].append(ConvertSecondsToTime(StopTime))
                        
                def RemoveTimeCallback(dialog=None, values=[]):
                    if len(values):
                        StartTimeSec = ConvertTimeToSeconds(values[0])
                        if StartTimeSec in self.LocalBusRoutes[RouteName].RouteStartTimes:
                            self.LocalBusRoutes[RouteName].RemoveStartTime(StartTimeSec)
                            self.ChangesMade = True
                            
                def AddTimeCallback(dialog=None):
                    def StartTimeValidate(timestr):
                        StartTimeSec = ConvertTimeToSeconds(timestr)
                        if(0 > StartTimeSec):
                            return 0
                        elif(21600 > StartTimeSec) or (72000 < StartTimeSec):
                            return 0
                        elif StartTimeSec in self.LocalBusRoutes[RouteName].RouteStartTimes:
                            return 0
                        return 1
                    if len (self.LocalBusRoutes[RouteName].RouteStartTimes):
                        InitialEntryTime = max(self.LocalBusRoutes[RouteName].RouteStartTimes)
                    else:
                        InitialEntryTime = 21600
                    InitialEntryTime += 3600
                    TempDialog = SingleEntryDialog(self.TkMaster, title = "Add Start Time", labeltext="Start Time (24hr HH:MM):", entryinit=ConvertSecondsToTime(InitialEntryTime), validatefun=StartTimeValidate)
                    if TempDialog.result:
                        StartTimeSec = ConvertTimeToSeconds(TempDialog.result)
                        if self.LocalBusRoutes[RouteName].AddStartTime(StartTimeSec):
                           NewIndex = self.LocalBusRoutes[RouteName].RouteStartTimes.index(StartTimeSec)
                           NewStopTimes = []
                           for StopTime in self.LocalBusRoutes[RouteName].RouteTimes[NewIndex]:
                               NewStopTimes.append(ConvertSecondsToTime(StopTime))
                           dialog.InsertRow(NewIndex, NewStopTimes)
                           self.ChangesMade = True
                
                TempDialog = AddRemoveGridDialog(self.TkMaster, title="Route Times", headings=StopNames, valueinits=StopTimes, validatefun=None, removefun=RemoveTimeCallback, addfun=AddTimeCallback, removeimage=self.RemovePhoto, addimage=self.PlusPhoto)
                if not TempDialog.result:
                    NewStartTimes = self.LocalBusRoutes[RouteName].RouteStartTimes[:]
                    for StartTime in NewStartTimes:
                        if StartTime not in RouteStartTimeCopy:
                            self.LocalBusRoutes[RouteName].RemoveStartTime(StartTime)
                    for StartTime in RouteStartTimeCopy:
                        if StartTime not in NewStartTimes:
                            self.LocalBusRoutes[RouteName].AddStartTime(StartTime)
                    self.ChangesMade = ChangesMadeCopy
            self.MainCanvas.update_idletasks()
        elif event.x >= self.MapBorderWidth and event.x < self.ButtonLeftOffset and event.y >= self.MapBorderWidth and event.y < self.MainCanvasHeight - self.MapBorderWidth:
            self.ModeLeftMousePress(event)
        
    def CanvasLeftMouseRelease(self, event):
        self.ModeLeftMouseRelease(event)

    def CanvasMouseEnter(self, event):
        self.ModeMouseEnter(event)

    def CanvasMouseMotion(self, event):
        if event.x >= self.MapBorderWidth and event.x < self.ButtonLeftOffset and event.y >= self.MapBorderWidth and event.y < self.MainCanvasHeight - self.MapBorderWidth:
            self.ModeMouseMotion(event)
        else:
            self.TkMaster.config(cursor='')
        

    def CanvasMouseLeave(self, event):
        self.ModeMouseLeave(event)

    def CanvasLeftMouseDrag(self, event):
        self.ModeLeftMouseDrag(event)

    def BusStopModeLeftMousePress(self, event):
        if self.CurrentSubMode == 'remove':
            Item = self.FindClosestItemWithTag('stop', event.x, event.y)
            if Item:
                ItemTypeName = self.GetItemTypeAndName(Item)
                if self.SimConfig.BusStation() != ItemTypeName[1]:
                    WantToRemove = tkinter.messagebox.askyesno("Remove Stop", "Do you want to remove stop " + ItemTypeName[1] + "?")
                    if WantToRemove:
                        PartOfRoute = False
                        for CurBusRoute in self.LocalBusRoutes:
                            if ItemTypeName[1] in self.LocalBusRoutes[CurBusRoute].RoutePath:
                                PartOfRoute = True
                                break
                        if PartOfRoute:
                            tkinter.messagebox.showerror("Remove Stop Error", "Remove the stop from the route(s) before removing stop.")
                        elif self.LocalBusStops.RemoveStop(ItemTypeName[1]):
                            self.RefreshMap()
                            self.ChangesMade = True
                        else:
                            tkinter.messagebox.showerror("Remove Stop Error", "Failed to remove stop "+ ItemTypeName[1] + "!")
                        
                else:
                    tkinter.messagebox.showerror("Remove Stop Error", "Can't remove the main bus station.")
            else:
                self.CurrentStatusText.set('')
        elif self.CurrentSubMode == 'add':
            MapLocation = self.CanvasToMapXY(event.x, event.y)
            LocationData = self.LocalStreetMap.FindNearestStreetLocation(MapLocation[0], MapLocation[1])
            StopNumber = 1
            while "S"+str(StopNumber) in self.LocalBusStops.StopNames:
                StopNumber += 1
            
            UpdateText = "Add stop on " + LocationData[0] + " " + str(int(LocationData[3]*100)) +"% between " + LocationData[1] + " and " + LocationData[2] + "?"
            def StopNameValidate(name):
                return 0 if name in self.LocalBusStops.StopNames else 1
                
            TempDialog = SingleEntryDialog(self.TkMaster, title = UpdateText, labeltext="Stop Name:", entryinit="S" + str(StopNumber), validatefun=StopNameValidate)
            if TempDialog.result:
                if self.LocalBusStops.AddStop(TempDialog.result, LocationData[0], LocationData[1], LocationData[2], LocationData[3]):
                    self.RefreshMap()
                    self.ChangesMade = True
                else:
                    tkinter.messagebox.showerror("Add Stop Error", "Failed to add stop "+ ItemTypeName[1] + "!")

    
    def BusStopModeLeftMouseRelease(self, event):
        pass
        
    def BusStopModeMouseEnter(self, event):
        pass
    
    def BusStopModeMouseMotion(self, event):
        if self.CurrentSubMode == 'select' or self.CurrentSubMode == 'remove':
            Item = self.FindClosestItemWithTag('stop', event.x, event.y)
            if Item:
                ItemTypeName = self.GetItemTypeAndName(Item)
                self.CurrentStatusText.set(ItemTypeName[1])
                self.TkMaster.config(cursor='X_cursor' if self.CurrentSubMode == 'remove' else "")
            else:
                self.TkMaster.config(cursor="")
                self.CurrentStatusText.set('')
        elif self.CurrentSubMode == 'add':
            self.TkMaster.config(cursor="dot" if self.FindClosestItemWithTag('street', event.x, event.y) else "")
            MapLocation = self.CanvasToMapXY(event.x, event.y)
            LocationData = self.LocalStreetMap.FindNearestStreetLocation(MapLocation[0], MapLocation[1])
            UpdateText = "On " + LocationData[0] + " " + str(int(LocationData[3]*100)) +"% between " + LocationData[1] + " and " + LocationData[2]
            self.CurrentStatusText.set(UpdateText)
            
                
    def BusStopModeMouseLeave(self, event):
        pass
    
    def BusStopModeMouseDrag(self, event):
        pass

    def BusRouteModeLeftMousePress(self, event):
        if self.CurrentSubMode == 'remove':
            Item = self.FindClosestItemWithTag('stop', event.x, event.y)
            if Item:
                ItemTypeName = self.GetItemTypeAndName(Item)
                StopName = ItemTypeName[1]
                RouteName = self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label')
                if self.SimConfig.BusStation() != StopName:
                    if StopName in self.LocalBusRoutes[RouteName].RoutePath:
                        WantToRemove = tkinter.messagebox.askyesno("Remove Stop", "Do you want to remove stop " + StopName + " from route " + RouteName + "?")
                        if WantToRemove:
                            if self.LocalBusRoutes[RouteName].RemoveStop(StopName):
                                self.RefreshMap()
                                self.HighlightRoute()
                                self.CurrentStatusText.set('')
                                self.ChangesMade = True
                            else:
                                tkinter.messagebox.showerror("Remove Stop Error", "Failed to remove stop "+ StopName + " from route " + RouteName + "!")        
                else:
                    tkinter.messagebox.showerror("Remove Stop Error", "Can't remove the main bus station.")
            else:
                self.CurrentStatusText.set('')
        elif self.CurrentSubMode == 'add':
            Item = self.FindClosestItemWithTag('stop', event.x, event.y)
            if Item:
                ItemTypeName = self.GetItemTypeAndName(Item)
                StopName = ItemTypeName[1]
                RouteName = self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label')
                if self.SimConfig.BusStation() != StopName:
                    if StopName in self.LocalBusRoutes[RouteName].RoutePath:
                        if self.LocalBusRoutes[RouteName].RoutePath[-1] == StopName:
                            tkinter.messagebox.showerror("Add Stop Error", "Cannot add stop twice in a row!")        
                            return
                        else:
                            WantToAdd = tkinter.messagebox.askyesno("Add Stop", "Do you really want to add " + StopName + " to route " + RouteName + " again?")
                            if not WantToAdd:
                                return
                    if self.LocalBusRoutes[RouteName].AddStop(StopName):
                        self.RefreshMap()
                        self.HighlightRoute()
                        self.CurrentStatusText.set('')
                        self.ChangesMade = True
                    else:
                        tkinter.messagebox.showerror("Add Stop Error", "Failed to add stop "+ StopName + " from route " + RouteName + "!")
                else:
                    tkinter.messagebox.showerror("Add Stop Error", "Can't add the main bus station.")
            else:
                self.CurrentStatusText.set('')
    def BusRouteModeLeftMouseRelease(self, event):
        pass
        
    def BusRouteModeMouseEnter(self, event):
        pass
    
    def BusRouteModeMouseMotion(self, event):
        Item = self.FindClosestItemWithTag('stop', event.x, event.y)
        if Item:
            ItemTypeName = self.GetItemTypeAndName(Item)
            StopName = ItemTypeName[1]
            RouteName = self.RouteMenu.entrycget(self.RouteMenuFirstRouteIndex + self.CurrentRoute.get(), 'label')
            if StopName in self.LocalBusRoutes[RouteName].RoutePath or StopName == self.SimConfig.BusStation():
                StopIndices = []
                if StopName == self.SimConfig.BusStation():
                    StopIndices.append(0)
                for Index in range(0, len(self.LocalBusRoutes[RouteName].RoutePath)):
                    if self.LocalBusRoutes[RouteName].RoutePath[Index] == StopName:
                        StopIndices.append(Index+1)
                StopTimes = []
                for CurRouteTimes in self.LocalBusRoutes[RouteName].RouteTimes:
                    for Index in StopIndices:
                        StopTimes.append(ConvertSecondsToTime(CurRouteTimes[Index]))
                StopTimes.sort()
                UpdateString = StopName + ": "
                if len(StopTimes):
                    UpdateString += StopTimes[0]
                    for StopTime in StopTimes[1:]:
                        UpdateString += ", " + StopTime
                self.TkMaster.config(cursor='X_cursor' if self.CurrentSubMode == 'remove' else '')
            else:
                UpdateString = StopName
                self.TkMaster.config(cursor='plus' if self.CurrentSubMode == 'add' else '')

            self.CurrentStatusText.set(UpdateString)
        else:
            self.TkMaster.config(cursor='')
            self.CurrentStatusText.set('')
    
    def BusRouteModeMouseLeave(self, event):
        pass
    
    def BusRouteModeMouseDrag(self, event):
        pass

    def BikePathModeLeftMousePress(self, event):
        if self.CurrentSubMode == 'remove':
            Item = self.FindClosestItemWithTag('path', event.x, event.y)
            if Item:
                ItemTypeName = self.GetItemTypeAndName(Item)
                if self.LocalBikePaths.RemoveEdge(ItemTypeName[1]):
                    self.RefreshMap()
                    self.ChangesMade = True
                else:
                    tkinter.messagebox.showerror("Remove Path Error", "Can't remove the path because it has other dependent paths.")
            else:
                self.CurrentStatusText.set('')
        elif self.CurrentSubMode == 'add':
            DXY = self.MapPointSearchDelta / self.MapScaling
            Coord = self.CanvasToMapXY(event.x, event.y)
            if 0 > Coord[0] or 0 > Coord[1] or self.LocalStreetMap.MaxX < Coord[0] or self.LocalStreetMap.MaxY < Coord[1]:
                self.BikePathAnchor = None
                return
                
            AnchorPoint = self.LocalBikePaths.FindNearestPointInArea(Coord[0], Coord[1], DXY, DXY)
            if len(AnchorPoint):
                self.BikePathAnchor = AnchorPoint 
            else:
                AnchorPoint = self.LocalBikePaths.FindNearestEdgeLocationInArea(Coord[0], Coord[1], DXY)
                if len(AnchorPoint[0]):
                    self.BikePathAnchor = AnchorPoint
                else:
                    
                    self.BikePathAnchor = Coord
            
    
    def BikePathModeLeftMouseRelease(self, event):
        if self.CurrentSubMode == 'add':
            DXY = self.MapPointSearchDelta / self.MapScaling
            Coord = self.CanvasToMapXY(event.x, event.y)
            if 0 > Coord[0] or 0 > Coord[1] or self.LocalStreetMap.MaxX < Coord[0] or self.LocalStreetMap.MaxY < Coord[1]:
                self.BikePathAnchor = None
                return
                
            
            SecondAnchorPoint = self.LocalBikePaths.FindNearestPointInArea(Coord[0], Coord[1], DXY, DXY)
            if len(SecondAnchorPoint):
                # Point Exists
                Point2 = SecondAnchorPoint
            else:
                SecondAnchorPoint = self.LocalBikePaths.FindNearestEdgeLocationInArea(Coord[0], Coord[1], DXY)
                if len(SecondAnchorPoint[0]):
                    # Point on edge
                    Point2 = self.LocalBikePaths.AddPointOnEdge(SecondAnchorPoint[0], SecondAnchorPoint[1], SecondAnchorPoint[2])
                else:
                    # Free point
                    Point2 = self.LocalBikePaths.AddPointXY(Coord[0], Coord[1])
            if isinstance(self.BikePathAnchor, str):
                # Point Exists
                Point1 = self.BikePathAnchor
            elif 3 == len(self.BikePathAnchor):
                # Point on edge
                Point1 = self.LocalBikePaths.AddPointOnEdge(self.BikePathAnchor[0], self.BikePathAnchor[1], self.BikePathAnchor[2])
            else:
                # Free point
                Point1 = self.LocalBikePaths.AddPointXY(self.BikePathAnchor[0], self.BikePathAnchor[1])
            if len(self.LocalBikePaths.AddEdge(Point1, Point2)):
                self.TkMaster.config(cursor='target')
                self.MainCanvas.config(cursor='')
                self.RefreshMap()
                self.ChangesMade = True
                self.TkMaster.update()
                
            else:
                self.TkMaster.config(cursor='plus')    
                self.RemoveBikePathDrag()
                

        
    def BikePathModeMouseEnter(self, event):
        pass
    
    def BikePathModeMouseMotion(self, event):
        if self.CurrentSubMode == 'remove':
            self.TkMaster.config(cursor='X_cursor' if self.FindClosestItemWithTag('path', event.x, event.y) else '')
            self.CurrentStatusText.set('')
        elif self.CurrentSubMode == 'add':
            DXY = self.MapPointSearchDelta / self.MapScaling
            Coord = self.CanvasToMapXY(event.x, event.y)
            self.TkMaster.config(cursor='plus' if 0 == len(self.LocalBikePaths.FindNearestPointInArea(Coord[0], Coord[1], DXY, DXY)) else 'target' )
            self.CurrentStatusText.set('')
        else:
            Coord = self.CanvasToMapXY(event.x, event.y)
            self.CurrentStatusText.set('(' + str(Coord[0]) + ', ' + str(Coord[1]) + ')')
    
    def BikePathModeMouseLeave(self, event):
        pass
    
    def BikePathModeMouseDrag(self, event):
        if self.CurrentSubMode == 'add':
            DXY = self.MapPointSearchDelta / self.MapScaling
            Coord = self.CanvasToMapXY(event.x, event.y)
            self.TkMaster.config(cursor='dotbox' if 0 == len(self.LocalBikePaths.FindNearestPointInArea(Coord[0], Coord[1], DXY, DXY)) else 'target')
            self.DrawBikePathDrag(event.x, event.y)
        else:
            self.TkMaster.config(cursor='')

def main():
    MainTkWindow = Tk()
    
    MainApp = RouteBuilderApp(MainTkWindow)
    
    MainTkWindow.mainloop()
    #MainTkWindow.destroy()

main()