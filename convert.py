import docx
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

doc = docx.Document(r"d:\Kartik\EM-4\PRD.docx")
md_lines = []

def process_runs(para):
    line = ""
    for run in para.runs:
        t = run.text
        if run.bold and t.strip():
            t = f"**{t}**"
        elif run.italic and t.strip():
            t = f"*{t}*"
        else:
            t = t
        line += t
    return line

for block in doc.element.body:
    if isinstance(block, CT_P):
        para = Paragraph(block, doc)
        style = para.style.name if para.style else 'Normal'
        text = process_runs(para)
        
        if not para.text.strip():
            md_lines.append("")
            continue
            
        if style.startswith('Heading 1'):
            md_lines.append(f"# {text}")
        elif style.startswith('Heading 2'):
            md_lines.append(f"## {text}")
        elif style.startswith('Heading 3'):
            md_lines.append(f"### {text}")
        elif style.startswith('Heading 4'):
            md_lines.append(f"#### {text}")
        elif 'Heading' in style:
            md_lines.append(f"##### {text}")
        elif 'Bullet' in style:
            md_lines.append(f"- {text}")
        elif 'Number' in style:
            md_lines.append(f"1. {text}")
        else:
            md_lines.append(text)
            
    elif isinstance(block, CT_Tbl):
        table = Table(block, doc)
        for i, row in enumerate(table.rows):
            row_data = [cell.text.strip().replace('\n', '<br>') for cell in row.cells]
            md_lines.append("| " + " | ".join(row_data) + " |")
            if i == 0:
                md_lines.append("|" + "|".join(["---"] * len(row.cells)) + "|")
        md_lines.append("")

with open(r"d:\Kartik\EM-4\PRD.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

print("Conversion complete.")
