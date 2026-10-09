import http from 'node:http';
import {createHash} from 'node:crypto';
import {mkdir, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseArgs} from 'node:util';
import {produce} from './cli.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
// This generic fixture is only materialized in ignored output. No challenge product is created.
const html = `<!doctype html><html lang="en"><meta charset="utf-8"><title>Checklist rehearsal</title>
<style>body{margin:0;background:#f2f5fa;color:#172238;font:24px Arial}main{max-width:860px;margin:65px auto}h1{font-size:48px;margin-bottom:12px}p{color:#506079}form{display:flex;gap:12px;margin:35px 0}input,button{font:24px Arial;padding:15px;border:1px solid #9daabd;border-radius:6px}input{flex:1}button{background:#17665d;color:white;cursor:pointer}li{padding:18px;background:white;margin-bottom:12px;list-style:none;border-radius:6px}ul{padding:0}label{display:flex;gap:18px;align-items:center}label input{flex:0;width:24px;height:24px}#status{font-weight:bold;color:#17665d}</style>
<main><h1>A simple checklist</h1><p>Disposable sample for recording rehearsal.</p><form><input id="task" aria-label="Task" placeholder="Add a task"><button>Add task</button></form><p id="error" role="alert"></p><ul id="list"></ul><p id="status" role="status">0 of 0 complete</p></main>
<script>let count=0;const form=document.querySelector('form');form.addEventListener('submit',event=>{event.preventDefault();const input=document.querySelector('#task');const error=document.querySelector('#error');if(!input.value.trim()){error.textContent='Enter a task first.';return}error.textContent='';const row=document.createElement('li');const label=document.createElement('label');const check=document.createElement('input');check.type='checkbox';const text=document.createElement('span');text.textContent=input.value.trim();label.append(check,text);row.append(label);document.querySelector('#list').append(row);count++;input.value='';const update=()=>{const done=document.querySelectorAll('li input:checked').length;document.querySelector('#status').textContent=done+' of '+count+' complete';text.style.textDecoration=check.checked?'line-through':'none'};check.addEventListener('change',update);update()});</script></html>`;
const {values} = parseArgs({options: {renderer: {type: 'string', default: 'remotion'}, tts: {type: 'string', default: 'auto'}}});
const directory = path.join(here, 'output', `rehearsal-${Date.now()}`);
await mkdir(directory, {recursive: true});
await writeFile(path.join(directory, 'sample.html'), html);
const server = http.createServer((request, response) => {response.writeHead(200, {'Content-Type': 'text/html; charset=utf-8'}); response.end(html);});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const add = [{type: 'fill', selector: '#task', value: 'Prepare a demo', pauseAfter: 1.8}, {type: 'click', selector: 'button'},
  {type: 'assertText', selector: '#list', value: 'Prepare a demo', pauseAfter: 0.8}];
const evidence = ['sample.html; runtime assertions recorded in evidence.json (rehearsal only)'];
const board = {mode: 'rehearsal', title: 'A simple checklist',
  build: {id: `generic-fixture-sha256:${createHash('sha256').update(html).digest('hex')}`},
  baseURL: `http://127.0.0.1:${server.address().port}`, scenes: [
    {id: 'hook', kind: 'title', card: 'intro', heading: 'One task. One clear next step.', eyebrow: 'A SIMPLE CHECKLIST',
      duration: 4, narrationStart: 0.35, caption: 'Keep one small task in view.', narration: 'Keep one small task in view.'},
    {id: 'add', kind: 'capture', duration: 8, ready: 'h1', leadIn: 0.5, actions: add, narrationStart: 0.4,
      camera: {scale: 1.05, x: 0.3, y: 0.53, start: 2.8, end: 4.5},
      captions: [{text: 'Type a task.', start: 0.4, end: 1.5}, {text: 'Add it to the checklist.', start: 1.5, end: 4.5}],
      caption: 'Add a task to the checklist.', narration: 'Type a task and add it to the checklist.'},
    {id: 'complete', kind: 'capture', duration: 7, ready: 'h1', leadIn: 0.4, actions: [...add, {type: 'check', selector: 'li input'},
      {type: 'assertText', selector: '#status', value: '1 of 1 complete'}],
      narrationStart: 2.4, camera: {scale: 1.06, x: 0.32, y: 0.61, start: 3.3, end: 5},
      highlight: {x: 0.155, y: 0.60, width: 0.25, height: 0.07},
      captions: [{text: 'Complete it.', start: 2.4, end: 3.5}, {text: 'The count updates.', start: 3.5, end: 6.2}],
      caption: 'Mark it complete and see the updated count.', narration: 'Complete it. The count updates.'},
    {id: 'error', kind: 'capture', duration: 5, ready: 'h1', leadIn: 0.5, narrationStart: 0.6, actions: [{type: 'click', selector: 'button'},
      {type: 'assertText', selector: '#error', value: 'Enter a task first.'}],
      caption: 'Empty input gets a clear message.', narration: 'Empty input gets a clear message.'},
    {id: 'close', kind: 'title', card: 'outro', heading: 'A small task, completed.', eyebrow: 'THE RESULT', duration: 5,
      narrationStart: 0.4, caption: 'Real clicks. Real results.', narration: 'Real clicks. Real results.'}
  ].map(scene => ({...scene, status: 'VERIFIED', evidence}))};
await writeFile(path.join(directory, 'storyboard.json'), JSON.stringify(board, null, 2));
try {
  await produce(path.join(directory, 'storyboard.json'), {out: path.join(directory, 'render'), ...values});
} finally {
  await new Promise(resolve => server.close(resolve));
}
