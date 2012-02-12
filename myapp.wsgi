import os.path, re

DOCUMENT_ROOT = '/var/www-ij'

fptr = open('%s/django/template' % DOCUMENT_ROOT,'r')
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

def nop(*args, **kwargs):
    return ""

ignore_dirs = [
    re.compile('.*\.git'),
    re.compile('.*/\..*'),
]

def serve_template(path):
    data = {}
    for root, dirs, file_paths in os.walk(path):
        dirs[:] = [dir for dir in dirs if not [reason for reason in ignore_dirs if reason.match(dir)]]
        file_paths = [f for f in file_paths if not [reason for reason in ignore_dirs if reason.match(f)]]
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
    return template % data, "text/html", '200 OK' 

def serve_css(path):
    fptr = open(path, 'r')
    content = fptr.read()
    fptr.close()
    return content, "text/css", '200 OK' 

def serve_js(path):
    fptr = open(path, 'r')
    content = fptr.read()
    fptr.close()
    return content, "text/javascript", '200 OK' 

def no_serve(*args, **kwargs):
    return 'Auauthorized', 'text/html', '403 Forbidden'

mappings = [
    #regex, template prep function, template index, direct serve transform
    (re.compile('.*\.swp'), nop, 'unused', no_serve),
    (re.compile('.*\.css'), stylesheet, 'style', serve_css),
    (re.compile('.*\.js'), script_tag, 'script', serve_js),
    (re.compile('.*'), no_transform, 'content', serve_template),
]

def get_file_contents(environ):
    path = "%s%s" % (DOCUMENT_ROOT, environ['REQUEST_URI'])
    modified = os.path.getmtime(path)
    if path in files and files[path][0] >= modified:
        return files[path][1]
    for mapping in mappings:
        if mapping[0].match(path):
            files[path] = (modified, mapping[3](path))
            return files[path][1]
    return "Error 404", "text/html", "404 Not Found"

def application(environ, start_response):
    output, type, status = get_file_contents(environ)

    response_headers = [('Content-type', type),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]
