import struct,csv,sys
o=open(sys.argv[1],'rb').read(); m=open(sys.argv[2],'rb').read()
rows=list(csv.DictReader(open(sys.argv[3],encoding='utf-8-sig')))
def parse(d):
    n,ps,bs=struct.unpack_from('<3I',d,0);B=len(d)-bs;assert B==12+n*4+ps
    R=[];p=12
    for _ in range(n):
        sz=struct.unpack_from('<I',d,p)[0];R.append((sz,list(struct.unpack_from('<%dI'%(sz//4),d,p+4))));p+=4+sz
    assert p==B;return n,ps,bs,B,R
a=parse(o);b=parse(m);assert a[:2]==b[:2]
print('header ok; blob',a[2],'->',b[2],'; filesize',len(o),'->',len(m),'; original blob preserved:',m[b[3]:b[3]+a[2]]==o[a[3]:a[3]+a[2]])
Sa=lambda w,i:o[a[3]+w[i]:a[3]+w[i]+w[i+1]];Sb=lambda w,i:m[b[3]+w[i]:b[3]+w[i]+w[i+1]]
ch=emp=0;bad=[]
for i,((s1,x),(s2,y),r) in enumerate(zip(a[4],b[4],rows)):
    if s1!=s2: bad.append(('rec_size',i));continue
    diff=[k for k in range(len(x)) if x[k]!=y[k]]
    if r['Thai_PUA'] and r['Status']!='Empty_Untouched':
        if not set(diff)<={7,8}: bad.append(('slot',i,diff))
        if Sb(y,7).decode()!=r['Thai_PUA']: bad.append(('text',i))
        if m[b[3]+y[7]+y[8]:b[3]+y[7]+y[8]+1]!=b'\0': bad.append(('nul',i))
        if y[7]<a[2]: bad.append(('not appended',i))
        for k in range(9,20,2):
            if Sa(x,k)!=Sb(y,k): bad.append(('other',i,k))
        if Sa(x,2)!=Sb(y,2): bad.append(('key',i))
        ch+=1
    else:
        if diff: bad.append(('empty changed',i))
        emp+=1
print('changed',ch,'untouched',emp,'problems',bad)
