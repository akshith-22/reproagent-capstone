#!/usr/bin/env python3
"""Embed execution evidence and compact formatting in the generated DOCX."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "proposal/Capstone_Proposal_completed.docx"
IMAGE = ROOT / "evidence/baseline_run.png"


def add_before(text: str, marker: str, addition: str) -> str:
    index = text.find(marker)
    if index < 0:
        raise RuntimeError(f"DOCX marker not found: {marker}")
    return text[:index] + addition + text[index:]


with zipfile.ZipFile(DOCX, "r") as source:
    members = {name: source.read(name) for name in source.namelist()}

document = members["word/document.xml"].decode("utf-8")
relationships = members["word/_rels/document.xml.rels"].decode("utf-8")
content_types = members["[Content_Types].xml"].decode("utf-8")

# textutil does not honor all HTML print CSS. Compact its generated half-point
# sizes directly so the seven short sections occupy the first page.
document = document.replace('w:val="25"', 'w:val="17"')
document = document.replace('w:val="29"', 'w:val="20"')
document = document.replace('w:val="42"', 'w:val="28"')
document = document.replace('w:after="160"', 'w:after="80"')
document = document.replace('w:after="106"', 'w:after="45"')

heading = '<w:t xml:space="preserve">Baseline Execution Evidence</w:t>'
heading_index = document.find(heading)
if heading_index < 0:
    raise RuntimeError("Evidence heading not found")
paragraph_index = document.rfind("<w:p>", 0, heading_index)
properties_index = document.find("<w:pPr>", paragraph_index, heading_index)
if paragraph_index < 0 or properties_index < 0:
    raise RuntimeError("Evidence heading paragraph properties not found")
properties_index += len("<w:pPr>")
document = (
    document[:properties_index]
    + '<w:pageBreakBefore w:val="1"/>'
    + document[properties_index:]
)

caption = (
    '<w:t xml:space="preserve">The image below records the successful local LLM '
    'agent run on September 6, 2026.</w:t>'
)
caption_index = document.find(caption)
if caption_index < 0:
    raise RuntimeError("Evidence caption not found")
caption_end = document.find("</w:p>", caption_index) + len("</w:p>")

# 5.55 inches square at 914400 EMU per inch.
extent = 5_075_000
drawing = f'''<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>
<wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" distT="0" distB="0" distL="0" distR="0">
<wp:extent cx="{extent}" cy="{extent}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>
<wp:docPr id="1" name="Baseline execution screenshot" descr="Successful ReproAgent test and baseline output"/>
<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>
<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="0" name="baseline_run.png"/><pic:cNvPicPr/></pic:nvPicPr>
<pic:blipFill><a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="rId3"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{extent}" cy="{extent}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''
document = document[:caption_end] + drawing + document[caption_end:]

page_setup = (
    '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
    '<w:pgMar w:top="500" w:right="576" w:bottom="500" w:left="576" '
    'w:header="250" w:footer="250" w:gutter="0"/></w:sectPr>'
)
document = document.replace("<w:sectPr></w:sectPr>", page_setup)

relationships = add_before(
    relationships,
    "</Relationships>",
    '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/baseline_run.png"/>',
)
content_types = add_before(
    content_types,
    "</Types>",
    '<Default Extension="png" ContentType="image/png"/>',
)

members["word/document.xml"] = document.encode("utf-8")
members["word/_rels/document.xml.rels"] = relationships.encode("utf-8")
members["[Content_Types].xml"] = content_types.encode("utf-8")
members["word/media/baseline_run.png"] = IMAGE.read_bytes()

with tempfile.NamedTemporaryFile(
    prefix="proposal-", suffix=".docx", dir=DOCX.parent, delete=False
) as temporary:
    temporary_path = Path(temporary.name)

with zipfile.ZipFile(temporary_path, "w", zipfile.ZIP_DEFLATED) as target:
    for name, data in members.items():
        target.writestr(name, data)

temporary_path.replace(DOCX)
print(f"Embedded {IMAGE.name} in {DOCX.name}")
