/* Plan-view illustration using the captured socket and skeleton section curves.
   Material is continuous across cells; masks represent actual through-openings.
   This does not create or modify Fusion geometry. */
function drawGridfinityPreview(container, plate, options) {
  const profile = GRIDFINITY_CELL_PROFILES;
  const {pw,pd,nx,ny,left,back,right,front,pieces} = plate;
  const width = container.clientWidth || 550;
  const height = Math.max(280, Math.min(470, width * .85));
  const gap = options.exploded ? 13 : 0;
  const totalW = pw + gap * Math.floor((nx - 1) / pieces[0].cols);
  const totalH = pd + gap * Math.floor((ny - 1) / pieces[0].rows);
  const scale = Math.min((width - 44) / totalW, (height - 50) / totalH);
  const ox = (width - totalW * scale) / 2;
  const oy = (height - totalH * scale) / 2;
  const rect = (x,y,w,h,extra='') => `<rect x="${x}" y="${y}" width="${w}" height="${h}" ${extra}/>`;
  const circle = (x,y,r,extra='') => `<circle cx="${x}" cy="${y}" r="${r}" ${extra}/>`;
  const outline = (p,extra='') => {
    const {x0:x,y0:y,x1,y1} = p;
    const tl=x===0&&y===0?3.75:0, tr=x1===pw&&y===0?3.75:0;
    const br=x1===pw&&y1===pd?3.75:0, bl=x===0&&y1===pd?3.75:0;
    return `<path d="M ${x+tl} ${y} H ${x1-tr} Q ${x1} ${y} ${x1} ${y+tr} V ${y1-br} Q ${x1} ${y1} ${x1-br} ${y1} H ${x+bl} Q ${x} ${y1} ${x} ${y1-bl} V ${y+tl} Q ${x} ${y} ${x+tl} ${y} Z" ${extra}/>`;
  };
  const cells = p => {
    const result = [];
    for(let y=p.y;y<p.y+p.rows;y++) for(let x=p.x;x<p.x+p.cols;x++) {
      result.push({x:left+x*profile.pitch,y:back+y*profile.pitch});
    }
    return result;
  };
  let svg = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${nx} by ${ny} continuous ${options.style} baseplate; ${options.style==='skeleton'?'open centers':'closed floors'}; ${pieces.length} print pieces">`;
  svg += `<defs><pattern id="gw-empty-grid" width="12" height="12" patternUnits="userSpaceOnUse"><rect width="12" height="12" fill="var(--gw-canvas)"/><path d="M 12 0 H 0 V 12" fill="none" stroke="var(--gw-line)" stroke-width="0.6"/></pattern>`;
  pieces.forEach((p,i) => {
    svg += `<clipPath id="gw-piece-clip-${i}">${outline(p)}</clipPath>`;
    svg += `<mask id="gw-material-${i}" maskUnits="userSpaceOnUse" x="${p.x0}" y="${p.y0}" width="${p.x1-p.x0}" height="${p.y1-p.y0}" style="mask-type:luminance">`;
    svg += rect(p.x0,p.y0,p.x1-p.x0,p.y1-p.y0,'fill="white"');
    for(const cell of cells(p)) {
      if(options.style==='skeleton') svg += `<path data-through-opening="skeleton" d="${profile.skeleton}" transform="translate(${cell.x} ${cell.y})" fill="black"/>`;
      if(options.screws) for(const [mx,my] of profile.magnetCenters) {
        svg += circle(cell.x+mx,cell.y+my,1.5,'data-through-opening="screw" fill="black"');
      }
    }
    svg += '</mask>';
  });
  svg += `</defs>${rect(0,0,width,height,'fill="url(#gw-empty-grid)"')}<g transform="translate(${ox} ${oy}) scale(${scale})">`;
  if(options.fit && !options.exploded) {
    svg += rect(-options.clearance,-options.clearance,pw+2*options.clearance,pd+2*options.clearance,
      `rx="4" fill="none" stroke="var(--gw-muted)" stroke-dasharray="3 3" stroke-width="${1/scale}"`);
  }
  pieces.forEach((p,i) => {
    const dx=gap*Math.round(p.x/pieces[0].cols),dy=gap*Math.round(p.y/pieces[0].rows);
    svg += `<g transform="translate(${dx} ${dy})"><g clip-path="url(#gw-piece-clip-${i})" mask="url(#gw-material-${i})" data-material="piece">`;
    // One continuous material sheet. The colored margin never fills cell seams.
    svg += rect(p.x0,p.y0,p.x1-p.x0,p.y1-p.y0,'fill="var(--gw-plate)"');
    for(const [x,y,w,h] of [[0,0,left,pd],[pw-right,0,right,pd],[left,0,pw-left-right,back],[left,pd-front,pw-left-right,front]]) {
      if(w>0 && h>0) svg += rect(x,y,w,h,'fill="var(--gw-pad)"');
    }
    for(const cell of cells(p)) {
      svg += `<g data-socket="cell" transform="translate(${cell.x} ${cell.y})">`;
      svg += `<path d="${profile.mouth}" fill="var(--gw-socket-upper)"/>`;
      svg += `<path d="${profile.shoulder}" fill="var(--gw-socket-lower)"/>`;
      svg += `<path data-socket-floor="true" d="${profile.floor}" fill="var(--gw-pocket)"/>`;
      if(options.magnets) for(const [mx,my] of profile.magnetCenters) {
        svg += circle(mx,my,options.magnetDiameter/2,
          `data-magnet-pocket="true" fill="var(--gw-recess)" stroke="var(--gw-muted)" stroke-width="${.6/scale}"`);
      }
      svg += '</g>';
    }
    svg += '</g>';
    // Only the printable piece has an outside boundary, not every grid cell.
    svg += outline(p,
      `fill="none" stroke="var(${pieces.length>1&&i===options.selected?'--gw-blue':'--gw-muted'})" stroke-width="${(pieces.length>1&&i===options.selected?1.5:.8)/scale}"`);
    if(options.showSplits && pieces.length>1) {
      if(p.x1<pw) svg += `<path d="M ${p.x1} ${p.y0} V ${p.y1}" fill="none" stroke="var(--gw-blue)" stroke-width="${1.5/scale}" stroke-dasharray="4 3"/>`;
      if(p.y1<pd) svg += `<path d="M ${p.x0} ${p.y1} H ${p.x1}" fill="none" stroke="var(--gw-blue)" stroke-width="${1.5/scale}" stroke-dasharray="4 3"/>`;
    }
    svg += '</g>';
  });
  container.innerHTML = svg + '</g></svg>';
}
