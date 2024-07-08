import asyncio
import ctypes
import pathlib
import tkinter as tk
from io import BytesIO

import aiohttp
from async_tkinter_loop import async_mainloop
from halo import Halo
from PIL import Image, ImageTk

from . import config


async def stream_from(resp):
    reader = aiohttp.MultipartReader.from_response(resp)

    while True:
        try:
            part = await reader.next()
            partdata = await part.read(decode=False)
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
            spinner = Halo(spinner="dots", text="Connecting...", color="blue")
            spinner.start()

            while True:
                try:
                    async with session.get(
                        f"http://{config['supernote_address']}:8080/screencast.mjpeg"
                    ) as resp:
                        spinner.color = "green"
                        spinner.start("Streaming...")
                        async for image in stream_from(resp):
                            label.update()
                            image.thumbnail((label.winfo_width(), label.winfo_height()))

                            photoimage = ImageTk.PhotoImage(image)
                            label.config(image=photoimage, text="")

                except aiohttp.client_exceptions.ServerTimeoutError:
                    label.config(text="Timed out...", image="")
                    spinner.color = "red"
                    spinner.text = "Timed out, retrying..."

                except aiohttp.client_exceptions.ClientConnectorError:
                    label.config(text="Connection refused...", image="")
                    spinner.color = "red"
                    spinner.text = "Connection refused, retrying..."

    myappid = "uk.me.intrinseca.supernote-viewer"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    root = tk.Tk()
    root.geometry("702x936")  # 50% of native resolution
    root.title("Supernote Screenshare Viewer")
    root.configure(background="black")

    root.bind(
        "<F11>",
        lambda event: root.attributes(
            "-fullscreen", not root.attributes("-fullscreen")
        ),
    )
    root.bind("<Escape>", lambda event: root.attributes("-fullscreen", False))

    module_path = pathlib.Path(__file__).parent

    ico = Image.open(module_path / "supernote-icon.png")
    photo = ImageTk.PhotoImage(ico)
    root.wm_iconphoto(False, photo)

    label = tk.Label(root)
    label.config(background="black", foreground="white")
    label.pack(expand=1, fill=tk.BOTH)

    asyncio.get_event_loop_policy().get_event_loop().create_task(load_image())

    async_mainloop(root)


if __name__ == "__main__":
    run_gui()
