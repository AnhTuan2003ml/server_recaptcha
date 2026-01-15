"""
Admin HTML generation module
"""

def generate_embedded_admin_html(database_data):
    """Generate comprehensive admin HTML with CRUD functionality"""

    # Generate tables HTML
    tables_html = ""
    tables = database_data.get('tables', {})

    for table_name, table_info in tables.items():
        columns = table_info.get('columns', [])
        data = table_info.get('data', [])
        count = table_info.get('count', 0)

        tables_html += f"""
    <div class="table-container">
        <h3>{table_name} ({count} records)</h3>
        <button class="btn btn-add" onclick="showAddForm('{table_name}', {columns})">Add New Record</button>
        <table class="data-table" data-table="{table_name}">
            <thead>
                <tr>
                    <th>ID</th>"""

        # Filter out sensitive columns
        sensitive_columns = ['password_hash', 'password']
        display_columns = [col for col in columns if col not in sensitive_columns and col != 'id']

        for col in display_columns:
            # Custom display names for better UX
            display_name = {
                'key': 'API Key',
                'email': 'Email',
                'credit': 'Credit',
                'created_at': 'Created At',
                'expires_at': 'Expires At',
                'user_id': 'User ID',
                'token': 'Token',
                'otp_code': 'OTP Code',
                'amount': 'Amount',
                'status': 'Status',
                'content': 'Content'
            }.get(col, col.replace('_', ' ').title())
            tables_html += f"<th>{display_name}</th>"
        tables_html += "<th>Actions</th></tr></thead><tbody>"

        for row in data:
            row_id = row.get('id', '')
            tables_html += f'<tr data-id="{row_id}">'
            tables_html += f'<td>{row_id}</td>'

            for col in display_columns:
                value = row.get(col, '')
                # Format values for better display
                if col in ['credit', 'amount'] and value and isinstance(value, (int, float)):
                    formatted_value = f"{value:,}"
                elif col == 'status' and value:
                    status_class = 'success' if str(value).lower() == 'completed' else 'warning' if str(value).lower() == 'pending' else 'danger'
                    formatted_value = f'<span class="badge badge-{status_class}">{value}</span>'
                elif col == 'created_at' and value:
                    # Simple date formatting
                    formatted_value = str(value)[:19] if len(str(value)) > 19 else str(value)
                else:
                    formatted_value = str(value) if value else ''

                tables_html += f'<td>{formatted_value}</td>'
            tables_html += f'''
                <td>
                    <button class="btn btn-edit" onclick="editRecord('{table_name}', {row_id}, {columns})">Edit</button>
                    <button class="btn btn-delete" onclick="deleteRecord('{table_name}', {row_id})">Delete</button>
                </td>
            </tr>'''

        tables_html += "</tbody></table></div>"

    html = """<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .card { background: white; padding: 20px; border: 1px solid #ddd; border-radius: 8px; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .table-container { background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .data-table { border-collapse: collapse; width: 100%; margin-top: 10px; }
        .data-table th, .data-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        .data-table th { background: #f8f9fa; font-weight: bold; }
        .data-table tr:nth-child(even) { background: #f8f9fa; }
        .data-table tr:hover { background: #e9ecef; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin: 2px; }
        .btn-add { background: #28a745; color: white; }
        .btn-edit { background: #ffc107; color: black; }
        .btn-delete { background: #dc3545; color: white; }
        .btn-save { background: #007bff; color: white; }
        .btn-cancel { background: #6c757d; color: white; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; }
        .modal-content { background: white; margin: 10% auto; padding: 20px; border-radius: 8px; width: 80%; max-width: 600px; }
        .form-group { margin: 10px 0; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .form-buttons { text-align: right; margin-top: 20px; }
        .message { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .message.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .message.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .loading { display: none; color: #666; font-style: italic; }
        .badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 500; display: inline-block; }
        .badge-success { background: #dcfce7; color: #166534; }
        .badge-warning { background: #fef3c7; color: #92400e; }
        .badge-danger { background: #fee2e2; color: #991b1b; }
    </style>
</head>
<body>
    <h1>🛠️ Admin Database Dashboard</h1>

    <div class="summary">
        <div class="card">
            <h3>👥 Total Users: """ + str(database_data.get('summary', {}).get('total_users', 0)) + """</h3>
        </div>
        <div class="card">
            <h3>💰 Total Credit: """ + str(database_data.get('summary', {}).get('total_credit', 0)) + """</h3>
        </div>
        <div class="card">
            <h3>📊 Tables: """ + str(len(tables)) + """</h3>
        </div>
    </div>

    <div id="messages"></div>
    """ + tables_html + """

    <!-- Modal for Add/Edit -->
    <div id="crudModal" class="modal">
        <div class="modal-content">
            <h3 id="modalTitle">Add/Edit Record</h3>
            <form id="crudForm">
                <input type="hidden" id="tableName" name="table_name">
                <input type="hidden" id="recordId" name="record_id">
                <div id="formFields"></div>
                <div class="form-buttons">
                    <button type="button" class="btn btn-cancel" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-save">Save</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let currentTable = '';
        let currentRecordId = null;

        function showMessage(message, type = 'success') {
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML = `<div class="message ${type}">${message}</div>`;
            setTimeout(() => messagesDiv.innerHTML = '', 5000);
        }

        function showAddForm(tableName, columns) {
            currentTable = tableName;
            currentRecordId = null;
            document.getElementById('modalTitle').textContent = `Add New ${tableName} Record`;
            document.getElementById('tableName').value = tableName;
            document.getElementById('recordId').value = '';

            const formFields = document.getElementById('formFields');
            formFields.innerHTML = '';

            // Filter out sensitive columns and ID
            const sensitiveColumns = ['password_hash', 'password', 'id'];
            const formColumns = columns.filter(col => !sensitiveColumns.includes(col));

            formColumns.forEach(col => {
                const fieldType = col.includes('email') ? 'email' :
                                col.includes('date') ? 'date' :
                                col.includes('credit') || col.includes('amount') ? 'number' : 'text';

                const displayName = {
                    'key': 'API Key',
                    'email': 'Email',
                    'credit': 'Credit',
                    'created_at': 'Created At',
                    'expires_at': 'Expires At',
                    'user_id': 'User ID',
                    'token': 'Token',
                    'otp_code': 'OTP Code',
                    'amount': 'Amount',
                    'status': 'Status',
                    'content': 'Content'
                }[col] || col.replace('_', ' ').replace(/\\b\\w/g, l => l.toUpperCase());

                const required = !['created_at', 'expires_at'].includes(col); // Make timestamps optional

                formFields.innerHTML += `
                    <div class="form-group">
                        <label for="${col}">${displayName}:</label>
                        <input type="${fieldType}" id="${col}" name="${col}" ${required ? 'required' : ''}>
                    </div>`;
            });

            document.getElementById('crudModal').style.display = 'block';
        }

        function editRecord(tableName, recordId, columns) {
            currentTable = tableName;
            currentRecordId = recordId;
            document.getElementById('modalTitle').textContent = `Edit ${tableName} Record (ID: ${recordId})`;
            document.getElementById('tableName').value = tableName;
            document.getElementById('recordId').value = recordId;

            // Get current data from table row
            const row = document.querySelector(`tr[data-id="${recordId}"]`);
            const cells = row.querySelectorAll('td');

            const formFields = document.getElementById('formFields');
            formFields.innerHTML = '';

            // Filter out sensitive columns and ID
            const sensitiveColumns = ['password_hash', 'password', 'id'];
            const formColumns = columns.filter(col => !sensitiveColumns.includes(col));

            let colIndex = 1; // Skip ID column
            formColumns.forEach(col => {
                const currentValue = cells[colIndex] ? cells[colIndex].textContent : '';
                const fieldType = col.includes('email') ? 'email' :
                                col.includes('date') ? 'date' :
                                col.includes('credit') || col.includes('amount') ? 'number' : 'text';

                const displayName = {
                    'key': 'API Key',
                    'email': 'Email',
                    'credit': 'Credit',
                    'created_at': 'Created At',
                    'expires_at': 'Expires At',
                    'user_id': 'User ID',
                    'token': 'Token',
                    'otp_code': 'OTP Code',
                    'amount': 'Amount',
                    'status': 'Status',
                    'content': 'Content'
                }[col] || col.replace('_', ' ').replace(/\\b\\w/g, l => l.toUpperCase());

                const required = !['created_at', 'expires_at'].includes(col); // Make timestamps optional

                formFields.innerHTML += `
                    <div class="form-group">
                        <label for="${col}">${displayName}:</label>
                        <input type="${fieldType}" id="${col}" name="${col}" value="${currentValue}" ${required ? 'required' : ''}>
                    </div>`;
                colIndex++;
            });

            document.getElementById('crudModal').style.display = 'block';
        }

        function deleteRecord(tableName, recordId) {
            if (confirm(`Are you sure you want to delete record ${recordId} from ${tableName}?`)) {
                fetch(`/recaptcha/admin/delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ table_name: tableName, record_id: recordId })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage(`Record ${recordId} deleted successfully`);
                        location.reload();
                    } else {
                        showMessage(data.message || 'Delete failed', 'error');
                    }
                })
                .catch(error => {
                    showMessage('Delete failed: ' + error.message, 'error');
                });
            }
        }

        function closeModal() {
            document.getElementById('crudModal').style.display = 'none';
        }

        document.getElementById('crudForm').addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            let data = Object.fromEntries(formData);

            // Remove empty values
            Object.keys(data).forEach(key => {
                if (data[key] === '') {
                    delete data[key];
                }
            });

            const url = currentRecordId ? '/recaptcha/admin/update' : '/recaptcha/admin/add';
            const method = 'POST';

            fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    const action = currentRecordId ? 'updated' : 'added';
                    showMessage(`Record ${action} successfully`);
                    closeModal();
                    location.reload();
                } else {
                    showMessage(result.error || result.message || `Operation failed`, 'error');
                }
            })
            .catch(error => {
                showMessage('Operation failed: ' + error.message, 'error');
            });
        });

        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('crudModal');
            if (event.target === modal) {
                closeModal();
            }
        }
    </script>
</body>
</html>"""
    return html
