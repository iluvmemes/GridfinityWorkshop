/* Lid label layout mirrors lid_label.py; all dimensions are millimeters. */
(function(root){
 'use strict';
 const defaults={lidLabelMode:'off',lidLabelText:'',lidLabelFont:'rubik',lidLabelLayout:'single',lidLabelHeight:5,lidLabelDepth:.6,lidColor:'grey',lidLabelColor:'white'};
 function plan(c){
  c={...defaults,...c};
  if(root.WorkshopFilaments)for(const key of ['lidColor','lidLabelColor'])if(!root.WorkshopFilaments.colors.some(color=>color.id===c[key]))throw Error('Choose a color swatch.');
  if(!['off','cutout','raised','embedded'].includes(c.lidLabelMode))throw Error('Choose a lid label style.');
  if(c.family!=='standard'||!c.dovetailLid||c.lidLabelMode==='off')return null;
  const text=c.lidLabelText,height=c.lidLabelHeight,depth=c.lidLabelDepth;
  if(typeof text!=='string'||!text.trim()||text.length>120)throw Error('Enter 1–120 characters for the lid label.');
  if(!['single','multi'].includes(c.lidLabelLayout))throw Error('Choose single or multiple label lines.');
  if(!Number.isFinite(height)||height<2||height>12||!Number.isFinite(depth)||depth<.2||depth>1.5)throw Error('Use 2–12 mm letter height and 0.2–1.5 mm label depth.');
  const width=c.cols*42-.5-12,available=c.rows*42-.5-12;
  const art=line=>{const a=root.WorkshopLettering.textSVG(line,c.lidLabelFont,2,240);return {...a,width:a.width/a.height*height};};
  let lines=[];
  if(c.lidLabelLayout==='single')lines=[text.trim().split(/\s+/).join(' ')];
  else{
   for(const paragraph of text.replace(/\r\n?/g,'\n').split('\n')){
    if(!paragraph.trim())throw Error('Remove blank label lines.');let current='';
    for(const word of paragraph.trim().split(/\s+/)){
     const candidate=(current+' '+word).trim();
     if(current&&art(candidate).width>width){lines.push(current);current=word;}else current=candidate;
    }
    if(current)lines.push(current);
   }
   if(lines.length>4)throw Error('Use at most four label lines; shorten text or reduce letter height.');
  }
  const artworks=lines.map(art),gap=height*.35,total=height*lines.length+gap*(lines.length-1);
  const scale=Math.min(1,width/Math.max(...artworks.map(a=>a.width)),available/total),actual=height*scale;
  if(actual<1.5)throw Error('Label would be smaller than 1.5 mm. Shorten it or use multiple lines/a larger lid.');
  const rows=lines.map((text,i)=>({text,svg:artworks[i].svg,width:artworks[i].width*scale,height:actual,x:(c.cols*42-.5)/2,y:(c.rows*42-.5)/2+total*scale/2-actual/2-i*(height+gap)*scale}));
  return {mode:c.lidLabelMode,depth,rows,height:actual,width:Math.max(...rows.map(r=>r.width)),totalHeight:total*scale,scale,margin:6};
 }
 function shapes(row,font,T,x=0,y=0){
  const data=root.WorkshopFonts[font],entries=[];let cursor=0,previous='';const bounds=[];
  for(const ch of row.text){const g=data.glyphs[ch];cursor+=data.kerning[previous+ch]||0;if(g.bounds){const [a,b,c,d]=g.bounds;bounds.push([a+cursor,b,c+cursor,d]);entries.push({g,cursor});}cursor+=g.advance;previous=ch;}
  const left=Math.min(...bounds.map(b=>b[0])),top=Math.min(...bounds.map(b=>b[1])),right=Math.max(...bounds.map(b=>b[2])),bottom=Math.max(...bounds.map(b=>b[3]));
  const scale=row.height/(bottom-top),result=[];
  for(const {g,cursor} of entries){
   const path=new T.ShapePath(),tokens=g.path.match(/[MLHVQZ]|[-+]?(?:\d*\.)?\d+(?:e[-+]?\d+)?/gi);let i=0,cmd,px=0,py=0;
   const X=v=>x+row.x-row.width/2+(v+cursor-left)*scale,Y=v=>y+row.y-row.height/2+(bottom-v)*scale;
   while(i<tokens.length){
    if(/^[MLHVQZ]$/i.test(tokens[i]))cmd=tokens[i++];
    if(cmd==='Z'){path.currentPath.closePath();cmd=null;continue;}
    if(cmd==='M'||cmd==='L'){px=+tokens[i++];py=+tokens[i++];path[cmd==='M'?'moveTo':'lineTo'](X(px),Y(py));if(cmd==='M')cmd='L';}
    else if(cmd==='H'){px=+tokens[i++];path.lineTo(X(px),Y(py));}
    else if(cmd==='V'){py=+tokens[i++];path.lineTo(X(px),Y(py));}
    else if(cmd==='Q'){const cx=+tokens[i++],cy=+tokens[i++];px=+tokens[i++];py=+tokens[i++];path.quadraticCurveTo(X(cx),Y(cy),X(px),Y(py));}
    else throw Error('Unsupported bundled glyph path command.');
   }
   result.push(...path.toShapes(false));
  }
  return result;
 }
 root.WorkshopLidLabel={defaults,plan,shapes};
 if(typeof module!=='undefined')module.exports={defaults,plan};
})(typeof window==='undefined'?globalThis:window);
