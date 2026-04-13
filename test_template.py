from flask import Flask, render_template_string

app = Flask(__name__)

TEST_HTML = '''
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
    <h1>Test Page Works!</h1>
    <p>If you see this, Flask is working correctly.</p>
</body>
</html>
'''

@app.route('/')
def test():
    return render_template_string(TEST_HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)