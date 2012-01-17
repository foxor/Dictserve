import os.path, re

fptr = open('/var/www/django/template','r')
template = fptr.read()
fptr.close()

files = {}

mappings = [
    (re.compile('(index\.html|content)'), 'content'),
    (re.compile('.*\.css'), 'style'),
    (re.compile('.*\.js'), 'script'),
]

def get_file_contents(environ):
    path = "/var/www%s" % (environ['REQUEST_URI'])
    modified = os.path.getmtime(path)
    if path in files and files[path][0] >= modified:
        return files[path][1]
    data = {}
    for root, _, file_paths in os.walk(path):
        for file_path in file_paths:
            fptr = open(root + '/' + file_path, 'r')
            content = fptr.read()
            fptr.close()
            for mapping in mappings:
                if mapping[0].match(file_path):
                    data[mapping[1]] = data.get(mapping[1], [])
                    data[mapping[1]].append(content)
    for mapping in mappings:
        data[mapping[1]] = '\n'.join(data.get(mapping[1], []))
    formatted = template % data
    files[path] = (modified, formatted)
    return files[path][1]

def application(environ, start_response):
    status = '200 OK' 
    output = get_file_contents(environ)

    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]
