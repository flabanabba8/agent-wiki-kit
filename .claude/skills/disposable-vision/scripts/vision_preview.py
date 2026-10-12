#!/usr/bin/env python3
"""Compress a whole image for vision uploads; never crop or overwrite its source."""
import argparse,io
from pathlib import Path
from PIL import Image,ImageOps

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--max-bytes',type=int,default=50000)
    p.add_argument('--max-edge',type=int,default=1024)
    a=p.parse_args()
    if a.source.resolve()==a.output.resolve():p.error('Output must differ from source')
    if a.max_bytes<1000 or a.max_edge<64:p.error('Invalid preview budget')
    source=ImageOps.exif_transpose(Image.open(a.source)).convert('RGBA')
    matte=Image.new('RGBA',source.size,(55,51,55,255));matte.alpha_composite(source)
    image=matte.convert('RGB');image.thumbnail((a.max_edge,a.max_edge),Image.Resampling.LANCZOS)
    while True:
        for quality in (75,65,55,45,35,25):
            buf=io.BytesIO();image.save(buf,format='JPEG',quality=quality,optimize=True)
            if buf.tell()<=a.max_bytes:
                a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(buf.getvalue())
                print(f'{a.output}: {buf.tell()} bytes, {image.width}x{image.height}, JPEG quality {quality}, whole image')
                return
        if min(image.size)<64:raise SystemExit('Cannot meet image budget')
        image=image.resize((max(1,int(image.width*.85)),max(1,int(image.height*.85))),Image.Resampling.LANCZOS)

if __name__=='__main__':main()
