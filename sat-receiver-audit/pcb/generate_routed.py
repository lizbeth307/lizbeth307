#!/usr/bin/env python3
"""Route a compact, unreleased two-layer DC_CORE prototype candidate.

Requires KiCad 10 pcbnew/CLI plus numpy/scipy. Never changes source graphs or
frozen placement starter. Publishes a PCB only after native all-severity DRC has
zero findings and zero ignored checks. This is not a fabrication release.
"""
from __future__ import annotations
import argparse, heapq, importlib.util, json, math, os
from pathlib import Path
import shutil, subprocess, sys, tempfile
from collections import defaultdict

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('starter_helpers',BASE/'pcb/generate_layout.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
NAME='detector-core-routed-prototype'
STATUS='ROUTED_INTERNAL_PROTOTYPE_NOT_FOR_FABRICATION'
STEP=.10
WIDTH=.20
CLEAR=.20
VIA_DIAM=.60
VIA_DRILL=.30


def positions():
    # High-impedance islands are compacted; output/gate circuits lie above them.
    p={'D450':(40,35,0),'R4400':(45,35,0),'U458':(49,40,0),'C4400':(45.5,39.05,180),
       'R4401':(38,44,0),'R4402':(58,40,0),'R4403':(58,43,0),'C4401':(58,46,0),
       'R4404':(64,40,0),'R4405':(64,43,0),'C4402':(64,46,0),
       'U456':(48,57,0),'C4416':(51.7,56.05,0),'C4403':(51.7,58.5,0),
       'R4406':(43,54,0),'R4407':(43,57,0),'C4405':(43,60,0),
       'U457':(48,71,0),'C4417':(51.7,70.05,0),'C4404':(51.7,72.5,0),
       'R4408':(43,68,0),'R4409':(43,71,0),'C4406':(43,74,0),
       'R4450':(48,51,0),'R4451':(53,51,0),'Q456':(58,54,0),
       'R4452':(48,80,0),'R4453':(53,80,0),'Q457':(58,78,0)}
    for i,y in enumerate((46,70,94)):
        r=4420+i*10;u=450+i*2
        p.update({f'U{u}':(80,y,0),f'U{u+1}':(74,y,0),
          f'C{4410+i*2}':(83.7,y-.95,0),f'C{4411+i*2}':(76,y-3.7,90),
          f'D{451+i}':(77,y+4,0),f'C{r+1}':(81,y+4,0),
          f'R{r+1}':(78,y+8,0),f'R{r+2}':(75,y+8,0),
          f'R{r+3}':(87,y-3,0),f'R{r+4}':(92,y-3,0),f'Q{450+i*2}':(97,y-2,0),
          f'R{r+5}':(87,y-7,0),f'R{r+6}':(92,y-7,0),f'Q{451+i*2}':(97,y-7,0)})
    return p


def place_references(pcb,board):
    def box(item,margin=0):
        q=item.GetBoundingBox(False,False) if isinstance(item,pcb.FOOTPRINT) else item.GetBoundingBox()
        return (pcb.ToMM(q.GetX())-margin,pcb.ToMM(q.GetY())-margin,
                pcb.ToMM(q.GetRight())+margin,pcb.ToMM(q.GetBottom())+margin)
    def overlap(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
    footprints=sorted(board.GetFootprints(),key=lambda f:f.GetReference())
    obstacles=[box(fp,.18) for fp in footprints];labels=[]
    for fp in footprints:
        ref=fp.Reference();ref.SetTextSize(pcb.VECTOR2I(pcb.FromMM(.8),pcb.FromMM(.8)));ref.SetTextThickness(pcb.FromMM(.12));ref.SetTextAngle(pcb.EDA_ANGLE(0,pcb.DEGREES_T))
        x,y=pcb.ToMM(fp.GetPosition().x),pcb.ToMM(fp.GetPosition().y)
        found=False
        for radius in (2.6,3.2,4,5,6,8):
            for dx,dy in ((0,-1),(0,1),(-1,0),(1,0),(-1,-1),(1,-1),(-1,1),(1,1)):
                ref.SetPosition(pcb.VECTOR2I(pcb.FromMM(x+dx*radius),pcb.FromMM(y+dy*radius)))
                bb=box(ref,.16)
                if not any(overlap(bb,other) for other in obstacles+labels):
                    labels.append(bb);found=True;break
            if found:break
        if not found:raise RuntimeError('No clear reference label position '+fp.GetReference())


class Router:
    def __init__(self,pcb,board):
        import numpy as np
        from scipy.ndimage import maximum_filter
        self.np=np;self.maxfilter=maximum_filter;self.pcb=pcb;self.board=board
        self.x0,self.y0=20,20;self.nx=1251;self.ny=1151
        self.occ=np.zeros((2,self.nx,self.ny),dtype=np.uint64)
        self.hole_block=np.zeros((self.nx,self.ny),dtype=bool)
        self.nets={pad.GetNetname():pad.GetNetCode() for fp in board.GetFootprints() for pad in fp.Pads() if pad.GetNetname()}
        self.bit={name:np.uint64(1)<<np.uint64(i) for i,name in enumerate(sorted(self.nets))}
        self.pad={};self.routes=[];self.vias=[];self.segments=set();self.ground_stubs=[]
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                n=pad.GetNumber()
                if not n:continue
                self.pad[(fp.GetReference(),str(n))]=pad
                xy=self.mm(pad.GetPosition());size=pad.GetSize()
                sx,sy=pcb.ToMM(size.x),pcb.ToMM(size.y)
                angle=pad.GetOrientationDegrees()%180
                if abs(angle-90)<1e-4:sx,sy=sy,sx
                # Axis-aligned conservative exclusion; rotated footprints only 0/90.
                bit=self.bit.get(pad.GetNetname(),np.uint64(1)<<np.uint64(63))
                self.rect(0,xy,sx/2+CLEAR+WIDTH/2+.06,sy/2+CLEAR+WIDTH/2+.06,bit)
        # Keep copper at least 0.8mm from the candidate board edge.
        self.occ[:,:9,:]=np.uint64(1)<<np.uint64(63)
        self.occ[:,-9:,:]=np.uint64(1)<<np.uint64(63)
        self.occ[:,:,:9]=np.uint64(1)<<np.uint64(63)
        self.occ[:,:,-9:]=np.uint64(1)<<np.uint64(63)

    def mm(self,p):return (self.pcb.ToMM(p.x),self.pcb.ToMM(p.y))
    def cell(self,p):return (int(round((p[0]-self.x0)/STEP)),int(round((p[1]-self.y0)/STEP)))
    def point(self,c):return (round(c[0]*STEP+self.x0,6),round(c[1]*STEP+self.y0,6))
    def vec(self,p):return self.pcb.VECTOR2I(self.pcb.FromMM(p[0]),self.pcb.FromMM(p[1]))
    def rect(self,z,p,hx,hy,bit):
        ax,ay=self.cell((p[0]-hx,p[1]-hy));bx,by=self.cell((p[0]+hx,p[1]+hy))
        self.occ[z,max(0,ax):min(self.nx,bx+1),max(0,ay):min(self.ny,by+1)] |= bit
    def circle(self,z,p,r,bit):
        np=self.np;cx,cy=self.cell(p);rr=int(math.ceil(r/STEP))+1
        ax=max(0,cx-rr);bx=min(self.nx,cx+rr+1);ay=max(0,cy-rr);by=min(self.ny,cy+rr+1)
        xx=np.arange(ax,bx)[:,None]*STEP+self.x0;yy=np.arange(ay,by)[None,:]*STEP+self.y0
        mask=(xx-p[0])**2+(yy-p[1])**2 <= (r+.075)**2
        view=self.occ[z,ax:bx,ay:by];view[mask] |= bit
    def track(self,name,z,a,b):
        if math.dist(a,b)<1e-6:return
        key=(name,z,tuple(sorted((a,b))))
        if key in self.segments:return
        self.segments.add(key)
        t=self.pcb.PCB_TRACK(self.board);t.SetStart(self.vec(a));t.SetEnd(self.vec(b));t.SetWidth(self.pcb.FromMM(WIDTH));t.SetLayer(self.pcb.F_Cu if z==0 else self.pcb.B_Cu);t.SetNetCode(self.nets[name]);self.board.Add(t)
        self.routes.append(dict(net=name,layer='F.Cu' if z==0 else 'B.Cu',a=a,b=b,length_mm=math.dist(a,b)))
        count=max(1,int(math.ceil(math.dist(a,b)/(STEP/2))))
        for i in range(count+1):self.circle(z,(a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count),CLEAR+WIDTH,self.bit[name])
    def via(self,name,p):
        v=self.pcb.PCB_VIA(self.board);v.SetPosition(self.vec(p));v.SetWidth(self.pcb.FromMM(VIA_DIAM));v.SetDrill(self.pcb.FromMM(VIA_DRILL));v.SetViaType(self.pcb.VIATYPE_THROUGH);v.SetLayerPair(self.pcb.F_Cu,self.pcb.B_Cu);v.SetNetCode(self.nets[name]);self.board.Add(v)
        self.vias.append(dict(net=name,xy=p))
        cx,cy=self.cell(p)
        for dx in range(-7,8):
            for dy in range(-7,8):
                if dx*dx+dy*dy<=42.25 and 0<=cx+dx<self.nx and 0<=cy+dy<self.ny:
                    self.hole_block[cx+dx,cy+dy]=True
        for z in (0,1):self.circle(z,p,VIA_DIAM/2+CLEAR+WIDTH/2,self.bit[name])
    def blocked(self,name):return (self.occ & ~self.bit[name]) != 0
    def astar(self,name,a,b,front_only=False):
        np=self.np;block=self.blocked(name);via_block=(self.maxfilter((block[0]|block[1]).astype(np.uint8),size=7)>0)|self.hole_block
        start=(*self.cell(a),0);goal=(*self.cell(b),0)
        if block[start[2],start[0],start[1]] or block[goal[2],goal[0],goal[1]]:
            raise RuntimeError(f'Endpoint blocked {name} {a}->{b}')
        def h(x,y,z):
            dx=abs(x-goal[0]);dy=abs(y-goal[1]);return max(dx,dy)+(math.sqrt(2)-1)*min(dx,dy)+z*40
        heap=[(h(*start),0,start)];cost={start:0};previous={};visited=0
        moves=((1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,math.sqrt(2)),(1,-1,math.sqrt(2)),(-1,1,math.sqrt(2)),(-1,-1,math.sqrt(2)))
        while heap:
            _,g,node=heapq.heappop(heap)
            if g!=cost.get(node):continue
            if node==goal:
                path=[node]
                while path[-1]!=start:path.append(previous[path[-1]])
                return list(reversed(path))
            visited+=1
            if visited>450000:raise RuntimeError(f'Router search limit {name} {a}->{b}')
            x,y,z=node
            for dx,dy,step in moves:
                xx,yy=x+dx,y+dy
                if not(0<=xx<self.nx and 0<=yy<self.ny) or block[z,xx,yy]:continue
                if dx and dy and (block[z,x+dx,y] or block[z,x,y+dy]):continue
                new=(xx,yy,z);newg=g+step*(1.0 if z==0 else 1.30)
                if newg+1e-8<cost.get(new,1e100):cost[new]=newg;previous[new]=node;heapq.heappush(heap,(newg+h(*new),newg,new))
            if not front_only and not via_block[x,y]:
                new=(x,y,1-z);newg=g+40
                if newg<cost.get(new,1e100):cost[new]=newg;previous[new]=node;heapq.heappush(heap,(newg+h(*new),newg,new))
        raise RuntimeError(f'No route {name} {a}->{b}')
    def connect(self,name,pina,pinb,front_only=False):
        a=self.mm(self.pad[pina].GetPosition());b=self.mm(self.pad[pinb].GetPosition())
        self.connect_points(name,a,b,front_only)
    def connect_points(self,name,a,b,front_only=False):
        path=self.astar(name,a,b,front_only)
        self.track(name,0,a,self.point(path[0][:2]))
        run=path[0];last=path[0];direction=None
        for node in path[1:]:
            d=(node[0]-last[0],node[1]-last[1],node[2]-last[2])
            if node[2]!=last[2]:
                self.track(name,last[2],self.point(run[:2]),self.point(last[:2]));self.via(name,self.point(last[:2]));run=node;direction=None
            elif direction is not None and d!=direction:
                self.track(name,last[2],self.point(run[:2]),self.point(last[:2]));run=last
            direction=d;last=node
        self.track(name,last[2],self.point(run[:2]),self.point(last[:2]));self.track(name,0,self.point(path[-1][:2]),b)
    def route_net(self,name,forced=(),front_only=False):
        pins=[key for key,pad in self.pad.items() if pad.GetNetname()==name]
        if len(pins)<2:return
        parent={p:p for p in pins}
        def root(p):
            while parent[p]!=p:parent[p]=parent[parent[p]];p=parent[p]
            return p
        edges=[]
        for a,b in forced:
            self.connect(name,a,b,front_only);parent[root(a)]=root(b)
        for i,a in enumerate(pins):
            for b in pins[i+1:]:edges.append((math.dist(self.mm(self.pad[a].GetPosition()),self.mm(self.pad[b].GetPosition())),a,b))
        for _,a,b in sorted(edges):
            if root(a)!=root(b):self.connect(name,a,b,front_only);parent[root(a)]=root(b)
    def ground(self):
        name='GND'
        for key,pad in sorted(self.pad.items()):
            if pad.GetNetname()!=name:continue
            a=self.mm(pad.GetPosition());block=self.blocked(name);vb=(self.maxfilter((block[0]|block[1]).astype(self.np.uint8),size=7)>0)|self.hole_block
            candidates=[]
            for radius in (1.2,1.5,1.8,2.2,2.8,3.5):
                for i in range(16):
                    p=self.point(self.cell((a[0]+radius*math.cos(math.pi*i/8),a[1]+radius*math.sin(math.pi*i/8))))
                    x,y=self.cell(p)
                    if 0<=x<self.nx and 0<=y<self.ny and not vb[x,y]:candidates.append((math.dist(a,p),p))
                if candidates:break
            done=False
            for _,p in sorted(candidates):
                try:self.connect_points(name,a,p,front_only=True)
                except RuntimeError:continue
                self.via(name,p);self.ground_stubs.append(dict(ref=key[0],pin=key[1],via=p,straight_distance_mm=math.dist(a,p)));done=True;break
            if not done:raise RuntimeError('No local GND escape for '+str(key))


def project(name):
    return {'meta':{'filename':name+'.kicad_pro','version':1},'board':{'design_settings':{'rule_severities':{key:'warning' for key in helper.EXTRA_DRC_WARNINGS},'rules':{'min_clearance':CLEAR,'min_track_width':WIDTH,'min_copper_edge_clearance':.5,'min_via_diameter':VIA_DIAM,'min_through_hole_diameter':VIA_DRILL,'min_via_annular_width':.1,'min_hole_clearance':.25,'min_hole_to_hole':.25}}},'net_settings':{'classes':[{'name':'Default','clearance':CLEAR,'track_width':WIDTH,'via_diameter':VIA_DIAM,'via_drill':VIA_DRILL,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':WIDTH,'diff_pair_gap':.25,'diff_pair_via_gap':.25}],'meta':{'version':4}}}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--runtime-root',type=Path);parser.add_argument('--kicad-cli',default='kicad-cli');args=parser.parse_args()
    if args.runtime_root and not os.environ.get('SR_RX_ROUTED_RUNTIME_ACTIVE'):
        env=dict(os.environ);runtime=args.runtime_root.resolve()
        env['LD_LIBRARY_PATH']=str(runtime/'usr/lib/x86_64-linux-gnu')+':'+env.get('LD_LIBRARY_PATH','')
        env['PYTHONPATH']=str(runtime/'usr/lib/python3/dist-packages')+':'+env.get('PYTHONPATH','')
        env['SR_RX_ROUTED_RUNTIME_ACTIVE']='1'
        os.execve(sys.executable,[sys.executable,str(Path(__file__).resolve()),*sys.argv[1:]],env)
    # SciPy's extension modules must initialize before KiCad's SWIG registry.
    import numpy
    from scipy.ndimage import maximum_filter
    import pcbnew as pcb
    sourcepath=BASE/'pcb/generated/detector-core-input.json';source=json.loads(sourcepath.read_text())
    starter=BASE/'build/kicad/pcb-preparation/detector-core-placement.kicad_pcb';frozen=helper.digest(starter)
    out=BASE/'build/kicad/pcb-prototype';out.mkdir(parents=True,exist_ok=True)
    report={'status':'ASSESSMENT_IN_PROGRESS','source_input_sha256':helper.digest(sourcepath),'frozen_starter_sha256':frozen,'published_board':False,'external_interfaces_selected':False,'release':'NOT_FOR_FABRICATION','constraints':source['constraints'],'source_preparation_blockers':source['blockers'],'blockers':[b for b in source['blockers'] if not b.startswith('Three explicitly0402')],'resource_gate_resolved':'R0402 resource bundled unmodified from official KiCad 10.0.7; passive production qualification remains open.'}
    auditfile=BASE/'verification/pcb-prototype-review.json'
    try:
        board=pcb.LoadBoard(str(starter));pos=positions()
        assert {f.GetReference() for f in board.GetFootprints()}==set(pos)
        for fp in board.GetFootprints():
            x,y,angle=pos[fp.GetReference()];fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)));fp.SetOrientationDegrees(angle)
        place_references(pcb,board)
        for drawing in list(board.GetDrawings()):
            if isinstance(drawing,pcb.PCB_TEXT):
                drawing.SetText('')
                drawing.SetLayer(pcb.Cmts_User)
        helper.add_text(pcb,board,'INTERNAL DC CORE PROTOTYPE / NOT FOR FABRICATION',(82.5,25),1.1)
        helper.add_text(pcb,board,'8 EXTERNAL INTERFACES UNRESOLVED - 50 PASSIVE MPNs UNQUALIFIED',(82.5,124),.8)
        helper.add_text(pcb,board,'125 x 115 mm CANDIDATE OUTLINE - NO ENCLOSURE FIT',(82.5,129),.9)
        title=pcb.TITLE_BLOCK();title.SetTitle('DC_CORE ROUTED INTERNAL PROTOTYPE - NOT FOR FABRICATION');title.SetRevision('prototype-candidate-1');board.SetTitleBlock(title)
        router=Router(pcb,board)
        print('Reserve local ground escapes',flush=True);router.ground()
        sensitive=[n for n in sorted(router.nets) if n.endswith('_SENSE')]
        for name in sensitive:print('Route sensitive',name,flush=True);router.route_net(name,front_only=True)
        for name in ('E4_DCS_REF12_LOW','E4_DCS_REF12_HIGH','E4_DCS_REF_FEED','E4_DCS_REF','E4_DCS_LOW','E4_DCS_HIGH','E4_DCS_REF_PG_LOW','E4_DCS_REF_PG_HIGH'):
            print('Route reference',name,flush=True);router.route_net(name)
        forced=[((f'U{450+i}','6'),(f'C{4410+i}','1')) for i in range(8)]
        router.route_net('3V3_Q6A',forced=forced)
        done=set(sensitive)|{'GND','3V3_Q6A','E4_DCS_REF12_LOW','E4_DCS_REF12_HIGH','E4_DCS_REF_FEED','E4_DCS_REF','E4_DCS_LOW','E4_DCS_HIGH','E4_DCS_REF_PG_LOW','E4_DCS_REF_PG_HIGH'}
        for name in sorted(set(router.nets)-done):print('Route control',name,flush=True);router.route_net(name)
        zone=pcb.ZONE(board);zone.SetLayer(pcb.B_Cu);zone.SetNetCode(router.nets['GND']);zone.SetLocalClearance(pcb.FromMM(CLEAR));zone.SetThermalReliefGap(pcb.FromMM(.25));zone.SetThermalReliefSpokeWidth(pcb.FromMM(.3));zone.SetMinThickness(pcb.FromMM(.2));zone.SetPadConnection(pcb.ZONE_CONNECTION_FULL)
        polygon=zone.Outline();polygon.NewOutline()
        for x,y in ((21,21),(144,21),(144,134),(21,134)):polygon.Append(pcb.FromMM(x),pcb.FromMM(y))
        board.Add(zone)
        with tempfile.TemporaryDirectory(prefix='sr-rx-routed-') as tmp:
            work=Path(tmp);candidate=work/(NAME+'.kicad_pcb')
            pcb.SaveBoard(str(candidate),board)
            helper.atomic_write(work/(NAME+'.kicad_pro'),json.dumps(project(NAME),indent=2)+'\n')
            table=(BASE/'build/kicad/pcb-preparation/fp-lib-table').read_text()
            # Temporary work uses absolute library paths; published table is portable.
            helper.atomic_write(work/'fp-lib-table',table.replace('${KIPRJMOD}/../footprints',str(BASE/'build/kicad/footprints')))
            cli=shutil.which(args.kicad_cli) or args.kicad_cli
            command=[str(cli),'pcb','drc','--format','json','--severity-all','--all-track-errors','--exit-code-violations','--refill-zones','--save-board','--output',str(work/'drc-raw.json'),str(candidate)]
            result=subprocess.run(command,capture_output=True,text=True)
            helper.atomic_write(out/'drc-command.log',result.stdout+'\n'+result.stderr)
            raw=json.loads((work/'drc-raw.json').read_text());helper.atomic_write(out/'drc-raw.json',(work/'drc-raw.json').read_bytes())
            counts={k:len(raw.get(k,[])) for k in ('violations','unconnected_items','schematic_parity')}
            report.update(drc={'exit_code':result.returncode,'sections':counts,'ignored_checks':raw.get('ignored_checks',[]),'raw_sha256':helper.digest(out/'drc-raw.json'),'suppressed_or_filtered':False},track_segments=len(router.routes),vias=len(router.vias),routing=router.routes,via_assignments=router.vias,local_ground_escapes=router.ground_stubs,positions=pos)
            reread=helper.audit(pcb,source,candidate)
            # Starter audit intentionally rejects copper; retain exact source-pad failures only.
            pad_errors=[e for e in reread['errors'] if e['kind']!='unexpected_copper']
            report['source_pad_audit']={'passed':not pad_errors,'errors':pad_errors,'parts':reread['components'],'pins':reread['source_pins'],'netted':reread['connected_pads'],'nc':reread['nc_pads']}
            if result.returncode or any(counts.values()) or raw.get('ignored_checks') or pad_errors:
                report['status']='BLOCKED_NATIVE_DRC_OR_PAD_AUDIT';print(json.dumps({k:v for k,v in report.items() if k not in ('routing','constraints','positions','local_ground_escapes','via_assignments')},indent=2));raise SystemExit(1)
            helper.atomic_write(out/candidate.name,candidate.read_bytes());helper.atomic_write(out/(NAME+'.kicad_pro'),json.dumps(project(NAME),indent=2)+'\n');helper.atomic_write(out/'fp-lib-table',table)
            export=subprocess.run([str(cli),'pcb','export','svg','--mode-single','--black-and-white','--layers','F.Cu,F.Silkscreen,Edge.Cuts','--page-size-mode','2','--exclude-drawing-sheet','--output',str(work/'prototype.svg'),str(candidate)],capture_output=True,text=True)
            if export.returncode:raise RuntimeError(export.stderr)
            helper.atomic_write(out/(NAME+'.svg'),(work/'prototype.svg').read_bytes())
            bottom=subprocess.run([str(cli),'pcb','export','svg','--mode-single','--layers','B.Cu,Edge.Cuts','--page-size-mode','2','--exclude-drawing-sheet','--output',str(work/'prototype-bottom.svg'),str(candidate)],capture_output=True,text=True)
            if bottom.returncode:raise RuntimeError(bottom.stderr)
            helper.atomic_write(out/(NAME+'-bottom.svg'),(work/'prototype-bottom.svg').read_bytes())
            try:
                import fitz
                doc=fitz.open(out/(NAME+'.svg'));helper.atomic_write(out/(NAME+'.png'),doc[0].get_pixmap(matrix=fitz.Matrix(3,3),alpha=False).tobytes('png'))
                back=fitz.open(out/(NAME+'-bottom.svg'));helper.atomic_write(out/(NAME+'-bottom.png'),back[0].get_pixmap(matrix=fitz.Matrix(3,3),alpha=False).tobytes('png'))
            except ImportError:pass
            report.update(status=STATUS,published_board=True,board_sha256=helper.digest(out/candidate.name))
    except Exception as exc:
        report.update(status='BLOCKED_ROUTING_ASSESSMENT',error=str(exc));print(type(exc).__name__+': '+str(exc),flush=True)
    finally:
        report['frozen_starter_unchanged']=helper.digest(starter)==frozen
        helper.atomic_write(auditfile,json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('routing','constraints','positions','local_ground_escapes','via_assignments')},indent=2))
    if not report['published_board']:raise SystemExit(1)

if __name__=='__main__':main()
