from PIL import Image, ImageDraw, ImageFont
import os

from .main import resource_path

class Draw():
    @classmethod
    async def draw_card(cls, pic_chosen, title, text, from_user):
        fontPath = {
            'title': f'{resource_path}/font/Mamelon.otf',
            'text': f'{resource_path}/font/sakura.ttf'
        }
        imgPath = pic_chosen

        img = Image.open(imgPath)

        # Draw title
        draw = ImageDraw.Draw(img)
        font_size = 45
        color = '#F5F5F5'
        image_font_center = (140, 99)
        ttfront = ImageFont.truetype(fontPath['title'], font_size)
        bbox = ttfront.getbbox(title)
        font_length = (bbox[2] - bbox[0], bbox[3] - bbox[1])
        draw.text((image_font_center[0]-font_length[0]/2, image_font_center[1]-font_length[1]/2),
                    title, fill=color,font=ttfront)
        # Text rendering
        font_size = 25
        color = '#323232'
        image_font_center = [140, 297]
        ttfront = ImageFont.truetype(fontPath['text'], font_size)
        result = cls.decrement(text)
        if not result[0]:
            return 
        textVertical = []
        for i in range(0, result[0]):
            font_height = len(result[i + 1]) * (font_size + 4)
            textVertical = cls.vertical(result[i + 1])
            x = int(image_font_center[0] + (result[0] - 2) * font_size / 2 + 
                    (result[0] - 1) * 4 - i * (font_size + 4))
            y = int(image_font_center[1] - font_height / 2)
            draw.text((x, y), textVertical, fill = color, font = ttfront)
        # Save
        os.system(f'mkdir -p {resource_path}/out')
        outPath = f'{resource_path}/out/{from_user}.png'
        img.save(outPath)
        return outPath

    @classmethod
    def decrement(cls, text):
        length = len(text)
        result = []
        cardinality = 9
        if length > 4 * cardinality:
            return [False]
        numberOfSlices = 1
        while length > cardinality:
            numberOfSlices += 1
            length -= cardinality
        result.append(numberOfSlices)
        # Optimize for two columns
        space = ' '
        length = len(text)
        if numberOfSlices == 2:
            if length % 2 == 0:
                # even
                fillIn = space * int(9 - length / 2)
                return [numberOfSlices, text[:int(length / 2)] + fillIn, fillIn + text[int(length / 2):]]
            else:
                # odd number
                fillIn = space * int(9 - (length + 1) / 2)
                return [numberOfSlices, text[:int((length + 1) / 2)] + fillIn,
                                        fillIn + space + text[int((length + 1) / 2):]]
        for i in range(0, numberOfSlices):
            if i == numberOfSlices - 1 or numberOfSlices == 1:
                result.append(text[i * cardinality:])
            else:
                result.append(text[i * cardinality:(i + 1) * cardinality])
        return result

    @classmethod
    def vertical(cls, str):
        list = []
        for s in str:
            list.append(s)
        return '\n'.join(list)