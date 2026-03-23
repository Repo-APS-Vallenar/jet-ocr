import sys
sys.path.append('.')
from app import app, db, RegistroOCR

with app.app_context():
    qs = RegistroOCR.query.all()
    macs = {}
    for r in qs:
        if r.mac:
             macs.setdefault(r.mac.strip().upper(), set()).add(r.sn.strip().upper())
             
    dups = {m: list(s) for m, s in macs.items() if len(s) > 1}
    print("MACs con multiples SN leidos en LOG:", dups)
