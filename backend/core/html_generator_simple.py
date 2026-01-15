"""
HTML Generator for Admin Dashboard - Simplified
"""
from datetime import datetime

def generate_embedded_admin_html(database_data):
    """Tạo HTML admin với data embedded"""
    try:
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
    <title>Admin Database Viewer</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #4f46e5; color: white; padding: 20px; text-align: center; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .card {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
        .copyable {{ cursor: pointer; background: #e0f2fe; padding: 2px 4px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Admin Database Viewer</h1>
            <p>Updated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>

        <div class="summary">
            <div class="card">
                <h3>Users</h3>
                <div>{total_users}</div>
            </div>
            <div class="card">
                <h3>Credit</h3>
                <div>{total_credit}</div>
            </div>
            <div class="card">
                <h3>Sessions</h3>
                <div>{total_sessions}</div>
            </div>
            <div class="card">
                <h3>Transactions</h3>
                <div>{total_transactions}</div>
            </div>
        </div>

        <div>
            {tables_html}
        </div>
    </div>

    <script>
        function copyToClipboard(text) {{
            navigator.clipboard.writeText(text).then(function() {{
                alert('Copied: ' + text);
            }});
        }}
    </script>
</body>
</html>"""

        return html
    except Exception as e:
        return f"<h1>Error generating HTML: {str(e)}</h1>"

def generate_embedded_table_html(table_name, table_info):
    """Tạo HTML table với data embedded"""
    try:
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
            <div style="margin: 20px 0;">
                <h2>{table_title} ({count} records)</h2>
                <table>
                    <thead>
                        <tr>"""

        # Header columns
        for col in display_columns:
            display_name = {{
                'id': 'ID',
                'email': 'Email',
                'credit': 'Credit',
                'created_at': 'Created',
                'key': 'API Key',
                'token': 'Token',
                'user_id': 'User ID',
                'expires_at': 'Expires',
                'otp_code': 'OTP Code',
                'amount': 'Amount',
                'status': 'Status',
                'content': 'Content'
            }}.get(col, col.title())
            html += f"<th>{display_name}</th>"

        html += """
                        </tr>
                    </thead>
                    <tbody>"""

        if not rows:
            html += f'<tr><td colspan="{len(display_columns)}" style="text-align: center;">No data</td></tr>'
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
            </div>"""

        return html
    except Exception as e:
        return f"<div>Error generating table: {str(e)}</div>"

def format_value_for_html(value, column):
    """Format giá trị cho HTML"""
    try:
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
            return f'<span class="copyable" onclick="copyToClipboard(\'{value}\')" title="Click to copy">{value}</span>'

        # Truncate long strings
        if isinstance(value, str) and len(value) > 50:
            return value[:50] + '...'

        return str(value)
    except Exception as e:
        return f"Error: {str(e)}"
