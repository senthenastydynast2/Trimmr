import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import time

class TrimmrApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trimmr")
        self.root.state('zoomed')  # Start maximized
        
        self.selected_images = []
        self.current_image_index = 0
        self.original_image = None
        self.zoom_level = 1.0
        self.frame_width = 512
        self.frame_height = 648
        self.frame_rect = None
        self.zoom_step = 1.1  # Default zoom step
        
        self.setup_ui()
        
    def setup_ui(self):
        # Left sidebar for buttons and options
        self.sidebar = tk.Frame(self.root, width=300, bg='white')
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        self.source_folder_btn = tk.Button(self.sidebar, text="Select Images", command=self.select_images)
        self.source_folder_btn.pack(pady=10)
        
        self.trim_button = tk.Button(self.sidebar, text="Trim", command=self.start_trimming)
        self.trim_button.pack(pady=10)
        
        self.output_folder_btn = tk.Button(self.sidebar, text="Select Output Folder", command=self.select_output_folder)
        self.output_folder_btn.pack(pady=10)
        
        # Instructions
        self.instructions = tk.Label(self.sidebar, text=(
            "Controls:\n\n"
            "- Scroll Wheel: +/-\n\n"
            "- Left Shift: Toggle frame size between square and vertical.\n\n"
            "- Left Click: Save trim and move to next image.\n\n"
            "- Ctrl+Left Click: Save trim without changing image.\n\n"
            "- Ctrl+Scroll: Faster zoom.\n\n"
            "- Esc: Minimizes."
        ), bg='white', justify=tk.LEFT, anchor='w', padx=10, pady=15, font=("Arial", 12))
        self.instructions.pack(pady=20, fill=tk.X)
        
        # Image counter
        self.image_counter = tk.Label(self.sidebar, text="", font=("Arial", 20, "bold"), bg='white')
        self.image_counter.pack(side=tk.BOTTOM, pady=20, fill=tk.X)
        
        # Canvas for displaying images
        self.canvas = tk.Canvas(self.root, bg='black')
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<Control-Button-1>", self.on_ctrl_click)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.root.bind("<Escape>", self.on_escape)
        self.root.bind("<Shift_L>", self.on_shift)
        self.root.bind("<Control-MouseWheel>", self.on_ctrl_scroll)

    def update_image_counter(self):
        if self.selected_images and self.image_counter:
            self.image_counter.config(text=f"Image {self.current_image_index + 1} of {len(self.selected_images)}")

    def select_images(self):
        filetypes = [("Image files", "*.png;*.jpeg;*.jpg")]
        self.selected_images = filedialog.askopenfilenames(filetypes=filetypes)
        if self.selected_images:
            messagebox.showinfo("Selected Images", f"{len(self.selected_images)} image(s) selected.")
            self.update_image_counter()
        
    def select_output_folder(self):
        self.output_folder = filedialog.askdirectory()
        if self.output_folder:
            messagebox.showinfo("Output Folder", f"Selected folder: {self.output_folder}")
        
    def start_trimming(self):
        if not self.selected_images:
            messagebox.showerror("Error", "No images selected.")
            return
        
        if not hasattr(self, 'output_folder') or not self.output_folder:
            messagebox.showerror("Error", "No output folder selected.")
            return
        
        self.current_image_index = 0
        self.show_image()
        
    def show_image(self):
        image_path = self.selected_images[self.current_image_index]
        self.original_image = Image.open(image_path)

        # Ensure minimum dimension is 648px
        min_dimension = 648
        width, height = self.original_image.size
        if width < min_dimension or height < min_dimension:
            if width < height:
                new_width = min_dimension
                new_height = int(height * (min_dimension / width))
            else:
                new_height = min_dimension
                new_width = int(width * (min_dimension / height))
            self.original_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
        
        self.zoom_level = 1.0
        self.update_image_display()
        self.update_image_counter()
        
    def update_image_display(self):
        display_image = self.original_image.copy()
        
        # Resize image based on zoom level
        width, height = display_image.size
        display_image = display_image.resize((int(width * self.zoom_level), int(height * self.zoom_level)), Image.LANCZOS)
        
        # Center image on canvas
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.img_width, self.img_height = display_image.size
        self.img_x = (canvas_width - self.img_width) // 2
        self.img_y = (canvas_height - self.img_height) // 2
        self.tk_image = ImageTk.PhotoImage(display_image)
        self.canvas.create_image(self.img_x, self.img_y, anchor=tk.NW, image=self.tk_image)
        
        # Draw trimming frame
        self.update_frame()

    def update_frame(self):
        if self.frame_rect:
            self.canvas.delete(self.frame_rect)
        self.frame_x = max(self.img_x, (self.canvas.winfo_width() - self.frame_width) // 2)
        self.frame_y = max(self.img_y, (self.canvas.winfo_height() - self.frame_height) // 2)
        self.frame_rect = self.canvas.create_rectangle(
            self.frame_x, self.frame_y, 
            self.frame_x + self.frame_width, self.frame_y + self.frame_height, 
            outline='lime green', width=12  # Increased thickness
        )
        self.frame_x, self.frame_y = self.frame_x, self.frame_y

    def on_mouse_move(self, event):
        if self.frame_rect:
            self.canvas.delete(self.frame_rect)
            x = min(max(event.x - self.frame_width // 2, self.img_x), self.img_x + self.img_width - self.frame_width)
            y = min(max(event.y - self.frame_height // 2, self.img_y), self.img_y + self.img_height - self.frame_height)
            self.frame_rect = self.canvas.create_rectangle(x, y, x + self.frame_width, y + self.frame_height, outline='lime green', width=12)
            self.frame_x, self.frame_y = x, y

    def on_mouse_click(self, event):
        self.save_trimmed_image()
        self.current_image_index += 1
        if self.current_image_index < len(self.selected_images):
            self.show_image()
        else:
            messagebox.showinfo("Done", "All images have been processed.")
            self.selected_images = []
            self.current_image_index = 0
            self.image_counter.config(text="")

    def on_ctrl_click(self, event):
        self.save_trimmed_image()
        # Stay on the same image
        self.update_image_counter()

    def on_escape(self, event):
        self.root.iconify()

    def on_shift(self, event):
        if self.frame_width == 512 and self.frame_height == 648:
            # Switch to square frame
            self.frame_width = 512
            self.frame_height = 512
        else:
            # Switch to vertical frame
            self.frame_width = 512
            self.frame_height = 648
        self.update_image_display()

    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.zoom_level *= self.zoom_step
        else:
            new_zoom_level = self.zoom_level / self.zoom_step
            # Calculate new dimensions
            new_width = self.original_image.width * new_zoom_level
            new_height = self.original_image.height * new_zoom_level
            # Allow zoom out only if the frame can fit inside the image
            if new_width >= self.frame_width and new_height >= self.frame_height:
                self.zoom_level = new_zoom_level
        self.update_image_display()

    def on_ctrl_scroll(self, event):
        if event.delta > 0:
            self.zoom_step = min(self.zoom_step + 0.05, 1.5)  # Increase zoom step up to 1.5x
        else:
            self.zoom_step = max(self.zoom_step - 0.05, 1.05)  # Decrease zoom step down to 1.05x
        self.zoom_level *= self.zoom_step
        self.update_image_display()

    def save_trimmed_image(self):
        if not hasattr(self, 'output_folder') or not self.output_folder:
            messagebox.showerror("Error", "No output folder selected.")
            return
        
        # Determine the output frame size
        output_width = self.frame_width
        output_height = self.frame_height

        # Get frame position relative to the image
        frame_x_rel = (self.frame_x - self.img_x) / self.zoom_level
        frame_y_rel = (self.frame_y - self.img_y) / self.zoom_level
        frame_w_rel = self.frame_width / self.zoom_level
        frame_h_rel = self.frame_height / self.zoom_level
        
        # Crop the image based on the frame position
        cropped_image = self.original_image.crop((frame_x_rel, frame_y_rel, frame_x_rel + frame_w_rel, frame_y_rel + frame_h_rel))
        
        # Resize cropped image to match the frame size
        resized_image = cropped_image.resize((output_width, output_height), Image.BICUBIC)
        
        # Save the image
        output_filename = os.path.join(self.output_folder, f"trimmed_{self.current_image_index + 1}_{int(time.time())}.png")
        resized_image.save(output_filename)
        
        # Move to the next image


if __name__ == "__main__":
    root = tk.Tk()
    app = TrimmrApp(root)
    root.mainloop()
