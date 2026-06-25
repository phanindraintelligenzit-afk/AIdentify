from PIL import Image, ImageDraw, ImageFont
import math

# Instagram square 1080x1080
W, H = 1080, 1080
img = Image.new("RGB", (W, H), "#0a0e1a")
draw = ImageDraw.Draw(img)

# Gradient background (dark blue to black)
for y in range(H):
    r = int(10 + (255-10) * (y / H) * 0.3)
    g = int(14 + (255-14) * (y / H) * 0.2)
    b = int(26 + (255-26) * (y / H) * 0.4)
    draw.rectangle([(0, y), (W, y)], fill=(r, g, b))

# Let's overlay a nicer radial gradient
for y in range(H):
    for x in range(W):
        cx, cy = W * 0.3, H * 0.4
        dx, dy = x - cx, y - cy
        dist = math.sqrt(dx*dx + dy*dy)
        max_dist = math.sqrt(cx*cx + cy*cy)
        factor = max(0, 1 - dist/(max_dist*0.9))
        r = int(10 + 30 * factor)
        g = int(14 + 50 * factor)
        b = int(26 + 100 * factor)
        img.putpixel((x, y), (r, g, b))

# Neural network nodes and connections
nodes = []
for i in range(6):
    for j in range(3):
        x = 180 + i * 150 + (j % 2) * 75
        y = 180 + j * 300 + (i % 2) * 60
        nodes.append((x, y))

# Connections
for i, (x1, y1) in enumerate(nodes):
    for j, (x2, y2) in enumerate(nodes):
        if i < j:
            dist = math.sqrt((x1-x2)**2 + (y1-y2)**2)
            if dist < 400:
                opacity = int(80 * (1 - dist/400))
                draw.line([(x1, y1), (x2, y2)], fill=(37, 99, 235, opacity), width=3)

# Nodes
for x, y in nodes:
    draw.ellipse([(x-18, y-18), (x+18, y+18)], fill=(37, 99, 235), outline=(147, 197, 253), width=4)
    draw.ellipse([(x-8, y-8), (x+8, y+8)], fill=(255, 255, 255))

def draw_text_centered(text, y, font, fill):
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    x = (W - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return y + (bbox[3]-bbox[1])

try:
    font_bold = ImageFont.truetype("arial.ttf", 72)
    font_sub = ImageFont.truetype("arial.ttf", 36)
    font_tag = ImageFont.truetype("arial.ttf", 28)
except:
    font_bold = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_tag = ImageFont.load_default()

# Accent line
line_y = 680
draw.rectangle([(W//2 - 120, line_y), (W//2 + 120, line_y+4)], fill=(37, 99, 235))

# Brand text
y = line_y + 60
y = draw_text_centered("AGENTSFACTORY", y, font_bold, (255, 255, 255))
y += 30
y = draw_text_centered("AI Automation Agency", y, font_sub, (147, 197, 253))
y += 40
draw_text_centered("#BuildBots #AI #Automation", y, font_tag, (148, 163, 184))

# @mention tag
draw.text((60, H - 80), "@agentsfactory", font=font_tag, fill=(148, 163, 184))

# Subtle corner branding
draw.text((W - 350, H - 80), "agentsfactory.ai", font=font_tag, fill=(148, 163, 184))

img.save(r"C:\Users\Admin\Projects\AgentsFactory\docs\social-assets\instagram_daily_01.png", "PNG", optimize=True)
print("Saved successfully")
