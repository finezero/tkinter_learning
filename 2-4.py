# coding:utf-8

import tkinter as tk
import tkinter.messagebox as msg
import os
import sqlite3

class Todo(tk.Tk):
    def __init__(self, tasks=None, finished_tasks=None):
        super().__init__()
        
        if not tasks:
            self.tasks = []
        else:
            self.tasks = tasks
            
        if not finished_tasks:
            self.finished_tasks = []
        else:
            self.finished_tasks = finished_tasks
            
        self.title('To-Do App v3')
        self.geometry('300x400')
        
        self.tasks_canvas = tk.Canvas(self)
        
        self.tasks_frame = tk.Frame(self.tasks_canvas)
        self.finished_tasks_frame = tk.Frame(self.tasks_frame)
        self.text_frame = tk.Frame(self)
        
        self.scrollbar = tk.Scrollbar(self.tasks_canvas, orient='vertical',
            command=self.tasks_canvas.yview)
        
        self.tasks_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.task_create = tk.Text(self.text_frame, height=3, bg='white', fg='black')
        
        self.tasks_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas_frame = self.tasks_canvas.create_window((0, 0), 
            window=self.tasks_frame, anchor='n')
        
        self.task_create.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.task_create.focus_set()
        
        finished_task = tk.Label(self.finished_tasks_frame, text='--- Here Are Finished Tasks ---',
                         bg='lightgrey', fg='black', pady=10)
        self.finished_tasks.append(finished_task)
        
        for task in self.tasks:
            task.pack(side=tk.TOP, fill=tk.X)
        
        self.bind('<Return>', self.add_task)
        self.bind('<Configure>', self.on_frame_configure)
        self.bind_all('<MouseWheel>', self.mouse_scroll)
        self.bind_all('<Button-4>', self.mouse_scroll)
        self.bind_all('<Button-5>', self.mouse_scroll)
        self.tasks_canvas.bind('<Configure>', self.task_width)
        
        self.colour_schemes = [{'bg':'lightgrey', 'fg':'black'},
                               {'bg':'grey', 'fg':'white'}]
        
        current_tasks = self.load_tasks()
        for task in current_tasks:
            task_text = task[0]
            self.add_task(None, task_text, True)
            
        finished_tasks = self.load_finished_tasks()
        for task in finished_tasks:
            self.view_finished_tasks(task)
        
    def add_task(self, event=None, task_text=None, from_db=False):
        if not task_text:
            task_text = self.task_create.get(1.0, tk.END).strip()
            if self.is_task_exist(task_text):
                msg.showwarning(task_text+' is Existed',
                                task_text+' is Existed, please try again?')
                self.task_create.delete(1.0, tk.END)
                return None            
        
        if len(task_text) > 0:
            new_task = tk.Label(self.tasks_frame, text=task_text, pady=10)
            delete_button = tk.Button(new_task, text='Delete', padx=20, pady=10,
                                      command=lambda:self.remove_task(new_task))
            delete_button.pack(side=tk.RIGHT)
            
            self.set_task_colour(len(self.tasks), new_task)
            
            new_task.pack(side=tk.TOP, fill=tk.X)
            
            self.tasks.append(new_task)
            
            if not from_db:
                self.save_task(task_text)
        
        self.task_create.delete(1.0, tk.END)
        
    def view_finished_tasks(self, task):
        old_task = tk.Label(self.finished_tasks_frame, text=task, pady=10)
        finished_button = tk.Button(old_task, text='Finished', state='disable',
                                    padx=20, pady=10)
        finished_button.pack(side=tk.RIGHT)
        
        self.set_task_colour(len(self.finished_tasks), old_task)
        old_task.pack(side=tk.TOP, fill=tk.X)
        
        self.finished_tasks.append(old_task)
        
    
    def is_task_exist(self, task=None):
        task_exist_query = 'SELECT * FROM tasks WHERE task=?'
        task_exist_data = (task,)
        exist_result = self.runQuery(task_exist_query, task_exist_data, receive=True)
        if exist_result:
            return exist_result
        else:
            return None
        
    def remove_task(self, task):
        if msg.askyesno('Really Delete?', 'Delete' + task.cget('text') + '?'):
            for delete_button in task.winfo_children():
                delete_button.configure(state='disable', text='Finished')            
            self.tasks.remove(task)
            self.finished_tasks.append(task)
            
            delete_task_query = 'DELETE FROM tasks WHERE task=?'
            delete_task_data = (task.cget('text'),)
            self.runQuery(delete_task_query, delete_task_data)
            finished_task_query = 'INSERT INTO finished VALUES (?)'
            self.runQuery(finished_task_query, delete_task_data)
            
            task.configure(bg='red')
            #task.destroy()
            self.recolour_tasks()
    
    def save_task(self, task):
        insert_task_query = 'INSERT INTO tasks VALUES (?)'
        insert_task_data = (task,)
        self.runQuery(insert_task_query, insert_task_data)
        
    def load_tasks(self):
        load_tasks_query = 'SELECT task FROM tasks'
        my_tasks = self.runQuery(load_tasks_query, receive=True)        
        return my_tasks
    
    def load_finished_tasks(self):
        load_finished_tasks_query = 'SELECT task FROM finished'
        finished_tasks = self.runQuery(load_finished_tasks_query, receive=True)
        return finished_tasks
    
    def recolour_tasks(self):
        for index, task in enumerate(self.tasks):
            self.set_task_colour(index, task)
            
    def set_task_colour(self, position, task):
        _, task_style_choice = divmod(position, 2)
        
        my_scheme_choice = self.colour_schemes[task_style_choice]
        
        task.configure(bg=my_scheme_choice['bg'])
        task.configure(fg=my_scheme_choice['fg'])
        
    def on_frame_configure(self, event=None):
        self.tasks_canvas.configure(scrollregion=self.tasks_canvas.bbox('all'))
        
    def task_width(self, event):
        canvas_width = event.width
        self.tasks_canvas.itemconfig(self.canvas_frame, width=canvas_width)
        
    def mouse_scroll(self, event):
        if event.delta:
            self.tasks_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
        else:
            if event.num == 5:
                move = 1
            else:
                move = -1
                
            self.tasks_canvas.yview_scroll(move, 'units')
            
    @staticmethod
    def firstTimeDB():
        create_tables = 'CREATE TABLE tasks (task TEXT)'
        Todo.runQuery(create_tables)
        create_tables = 'CREATE TABLE finished (task TEXT)'
        Todo.runQuery(create_tables)        
        
        default_task_query = 'INSERT INTO tasks VALUES (?)'
        default_task_data = ('--- Add Items Here ---', )
        Todo.runQuery(default_task_query, default_task_data)
        
    @staticmethod
    def runQuery(sql, data=None, receive=False):
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        if data:
            cursor.execute(sql, data)
        else:
            cursor.execute(sql)
        
        if receive:
            return cursor.fetchall()
        else:
            conn.commit()
        
        conn.close()
        
if __name__ == '__main__':
    if not os.path.isfile('tasks.db'):
        Todo.firstTimeDB()
    todo = Todo()
    todo.mainloop()