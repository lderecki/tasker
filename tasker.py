import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyautogui
import keyboard
import time
import threading
import csv
import random
import re
from pynput import mouse

class TaskerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tasker")
        self.tasks = []
        self.task_threads = []
        self.running = False
        self.global_lock = threading.Lock()

        self.randomize_time_var = tk.BooleanVar()
        self.delay_var = tk.IntVar()
        self.random_from_var = tk.IntVar()
        self.random_to_var = tk.IntVar()

        options_frame = tk.Frame(self.root)
        options_frame.pack(pady=10)

        self.randomize_checkbox = tk.Checkbutton(options_frame, text="Randomize Time", variable=self.randomize_time_var)
        self.randomize_checkbox.grid(row=0, column=0, padx=5)

        tk.Label(options_frame, text="From:").grid(row=0, column=1, padx=5)
        self.random_from_entry = tk.Entry(options_frame, textvariable=self.random_from_var, width=5)
        self.random_from_entry.grid(row=0, column=2, padx=5)

        tk.Label(options_frame, text="To:").grid(row=0, column=3, padx=5)
        self.random_to_entry = tk.Entry(options_frame, textvariable=self.random_to_var, width=5)
        self.random_to_entry.grid(row=0, column=4, padx=5)

        tk.Label(options_frame, text="Delay:").grid(row=0, column=5, padx=5)
        self.delay_entry = tk.Entry(options_frame, textvariable=self.delay_var, width=5)
        self.delay_entry.grid(row=0, column=6, padx=5)

        self.tree = ttk.Treeview(root, columns=("Type", "Interval", "Details"), show="headings")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Interval", text="Interval (s)")
        self.tree.heading("Details", text="Details")
        self.tree.pack(pady=10, fill="both", expand=True)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.add_task_button = tk.Button(button_frame, text="Add Task", command=self.add_task)
        self.add_task_button.grid(row=0, column=0, padx=5)

        self.delete_task_button = tk.Button(button_frame, text="Delete Task", command=self.delete_task)
        self.delete_task_button.grid(row=0, column=1, padx=5)

        self.start_button = tk.Button(button_frame, text="Start", command=self.start_tasks)
        self.start_button.grid(row=0, column=2, padx=5)

        self.stop_button = tk.Button(button_frame, text="Stop", command=self.stop_tasks, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=3, padx=5)

        self.save_button = tk.Button(button_frame, text="Save Tasks", command=self.save_tasks)
        self.save_button.grid(row=0, column=4, padx=5)

        self.load_button = tk.Button(button_frame, text="Load Tasks", command=self.load_tasks)
        self.load_button.grid(row=0, column=5, padx=5)

        keyboard.add_hotkey("ctrl+f12", self.stop_tasks)

    def add_task(self):
        new_task_window = tk.Toplevel(self.root)
        new_task_window.title("Add Task")

        tk.Label(new_task_window, text="Operation Type:").grid(row=0, column=0, padx=10, pady=5)
        operation_type = ttk.Combobox(new_task_window, values=["Click", "Drag and Drop", "Keyboard"])
        operation_type.grid(row=0, column=1, padx=10, pady=5)
        operation_type.bind("<<ComboboxSelected>>", lambda event: update_ui())

        tk.Label(new_task_window, text="Interval (s):").grid(row=1, column=0, padx=10, pady=5)
        interval_entry = tk.Entry(new_task_window)
        interval_entry.grid(row=1, column=1, padx=10, pady=5)

        coordinates_button1 = tk.Button(new_task_window, text="Select Coordinates", command=lambda: wait_for_click(coordinates_button1, new_task_window))
        coordinates_button2 = tk.Button(new_task_window, text="Select End Coordinates", command=lambda: wait_for_click(coordinates_button2, new_task_window))
        mouse_button_choice = ttk.Combobox(new_task_window, values=["Left", "Right", "Middle"])
        keyboard_button = tk.Entry(new_task_window)
        keyboard_label = tk.Label(new_task_window, text="Keyboard button:")

        def update_ui():
            selected = operation_type.get()
            coordinates_button1.grid_forget()
            coordinates_button2.grid_forget()
            mouse_button_choice.grid_forget()
            keyboard_button.grid_forget()
            keyboard_label.grid_forget()

            if selected == "Click":
                coordinates_button1.grid(row=2, column=0, columnspan=2, pady=5)
                mouse_button_choice.grid(row=3, column=0, columnspan=2, pady=5)
            elif selected == "Drag and Drop":
                coordinates_button1.grid(row=2, column=0, columnspan=2, pady=5)
                coordinates_button2.grid(row=3, column=0, columnspan=2, pady=5)
            elif selected == "Keyboard":
                keyboard_label.grid(row=2, column=0, padx=10, pady=5)
                keyboard_button.grid(row=2, column=1, padx=10, pady=5)

        def wait_for_click(button, window):
            window.withdraw()
            time.sleep(0.5)

            def on_click(x, y, button_pressed, pressed):
                if pressed:
                    button.config(text=f"({x}, {y})")
                    window.deiconify()
                    return False

            listener_thread = threading.Thread(target=self.listen_for_click, args=(on_click,))
            listener_thread.start()

        def save_task():
            operation = operation_type.get()
            interval = float(interval_entry.get()) if interval_entry.get() else 1
            details = ""

            if operation == "Click":
                coords = parse_coordinates(coordinates_button1.cget("text"))
                button = mouse_button_choice.get()
                task = {"operation": operation, "interval": interval, "coordinates": coords, "mouse_button": button}
                details = f"Click at {coords}, Button: {button}"
            elif operation == "Drag and Drop":
                start = parse_coordinates(coordinates_button1.cget("text"))
                end = parse_coordinates(coordinates_button2.cget("text"))
                task = {"operation": operation, "interval": interval, "coordinates": (start, end)}
                details = f"Drag from {start} to {end}"
            elif operation == "Keyboard":
                key = keyboard_button.get()
                task = {"operation": operation, "interval": interval, "keyboard_key": key}
                details = f"Press {key}"

            self.tasks.append(task)
            self.tree.insert("", "end", values=(operation, interval, details))
            new_task_window.destroy()

        save_button = tk.Button(new_task_window, text="Save", command=save_task)
        save_button.grid(row=4, column=0, columnspan=2, pady=10)

    def delete_task(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a task to delete.")
            return
        for item in selected_item:
            index = self.tree.index(item)
            self.tasks.pop(index)
            self.tree.delete(item)

    def start_tasks(self):
        if not self.tasks:
            messagebox.showwarning("Warning", "No tasks to start.")
            return

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.randomize_checkbox.config(state=tk.DISABLED)
        self.random_from_entry.config(state=tk.DISABLED)
        self.random_to_entry.config(state=tk.DISABLED)
        self.delay_entry.config(state=tk.DISABLED)

        delay = self.delay_var.get()
        if delay > 0:
            delay_thread = threading.Thread(target=self.handle_delay, args=(delay,))
            delay_thread.start()
        else:
            self.start_all_task_loops()

    def handle_delay(self, delay):
        time.sleep(delay)
        self.start_all_task_loops()

    def start_all_task_loops(self):
        self.task_threads = []
        for task in self.tasks:
            t = threading.Thread(target=self.run_task_loop, args=(task,))
            t.start()
            self.task_threads.append(t)

    def stop_tasks(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.randomize_checkbox.config(state=tk.NORMAL)
        self.random_from_entry.config(state=tk.NORMAL)
        self.random_to_entry.config(state=tk.NORMAL)
        self.delay_entry.config(state=tk.NORMAL)

    def run_task_loop(self, task):
        while self.running:
            interval = task["interval"]
            if self.randomize_time_var.get():
                random_offset = random.uniform(self.random_from_var.get(), self.random_to_var.get())
                interval += random_offset
            self.execute_task(task)

            while self.running and interval > 0:
                time.sleep(1)
                interval -= 1

    def execute_task(self, task):
        with self.global_lock:
            operation = task["operation"]
            if operation == "Click":
                x, y = task["coordinates"]
                button = task["mouse_button"].lower()
                pyautogui.click(x, y, button=button)
            elif operation == "Drag and Drop":
                start, end = task["coordinates"]
                pyautogui.moveTo(*start)
                pyautogui.mouseDown()
                pyautogui.moveTo(*end)
                pyautogui.mouseUp()
            elif operation == "Keyboard":
                keyboard.press_and_release(task["keyboard_key"])

            random_offset = random.uniform(1, 5)
            time.sleep(random_offset)

    def save_tasks(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not filename:
            return

        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Operation", "Interval", "Details"])
            for task in self.tasks:
                operation = task["operation"]
                interval = task["interval"]
                if operation == "Click":
                    coords = task["coordinates"]
                    button = task["mouse_button"]
                    details = f"Click at {coords}, Button: {button}"
                elif operation == "Drag and Drop":
                    start, end = task["coordinates"]
                    details = f"Drag from {start} to {end}"
                elif operation == "Keyboard":
                    key = task["keyboard_key"]
                    details = f"Press {key}"
                writer.writerow([operation, interval, details])

    def load_tasks(self):
        filename = filedialog.askopenfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not filename:
            return

        with open(filename, mode="r") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                operation, interval, details = row
                interval = float(interval)

                if "Click" in details:
                    match = re.search(r'\((\d+),\s*(\d+)\)', details)
                    if match:
                        coords = (int(match.group(1)), int(match.group(2)))
                    else:
                        coords = (0, 0)
                    button = details.split("Button:")[1].strip()
                    task = {"operation": operation, "interval": interval, "coordinates": coords, "mouse_button": button}
                elif "Drag" in details:
                    matches = re.findall(r'\((\d+),\s*(\d+)\)', details)
                    if matches and len(matches) >= 2:
                        start = (int(matches[0][0]), int(matches[0][1]))
                        end = (int(matches[1][0]), int(matches[1][1]))
                    else:
                        start, end = (0, 0), (0, 0)
                    task = {"operation": operation, "interval": interval, "coordinates": (start, end)}
                elif "Press" in details:
                    key = details.split("Press")[1].strip()
                    task = {"operation": operation, "interval": interval, "keyboard_key": key}

                self.tasks.append(task)
                self.tree.insert("", "end", values=(operation, interval, details))

    def listen_for_click(self, on_click):
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

def parse_coordinates(coord_str):
    coords = coord_str.strip("()").split(",")
    return tuple(map(int, coords))

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskerApp(root)
    root.mainloop()
