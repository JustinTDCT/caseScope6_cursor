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
