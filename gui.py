import ctypes
import tkinter as tk
from io import BytesIO

import aiohttp
from async_tkinter_loop import async_handler, async_mainloop
from PIL import Image, ImageTk
import toml

config = toml.load("settings.toml")


async def load_image():
    button.config(state=tk.DISABLED)
    label.config(text="Loading...", image="")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://{config['supernote_address']}:8080/screencast.mjpeg"
        ) as resp:
            reader = aiohttp.MultipartReader.from_response(resp)
            while True:
                part = await reader.next()
                partdata = await part.read(decode=False)
                print(f"Got Part of {len(partdata)} bytes")

                partdatastream = BytesIO(partdata)

                pil_image = Image.open(partdatastream)

                label.update()
                pil_image.thumbnail((label.winfo_width(), label.winfo_height()))

                image = ImageTk.PhotoImage(pil_image)
                label.image = image
                label.config(image=image, text="")
                button.config(state=tk.NORMAL)


if __name__ == "__main__":
    myappid = "uk.me.intrinseca.supernote-viewer"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    root = tk.Tk()
    root.geometry("800x640")
    root.title("Supernote Screenshare Viewer")
    root.configure(background="black")

    ico = Image.open("supernote-icon.png")
    photo = ImageTk.PhotoImage(ico)
    root.wm_iconphoto(False, photo)

    button = tk.Button(root, text="Load an image", command=async_handler(load_image))
    button.pack()

    label = tk.Label(root)
    label.pack(expand=1, fill=tk.BOTH)

    async_mainloop(root)
