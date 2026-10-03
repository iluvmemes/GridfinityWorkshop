/* Channel planning in millimeters; independent of DOM and Fusion. */
function planMagnetChannels(c, envelope, family) {
  const shape=c.channelShape;
  const width=(shape==='round'?c.storedDiameter:c.channelWidth)+c.storedClearance;
  const depth=(shape==='rectangle'?c.channelDepth:shape==='square'?c.channelWidth:c.storedDiameter)+c.storedClearance;
  const edge=2, gapX=c.channelGapX===undefined?1:c.channelGapX;
  const gapY=c.channelGapLinked===false?(c.channelGapY===undefined?1:c.channelGapY):gapX;
  const endAllowance=(family==='clasp'||family==='cartridge')?12.2:0;
  const usableWidth=Math.max(0,envelope.w-endAllowance-2*edge);
  const usableDepth=Math.max(0,envelope.d-2*edge);
  const columns=c.channelColumns, rows=c.channelRows;
  const valid=['round','square','rectangle'].includes(shape)&&
    [width,depth,usableWidth,usableDepth,gapX,gapY].every(Number.isFinite)&&width>0&&depth>0&&gapX>=1&&gapX<=30&&gapY>=1&&gapY<=30&&
    Number.isInteger(columns)&&Number.isInteger(rows)&&columns>=1&&rows>=1&&columns<=48&&rows<=48;
  if(!valid)return {valid:false,error:'Enter valid channel dimensions and whole-number counts.',positions:[]};
  const maxColumns=Math.max(0,Math.floor((usableWidth+gapX)/(width+gapX)));
  const maxRows=Math.max(0,Math.floor((usableDepth+gapY)/(depth+gapY)));
  const usedWidth=columns*width+(columns-1)*gapX,usedDepth=rows*depth+(rows-1)*gapY;
  const fits=columns<=maxColumns&&rows<=maxRows;
  const x0=(envelope.w-usedWidth)/2,y0=(envelope.d-usedDepth)/2;
  const positions=[];
  if(fits)for(let row=0;row<rows;row++)for(let column=0;column<columns;column++)
    positions.push({x:x0+column*(width+gapX),y:y0+row*(depth+gapY)});
  return {valid:fits,shape,width,depth,columns,rows,count:columns*rows,maxColumns,maxRows,capacity:maxColumns*maxRows,
    usableWidth,usableDepth,usedWidth,usedDepth,x0,y0,edge,gapX,gapY,positions,
    error:fits?null:`Requested ${columns} × ${rows} (${columns*rows}) channels exceeds the available space. This shape and size fit at most ${maxColumns} × ${maxRows} (${maxColumns*maxRows}).`};
}
if(typeof module!=='undefined')module.exports={planMagnetChannels};
