import textwrap
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
from pypandoc import *
from dotenv import load_dotenv
import numpy as np
import os
import threading
import tkinter as ttk
import pandas as pd
import json
from pdfplumber import PDF
from docx2txt import process as docx2txt
import google.generativeai as genai
import tkinter as tk
from tkinter import font as tkfont
import numpy as np
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class MiniProject:
    def __init__(self):
        GeminiAPI = ''
        genai.configure(api_key=GeminiAPI)
        # Correcting generation_config to be a dictionary
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            # Telling the LLM to generate the content in the JSON FORMAT
            generation_config={'response_mime_type': 'application/json'}
        )
        self.relevance_score = 0
        self.missing_skills = None
        self.missing_keywords = None
        self.recommendations = None
        self.jsonData = None
        self.course_recommendations = None
        self.cover_letter = None

    def to_markdown(self, text):
        text = text.replace('*', '')
        return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

    def getGeminiResponse(self, input_prompt):
        try:
            generation_config = genai.GenerationConfig(response_mime_type="application/json")
            response = self.model.generate_content(input_prompt, generation_config=generation_config)
            response.resolve()
            return response.text
        except Exception as e:
            return f"An error occurred! {e}"

    def DocToText(self, doc_file):
        try:
            text = convert_file(doc_file, 'plain')
            return text
        except Exception as e:
            return f"Error reading .doc file: {str(e)}"

    def TextExtraction(self, resume_file):
        try:
            if resume_file is None:
                return "Resume is a None object"

            file_extension = os.path.splitext(resume_file)[1].lower()
            text = ""
            if file_extension == ".pdf":
                with open(resume_file, "rb") as f:
                    with PDF(f) as pdf:
                        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
            elif file_extension == ".txt":
                with open(resume_file, "r", encoding="utf-8") as f:
                    text = f.read()
            elif file_extension == ".docx":
                text = docx2txt(resume_file)
            elif file_extension == ".doc":
                text = self.DocToText(resume_file)
            else:
                return "Unsupported file format"

            return text
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def ResumeParser(self, job_description, resume):
        try:
            if job_description and resume:
                resume_text = self.TextExtraction(resume)
                if resume_text.startswith("Error") or resume_text == "Unsupported file format!":
                    return resume_text

                prompt = f"""
                Analyze the following resume and job description.
                Provide a JSON response with the following structure:
                {{
                    "relevance_score": (a percentage as a number),
                    "missing_skills": [list of missing skills],
                    "missing_keywords": [list of missing keywords],
                    "recommendations": [list of recommendations]
                }}

                Resume: {resume_text}
                Job Description: {job_description}
                Return this inside the list so the output looks like this
                [(relevance_score),[missing_skills],[missing_keywords],[recommendations]]
                """
                response = self.getGeminiResponse(prompt)
                print("raw response :", response)
                try:
                    jsonData = json.loads(response)
                    self.relevance_score = jsonData['relevance_score']

                    skills = []
                    for skill in jsonData['missing_skills']:
                        skills.append(skill)
                    self.missing_skills = skills

                    keywords = []
                    for keyword in jsonData['missing_keywords']:
                        keywords.append(keyword)
                    self.missing_keywords = keywords

                    recommendations = []
                    for recommendation in jsonData['recommendations']:
                        recommendations.append(recommendation)
                    self.recommendations = recommendations

                except json.JSONDecodeError as json_error:
                    print(f"JSON Parsing Error: {str(json_error)}")
                    return f"Error: Unable to parse JSON response. Details: {str(json_error)}"
                return json.dumps(self.jsonData, indent=2)
            else:
                return "Error: Job description or resume is missing"

        except Exception as e:
            return f"An error occurred: {str(e)}"

    def create_gauge_chart(self):
        fig, ax = plt.subplots(figsize=(6, 3))  # Reduced figure size
        colors = ['#ff6f69', '#ffcc5c', '#88d8b0']
        ranges = [0, 50, 75, 100]
        patches = []

        for i, (color, start, end) in enumerate(zip(colors, ranges[:-1], ranges[1:])):
            patch = plt.barh(0, width=(end-start), left=start, color=color, height=0.5)  # Reduced height
            patches.append(patch)

        needle_position = np.clip(self.relevance_score, 0, 100)
        ax.plot([needle_position, needle_position], [0, 0.5], color='black', linewidth=2)  # Adjusted needle

        labels = ['not Relevant', 'some what Relevant', 'Relevant']
        legend_handles = patches
        plt.legend(legend_handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.2),
                   ncol=3, fontsize='small', title='Relevance Score', title_fontsize='small')

        ax.text(0,   0.6, '0%',   ha='center', fontsize=8)
        ax.text(50,  0.6, '50%',  ha='center', fontsize=8)
        ax.text(75,  0.6, '75%',  ha='center', fontsize=8)
        ax.text(100, 0.6, '100%', ha='center', fontsize=8)
        ax.text(50, -0.3, f'Relevance Score: {self.relevance_score}%', ha='center', fontsize=10, fontweight='bold')

        ax.axis('off')
        plt.tight_layout()

        return fig

    def get_required_courses(self):
        try:
            if not self.missing_skills:
                return "Error: Missing skills have not been identified yet. Please run ResumeParser first."

            prompt = f"""
            I have the following list of missing skills: {', '.join(self.missing_skills)}.
            Take all the important missing skills that could provide immense value.
            Please suggest relevant online courses or certifications that would help someone learn these skills.
            For each skill, provide up to 3 course recommendations.

            Format the response as a JSON object with the following structure:
            {{
                "skill_name": [
                    {{
                        "course_name": "Name of the course",
                        "platform": "Platform offering the course",
                        "description": "Brief description of the course",
                        "difficulty_level": "Beginner/Intermediate/Advanced",
                        "estimated_duration": "Estimated time to complete the course",
                        "Course Link": "The website link of that course"
                    }}
                ]
            }}
            """
            response = self.getGeminiResponse(prompt)
            print("raw response :", response)
            self.course_recommendations = json.loads(response)
            return self.course_recommendations

        except Exception as e:
            return f"An error occurred while getting course recommendations: {str(e)}"

    def display_course_recommendations(self):
        if not self.course_recommendations:
            return "No course recommendations available. Please run get_required_courses() first."

        markdown_output = "# Course Recommendations\n\n"
        for skill, courses in self.course_recommendations.items():
            markdown_output += f"## {skill}\n\n"
            for course in courses:
                markdown_output += f"### {course['course_name']}\n"
                markdown_output += f"- *Platform:* {course['platform']}\n"
                markdown_output += f"- *Description:* {course['description']}\n"
                markdown_output += f"- *Difficulty:* {course['difficulty_level']}\n"
                markdown_output += f"- *Duration:* {course['estimated_duration']}\n\n"

        return markdown_output

    def RelevanceScore(self):
        return self.relevance_score

    def Applyinglabel(self):
        if self.relevance_score >= 70:
            return 'Yes'
        else:
            return 'Need some Improvements'

    def generate_cover_letter(self, resumePath, job_description):
        resume_text = self.TextExtraction(resumePath)
        if self.relevance_score < 10:
            return "Cover letter generation is only available for candidates with a relevance score of 80% or higher."

        prompt = f"""
        Based on the following resume and job description, generate a professional cover letter.
        The cover letter should highlight the candidate's relevant skills and experiences that match the job requirements.

        Resume:
        {resume_text}

        Job Description:
        {job_description}

        Please format the cover letter as follows:
        1. Start with a professional greeting
        2. Include an opening paragraph that expresses interest in the position
        3. In the body paragraphs, highlight 2-3 key qualifications that match the job requirements
        4. Include a closing paragraph that reiterates interest and provides contact information
        5. End with a professional sign-off

        The tone should be professional, enthusiastic, and confident & just give me the cover letter no additional greetings to the user.
        """

        response = self.getGeminiResponse(prompt)
        self.cover_letter = response
        return self.cover_letter

    def save_cover_letter_to_file(self, filename="cover_letter.txt"):
        if self.cover_letter:
            with open(filename, 'w') as file:
                file.write(self.cover_letter)
            return f"Cover letter saved to {filename}"
        else:
            return "No cover letter available to save."

class CVAnalysisDashboard:
    def __init__(self, master):
        self.master = master
        self.master.title("CV Analysis Dashboard")
        self.master.geometry("1200x800")

        self.mini_project = MiniProject()

        self.create_scrollable_frame()
        self.create_title()
        self.create_widgets()
        self.create_loading_window()

    def create_scrollable_frame(self):
        # Create a canvas
        self.canvas = tk.Canvas(self.master)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a scrollbar to the canvas
        self.scrollbar = ttk.Scrollbar(self.master, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Create a frame inside the canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Bind mouse wheel event to the canvas
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_title(self):
        # Create a frame for the title
        title_frame = ttk.Frame(self.scrollable_frame, padding="20")
        title_frame.grid(row=0, column=0, columnspan=3, sticky="ew")

        # Create a custom font
        title_font = tkfont.Font(family="Arial", size=24, weight="bold")

        # Add the title label with color
        title_label = tk.Label(title_frame, text="CV / JOB DESCRIPTION ANALYTICS DASHBOARD",
                               font=title_font, fg="#4A90E2", bg="#F0F0F0")
        title_label.pack()

        # Add a separator
        ttk.Separator(self.scrollable_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)

    def create_widgets(self):
        # Input Frame
        input_frame = ttk.Frame(self.scrollable_frame, padding="10")
        input_frame.grid(row=2, column=0, columnspan=3, sticky="ew")

        ttk.Label(input_frame, text="Job Description:").grid(row=0, column=0, sticky="w")
        self.job_desc = tk.Text(input_frame, height=15, width=80)
        self.job_desc.grid(row=1, column=0, columnspan=2, pady=5)

        ttk.Label(input_frame, text="Upload Resume:").grid(row=2, column=0, sticky="w")
        self.resume_path = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.resume_path, width=60).grid(row=2, column=1, pady=5)
        ttk.Button(input_frame, text="Browse", command=self.browse_file).grid(row=2, column=2, pady=5)

        ttk.Button(input_frame, text="Submit", command=self.analyze_resume).grid(row=3, column=1, pady=10)

        # Results Frame
        results_frame = ttk.Frame(self.scrollable_frame, padding="10")
        results_frame.grid(row=3, column=0, columnspan=3, sticky="nsew")

        # Accuracy Score
        self.accuracy_var = tk.StringVar()
        ttk.Label(results_frame, textvariable=self.accuracy_var, font=("Arial", 24)).grid(row=0, column=0, padx=10, pady=10)

        # Visualizations
        self.viz_frame = ttk.Frame(results_frame)
        self.viz_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10)

        # Missing Skills & Keywords
        skills_frame = ttk.Frame(results_frame)
        skills_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
        ttk.Label(skills_frame, text="Missing Skills & Keywords", font=("Arial", 12, "bold")).pack()
        self.skills_text = tk.Text(skills_frame, height=15, width=50)
        self.skills_text.pack()

        # Course Recommendations
        course_frame = ttk.Frame(results_frame)
        course_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=10, sticky="ne")
        ttk.Label(course_frame, text="Course Recommendations", font=("Arial", 12, "bold")).pack()
        self.course_text = tk.Text(course_frame, height=25, width=55)
        self.course_text.pack()

        # Resume Summary
        summary_frame = ttk.Frame(results_frame)
        summary_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="sw")
        ttk.Label(summary_frame, text="Summary of your Resume", font=("Arial", 12, "bold")).pack()
        self.summary_text = tk.Text(summary_frame, height=12, width=100)
        self.summary_text.pack()

        # Apply Button
        ttk.Button(results_frame, text="Cover Letter?", command=self.generate_cover_letter).grid(row=3, column=1, pady=10)

    def create_loading_window(self):
        self.loading_window = tk.Toplevel(self.master)
        self.loading_window.title("Processing")
        self.loading_window.geometry("300x100")
        self.loading_window.withdraw()  # Hide the window initially

        self.loading_label = ttk.Label(self.loading_window, text="Processing, please wait...", font=("Arial", 12))
        self.loading_label.pack(pady=20)

        self.progress_bar = ttk.Progressbar(self.loading_window, mode="indeterminate")
        self.progress_bar.pack(pady=10, padx=20, fill=tk.X)

    def show_loading(self):
        self.loading_window.deiconify()  # Show the loading window
        self.progress_bar.start()

    def hide_loading(self):
        self.progress_bar.stop()
        self.loading_window.withdraw()  # Hide the loading window

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF files", ".pdf"), ("Word files", ".docx"), ("Text files", "*.txt")])
        self.resume_path.set(filename)

    def analyze_resume(self):
        job_description = self.job_desc.get("1.0", tk.END).strip()
        resume_file = self.resume_path.get()

        if not job_description or not resume_file:
            messagebox.showerror("Error", "Please provide both job description and resume file.")
            return

        self.show_loading()

        # Run the analysis in a separate thread
        threading.Thread(target=self._run_analysis, args=(job_description, resume_file), daemon=True).start()

    def _run_analysis(self, job_description, resume_file):
        result = self.mini_project.ResumeParser(job_description, resume_file)

        # Use after() to update GUI from the main thread
        self.master.after(0, self._handle_analysis_result, result)

    def _handle_analysis_result(self, result):
        self.hide_loading()

        if isinstance(result, str) and result.startswith("Error"):
            messagebox.showerror("Error", result)
        else:
            self.display_results()

    def display_results(self):
        self.show_loading()

        # Run the display in a separate thread
        threading.Thread(target=self._run_display, daemon=True).start()

    def _run_display(self):
        # Accuracy Score
        accuracy = self.mini_project.RelevanceScore()
        self.master.after(0, lambda: self.accuracy_var.set(f"{accuracy:.2f}%"))

        # Visualizations
        self.master.after(0, self.create_visualizations)

        # Missing Skills & Keywords
        skills_keywords = "Missing Skills:\n"
        skills_keywords += "\n".join(f"• {skill}" for skill in self.mini_project.missing_skills)
        skills_keywords += "\n\nMissing Keywords:\n"
        skills_keywords += "\n".join(f"• {keyword}" for keyword in self.mini_project.missing_keywords)
        self.master.after(0, lambda: self.skills_text.delete("1.0", tk.END))
        self.master.after(0, lambda: self.skills_text.insert(tk.END, skills_keywords))

        # Course Recommendations
        recommendations = self.mini_project.get_required_courses()
        course_text = ""
        for skill, courses in recommendations.items():
            course_text += f"{skill}:\n"
            for course in courses:
                course_text += f"• {course['course_name']} ({course['platform']})\n"
                course_text += f"  Description: {course['description']}\n"
                course_text += f"  Difficulty: {course['difficulty_level']}\n"
                course_text += f"  Duration: {course['estimated_duration']}\n\n"
        self.master.after(0, lambda: self.course_text.delete("1.0", tk.END))
        self.master.after(0, lambda: self.course_text.insert(tk.END, course_text))

        # Resume Summary
        summary = "Key Points:\n"
        summary += "\n".join(f"• {point}" for point in self.mini_project.recommendations)
        self.master.after(0, lambda: self.summary_text.delete("1.0", tk.END))
        self.master.after(0, lambda: self.summary_text.insert(tk.END, summary))

        self.master.after(0, self.hide_loading)

    def create_visualizations(self):
        for widget in self.viz_frame.winfo_children():
            widget.destroy()

        fig = self.mini_project.create_gauge_chart()
        canvas = FigureCanvasTkAgg(fig, master=self.viz_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def generate_cover_letter(self):
        self.show_loading()

        # Run the cover letter generation in a separate thread
        threading.Thread(target=self._run_cover_letter_generation, daemon=True).start()

    def _run_cover_letter_generation(self):
        cover_letter = self.mini_project.generate_cover_letter(self.resume_path.get(),
                                                               self.job_desc.get("1.0", tk.END).strip())

        self.master.after(0, lambda: self._display_cover_letter(cover_letter))

    def _display_cover_letter(self, cover_letter):
        self.hide_loading()

        # Display cover letter in a new window
        cover_window = tk.Toplevel(self.master)
        cover_window.title("Generated Cover Letter")
        cover_window.geometry("800x600")  # Increased window size

        # Create a frame to hold the text widget and scrollbar
        frame = ttk.Frame(cover_window)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        # Create the text widget with default font
        cover_text = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        cover_text.pack(expand=True, fill="both")

        # Configure the scrollbar
        scrollbar.config(command=cover_text.yview)

        # Insert the cover letter text
        cover_text.insert(tk.END, cover_letter)

        # Add the save button at the bottom of the window
        ttk.Button(cover_window, text="Save", command=lambda: self.save_cover_letter(cover_letter)).pack(pady=10)

    def save_cover_letter(self, cover_letter):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if filename:
            with open(filename, "w") as f:
                f.write(cover_letter)
            messagebox.showinfo("Success", f"Cover letter saved to {filename}")

def main():
    root = tk.Tk()
    app = CVAnalysisDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()
