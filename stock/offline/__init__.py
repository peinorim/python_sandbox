from datetime import datetime, timezone


def render_html_index(symbols: list = None):
    # Générer les divs placeholder pour chaque symbole
    divs = "\n".join(
        f'    <div class="chart-cell" id="chart-{symbol.replace(".", "-").replace("=", "-").replace("^", "_")}" '
        f'data-src="offline/{symbol}.html"></div>'
        for symbol in symbols
    )

    timestamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S %Z")

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-4.0.0.min.js"></script>
  <link rel="icon" href="https://avatars.githubusercontent.com/u/5997976?v=4">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #0e1117;
      color: #c9d1d9;
      font-family: Arial, Helvetica, sans-serif;
      padding: 1rem;
    }}
    header {{
      text-align: center;
      padding: 0.8rem 0 1.2rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.75rem;
    }}
    .chart-cell {{
      background: #161b22;
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 10px;
      overflow: hidden;
      min-height: 500px;
      position: relative;
    }}
    @media (max-width: 600px) {{
      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
    /* Spinner de chargement */
    .chart-cell:empty::after {{
      content: '';
      position: absolute;
      top: 50%; left: 50%;
      width: 28px; height: 28px;
      margin: -14px 0 0 -14px;
      border: 3px solid rgba(255,255,255,0.08);
      border-top-color: #58a6ff;
      border-radius: 50%;
      animation: spin .7s linear infinite;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    /* Plotly chart remplit sa cellule */
    .chart-cell .plotly-graph-div {{
      width: 100% !important;
      height: 100% !important;
    }}
  </style>
</head>
<body>
  <header>
    <h2>Dernière mise à jour : {timestamp}</h2>
  </header>
  <div class="grid">
{divs}
  </div>

  <script>
    /**
     * Charge chaque fichier HTML Plotly via fetch() et l'injecte dans le DOM.
     * Plotly.js est déjà chargé globalement dans le <head>, donc on ignore les
     * scripts src et on ne réinjecte que les scripts inline (Plotly.newPlot, etc.).
     */
    document.querySelectorAll('.chart-cell[data-src]').forEach(cell => {{
      fetch(cell.dataset.src)
        .then(r => r.text())
        .then(html => {{
          const doc = new DOMParser().parseFromString(html, 'text/html');
          const content = doc.body || doc.documentElement;

          // Injecter les éléments non-script
          cell.innerHTML = content.innerHTML;

          // Réinjecter uniquement les scripts inline (pas les src externes)
          content.querySelectorAll('script').forEach(oldScript => {{
            if (oldScript.src) return; // Plotly.js déjà chargé, on skip
            const s = document.createElement('script');
            s.textContent = oldScript.textContent;
            cell.appendChild(s);
          }});
        }})
        .catch(() => {{
          cell.innerHTML = '<p style="color:#f85149;padding:1rem;">Erreur de chargement</p>';
        }});
    }});
  </script>
</body>
</html>"""
