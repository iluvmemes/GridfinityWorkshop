"""Bounded straight-seam planning; signatures preserve original boundary geometry."""
import math


def axis_options(count, leading, trailing, bed, maximum):
    options = set()
    def add(parts):
        if not parts or sum(parts) != count or min(parts) < 1 or max(parts) > maximum:
            return
        spans = [n*42 + (leading-.25 if i == 0 else 0) + (trailing-.25 if i == len(parts)-1 else 0) for i,n in enumerate(parts)]
        if max(spans) <= bed+1e-8:
            options.add(tuple(parts))
    for size in range(1, maximum+1):
        n, rem = divmod(count, size)
        add([size]*n + ([rem] if rem else []))
        add(([rem] if rem else []) + [size]*n)
        if rem:
            add([size]*(n//2)+[rem]+[size]*(n-n//2))
        for edge in range(1, size+1):
            middle=count-2*edge
            if middle >= 0 and middle % size == 0:
                add([edge]+[size]*(middle//size)+[edge])
    # Balanced partitions and exact minimum-count path handle padded boundaries.
    for n in range(math.ceil(count/maximum), count+1):
        lo, rem=divmod(count,n)
        add([lo+1]*rem+[lo]*(n-rem))
        add([lo]*(n-rem)+[lo+1]*rem)
    paths={0:[]}
    for start in range(count):
        if start not in paths: continue
        for size in range(1,min(maximum,count-start)+1):
            end=start+size
            span=size*42+(leading-.25 if start==0 else 0)+(trailing-.25 if end==count else 0)
            candidate=paths[start]+[size]
            if span<=bed+1e-8 and (end not in paths or len(candidate)<len(paths[end])):
                paths[end]=candidate
    if count in paths: add(paths[count])
    if not options: raise ValueError('The print bed is too small for one cell with this padding.')
    return sorted(options, key=lambda v:(len(v),v))


def signature(p):
    return [p['columns'],p['rows'],*p['margins'],*p['edges']]


def rotate(s):
    c,r,l,rt,b,f,el,er,eb,ef=s
    return [r,c,f,b,l,rt,ef,eb,el,er]


def key(s):
    return tuple(round(v,6) for v in s)


def group(pieces):
    types=[]; lookup={}
    for p in pieces:
        k=key(signature(p))
        if k not in lookup:
            t=dict(p, typeId=chr(65+len(types)) if len(types)<26 else 'T'+str(len(types)+1), quantity=0)
            types.append(t)
            s=signature(p)
            for rotation in range(4):
                lookup.setdefault(key(s),(len(types)-1,rotation*90))
                s=rotate(s)
        index,rotation=lookup[k]
        types[index]['quantity']+=1
        p.update(typeId=types[index]['typeId'],rotation=rotation,typeIndex=index)
    return types


def pieces_for(xs,ys,s):
    result=[]; y=0
    for iy,rows in enumerate(ys):
        x=0
        for ix,cols in enumerate(xs):
            edges=[ix==0,ix==len(xs)-1,iy==0,iy==len(ys)-1]
            margins=[s['left'] if edges[0] else .25,s['right'] if edges[1] else .25,s['back'] if edges[2] else .25,s['front'] if edges[3] else .25]
            l,r,b,f=margins
            result.append(dict(x=x,y=y,columns=cols,rows=rows,x0=x*42-l,y0=y*42-b,x1=(x+cols)*42-.5+r,y1=(y+rows)*42-.5+f,margins=margins,edges=edges,layoutRow=iy+1,layoutColumn=ix+1))
            x+=cols
        y+=rows
    return result


def plan(s):
    preference=s.get('planningPreference','repeat')
    if preference not in ('repeat','plates','unique'): raise ValueError('Choose a print planning preference.')
    symmetry=s.get('preferSymmetry',True)
    if type(symmetry) is not bool: raise ValueError('Symmetric splits must be on or off.')
    output=s.get('outputMode','unique')
    if output not in ('unique','layout'): raise ValueError('Choose unique plates or full layout.')
    xs=axis_options(s['columns'],s['left'],s['right'],s['bedWidth'],s['maxPlateColumns'])
    ys=axis_options(s['rows'],s['back'],s['front'],s['bedDepth'],s['maxPlateRows'])
    minimum=len(xs[0])*len(ys[0]); candidates=[]
    # Score axis diversity cheaply before constructing full geometry descriptors.
    def diversity(parts,leading,trailing):
        return len(set((n,round(leading if i==0 else .25,6),round(trailing if i==len(parts)-1 else .25,6),i==0,i==len(parts)-1) for i,n in enumerate(parts)))
    for x in xs:
        for y in ys:
            total=len(x)*len(y)
            if preference=='plates' and total!=minimum: continue
            if preference=='repeat' and total>math.ceil(minimum*1.25): continue
            unique=diversity(x,s['left'],s['right'])*diversity(y,s['back'],s['front'])
            asym=sum(abs(a-b) for parts in (x,y) for a,b in zip(parts,reversed(parts))) if symmetry else 0
            candidates.append((unique,total,asym,x,y))
    candidates.sort()
    finalists=candidates[:48]
    # Include the minimum-count candidate even if diversity ranks it lower.
    finalists+=sorted(candidates,key=lambda c:(c[1],c[0],c[2]))[:8]
    best=None
    for _,total,asym,x,y in finalists:
        pieces=pieces_for(x,y,s); types=group(pieces)
        score=(len(types),total,asym,x,y) if preference!='plates' else (total,len(types),asym,x,y)
        if best is None or score<best[0]: best=(score,pieces,types,x,y)
    _,pieces,types,x,y=best
    return dict(pieces=pieces,plateTypes=types,xSections=list(x),ySections=list(y),chunkX=max(x),chunkY=max(y),minimumPlateCount=minimum,planningPreference=preference,preferSymmetry=symmetry,outputMode=output)
