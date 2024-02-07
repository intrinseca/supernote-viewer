import asyncio
import ctypes
import pathlib
import tkinter as tk
from io import BytesIO

import aiohttp
from async_tkinter_loop import async_mainloop
from PIL import Image, ImageTk

from . import config


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
            return

        partdatastream = BytesIO(partdata)

        yield Image.open(partdatastream)


def run_gui():
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
                        async for image in stream_from(resp):
                            label.update()
                            image.thumbnail((label.winfo_width(), label.winfo_height()))

                            photoimage = ImageTk.PhotoImage(image)
                            label.config(image=photoimage, text="")

                except aiohttp.client_exceptions.ServerTimeoutError:
                    label.config(text="Timed out...", image="")
                    continue

    myappid = "uk.me.intrinseca.supernote-viewer"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    root = tk.Tk()
    root.geometry("800x640")
    root.title("Supernote Screenshare Viewer")
    root.configure(background="black")

    module_path = pathlib.Path(__file__).parent

    ico = Image.open(module_path / "supernote-icon.png")
    photo = ImageTk.PhotoImage(ico)
    root.wm_iconphoto(False, photo)

    label = tk.Label(root)
    label.pack(expand=1, fill=tk.BOTH)

    asyncio.get_event_loop_policy().get_event_loop().create_task(load_image())

    async_mainloop(root)


if __name__ == "__main__":
    run_gui()
