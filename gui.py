from __future__ import annotations
import csv, threading, tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from realm_analyzer import analyze

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Realm Log Analyzer"); self.geometry("980x640"); self.minsize(780,500); self.build()
    def build(self):
        top=ttk.Frame(self,padding=12); top.pack(fill="x")
        ttk.Label(top,text="Realm Log Analyzer",font=("Segoe UI",16,"bold")).pack(anchor="w")
        ttk.Label(top,text="Parse supported player join/leave events and export CSV reports.").pack(anchor="w",pady=(2,8))
        row=ttk.Frame(top); row.pack(fill="x"); self.path=tk.StringVar()
        ttk.Entry(row,textvariable=self.path).pack(side="left",fill="x",expand=True)
        ttk.Button(row,text="Open log",command=self.choose).pack(side="left",padx=6)
        self.go=ttk.Button(row,text="Analyze",command=self.run); self.go.pack(side="left")
        self.status=tk.StringVar(value="Ready"); ttk.Label(top,textvariable=self.status).pack(anchor="w",pady=(8,0))
        tabs=ttk.Notebook(self); tabs.pack(fill="both",expand=True,padx=12,pady=(0,12))
        self.events=ttk.Treeview(tabs,columns=("time","player","event","line"),show="headings")
        self.sessions=ttk.Treeview(tabs,columns=("player","joined","left"),show="headings")
        for tree,cols in ((self.events,("time","player","event","line")),(self.sessions,("player","joined","left"))):
            for c in cols: tree.heading(c,text=c.title()); tree.column(c,width=180 if c!="player" else 260,anchor="w")
            tree.pack(fill="both",expand=True)
        tabs.add(self.events,text="Events"); tabs.add(self.sessions,text="Sessions")
        bottom=ttk.Frame(self,padding=12); bottom.pack(fill="x")
        self.summary=tk.StringVar(value="No analysis yet."); ttk.Label(bottom,textvariable=self.summary).pack(side="left")
        ttk.Button(bottom,text="Export CSVs",command=self.export).pack(side="right")
    def choose(self):
        p=filedialog.askopenfilename(filetypes=[("Log files","*.log *.txt"),("All files","*.*")])
        if p:self.path.set(p)
    def run(self):
        p=Path(self.path.get())
        if not p.is_file(): messagebox.showerror("Analyze","Choose a log file."); return
        self.go.configure(state="disabled"); self.status.set("Analyzing...")
        def work():
            try: data=analyze(p); err=None
            except Exception as e: data=None; err=str(e)
            self.after(0,lambda:self.finish(data,err))
        threading.Thread(target=work,daemon=True).start()
    def finish(self,data,err):
        self.go.configure(state="normal")
        if err: self.status.set("Failed"); messagebox.showerror("Analysis failed",err); return
        events,sessions,lines=data
        for tree in (self.events,self.sessions):
            for i in tree.get_children(): tree.delete(i)
        for e in events:self.events.insert("", "end", values=(e.timestamp,e.player,e.event,e.line_number))
        for s in sessions:self.sessions.insert("", "end", values=(s.player,s.joined,s.left or "OPEN"))
        self.last=data; self.summary.set(f"Read {lines} lines • {len(events)} events • {len(sessions)} sessions"); self.status.set("Complete")
    def export(self):
        if not hasattr(self,"last"): messagebox.showinfo("Export","Analyze a log first."); return
        folder=filedialog.askdirectory(title="Choose export folder")
        if not folder:return
        events,sessions,_=self.last; folder=Path(folder)
        with (folder/"events.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["timestamp","player","event","line"]); w.writerows([e.timestamp,e.player,e.event,e.line_number] for e in events)
        with (folder/"players.csv").open("w",newline="",encoding="utf-8") as f:
            from collections import Counter
            joins=Counter(e.player for e in events if e.event=="join"); dur=Counter(); opens=Counter()
            for s in sessions:
                if s.left: dur[s.player]+=max(0,int((s.left-s.joined).total_seconds()))
                else: opens[s.player]+=1
            names=sorted(set(joins)|set(dur)|set(opens),key=str.casefold)
            w=csv.writer(f); w.writerow(["player","joins","matched_play_seconds","open_sessions"])
            w.writerows([n,joins[n],dur[n],opens[n]] for n in names)
        self.status.set(f"Saved reports to {folder}")

if __name__=="__main__": App().mainloop()
