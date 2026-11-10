import struct,csv,sys
o=open(sys.argv[1],'rb').read(); m=open(sys.argv[2],'rb').read()
rows={int(r['id']):r for r in csv.DictReader(open(sys.argv[3],encoding='utf-8-sig'))}
def parse(d):
    n,ps,bs=struct.unpack_from('<3I',d,0);B=len(d)-bs;assert B==12+n*4+ps
    R=[];p=12
    for _ in range(n):
        assert struct.unpack_from('<I',d,p)[0]==96;R.append(list(struct.unpack_from('<24I',d,p+4)));p+=100
    return n,ps,bs,B,R
a=parse(o);b=parse(m)
assert a[0]==b[0] and a[1]==b[1]
print('header ok; blob',a[2],'->',b[2],'; original blob prefix preserved:',m[b[3]:b[3]+a[2]]==o[a[3]:a[3]+a[2]])
S=lambda d,B,w,i:d[B+w[i]:B+w[i]+w[i+1]]
ch=emp=0;bad=[]
for x,y in zip(a[4],b[4]):
    diff=[i for i in range(24) if x[i]!=y[i]]
    if x[0] in rows:
        if not set(diff)<= {6,7}: bad.append(('slot',x[0],diff))
        if S(m,b[3],y,6).decode('utf-8')!=rows[x[0]]['th_pua']: bad.append(('text',x[0]))
        if S(m,b[3],y,6)+b'\0'!=m[b[3]+y[6]:b[3]+y[6]+y[7]+1]: bad.append(('nul',x[0]))
        for k in range(8,20,2):
            if S(o,a[3],x,k)!=S(m,b[3],y,k): bad.append(('other',x[0],k))
        ch+=1
    else:
        if diff: bad.append(('empty changed',x[0]))
        emp+=1
print('changed',ch,'untouched',emp,'problems',bad)
