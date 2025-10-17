from datetime import datetime


def render_html_index(symbols: list = None):
    html = ""
    for symbol in symbols:
        html += f'<iframe src="offline/{symbol}.html" width="48%" height="600px" style="border:none;"></iframe>'

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Dashboard</title>
</head>
<body style="background-color:black;">
  <h2 style='color:lightgray;'>Last update on : {datetime.now().isoformat()}</h2>
  <!-- Inclusion d’un fichier externe -->
  <div>
    {html}
  </div>
</body>
</html>
"""
