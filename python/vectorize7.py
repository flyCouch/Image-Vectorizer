#!/usr/bin/env python3
"""
vectorize_gui.py - Interactive GUI for bitmap vectorization using OpenCV contours.
"""

import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageEnhance, ImageTk
import numpy as np
import cv2

class VectorizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vectorize GUI (LaserGRBL Linux Alternative)")
        self.root.geometry("900x700")

        self.image_path = None
        self.original_image = None

        # --- Top Frame: Controls & Buttons ---
        ctrl_frame = tk.Frame(root, padx=10, pady=10)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_load = tk.Button(ctrl_frame, text="Load Image", command=self.load_image, font=("Arial", 11, "bold"))
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.btn_save = tk.Button(ctrl_frame, text="Save SVG", command=self.save_svg, font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", state=tk.DISABLED)
        self.btn_save.pack(side=tk.RIGHT, padx=5)

        # --- Sliders Frame ---
        slider_frame = tk.Frame(root, padx=10, pady=10)
        slider_frame.pack(side=tk.TOP, fill=tk.X)

        # Brightness Slider
        tk.Label(slider_frame, text="Brightness:").grid(row=0, column=0, sticky="w")
        self.brightness_slider = tk.Scale(slider_frame, from_=0.1, to=3.0, resolution=0.05, orient=tk.HORIZONTAL, length=200, command=self.update_preview)
        self.brightness_slider.set(1.0)
        self.brightness_slider.grid(row=0, column=1, padx=10)

        # Contrast Slider
        tk.Label(slider_frame, text="Contrast:").grid(row=1, column=0, sticky="w")
        self.contrast_slider = tk.Scale(slider_frame, from_=0.1, to=3.0, resolution=0.05, orient=tk.HORIZONTAL, length=200, command=self.update_preview)
        self.contrast_slider.set(1.0)
        self.contrast_slider.grid(row=1, column=1, padx=10)

        # Threshold Slider
        tk.Label(slider_frame, text="Threshold:").grid(row=2, column=0, sticky="w")
        self.threshold_slider = tk.Scale(slider_frame, from_=0, to=255, resolution=1, orient=tk.HORIZONTAL, length=200, command=self.update_preview)
        self.threshold_slider.set(128)
        self.threshold_slider.grid(row=2, column=1, padx=10)

        # --- Canvas Frame (Live Preview) ---
        self.canvas_frame = tk.Frame(root, bg="#333333")
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#222222")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff")])
        if file_path:
            self.image_path = file_path
            self.original_image = Image.open(file_path).convert("L")
            self.btn_save.config(state=tk.NORMAL)
            self.update_preview()

    def get_processed_binary_array(self):
        if not self.original_image:
            return None

        b_val = self.brightness_slider.get()
        c_val = self.contrast_slider.get()
        t_val = self.threshold_slider.get()

        # Apply Pillow enhancements
        img = ImageEnhance.Brightness(self.original_image).enhance(b_val)
        img = ImageEnhance.Contrast(img).enhance(c_val)

        np_img = np.array(img)
        
        # Threshold: standard binary threshold
        _, thresh = cv2.threshold(np_img, t_val, 255, cv2.THRESH_BINARY)
        return thresh

    def update_preview(self, event=None):
        if not self.original_image:
            return

        thresh = self.get_processed_binary_array()
        bw_img = Image.fromarray(thresh)
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width < 50: canvas_width = 500
        if canvas_height < 50: canvas_height = 400

        bw_img.thumbnail((canvas_width - 20, canvas_height - 20), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(bw_img)

        self.canvas.delete("all")
        self.canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.tk_img, anchor=tk.CENTER)

    def save_svg(self):
        if not self.original_image:
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG Files", "*.svg")])
        if not output_path:
            return

        try:
            thresh = self.get_processed_binary_array()
            height, width = thresh.shape

            # Invert for OpenCV contour tracing of dark regions
            inverted_thresh = cv2.bitwise_not(thresh)
            contours, _ = cv2.findContours(inverted_thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

            svg_lines = [
                f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            ]
            
            # Solid white background rect
            svg_lines.append(f'  <rect width="{width}" height="{height}" fill="white" />')
            
            # CHANGED: Use fill="none" and stroke="black" so it traces lines/outlines instead of solid blocks
            svg_lines.append('  <g fill="none" stroke="black" stroke-width="1">')

            for cnt in contours:
                if len(cnt) < 3:
                    continue
                path_data = []
                for i, pt in enumerate(cnt):
                    x, y = pt[0]
                    cmd = "M" if i == 0 else "L"
                    path_data.append(f"{cmd} {x} {y}")
                path_data.append("Z")
                svg_lines.append(f'    <path d="{" ".join(path_data)}" />')

            svg_lines.append('  </g>')
            svg_lines.append('</svg>')

            with open(output_path, "w") as f:
                f.write("\n".join(svg_lines))

            messagebox.showinfo("Success", f"Vectorized SVG successfully saved to:\n{output_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to vectorize image:\n{e}")
if __name__ == "__main__":
    root = tk.Tk()
    app = VectorizerApp(root)
    root.mainloop()
