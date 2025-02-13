import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

DEFAULT_CONFIG_FILENAME = "config.json"

class settingsApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Questionnaire Settings")

        # fallback config if loading fails
        self.config_data = {
            "app_settings": {
                "window_title": "Dynamic Questionnaire App",
                "window_size": "600x700"
            },
            "rating_settings": {
                "default_rating_range": [1, 5],
                "force_ratings": True,
                "questions": [
                    {
                        "statement": "I quickly understood how to interact with the installation.",
                        "is_negative": False
                    }
                ]
            },
            "open_questions_settings": {
                "questions": []
            },
            "visualization_settings": {
                "plot_defaults": {
                    "heatmap_colormap": "viridis",
                    "show_means_in_violin": True
                },
                "save_plot_formats": ["png", "pdf"]
            }
        }

        self.load_config()

        self.create_widgets()

    # load config
    def load_config(self):
        if os.path.isfile(DEFAULT_CONFIG_FILENAME):
            try:
                with open(DEFAULT_CONFIG_FILENAME, "r") as f:
                    self.config_data = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load '{DEFAULT_CONFIG_FILENAME}': {e}")

    # save config
    def save_config(self):
        try:
            with open(DEFAULT_CONFIG_FILENAME, "w") as f:
                json.dump(self.config_data, f, indent=2)
            messagebox.showinfo("Success", f"Settings saved to {DEFAULT_CONFIG_FILENAME}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save '{DEFAULT_CONFIG_FILENAME}': {e}")

    # create main ui
    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.app_settings_frame = ttk.Frame(notebook)
        notebook.add(self.app_settings_frame, text="App Settings")

        self.rating_settings_frame = ttk.Frame(notebook)
        notebook.add(self.rating_settings_frame, text="Rating Settings")

        self.open_questions_frame = ttk.Frame(notebook)
        notebook.add(self.open_questions_frame, text="Open Questions")

        self.viz_settings_frame = ttk.Frame(notebook)
        notebook.add(self.viz_settings_frame, text="Visualization")

        # Create controls for each tab
        self.create_app_settings_tab()
        self.create_rating_settings_tab()
        self.create_open_questions_tab()
        self.create_viz_settings_tab()

        # Bottom "Save" button
        save_button = ttk.Button(self, text="Save Settings", command=self.on_save)
        save_button.pack(pady=5)

    # app settings
    def create_app_settings_tab(self):
        frame = self.app_settings_frame

        ttk.Label(frame, text="Window Title:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.var_window_title = tk.StringVar(value=self.config_data["app_settings"].get("window_title", "Questionnaire App"))
        ttk.Entry(frame, textvariable=self.var_window_title, width=40).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame, text="Window Size (e.g., '600x700'):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.var_window_size = tk.StringVar(value=self.config_data["app_settings"].get("window_size", "600x700"))
        ttk.Entry(frame, textvariable=self.var_window_size, width=40).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        frame.columnconfigure(1, weight=1)

    # rating settings
    def create_rating_settings_tab(self):
        frame = self.rating_settings_frame

        rating_settings = self.config_data["rating_settings"]
        default_range = rating_settings.get("default_rating_range", [1, 5])
        start_val, end_val = default_range

        ttk.Label(frame, text="Default Rating Scale (start):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.var_scale_start = tk.IntVar(value=start_val)
        ttk.Entry(frame, textvariable=self.var_scale_start, width=5).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame, text="Default Rating Scale (end):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.var_scale_end = tk.IntVar(value=end_val)
        ttk.Entry(frame, textvariable=self.var_scale_end, width=5).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.var_force_ratings = tk.BooleanVar(value=rating_settings.get("force_ratings", False))
        ttk.Checkbutton(frame, text="Force Ratings?", variable=self.var_force_ratings).grid(
            row=2, column=1, padx=5, pady=5, sticky="w"
        )

        self.questions_container = ttk.Frame(frame)
        self.questions_container.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        self.question_rows = []
        questions = rating_settings.get("questions", [])
        for q_obj in questions:
            row = self.add_question_row(q_obj)
            self.question_rows.append(row)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        ttk.Button(btn_frame, text="Add Question", command=self.on_add_question).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Last", command=self.on_remove_last_question).pack(side="left", padx=5)

        frame.columnconfigure(1, weight=1)

    def add_question_row(self, q_obj=None):
        row_frame = ttk.Frame(self.questions_container)
        row_frame.pack(fill="x", pady=2)

        statement_var = tk.StringVar(value=q_obj.get("statement", "")) if q_obj else tk.StringVar()
        negative_var = tk.BooleanVar(value=q_obj.get("is_negative", False)) if q_obj else tk.BooleanVar()

        ttk.Label(row_frame, text="Statement:").pack(side="left", padx=5)
        entry = ttk.Entry(row_frame, textvariable=statement_var, width=60)
        entry.pack(side="left", padx=5)

        neg_check = ttk.Checkbutton(row_frame, text="Negative?", variable=negative_var)
        neg_check.pack(side="left", padx=5)

        return {
            "frame": row_frame,
            "statement_var": statement_var,
            "negative_var": negative_var
        }

    def on_add_question(self):
        new_row = self.add_question_row()
        self.question_rows.append(new_row)

    def on_remove_last_question(self):
        if self.question_rows:
            last_row = self.question_rows.pop()
            last_row["frame"].destroy()

    # open-ended questions
    def create_open_questions_tab(self):
        frame = self.open_questions_frame

        self.open_questions_container = ttk.Frame(frame)
        self.open_questions_container.pack(fill="x", pady=5)

        self.open_question_rows = []
        open_questions = self.config_data.get("open_questions_settings", {}).get("questions", [])

        for question_text in open_questions:
            row_frame = self.add_open_question_row(question_text)
            self.open_question_rows.append(row_frame)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="Add Open Question", command=self.on_add_open_question).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Last", command=self.on_remove_last_open_question).pack(side="left", padx=5)

    def add_open_question_row(self, text=""):
        row_frame = ttk.Frame(self.open_questions_container)
        row_frame.pack(fill="x", pady=2)

        q_var = tk.StringVar(value=text)
        entry = ttk.Entry(row_frame, textvariable=q_var, width=60)
        entry.pack(side="left", padx=5)

        return {
            "frame": row_frame,
            "question_var": q_var
        }

    def on_add_open_question(self):
        new_row = self.add_open_question_row()
        self.open_question_rows.append(new_row)

    def on_remove_last_open_question(self):
        if self.open_question_rows:
            last_row = self.open_question_rows.pop()
            last_row["frame"].destroy()

    #viz settings
    def create_viz_settings_tab(self):
        frame = self.viz_settings_frame

        colormap_choices = ["viridis", "plasma", "inferno", "magma", "cividis", "Greens", "Blues"]

        plot_defaults = self.config_data.setdefault("visualization_settings", {})\
                                        .setdefault("plot_defaults", {})
        current_cmap = plot_defaults.get("heatmap_colormap", "viridis")

        ttk.Label(frame, text="Heatmap Colormap:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.var_colormap = tk.StringVar(value=current_cmap)

        self.cmap_combobox = ttk.Combobox(frame, textvariable=self.var_colormap,
                                          values=colormap_choices, state="readonly")
        self.cmap_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        frame.columnconfigure(1, weight=1)

    #save updated config
    def on_save(self):
        
        self.config_data["app_settings"]["window_title"] = self.var_window_title.get().strip()
        self.config_data["app_settings"]["window_size"] = self.var_window_size.get().strip()

        rating_settings = self.config_data["rating_settings"]
        start_val = self.var_scale_start.get()
        end_val = self.var_scale_end.get()
        rating_settings["default_rating_range"] = [start_val, end_val]
        rating_settings["force_ratings"] = self.var_force_ratings.get()

        updated_questions = []
        for row in self.question_rows:
            st_val = row["statement_var"].get().strip()
            neg_val = row["negative_var"].get()
            if st_val:
                updated_questions.append({
                    "statement": st_val,
                    "is_negative": neg_val
                })
        rating_settings["questions"] = updated_questions

        open_questions_list = []
        for row in self.open_question_rows:
            q_text = row["question_var"].get().strip()
            if q_text:
                open_questions_list.append(q_text)
        self.config_data.setdefault("open_questions_settings", {})["questions"] = open_questions_list

        vis_settings = self.config_data.setdefault("visualization_settings", {})
        plot_defaults = vis_settings.setdefault("plot_defaults", {})
        plot_defaults["heatmap_colormap"] = self.var_colormap.get()

        self.save_config()


if __name__ == "__main__":
    app = settingsApp()
    app.mainloop()