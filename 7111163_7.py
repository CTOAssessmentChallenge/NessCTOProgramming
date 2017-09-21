# module imports
import textwrap
import Tkinter
import tkMessageBox
import os
import pytesseract
import textract
import shutil
import distutils.dir_util
from PyPDF2 import PdfFileWriter, PdfFileReader
from docx import Document
from Tkinter import *
from tkFileDialog import *
from functools import partial
from PIL import Image


# Global Variables
global mainFolder
global OutputText
global tempFolder
global indxFolder


# Function Name : Help
# Description   : It shows the steps to use this uuse this utility.
# Return Value  : If success return 0.
def Help():
    tkMessageBox.showinfo("How To Use", "Below are the steps:\n  \
                          1. Enter the string to be searched.\n  \
                          2. Click on '...' button to browse for Resume Repository folder.\n  \
                          3. Click on 'Search' button to find the list of searched resumes.")


# Function Name : CheckBoxProcess
# Description   : Processing of check box. 
# Return Value  : If success return 0.
def CheckBoxProcess(IngestInput, checkCmd):
    if checkCmd.get() == 1:
        IngestInput.config(state='normal')
    else:
        IngestInput.config(state='disabled')
        


# Function Name : CreateIndexFile
# Description   : If index file is not present or modified date is different, then create
#                 index file.
# Return Value  : If success return 0.
def CreateIndexFile(fileName):
    global indxFolder
    baseFileName = os.path.splitext(fileName)[0]
    baseFileNameWithoutPath= os.path.splitext(os.path.basename(fileName))[0]
    fileExt = os.path.splitext(fileName)[1][1:]
    fileModifiedTime = os.path.getmtime(fileName)
    fileModifiedTime = str(fileModifiedTime)
    IndexModifiedDate = ""
    textData = ""

    current_directory = os.getcwd()
    index_directory = os.path.join(current_directory, indxFolder)
    if not os.path.exists(index_directory):
        os.makedirs(index_directory)

    indexFileName = os.path.join(index_directory, baseFileNameWithoutPath)
    #indexFileName = index_directory + "\\"+ baseFileNameWithoutPath +"_" + fileExt + ".idx"
    indexFileName = indexFileName +"_" + fileExt + ".idx"
    indexFilePresent = os.path.exists(indexFileName)
    if indexFilePresent == True:
        indexFile = open(indexFileName, 'r')
        IndexModifiedDate = indexFile.readline()
        IndexModifiedDate = IndexModifiedDate[:-1]
        indexFile.close()
        if fileModifiedTime == IndexModifiedDate :
            return False
        else:
            os.remove(indexFileName)

    # Todo: "PDF" & other formats are missed in below conditions.
    if (fileExt.lower() == "docx") or (fileExt.lower() == "doc"):
        textData = textract.process(fileName)
    elif fileExt.lower() == "jpg":
        textData = pytesseract.image_to_string(Image.open(fileName))
    elif fileExt.lower() == "pdf":
        textData = textract.process(fileName, method='pdfminer')        
    else:
        return False
    
    indexFile = open(indexFileName, 'w')
    indexFile.write(fileModifiedTime + '\n')
    indexFile.write(textData)
    indexFile.close()
    return indexFileName


# Function Name : FolderPicker
# Description   : Gets the folder from user
# Return Value  : None.
def FolderPicker(label , entryText):
        global mainFolder
        dir_opt = {}
        dir_opt['initialdir'] = os.environ["HOME"] #+ '\\'
        dir_opt['mustexist'] = False
        dir_opt['title'] = 'Please select directory'
        mainFolder = askdirectory(**dir_opt)
        #label.insert(END,mainFolder)
        entryText.set(mainFolder)


# Function Name : FolderIteration
# Description   : Iterates through all the files from mainFolder
# Return Value  : None.
def FolderIteration(InputField,label, checkCmd, IngestInput):
    file_paths = []  # List which will store all of the full filepaths.
    global mainFolder
    global OutputText
    global tempFolder
    global indxFolder
    
    fileExt = "temp"

    OutputText.delete('1.0', END)

    ingestInputData = IngestInput.get()
    # Validity check of input paths
    if checkCmd.get() == 1:
        if not os.access(ingestInputData, os.W_OK):
            tkMessageBox.showinfo("Invalid Path", "Shared Path is invalid!")
            return
    if not os.access(label.get(), os.W_OK):
        tkMessageBox.showinfo("Invalid Path", "Resume Directory Path is invalid!")
        return
    if len(InputField.get()) == 0:
        tkMessageBox.showinfo("Invalid Path", "Text Field is empty!")
        return
    
    
    current_directory = os.getcwd()
    temp_directory = os.path.join(current_directory, tempFolder)


    if checkCmd.get() == 1:
        src = (ingestInputData) # r
        dst = (label.get("1.0",'end-1c'))
        dst = os.path.join(dst, tempFolder)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src,dst)        
    
    print("Searching for below Text:")
    print(InputField.get())
    mainFolder = label.get()#("1.0",'end-1c')

    if os.path.exists(temp_directory):
        shutil.rmtree(temp_directory)
  
    SearchString = InputField.get()
    # Iterate through all files & sub directories
    for root, directories, files in os.walk(mainFolder):#mainFolder
        for filename in files:
            # Join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)  # Add it to the list.
            fileExt = os.path.splitext(filepath)[1][1:]
            fileExt = fileExt.lower()
            
            # ToDo: In below If condition , "PDF" & other formats needs to be added later
            if (fileExt== "docx") or (fileExt== "jpg") or (fileExt == "pdf") or (fileExt == "pdf"):
                fileCreated = CreateIndexFile(filepath)
                if fileCreated != False:
                    fileExt = "idx"
                    filepath = fileCreated                  
    
    for root, directories, files in os.walk(indxFolder):#mainFolder
        for filename in files:
            # Join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)  # Add it to the list.
            fileExt = os.path.splitext(filepath)[1][1:]
            fileExt = fileExt.lower()
            
            if fileExt == "idx":
                with open(filepath, 'r') as indexFileObj:
                    fileData=indexFileObj.read().replace('\n', ' ')
                if SearchString in fileData :
                    # Get the base file from idx file name
                    baseFileName = os.path.splitext(filepath)[0]
                    counter = 0
                    ExtBase = 0
                    for chars in baseFileName:
                        if chars == '_':
                            ExtBase = counter
                        counter = counter + 1
                    indexExt = baseFileName[(ExtBase+1):] # Getting Index from file name
                    baseFileName = baseFileName[:(ExtBase)] # Getting base file name from index file
                    baseFileName = baseFileName + "." + indexExt
                    baseFileName = os.path.join(mainFolder,os.path.basename(baseFileName))
                    #print(baseFileName)
                    OutputText.insert(END,baseFileName + "\n")

    if len(OutputText.get("1.0",END)) == 1:
        OutputText.insert(END,"No match found!!!")
        return                
    print("Search End here ...")




# Function Name : MainGUI
# Description   : Creates basic GUI for the program.
# Return Value  : None.
def MainGUI():
    global OutputText
    
    root = Tkinter.Tk()
    root.title("Resume Search Engine")
    root.minsize(width=400,height=80)
    
    menubar = Menu(root)
    filemenu = Menu(menubar, tearoff=0)
    #filemenu.add_command(label="Save Output")
    #filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=filemenu)
    Helpmenu = Menu(menubar, tearoff=0)
    Helpmenu.add_command(label="How To Use", command=Help)
    menubar.add_cascade(label="Help", menu=Helpmenu)
    root.config(menu=menubar)

    
    SearchLabel = Tkinter.Label(root, text="Please Enter Text To Search",relief=RIDGE,width=35)
    SearchLabel.grid(row=4,column=0,padx=10)
    InputField = Entry(root, width=42)    
    InputField.grid(row=4,column=1)

    IngestLabel = Tkinter.Label(root, text="Do you want to ingest from Shared Path?",relief=RIDGE,width=35)
    IngestLabel.grid(row=1,column=0,padx=10)
    IngestInput = Entry(root, width=42)
    IngestInput.grid(row=1,column=1)
    IngestInput.config(state='disabled')
    checkCmd = IntVar()
    checkCmd.set(0)
    CheckBoxProcessWithArgs = partial(CheckBoxProcess, IngestInput, checkCmd)
    CheckBox = Checkbutton(root,variable=checkCmd, onvalue=1, offvalue=0, text="Tick for ingest", command=CheckBoxProcessWithArgs)
    CheckBox.grid(row=1,column=2)

    IngestInfo = Tkinter.Label(root, text="Note : In case ingesting resumes from shared path, Resumes will be copied to 'Resume Directory Path' in Local system. \
                               \n Then text will be searched in 'Resume Directory Path'.", fg='green')
    IngestInfo.grid(row=2,columnspan=3,padx=10)
    
    PathLabel = Tkinter.Label(root, text="Resume Directory Path",relief=RIDGE,width=35)
    PathLabel.grid(row=3,column=0)
    entryText = Tkinter.StringVar()
    label = Entry(root,width=42,textvariable=entryText)#Text(root,width=38,height=1)
    label.grid(row=3,column=1)
    FolderPickerWithArgs = partial(FolderPicker, label, entryText)
    BrowseButton = Tkinter.Button(root,text='...', width=2,command=FolderPickerWithArgs)
    BrowseButton.grid(row=3,column=2)

    FolderIterationWithArgs = partial(FolderIteration, InputField, label, checkCmd, IngestInput)
    StartButton = Tkinter.Button(root,text='Search', width=6, command=FolderIterationWithArgs)
    StartButton.grid(row=5,column=1,pady=10)

    OutputText = Text(root,borderwidth=3,relief="sunken",wrap='word', height=10)# 
    OutputText.grid(row=6,columnspan=2,padx=10, sticky='nsew')#,column=1
    OutputTextScroll= Scrollbar(root,command=OutputText.yview)
    OutputTextScroll.grid(row=6,column=2, sticky='nsew')
    OutputText['yscrollcommand'] = OutputTextScroll.set


    root.mainloop()


# Main Program execution starts from here
tempFolder = r"Resume"
indxFolder = r"IndexFolder"
MainGUI()    

    



