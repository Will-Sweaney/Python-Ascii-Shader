import tkinter as tk,subprocess,tempfile,threading,os
from tkinter import filedialog
from tkinter import ttk
from moviepy.editor import VideoFileClip

def selectMP4():
    root = tk.Tk()
    root.withdraw()
    root.iconbitmap('./MP42ASCII.ico')

    path = filedialog.askopenfilename(
        title="Select a Video",
        filetypes=(("MP4 files", "*.mp4"), ("All files", "*.*"))
    )
    
    return path

def selectAscii():
    root = tk.Tk()
    root.withdraw()
    root.iconbitmap('./MP42ASCII.ico')

    path = filedialog.askopenfilename(
        title="Select An Ascii File",
        filetypes=(("Ascii files", "*.ascii"), ("All files", "*.*"))
    )
    
    return path

def runScriptWithArgs(progressVar, selectedPath):
    process = subprocess.Popen(f'py ./src/videoEncode.py "{selectedPath}"', stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    print("INFO: | Extracting Audio...")
    
    video = VideoFileClip(selectedPath)
    tmp=tempfile.gettempdir()
    audio = video.audio

    print("INFO: | Saving Audio...")
    try:
        audio.write_audiofile(f'{tmp}\\{selectedPath[:-3].rsplit("/", 1)[-1]}mp3')
        audio.close()
    except:
        print("WARN: | Failed to load audio. Does this video have audio?")
    video.close()

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"INFO: | {output.strip()}")
            if "%" in output:
                try:
                    parts = output.split('|')
                    for part in parts:
                        if '%' in part:
                            percentageStr = part.strip().split('%')[0]
                            progressPercentage = float(percentageStr.strip())
                            progressVar.set(progressPercentage)
                            break
                except ValueError:
                    pass

    while True:
        error = process.stderr.readline()
        if error == '' and process.poll() is not None:
            break
        if error:
            print(f"ERROR: | {error.strip()}")

    return process.poll()

class home():
    def __init__(self):
        self.root = tk.Tk()

        self.root.iconbitmap('./MP42ASCII.ico')
        self.root.geometry('1280x720')
        self.root.title('MP42ASCII')
        self.mainframe = tk.Frame(self.root,background='#213538')

        self.mainframe.pack(fill='both', expand=True)

        self.text = ttk.Label(self.mainframe, text='MP42ASCII',background='#743f2c', font=("Calibri", 40))
        self.text.grid(row=0, column=0)

        startButton = ttk.Button(self.mainframe, text='Start', command=self.start)
        startButton.grid(row=1,column=1,pady=10)

        dropdownList = ['Convert to Ascii', 'Play Ascii File']
        self.startOption = ttk.Combobox(self.mainframe, values=dropdownList)
        self.startOption.grid(row=1, column=0, sticky='NWES', pady=10)

        self.root.mainloop()
    
    def start(self):
        selectedOption = self.startOption.get()
        
        if selectedOption == 'Convert to Ascii':
            selectedPath = selectMP4()
            if selectedPath:
                if not hasattr(self, 'progressVar'):
                    self.progressVar = tk.DoubleVar()
                    self.progressBar = ttk.Progressbar(self.root, orient="horizontal", length=1000, mode="determinate", variable=self.progressVar)
                    self.progressBar.pack(pady=20)
                
                threading.Thread(target=self.runScript, args=(self.progressVar, selectedPath)).start()
        
        elif selectedOption == 'Play Ascii File':
            asciiPath = selectAscii()
            if asciiPath:
                command = f'py ./src/videoDecode.py "{asciiPath}"'
                os.system(f'cmd /c start cmd /k {command}')



    def runScript(self, progressVar, selectedPath):
        runScriptWithArgs(progressVar, selectedPath)

if __name__ == '__main__':
    home()
