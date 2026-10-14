/* Never submit geometry until the live Python handler acknowledges the connection. */
(function(root){
 function decode(raw){const reply=typeof raw==='string'?JSON.parse(raw):raw;if(!reply||reply.ok!==true)throw Error(reply?.error||'Fusion did not acknowledge the request.');return reply;}
 async function submit(action,data){
  if(typeof adsk==='undefined'||typeof adsk.fusionSendData!=='function')throw Error('Open this panel inside Fusion.');
  let timer;
  try{await Promise.race([Promise.resolve(adsk.fusionSendData('ping','{}')).then(decode),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('The panel lost its Fusion connection. Close and reopen it, then try again. No creation request was sent.')),5000);})]);}finally{clearTimeout(timer);}
  return decode(await adsk.fusionSendData(action,JSON.stringify(data)));
 }
 root.FusionBridge={submit};
})(window);
