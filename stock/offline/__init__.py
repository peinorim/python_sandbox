def render_html_index(symbols: list = None):
    html = ""
    for symbol in symbols:
        html += f'<iframe src="offline/{symbol}.html" width="48%" height="600px" style="border:none;"></iframe>'

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Page principale</title>
</head>
<body class="container">
  <!-- Inclusion d’un fichier externe -->
  {html}
</body>
</html>
"""
