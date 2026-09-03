import subprocess, json
r = subprocess.run(['gh','run','list','--repo','esterz123/campagne-zoho','--limit','12',
    '--json','name,status,conclusion,createdAt,workflowName'],
    capture_output=True, text=True)
print(r.stdout or r.stderr)
