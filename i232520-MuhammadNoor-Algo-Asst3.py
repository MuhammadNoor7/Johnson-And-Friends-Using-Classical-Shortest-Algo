#i232520
#Muhammad Noor
#Ds-A
#Algo -Asst3

import argparse
import sys
import math
import random
import re
import heapq
import tracemalloc
from time import perf_counter
from pathlib import Path

#classes for graph representation
class Edge:
    def __init__(self,u,v,w):
        self.u=u
        self.v=v
        self.w=w

class Graph:
    def __init__(self,n,directed=True):
        self.num_vertices=n
        self.directed=directed
        self._adj=[[] for _ in range(n)]
        self._edges=[]
    
    def add_edge(self,u,v,w):
        self._adj[u].append((v,w))
        self._edges.append(Edge(u,v,w))
        if not self.directed:
            self._adj[v].append((u,w))
            self._edges.append(Edge(v,u,w))

    def neighbors(self,u):
        return self._adj[u]

    @property
    def edges(self):
        return self._edges

class GraphMatrix:
    def __init__(self,n,directed=True):
        self.num_vertices=n
        self.directed=directed
        self._inf=math.inf
        self._mat=[[self._inf]*n for _ in range(n)]
        for i in range(n):
            self._mat[i][i]=0.0

    def add_edge(self,u,v,w):
        if w < self._mat[u][v]:
            self._mat[u][v]=w
        if not self.directed:
            if w < self._mat[v][u]:
                self._mat[v][u]=w

    @property
    def edges(self):
        out=[]
        for u in range(self.num_vertices):
            for v in range(self.num_vertices):
                w=self._mat[u][v]
                if w!=self._inf and u!=v:
                    out.append(Edge(u,v,w))
        return out

    def neighbors(self,u):
        row=self._mat[u]
        return [(v,w) for v,w in enumerate(row) if w!=self._inf and v!=u]

    @staticmethod
    def from_matrix(mat,directed=True):
        n=len(mat)
        g=GraphMatrix(n,directed)
        for u in range(n):
            for v in range(n):
                w=mat[u][v]
                if w!=math.inf and u!=v:
                    g.add_edge(u,v,w)
        return g

    @staticmethod
    def from_edges(n,edges,directed=True):
        g=GraphMatrix(n,directed)
        for u,v,w in edges:
            g.add_edge(u,v,w)
        return g

#class for result
class AlgorithmResult:
    def __init__(self,distances,predecessors,relaxations,negative_cycle=False):
        self.distances=distances
        self.predecessors=predecessors
        self.relaxations=relaxations
        self.negative_cycle=negative_cycle

class AlgorithmMetrics:
    def __init__(self,result,runtime_ms,peak_memory_kb):
        self.result=result
        self.runtime_ms=runtime_ms
        self.peak_memory_kb=peak_memory_kb

def run_with_metrics(func,*args,**kwargs):
    tracemalloc.start()
    start=perf_counter()
    res=func(*args,**kwargs)
    runtime=(perf_counter()-start)*1000.0
    _,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return AlgorithmMetrics(res,runtime,peak/1024.0)

#parsing helpers
def _detect_one_indexing(edges,n):
    if not edges:
        return False
    maxv=max(max(u,v) for u,v,_ in edges)
    return maxv==n

def _parse_graph_lines(lines,directed=True):
    #already filtered;supports header (n m),adjacency matrix,or edge list
    first=line0=lines[0].split()
    num_vertices=None
    num_edges=None
    rest=lines
    try:
        if len(first)==2:
            num_vertices=int(first[0]); num_edges=int(first[1]); rest=lines[1:]
        elif len(first)==1:
            #supporting header format with just number of vertices followed by matrix rows
            try:
                maybe_n=int(first[0])
            except Exception:
                maybe_n=None
            if maybe_n is not None and len(lines)>=maybe_n+1:
                #checking that the following maybe_n lines look like matrix rows of length maybe_n
                cand=[row.split() for row in lines[1:1+maybe_n]]
                if len(cand)==maybe_n and all(len(r)==maybe_n for r in cand):
                    num_vertices=maybe_n
                    rest=lines[1:]
                else:
                    rest=lines
            else:
                rest=lines
    except Exception:
        rest=lines

    #detecting matrix
    is_matrix=False
    parsed_rows=[r.split() for r in rest]
    if parsed_rows:
        m=len(parsed_rows)
        if all(len(r)==m for r in parsed_rows):
            is_matrix=True
    if num_vertices is not None and len(rest)>=num_vertices:
        cand=[row.split() for row in rest[:num_vertices]]
        if all(len(r)==num_vertices for r in cand):
            parsed_rows=cand; is_matrix=True

    if is_matrix:
        mat=[]
        for row in parsed_rows:
            vals=[]
            for tok in row:
                if tok.upper()=="INF":
                    vals.append(math.inf)
                else:
                    try:
                        vals.append(float(tok))
                    except Exception:
                        vals.append(math.inf)
            mat.append(vals)
        return GraphMatrix.from_matrix(mat,directed=directed)

    #edge list
    edge_tuples=[]
    for idx,line in enumerate(rest, start=(2 if num_vertices is not None else 1)):
        parts=line.split()
        if len(parts)!=3:
            raise ValueError(f"line {idx} must contain three values (u v w)")
        u=int(parts[0]); v=int(parts[1]); w=float(parts[2])
        edge_tuples.append((u,v,w))

    if num_vertices is None:
        maxv=0
        for u,v,_ in edge_tuples:
            maxv=max(maxv,u,v)
        one_indexed=_detect_one_indexing(edge_tuples,maxv)
        if one_indexed:
            num_vertices=maxv
            adjusted=[(u-1,v-1,w) for u,v,w in edge_tuples]
        else:
            num_vertices=maxv+1
            adjusted=edge_tuples
    else:
        if len(edge_tuples)!=num_edges:
            raise ValueError("edge count does not match header")
        one_indexed=_detect_one_indexing(edge_tuples,num_vertices)
        if one_indexed:
            adjusted=[(u-1,v-1,w) for u,v,w in edge_tuples]
        else:
            adjusted=edge_tuples

    g=Graph(num_vertices,directed=directed)
    for u,v,w in adjusted:
        if not (0<=u<num_vertices and 0<=v<num_vertices):
            raise ValueError("vertex index out of range")
        g.add_edge(u,v,w)
    return g

#reading graph
def read_graph(path,directed=True):
    t=Path(path).read_text(encoding='utf-8')
    t=re.sub(r"/\*.*?\*/","",t,flags=re.S)
    raw_lines=t.splitlines()
    lines=[]
    def _is_numeric_token(tok):
        if not tok: return False
        if tok.upper()=="INF": return True
        try:
            float(tok)
            return True
        except Exception:
            return False

    for ln in raw_lines:
        s=ln.rstrip()
        if not s.strip():
            continue
        ls=s.lstrip()
        if ls.startswith('#') or ls.startswith('//'):
            continue
        if re.match(r'^\s*`{3,}', s):
            continue
        first_tok=ls.split()[0]
        if _is_numeric_token(first_tok):
            lines.append(s)
        else:
            # skip descriptive or header lines (like '/Block 8: Sample Input')
            continue
    if not lines:
        raise ValueError('input graph file is empty')
    #trying parse each blank-separated block (take first that parses)
    blocks=[]
    cur=[]
    for ln in lines:
        if ln.strip()=="":
            if cur: blocks.append(cur); cur=[]
        else:
            cur.append(ln)
    if cur: blocks.append(cur)
    for blk in blocks if blocks else [lines]:
        try:
            return _parse_graph_lines(blk,directed=directed)
        except Exception:
            continue
    #parsing all lines as single block
    return _parse_graph_lines(lines,directed=directed)

#single-source algos
def dijkstra(graph,source):
    if not (0<=source<graph.num_vertices):
        raise ValueError('source out of range')
    dist=[math.inf]*graph.num_vertices
    parent=[-1]*graph.num_vertices
    dist[source]=0.0
    heap=[(0.0,source)]
    relax=0
    while heap:
        d,u=heapq.heappop(heap)
        if d>dist[u]:
            continue
        for v,w in graph.neighbors(u):
            cand=d+w
            if cand<dist[v]:
                dist[v]=cand; parent[v]=u; relax+=1
                heapq.heappush(heap,(cand,v))
    return AlgorithmResult(dist,parent,relax,False)

def bellman_ford(graph,source):
    if not (0<=source<graph.num_vertices):
        raise ValueError('source out of range')
    n=graph.num_vertices
    dist=[math.inf]*n
    parent=[-1]*n
    dist[source]=0.0
    relax=0
    for _ in range(n-1):
        updated=False
        for e in graph.edges:
            if dist[e.u]==math.inf: continue
            cand=dist[e.u]+e.w
            if cand<dist[e.v]:
                dist[e.v]=cand; parent[e.v]=e.u; relax+=1; updated=True
        if not updated: break
    # check for negative-weight cycles by attempting one more relaxation
    neg=False
    eps=1e-12
    for e in graph.edges:
        if dist[e.u]==math.inf: continue
        if dist[e.u]+e.w < dist[e.v] - eps:
            neg=True
            break
    return AlgorithmResult(dist,parent,relax,neg)

def floyd_warshall(graph):
    n=graph.num_vertices
    dist=[[math.inf]*n for _ in range(n)]
    for v in range(n): dist[v][v]=0.0
    for e in graph.edges:
        if e.w<dist[e.u][e.v]: dist[e.u][e.v]=e.w
    relax=0
    for k in range(n):
        for i in range(n):
            if dist[i][k]==math.inf: continue
            for j in range(n):
                if dist[k][j]==math.inf: continue
                cand=dist[i][k]+dist[k][j]
                if cand<dist[i][j]: dist[i][j]=cand; relax+=1
    neg=any(dist[i][i]<0 for i in range(n))
    return AlgorithmResult(dist,None,relax,neg)

def johnson(graph):
    n=graph.num_vertices
    aug=Graph(n+1,directed=True)
    for e in graph.edges: aug.add_edge(e.u,e.v,e.w)
    for v in range(n): aug.add_edge(n,v,0.0)
    br=bellman_ford(aug,n)
    if br.negative_cycle:
        mat=[[math.inf]*n for _ in range(n)]
        return AlgorithmResult(mat,None,br.relaxations,True)
    h=list(br.distances)
    rewe=Graph(n,directed=True)
    for e in graph.edges:
        rewe.add_edge(e.u,e.v,e.w + h[e.u]-h[e.v])
    allp=[[math.inf]*n for _ in range(n)]
    tot=br.relaxations
    for s in range(n):
        ss=dijkstra(rewe,s)
        tot+=ss.relaxations
        row=[]
        for t in range(n):
            d=ss.distances[t]
            if d==math.inf: row.append(math.inf)
            else: row.append(d - h[s] + h[t])
        allp[s]=row
    return AlgorithmResult(allp,None,tot,False)

#small helper funcs for printing and detection
def _print_single_source(result):
    dists=result.distances
    if not isinstance(dists,list): raise ValueError('expected single-source vector')
    print('Vertex\tDistance')
    for i,val in enumerate(dists):
        if val==math.inf:
            sval="INF"
        else:
            sval=f"{val:.3f}"
        print(f"{i+1}\t{sval}")

def _print_all_pairs(result):
    mat=result.distances
    n=len(mat)
    hdr=['v\\u'] + [str(i+1) for i in range(n)]
    print('\t'.join(hdr))
    for i,row in enumerate(mat):
        formatted=["INF" if v==math.inf else f"{v:.3f}" for v in row]
        print('\t'.join([str(i+1)]+formatted))

def _print_metrics(result,metrics):
    print(f"Relaxations: {result.relaxations}")
    print(f"Runtime (ms): {metrics.runtime_ms:.3f}")
    print(f"Peak memory (KB): {metrics.peak_memory_kb:.3f}")
    if result.negative_cycle: print('Negative cycle detected')

#negative weight detection
def has_negative_weights(graph):
    try:
        for e in graph.edges:
            if e.w<0: return True
    except Exception:
        return False
    return False

#graph generators
def _possible_edges(n,directed):
    pairs=[]
    if directed:
        for u in range(n):
            for v in range(n):
                if u!=v: pairs.append((u,v))
    else:
        for u in range(n):
            for v in range(u+1,n): pairs.append((u,v))
    return pairs

def _sample_weights(count,weight_range):
    low,high=weight_range
    return [random.uniform(low,high) for _ in range(count)]

def _build_graph(n,edges,directed):
    g=Graph(n,directed)
    for u,v,w in edges: g.add_edge(u,v,w)
    return g

#graph generation
def _generate_graph(n,target_edges,directed,allow_negative,weight_range,allow_negative_cycles=False):
    all_edges=_possible_edges(n,directed)
    random.shuffle(all_edges)
    chosen=all_edges[:min(target_edges,len(all_edges))]
    if n>1:
        for v in range(1,n):
            e=(v-1,v) if directed else (min(v-1,v),max(v-1,v))
            if e not in chosen: chosen.append(e)
    # If negatives are not allowed, produce first graph and return
    max_attempts=8 if allow_negative else 1
    for _ in range(max_attempts):
        weights=_sample_weights(len(chosen),weight_range)
        weighted=[(u,v,w) for (u,v),w in zip(chosen,weights)]
        g=_build_graph(n,weighted,directed)
        if not allow_negative:
            return g
        # If negative weights are allowed and negative cycles are explicitly allowed, return graph as-is
        if allow_negative and allow_negative_cycles:
            return g
        # Otherwise, only accept graphs that contain negative weights but no negative cycles
        has_neg=False
        for s in range(n):
            if bellman_ford(g,s).negative_cycle: has_neg=True; break
        if not has_neg: return g
    raise RuntimeError('unable to generate graph without negative cycles')

def generate_sparse_graph(n,directed=True,allow_negative=False,weight_range=(1.0,10.0)):
    target=max(n,(n*2)//3)
    return _generate_graph(n,target,directed,allow_negative,weight_range)

def generate_dense_graph(n,directed=True,allow_negative=False,weight_range=(1.0,10.0)):
    max_edges=n*(n-1) if directed else n*(n-1)//2
    target=min(max_edges,int(0.75*max_edges))
    return _generate_graph(n,target,directed,allow_negative,weight_range)

def generate_mixed_graph(n,directed=True,allow_negative=True,allow_negative_cycles=True,weight_range=(-8.0,12.0)):
    target=max(n*2,int(0.4*n*(n-1)))
    return _generate_graph(n,target,directed,allow_negative,weight_range,allow_negative_cycles=allow_negative_cycles)

#command line
def _build_parser():
    p=argparse.ArgumentParser(description='Assignment 3 short-path toolkit (compact)')
    sub=p.add_subparsers(dest='command',required=True)
    runp=sub.add_parser('run')
    runp.add_argument('--input',help='path to graph file')
    runp.add_argument('--algorithm',default='Dijkstra')
    runp.add_argument('--source',type=int,default=1)
    runp.add_argument('--undirected',action='store_true')
    runp.add_argument('--representation',choices=['list','matrix'],default='list')
    ex=sub.add_parser('experiment')
    ex.add_argument('--output',default=Path('algos_exp_analysis.csv'))
    ex.add_argument('--graph-types',nargs='*',default=['Sparse','Dense','Mixed'])
    ex.add_argument('--undirected',action='store_true')
    ex.add_argument('--sizes',nargs='*',type=int)
    ex.add_argument('--seed',type=int,default=1234)
    return p

#main func
def main(argv=None):
    if argv is None and len(sys.argv)==1: argv=['run']
    p=_build_parser(); parsed=p.parse_args(argv)
    if parsed.command=='run':
        if getattr(parsed,'input',None):
            graph=read_graph(parsed.input,directed=not parsed.undirected)
        else:
            default=Path('..')/'inputs.txt'
            if default.exists(): graph=read_graph(str(default),directed=not parsed.undirected)
            else: raise SystemExit('No --input and ../inputs.txt not found')
        if parsed.representation=='matrix' and not isinstance(graph,GraphMatrix):
            graph=GraphMatrix.from_edges(graph.num_vertices,[(e.u,e.v,e.w) for e in graph.edges],directed=not parsed.undirected)
        elif parsed.representation=='list' and isinstance(graph,GraphMatrix):
            g2=Graph(graph.num_vertices,directed=not parsed.undirected)
            for e in graph.edges: g2.add_edge(e.u,e.v,e.w)
            graph=g2

        algmap={'Dijkstra':dijkstra,'Bellman-Ford':bellman_ford,'Floyd-Warshall':floyd_warshall,'Johnson':johnson}
        algo_name=parsed.algorithm if parsed.algorithm in algmap else parsed.algorithm.title()
        algo=algmap.get(algo_name, dijkstra)
        if algo_name in ('Dijkstra','Bellman-Ford'):
            s=parsed.source-1
            if algo_name=='Dijkstra' and has_negative_weights(graph):
                print("ERROR: negative-weight edges; Dijkstra cannot be used."); raise SystemExit(1)
            metrics=run_with_metrics(lambda g,s0: algo(g,s0),graph,s)
            _print_single_source(metrics.result)
        else:
            metrics=run_with_metrics(algo,graph)
            if metrics.result.negative_cycle: print('Negative cycle detected')
            else: _print_all_pairs(metrics.result)
        _print_metrics(metrics.result,metrics)
        return

    #experiment
    random.seed(parsed.seed)
    exp_directed=not getattr(parsed,'undirected',False)
    factories={'Sparse':lambda n: generate_sparse_graph(n,directed=exp_directed,allow_negative=False),
               'Dense':lambda n: generate_dense_graph(n,directed=exp_directed,allow_negative=False),
               # Mixed graphs may contain negative weights — enable explicitly so Bellman-Ford/Johnson exercise negatives
               'Mixed':lambda n: generate_mixed_graph(n,directed=exp_directed,allow_negative=True)}
    algorithms={'Dijkstra':dijkstra,'Bellman-Ford':bellman_ford,'Floyd-Warshall':floyd_warshall,'Johnson':johnson}
    supports_negative={'Dijkstra':False,'Bellman-Ford':True,'Floyd-Warshall':True,'Johnson':True}
    complexity={'Dijkstra':'O(m + n log n)','Bellman-Ford':'O(nm)','Floyd-Warshall':'O(n^3)','Johnson':'O(nm + n^2 log n)'}
    display={'Dijkstra':'Dijkstra','Bellman-Ford':'Bellman-Ford','Floyd-Warshall':'Floyd-Warshall','Johnson':'Johnson'}
    rows=[]
    for gtype in parsed.graph_types:
        sizes=list(parsed.sizes) if parsed.sizes else ([10,30,50] if gtype=='Sparse' else ([100,150,200] if gtype=='Dense' else [25,60]))
        factory=factories[gtype]
        for n in sizes:
            try:
                g=factory(n)
            except RuntimeError as exc:
                print(f"Skipping {gtype}|n={n}: {exc}"); continue
            src=random.randrange(g.num_vertices)
            edges=len(g.edges)
            for aname,afn in algorithms.items():
                if gtype=='Mixed' and aname=='Dijkstra': continue
                if aname in ('Dijkstra','Bellman-Ford'):
                    m=run_with_metrics(lambda G,s0: afn(G,s0),g,src)
                else:
                    m=run_with_metrics(afn,g)
                res=m.result
                rows.append({'Algorithm':display.get(aname,aname),'Graph Type':gtype,'Time (ms)':round(m.runtime_ms,4),'Works with Negative Weights':('Yes' if supports_negative.get(aname) else 'No'),'Complexity':complexity.get(aname,''),'Number of Relaxations':res.relaxations,'Memory (KB)':round(m.peak_memory_kb,4)})

    #writing to CSV
    import csv
    out=Path(parsed.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    fieldnames=["Algorithm","Graph Type","Time (ms)","Works with Negative Weights","Complexity","Number of Relaxations","Memory (KB)"]
    # keep provided extension if present, otherwise add .csv
    csv_path = out if out.suffix else out.with_suffix('.csv')
    with open(csv_path,'w',newline='',encoding='utf-8') as fh:
        writer=csv.writer(fh)
        writer.writerow(fieldnames)
        for r in rows:
            writer.writerow([r.get('Algorithm'),r.get('Graph Type'),r.get('Time (ms)'),r.get('Works with Negative Weights'),r.get('Complexity'),r.get('Number of Relaxations'),r.get('Memory (KB)')])
    print(f"Results written to {csv_path}")

if __name__=='__main__':
    main()