"""
HTML Generator for Admin Dashboard
"""
from datetime import datetime

def generate_embedded_admin_html(database_data):
    """Tạo HTML admin với data embedded"""
    tables_data = database_data['tables']
    summary = database_data['summary']

    # Format summary values
    total_users = summary.get('total_users', 0)
    total_credit = f"{summary.get('total_credit', 0):,}"
    total_sessions = summary.get('total_sessions', 0)
    total_transactions = summary.get('total_transactions', 0)
    total_otps = summary.get('total_otps', 0)
    database_size = summary.get('database_size', 0)

    # Tạo HTML cho tables
    tables_html = ""
    table_order = ['users', 'sessions', 'transactions', 'otps']
    for table_name in table_order:
        table_info = tables_data.get(table_name)
        if table_info:
            tables_html += generate_embedded_table_html(table_name, table_info)

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Database Viewer - Recaptcha API</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8fafc;
        }}

        .card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            border-left: 4px solid #4f46e5;
        }}

        .card h3 {{
            color: #1f2937;
            margin-bottom: 10px;
            font-size: 1.2em;
        }}

        .card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #4f46e5;
        }}

        .tables-section {{
            padding: 30px;
        }}

        .table-container {{
            margin-bottom: 40px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            overflow: hidden;
        }}

        .table-header {{
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 20px;
            font-size: 1.3em;
            font-weight: bold;
        }}

        .table-wrapper {{
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}

        th {{
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
        }}

        tr:nth-child(even) {{
            background: #f9fafb;
        }}

        .badge {{
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
        }}

        .badge-success {{
            background: #dcfce7;
            color: #166534;
        }}

        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}

        .badge-danger {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .copyable {{
            cursor: pointer;
            background: #f0f9ff;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
        }}

        .timestamp {{
            color: #6b7280;
            font-size: 0.9em;
            margin-top: 5px;
        }}

        @media (max-width: 768px) {{
            .header {{
                padding: 20px;
            }}

            .header h1 {{
                font-size: 2em;
            }}

            .summary-cards {{
                padding: 20px;
                grid-template-columns: 1fr;
            }}

            .tables-section {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Admin Database Viewer</h1>
            <p>Recaptcha API - Database Management System</p>
            <div class="timestamp">Cap nhat: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>
        </div>

        <div class="summary-cards">
            <div class="card">
                <h3>Users</h3>
                <div class="value" style="color: #4f46e5">{total_users}</div>
            </div>
            <div class="card">
                <h3>Credit</h3>
                <div class="value" style="color: #10b981">{total_credit}</div>
            </div>
            <div class="card">
                <h3>Sessions</h3>
                <div class="value" style="color: #f59e0b">{total_sessions}</div>
            </div>
            <div class="card">
                <h3>Transactions</h3>
                <div class="value" style="color: #ef4444">{total_transactions}</div>
            </div>
            <div class="card">
                <h3>OTP Codes</h3>
                <div class="value" style="color: #8b5cf6">{total_otps}</div>
            </div>
            <div class="card">
                <h3>Tables</h3>
                <div class="value" style="color: #06b6d4">{database_size}</div>
            </div>
        </div>

        <div class="tables-section">
            {tables_html}
        </div>
    </div>

    <script>
        // Copy to clipboard function
        function copyToClipboard(text) {{
            navigator.clipboard.writeText(text).then(function() {{
                const notification = document.createElement('div');
                notification.textContent = 'Da copy!';
                notification.style.cssText = 'position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #10b981; color: white; padding: 10px 20px; border-radius: 8px; z-index: 10000; font-weight: bold;';
                document.body.appendChild(notification);
                setTimeout(() => document.body.removeChild(notification), 2000);
            }}).catch(function(err) {{
                console.error('Khong the copy:', err);
            }});
        }}
    </script>
</body>
</html>"""

    return html

def generate_embedded_table_html(table_name, table_info):
    """Tạo HTML table với data embedded"""
    columns = table_info['columns']
    rows = table_info['data']
    count = table_info['count']

    table_title = {{
        'users': 'Users',
        'sessions': 'Sessions',
        'transactions': 'Transactions',
        'otps': 'OTP Codes'
    }}.get(table_name, table_name.title())

    # Lọc bỏ cột password_hash
    display_columns = [col for col in columns if col != 'password_hash']

    html = f"""
        <div class="table-container">
            <div class="table-header">
                <span>{table_title} ({count} records)</span>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>"""

    # Header columns
    for col in display_columns:
        display_name = {{
            'id': 'ID',
            'email': 'Email',
            'credit': 'Credit',
            'created_at': 'Ngay tao',
            'key': 'API Key',
            'token': 'Token',
            'user_id': 'User ID',
            'expires_at': 'Het han',
            'otp_code': 'OTP Code',
            'amount': 'So tien',
            'status': 'Trang thai',
            'content': 'Noi dung'
        }}.get(col, col.title())
        html += f"<th>{display_name}</th>"

    html += """
                        </tr>
                    </thead>
                    <tbody>"""

    if not rows:
        html += f'<tr><td colspan="{len(display_columns)}" style="text-align: center; padding: 40px;">Khong co du lieu</td></tr>'
    else:
        for row in rows:
            html += "<tr>"
            for col in display_columns:
                value = row.get(col, '')
                display_value = format_value_for_html(value, col)
                html += f"<td>{display_value}</td>"
            html += "</tr>"

    html += """
                    </tbody>
                </table>
            </div>
        </div>"""

    return html

def format_value_for_html(value, column):
    """Format giá trị cho HTML"""
    if value is None or value == '':
        return 'NULL'

    if column in ['created_at', 'expires_at']:
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime('%d/%m/%Y %H:%M:%S')
            except:
                return str(value)
        elif isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(value)
            return dt.strftime('%d/%m/%Y %H:%M:%S')

    if column in ['credit', 'amount'] and isinstance(value, (int, float)):
        return f"{value:,}"

    if column == 'status':
        status = str(value).lower()
        if status == 'completed':
            return f'<span style="color: green;">{value}</span>'
        elif status == 'failed':
            return f'<span style="color: red;">{value}</span>'
        else:
            return f'<span style="color: orange;">{value}</span>'

    if column in ['password_hash', 'key'] and value == '***HIDDEN***':
        return '***HIDDEN***'

    # API key có thể copy
    if column == 'key':
        return f'<span class="copyable" onclick="copyToClipboard(\'{value}\')" title="Click de copy">{value}</span>'

    # Truncate long strings
    if isinstance(value, str) and len(value) > 50:
        return value[:50] + '...'

    return str(value)
