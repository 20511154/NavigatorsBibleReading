# Minimal test for PythonAnywhere
def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'text/html')]
    start_response(status, headers)
    return [b'<h1>Hello from PythonAnywhere!</h1><p>If you see this, the basic setup works.</p>']
