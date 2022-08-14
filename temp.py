import os
from PIL import Image

os.chdir(os.path.dirname(os.path.abspath(__file__)))

masu = Image.new(mode="RGB",size=(50,50),color=0x00ff)
masu_naka = Image.new(mode="RGB",size=(46,46),color=0x000000)
masu.paste(masu_naka,(2,2))
masu.save("buried.png")

masu = Image.new(mode="RGB",size=(50,50),color=0x000000)
masu_naka = Image.new(mode="RGB",size=(46,46),color=0xffffff)
masu.paste(masu_naka,(2,2))
masu.save("void.png")