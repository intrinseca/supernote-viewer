import asyncio
import ctypes
import tkinter as tk
from io import BytesIO

import aiohttp
from async_tkinter_loop import async_mainloop
from PIL import Image, ImageTk

from . import config


def run_gui():
    async def stream_from(resp):
        reader = aiohttp.MultipartReader.from_response(resp)
        while True:
            try:
                part = await reader.next()
                partdata = await part.read(decode=False)
                print("Got part")
            except (
                asyncio.exceptions.TimeoutError,
                aiohttp.client_exceptions.ClientPayloadError,
            ):
                label.config(text="Timed out...", image="")
                break

            partdatastream = BytesIO(partdata)

            pil_image = Image.open(partdatastream)

            label.update()
            pil_image.thumbnail((label.winfo_width(), label.winfo_height()))

            image = ImageTk.PhotoImage(pil_image)
            label.image = image
            label.config(image=image, text="")

    async def load_image():
        label.config(text="Loading...", image="")

        timeout = aiohttp.ClientTimeout(connect=2, total=60)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            while True:
                print("Connecting...")
                try:
                    async with session.get(
                        f"http://{config['supernote_address']}:8080/screencast.mjpeg"
                    ) as resp:
                        await stream_from(resp)
                except aiohttp.client_exceptions.ServerTimeoutError:
                    label.config(text="Timed out...", image="")
                    continue

    myappid = "uk.me.intrinseca.supernote-viewer"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    root = tk.Tk()
    root.geometry("800x640")
    root.title("Supernote Screenshare Viewer")
    root.configure(background="black")

    ico = Image.open("supernote-icon.png")
    photo = ImageTk.PhotoImage(ico)
    root.wm_iconphoto(False, photo)

    label = tk.Label(root)
    label.pack(expand=1, fill=tk.BOTH)

    asyncio.get_event_loop_policy().get_event_loop().create_task(load_image())

    async_mainloop(root)


if __name__ == "__main__":
    run_gui()
