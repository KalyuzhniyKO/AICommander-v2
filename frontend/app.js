let task=null,round=null;
const el=id=>document.getElementById(id);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
async function api(path,method="GET",payload){
 const options={method,headers:{"Content-Type":"application/json"}};
 if(payload!==undefined)options.body=JSON.stringify(payload);
 const response=await fetch(path,options);
 const data=await response.json();
 if(!response.ok)throw new Error(JSON.stringify(data));return data;
}
function status(s){el("status").textContent=s}
async function refresh(){
 if(!task)return;task=await api("/tasks/"+task.id);
 round=task.rounds[task.rounds.length-1]||null;
 el("roundMeta").textContent=round?"Раунд #"+round.round_number:"Пока без раундов";
 el("rounds").innerHTML=task.rounds.map(r=>'<article class="round-card"><h3>Раунд '+r.round_number+'</h3>'+
 (r.role_outputs||[]).map(x=>'<details><summary>'+esc(x.role)+' · '+esc(x.status)+' · '+esc(x.model_id)+'</summary><pre>'+esc(x.output)+'</pre></details>').join("")+'</article>').join("");
}
async function models(){try{el("models").textContent=JSON.stringify(await api("/models/status"),null,2)}catch(e){status(e.message)}}
el("runTeam").onclick=async()=>{try{const s=el("taskText").value.trim();if(!s)return status("Введите задачу");status("Выполняется");task=await api("/tasks","POST",{description:s});round=await api("/tasks/"+task.id+"/rounds","POST",{});await refresh();await models();status("Раунд завершён")}catch(e){status(e.message)}};
el("runNext").onclick=async()=>{try{if(!task)return status("Сначала создайте задачу");round=await api("/tasks/"+task.id+"/rounds","POST",{user_comment:el("commentText").value});await refresh();status("Раунд завершён")}catch(e){status(e.message)}};
el("rerunRole").onclick=async()=>{try{if(!round)return status("Нет раунда");await api("/rounds/"+round.id+"/roles/"+el("roleSelect").value+"/rerun","POST");await refresh();status("Роль перезапущена")}catch(e){status(e.message)}};
el("checkModels").onclick=async()=>{try{const data=await api("/models/check","POST");status(JSON.stringify(data));await models()}catch(e){status(e.message)}};
el("refreshModels").onclick=models;models();
