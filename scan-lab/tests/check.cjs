process.chdir(require('node:path').join(__dirname, '..'));
const assert=require('node:assert/strict');
const fs=require('node:fs'), vm=require('node:vm');
const elem=()=>({value:'5',addEventListener(){},getContext(){return {clearRect(){},fillRect(){}}},classList:{add(){},remove(){}},style:{},setPointerCapture(){},width:900,height:530});
const elements={};const sandbox={document:{getElementById:id=>elements[id]??=elem(),querySelectorAll:()=>[],createElement:()=>elem()},module:{exports:{}},console,TextDecoder,Blob,URL};
vm.runInNewContext(fs.readFileSync('app.js','utf8'),sandbox);
const {validatePacket,depthStats,makePoints,transformed}=sandbox.module.exports;
const packet=JSON.parse(fs.readFileSync('tests/demo-depth.json','utf8'));
assert.equal(validatePacket(packet),packet);const stats=depthStats(packet,5);assert.equal(stats.inside,stats.valid);assert(stats.inside>0&&stats.inside<stats.total);assert.equal(depthStats(packet,1).inside,0);assert.throws(()=>validatePacket({...packet,depthMeters:[1]}));const p=makePoints(packet,5);assert.equal(p.length,stats.inside);const moved=transformed({x:1,y:2,z:3,color:[1,2,3]},{x:1,y:0,z:0,yaw:0});assert.equal(moved.x,2);assert.equal(moved.z,3);console.log('OK: packet validation, 5 m statistics, point projection and manual transform');
