

from flask import Flask, request, send_file, make_response
import pandas as pd
import io

app = Flask(__name__)

# Define the function to categorize based on text combination
def categorize_cell(value):
    if isinstance(value, str):  # Ensure the value is a string
        if 'CDTFA' in value:
            return 'Sales Tax'
        elif 'BANKCARD' in value:
            return 'Deposit'
        elif 'text4' in value or 'text5' in value:
            return 'Category C'
        else:
            return 'Other'
    return 'Other'

def process_dataframe(df):
    # Remove unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Apply a function to a specific column (example)
    column_name = "Unnamed"  # 'Replace with your column name'
    if column_name in df.columns:
        df[column_name] = df[column_name].apply(lambda x: x * 2 if pd.api.types.is_numeric_dtype(type(x)) else x)
    
    return df

# Upload the CSV File
@app.route('/')
def upload_form():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <title>Upload CSV File</title>
        <style>
            body {
                background-color: #f8f9fa;
            }
            .container {
                max-width: 600px;
                margin-top: 50px;
                padding: 20px;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            .logo {
                max-width: 150px;
                margin-bottom: 20px;
            }
            .drop-zone {
                border: 2px dashed #007bff;
                padding: 50px;
                text-align: center;
                cursor: pointer;
                background-color: #f1f1f1;
                transition: background-color 0.3s ease;
                font-size: 18px;
                color: #555;
                height: 200px;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .drop-zone.dragover {
                background-color: #d9ecff;
            }
            input[type="file"] {
                display: none;
            }
            button {
                margin-top: 20px;
                width: 100%;
            }
            .file-name {
                margin-top: 20px;
                font-size: 16px;
                color: #333;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <img src="/static/logo.png" alt="Company Logo" class="logo">
            <h1 class="text-primary">Upload CSV File</h1>
            <div id="dropZone" class="drop-zone">
                Drag & Drop CSV Here or Click to Upload
            </div>
            <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" id="fileInput" name="file" accept=".csv">
                <button type="submit" class="btn btn-primary">Upload</button>
            </form>
            <div id="fileName" class="file-name" style="display: none;">
                <strong>Selected File:</strong> <span id="fileNameText"></span>
            </div>
        </div>
        <script>
            const dropZone = document.getElementById('dropZone');
            const fileInput = document.getElementById('fileInput');
            const fileNameDiv = document.getElementById('fileName');
            const fileNameText = document.getElementById('fileNameText');

            // Highlight drop zone on drag over
            dropZone.addEventListener('dragover', (event) => {
                event.preventDefault();
                dropZone.classList.add('dragover');
            });

            // Remove highlight on drag leave
            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('dragover');
            });

            // Handle file drop
            dropZone.addEventListener('drop', (event) => {
                event.preventDefault();
                dropZone.classList.remove('dragover');
                const files = event.dataTransfer.files;
                if (files.length) {
                    fileInput.files = files; // Assign files to the input element
                    displayFileName(files[0].name);
                }
            });

            // Trigger file input on click
            dropZone.addEventListener('click', () => {
                fileInput.click();
            });

            // Handle file input change
            fileInput.addEventListener('change', (event) => {
                const file = event.target.files[0];
                if (file) {
                    displayFileName(file.name);
                }
            });

            // Display selected file name
            function displayFileName(name) {
                fileNameText.textContent = name;
                fileNameDiv.style.display = 'block';
            }
        </script>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        # Validate file type
        if not file.filename.endswith('.csv'):
            return "Invalid file type! Please upload a CSV file.", 400
        try:
            # Load the CSV and process it
            df = pd.read_csv(file)
            if "Description" not in df.columns:
                return "The file does not contain the required 'Description' column.", 400
            df['Category'] = df['Description'].apply(categorize_cell)

            # Create the pivot table
            pivot_table = pd.pivot_table(
                df,
                values="Amount",  # Replace with your column name
                index="Category",
                aggfunc="sum",
                fill_value=0
            )

            # Store pivot table globally for export
            app.config['pivot_table'] = pivot_table

            html_table = pivot_table.to_html(classes="table table-striped")
            return f'''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <title>Account Codings</title>
                <style>
                    body {{
                        background-color: #f8f9fa;
                    }}
                    .container {{
                        max-width: 800px;
                        margin-top: 50px;
                        padding: 20px;
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        text-align: center;
                    }}
                    .logo {{
                        max-width: 150px;
                        margin-bottom: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container mt-5">
                    <img src="/static/logo.png" alt="Company Logo" class="logo">
                    <h1 class="text-primary">Account Codings</h1>
                    {html_table}
                    <div class="text-center mt-4">
                        <a href="/export/csv" class="btn btn-primary me-2">Download CSV</a>
                    </div>
                </div>
            </body>
            </html>
            '''
        except Exception as e:
            return f"Error processing file: {e}", 500
    return "No file uploaded!", 400

@app.route('/export/<filetype>', methods=['GET'])
def export_table(filetype):
    try:
        pivot_table = app.config.get('pivot_table')
        if pivot_table is None:
            return "No data to export. Please upload a file first.", 400

        if filetype == 'csv':
            output = io.StringIO()
            pivot_table.to_csv(output)
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name='pivot_table.csv'
            )
        else:
            return "Unsupported file type!", 400
    except Exception as e:
        return f"Error exporting file: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)

# Load the CSV file
#file_path = r'C:\Users\jared\OneDrive\Python Code Files\Test_Bank_File.csv'  # Replace with your file path
#data = pd.read_csv(file_path)


# Apply the function to a specific column (replace 'ColumnName' with your column name)
#data['Category'] = data['Description'].apply(categorize_cell)

# Save the updated data to a new CSV
#output_path = r'C:\Users\jared\OneDrive\Python Code Files\Test_Bank_File_Output.csv'  # Replace with your desired output path
#data.to_csv(output_path, index=False)

#print(f"Categorized data saved to {output_path}")