(function(){
  const key = "casescope-theme";
  function apply(mode){
    const m = (mode === "light" ? "light" : "dark");
    document.documentElement.setAttribute("data-theme", m);
    if(m === "light"){ document.body.classList.remove("bg"); } else { document.body.classList.add("bg"); }
    localStorage.setItem(key, m);
  }
  document.addEventListener('DOMContentLoaded', () => {
    apply(localStorage.getItem(key) || 'dark');
    const btn = document.getElementById('themeToggle');
    if(btn){ btn.addEventListener('click', ()=> apply((localStorage.getItem(key)||'dark')==='dark'?'light':'dark')); }
  });
})();

// Case management
function loadCases() {
  fetch('/api/cases')
    .then(response => response.json())
    .then(data => {
      const select = document.getElementById('currentCase');
      select.innerHTML = '<option value="">Select Case...</option>';
      
      data.cases.forEach(caseItem => {
        const option = document.createElement('option');
        option.value = caseItem.id;
        option.textContent = caseItem.name;
        select.appendChild(option);
      });
      
      // Restore selected case from localStorage
      const savedCase = localStorage.getItem('currentCase');
      if (savedCase) {
        select.value = savedCase;
      }
    })
    .catch(error => console.error('Failed to load cases:', error));
}

function switchCase(caseId) {
  if (caseId) {
    localStorage.setItem('currentCase', caseId);
    window.location.href = `/cases/${caseId}`;
  } else {
    localStorage.removeItem('currentCase');
    window.location.href = '/dashboard';
  }
}

// Load cases when page loads
document.addEventListener('DOMContentLoaded', () => {
  loadCases();
});
