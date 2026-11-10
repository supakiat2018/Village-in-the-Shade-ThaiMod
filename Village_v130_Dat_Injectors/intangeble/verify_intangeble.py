import struct,csv,sys
sys.path.insert(0,'.')
o=open(sys.argv[1],'rb').read(); m=open(sys.argv[2],'rb').read()
rows=list(csv.DictReader(open(sys.argv[3],encoding='utf-8-sig')))
EXPECT={422:"ไบเคองหานเมดแว!"}
def parse(d):
    n,ps,bs=struct.unpack_from('<3I',d,0);B=len(d)-bs;assert B==12+n*4+ps
    R=[];p=12
    for _ in range(n):
        assert struct.unpack_from('<I',d,p)[0]==116;R.append(list(struct.unpack_from('<29I',d,p+4)));p+=120
    assert p==B;return n,ps,bs,B,R
a=parse(o);b=parse(m);assert a[:2]==b[:2] and a[0]==len(rows)+1
print('header ok; blob',a[2],'->',b[2],'; filesize',len(o),'->',len(m),'; original blob preserved:',m[b[3]:b[3]+a[2]]==o[a[3]:a[3]+a[2]])
Sa=lambda w,i:o[a[3]+w[i]:a[3]+w[i]+w[i+1]];Sb=lambda w,i:m[b[3]+w[i]:b[3]+w[i]+w[i+1]]
bad=[]
for i,(x,y) in enumerate(zip(a[4],b[4])):
    want=EXPECT[i] if i in EXPECT else rows[i]['Thai_PUA']
    diff=[k for k in range(29) if x[k]!=y[k]]
    if not set(diff)<={4,5}: bad.append(('slot',i,diff))
    if Sb(y,4).decode()!=want: bad.append(('text',i))
    if m[b[3]+y[4]+y[5]:b[3]+y[4]+y[5]+1]!=b'\0': bad.append(('nul',i))
    if y[4]<a[2]: bad.append(('not appended',i))
    if Sa(x,2)!=Sb(y,2) or Sa(x,6)!=Sb(y,6): bad.append(('key/en',i))
print('changed',a[0],'problems',bad)
