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
keys=[Sa(w,2).decode() for _,w in a[4]]
want={(r['Record_Key'],int(r['Line_Index'])):r['Thai_PUA'] for r in rows}
bad=[];ch=0
for (s1,x),(s2,y),k in zip(a[4],b[4],keys):
    if s1!=s2: bad.append(('rec_size',k))
    exp={5+14*li for (kk,li) in want if kk==k}|{6+14*li for (kk,li) in want if kk==k}
    diff={i for i in range(len(x)) if x[i]!=y[i]}
    if not diff<=exp: bad.append(('unexpected change',k,sorted(diff-exp)))
    for li in range(x[4]):
        if (k,li) in want:
            t=Sb(y,5+14*li)
            if t.decode()!=want[(k,li)]: bad.append(('text',k,li))
            e=b[3]+y[5+14*li]+y[6+14*li]
            if m[e:e+1]!=b'\0' or y[5+14*li]<a[2]: bad.append(('nul/append',k,li))
            ch+=1
        elif Sa(x,5+14*li)!=Sb(y,5+14*li): bad.append(('skipped line changed',k,li))
        for k2 in range(2,14,2):   # EN + other 5 languages of the line must be unchanged
            if Sa(x,5+14*li+k2)!=Sb(y,5+14*li+k2): bad.append(('other lang',k,li,k2))
print('changed',ch,'of',len(want),'problems',bad)
