import base64
from django.contrib.staticfiles import finders

def logo_b64(request):
    path = finders.find("images/logo_cnss.png")
    if not path:
        return {"logo_b64": None}
    with open(path, "rb") as f:
        data = f.read()
    return {"logo_b64": "data:image/png;base64," + base64.b64encode(data).decode("ascii")}
