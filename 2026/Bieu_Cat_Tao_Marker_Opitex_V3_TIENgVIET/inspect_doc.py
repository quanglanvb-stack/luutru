from docx import Document
from zipfile import ZipFile
p=r'C:\Users\lan\Downloads\26. MG Tân Dương Vinagreen 28.8.2026.docx'
d=Document(p)
print('paras',len(d.paragraphs),'tables',len(d.tables),'shapes',len(d.inline_shapes))
for i,p in enumerate(d.paragraphs):
 t=p.text.strip()
 if t: print('P',i,repr(t))
for i,s in enumerate(d.inline_shapes): print('SHAPE',i,s.type,s.width,s.height)
with ZipFile(p) as z: print('MEDIA',[n for n in z.namelist() if n.startswith('word/media/')])