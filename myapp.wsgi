import os.path, re

DOCUMENT_ROOT = '/var/www'

fptr = open('/var/www/django/template','r')
template = fptr.read()
fptr.close()

files = {}

def fq_to_doc_root(path):
    if (path.startswith(DOCUMENT_ROOT)):
        return path[len(DOCUMENT_ROOT):]
    return path

def no_transform(path, contents):
    return contents

def stylesheet(path, contents):
    return '<link type="text/css" rel="stylesheet" href="%s" />' % fq_to_doc_root(path)

def script_tag(path, contents):
    return '<script type="text/javascript" src="%s"></script>' % fq_to_doc_root(path)

def serve_template(path):
    data = {}
    for root, _, file_paths in os.walk(path):
        for file_path in file_paths:
            full_path = root + '/' + file_path
            fptr = open(full_path, 'r')
            content = fptr.read()
            fptr.close()
            for mapping in mappings:
                if mapping[0].match(file_path):
                    data[mapping[2]] = data.get(mapping[2], [])
                    data[mapping[2]].append(mapping[1](full_path, content))
                    break
    for mapping in mappings:
        data[mapping[2]] = '\n'.join(data.get(mapping[2], []))
    return template % data

def serve_file(path):
    fptr = open(path, 'r')
    content = fptr.read()
    fptr.close()
    return content

def nop(*args, **kwargs):
    return ''

mappings = [
    #regex, template prep function, template index, direct serve transform
    (re.compile('.*.swp'), nop, 'unused', nop),
    (re.compile('.*\.css'), stylesheet, 'style', serve_file),
    (re.compile('.*\.js'), script_tag, 'script', serve_file),
    (re.compile('.*'), no_transform, 'content', serve_template),
]

def get_file_contents(environ):
    path = "/var/www%s" % (environ['REQUEST_URI'])
    modified = os.path.getmtime(path)
    if path in files and files[path][0] >= modified:
        return files[path][1]
    for mapping in mappings:
        if mapping[0].match(path):
            files[path] = (modified, mapping[3](path))
            break
    return files[path][1]

def application(environ, start_response):
    status = '200 OK' 
    output = get_file_contents(environ)

    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]
