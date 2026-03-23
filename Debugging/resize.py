# For resizing images
import os
from PIL import Image

# Source directory
directory = "C:/Users/SmeetsJulia(Calco)/Downloads/openmoji-72x72-color"

# Target directory
target_directory = "C:/CodingProjects/Browser/Emojis"

# Takes all photos in a folder and converts them to 16x16 pixels
for filename in os.listdir(directory):
    img = Image.open(f"{directory}/{filename}")
    res = img.resize((16, 16))
    res.save(f"{target_directory}/{filename}")