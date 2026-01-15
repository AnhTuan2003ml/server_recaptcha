"""
Very simple HTML generator
"""

def generate_embedded_admin_html(database_data):
    """Simple HTML generator"""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f0f0f0; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .card { background: white; padding: 15px; border: 1px solid #ddd; border-radius: 5px; flex: 1; }
    </style>
</head>
<body>
    <h1>Admin Database Viewer</h1>

    <div class="summary">
        <div class="card">
            <h3>Users: """ + str(database_data.get('summary', {}).get('total_users', 0)) + """</h3>
        </div>
        <div class="card">
            <h3>Credit: """ + str(database_data.get('summary', {}).get('total_credit', 0)) + """</h3>
        </div>
    </div>

    <h2>Tables</h2>
    <p>Data loaded successfully</p>
</body>
</html>"""
    return html
