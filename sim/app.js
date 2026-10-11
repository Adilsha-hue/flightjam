const sections={
assembly:['assembly-workbench.html','Hardware workbench','Arrange boards and explore antenna and power connections.'],
wiring:['hardware-lab.html','Wiring & faults','Inspect connections and simulate component failures.'],
flight:['flight-world.html','Flight world','Watch simulated telemetry travel from the RC plane to ground.'],
code:['implementation-lab.html','Code walkthrough','Step through input, encryption, transport and decoding.'],
build:['build-setup.html','Parts & firmware','Explore component requirements, antennas and TX/RX source.'],
learning:['learning-lab.html','Learning lab','Understand authentication, packet loss and replay rejection.'],
bench:['bench-simulator.html','Original simulator','Explore the original repository’s bench demonstration.']};
const frames=new Map();
function navigate(){const requested=location.hash.slice(1);const key=Object.hasOwn(sections,requested)?requested:'assembly';if(key!==requested){history.replaceState(null,'','#'+key)}const [file,title,description]=sections[key];document.title=title+' · FlightJam';document.getElementById('view-title').textContent=title;document.getElementById('view-description').textContent=description;for(const link of document.querySelectorAll('[data-view]')){if(link.dataset.view===key)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current')}if(!frames.has(key)){const frame=document.createElement('iframe');frame.title=title;frame.src=file;document.getElementById('views').append(frame);frames.set(key,frame)}for(const [id,frame]of frames)frame.hidden=id!==key;}
window.addEventListener('hashchange',navigate);
window.addEventListener('message',event=>{if(event.origin!==location.origin||![...frames.values()].some(frame=>frame.contentWindow===event.source)||event.data?.type!=='flightjam:navigate')return;const entry=Object.entries(sections).find(([,info])=>info[0]===event.data.file);if(entry)location.hash=entry[0]});
document.querySelector('.menu').addEventListener('click',e=>{const nav=document.getElementById('navigation');nav.hidden=!nav.hidden;e.currentTarget.setAttribute('aria-expanded',String(!nav.hidden))});navigate();
document.querySelector('.skip').addEventListener('click',event=>{event.preventDefault();document.getElementById('workspace').focus()});
