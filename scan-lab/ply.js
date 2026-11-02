'use strict';
// Reads vertex properties only. Faces are deliberately not rendered.
function parsePLY(buffer,maxPoints=50000){
 const bytes=new Uint8Array(buffer),search=new TextDecoder('latin1').decode(bytes.subarray(0,Math.min(bytes.length,65536))),match=/end_header\r?\n/.exec(search);
 if(!match||!search.startsWith('ply\n')&&!search.startsWith('ply\r\n'))throw Error('Ungültiger oder zu großer PLY-Header.');
 const offset=match.index+match[0].length,lines=search.slice(0,match.index).split(/\r?\n/);let format='',count=-1,current='',props=[];
 for(const line of lines){const a=line.trim().split(/\s+/);if(a[0]==='format')format=a[1];if(a[0]==='element'){current=a[1];if(current==='vertex')count=Number(a[2]);else if(count<0)throw Error('PLY muss mit Vertex-Element beginnen.')}if(a[0]==='property'&&current==='vertex'){if(a[1]==='list')throw Error('Listen in Vertex-Eigenschaften werden nicht unterstützt.');props.push({type:a[1],name:a[2]})}}
 if(!Number.isSafeInteger(count)||count<1||count>5000000||!['ascii','binary_little_endian','binary_big_endian'].includes(format))throw Error('PLY-Format oder Punktzahl wird nicht unterstützt.');
 for(const k of ['x','y','z'])if(!props.some(p=>p.name===k))throw Error('PLY benötigt x, y und z.');
 const types={char:['getInt8',1],uchar:['getUint8',1],int8:['getInt8',1],uint8:['getUint8',1],short:['getInt16',2],ushort:['getUint16',2],int16:['getInt16',2],uint16:['getUint16',2],int:['getInt32',4],uint:['getUint32',4],int32:['getInt32',4],uint32:['getUint32',4],float:['getFloat32',4],float32:['getFloat32',4],double:['getFloat64',8],float64:['getFloat64',8]};if(props.some(p=>!types[p.type]))throw Error('Nicht unterstützter PLY-Datentyp.');
 let points=[],stride=Math.max(1,Math.ceil(count/maxPoints));function add(values){let o={};props.forEach((p,i)=>o[p.name]=values[i]);if(![o.x,o.y,o.z].every(Number.isFinite))return;let color=['red','green','blue'].every(k=>Number.isFinite(o[k]))?[o.red,o.green,o.blue].map(x=>Math.max(0,Math.min(255,Math.round(x)))):[112,226,188];points.push({x:o.x,y:o.y,z:o.z,color})}
 if(format==='ascii'){let rows=new TextDecoder().decode(bytes.subarray(offset)).split(/\r?\n/);if(rows.length<count)throw Error('PLY-Datei ist unvollständig.');for(let i=0;i<count;i+=stride){let values=rows[i].trim().split(/\s+/).map(Number);if(values.length<props.length||values.slice(0,props.length).some(x=>!Number.isFinite(x)))throw Error('Ungültige Vertex-Daten.');add(values)}}
 else {let view=new DataView(buffer),size=props.reduce((n,p)=>n+types[p.type][1],0);if(offset+size*count>bytes.length)throw Error('PLY-Datei ist unvollständig.');for(let i=0;i<count;i+=stride){let at=offset+i*size,values=[];for(const p of props){const [fn,len]=types[p.type];values.push(view[fn](at,format==='binary_little_endian'));at+=len}add(values)}}
 if(!points.length)throw Error('Keine gültigen Punkte gefunden.');return {points,total:count,format};
}
if(typeof module!=='undefined')module.exports={parsePLY};
