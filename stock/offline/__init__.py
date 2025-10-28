from datetime import datetime, timezone


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
  <link rel="icon" type="image/x-icon" href="https://icons.iconarchive.com/icons/graphicloads/colorful-long-shadow/256/Chart-icon.png">
</head>
<body style="background-color:black;font-family: Arial, Helvetica, sans-serif;">
  <h2 style='color:lightgray;'>Last update on : {datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%dT%H:%M:%S %Z')}</h2>
  <!-- Inclusion d’un fichier externe -->
  <div>
    {html}
  </div>
</body>
</html>
"""
