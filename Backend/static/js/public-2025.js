(function(){
  // Navbar efecto scrolled
  const navbar = document.querySelector('.navbar');
  const onScroll = () => {
    if (!navbar) return;
    if (window.scrollY > 8) navbar.classList.add('scrolled');
    else navbar.classList.remove('scrolled');
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Activar enlace actual en navbar
  const currentPath = window.location.pathname.replace(/\/$/, '');
  document.querySelectorAll('.navbar .nav-link').forEach(link => {
    const href = link.getAttribute('href') || '';
    const normalized = href.replace(/\/$/, '');
    if (normalized && currentPath === normalized) link.classList.add('active');
  });

  // IntersectionObserver para revelar elementos
  const observer = new IntersectionObserver((entries)=>{
    entries.forEach(entry=>{
      if(entry.isIntersecting){
        entry.target.classList.add('reveal-visible');
        observer.unobserve(entry.target);
      }
    });
  },{threshold:0.12});

  document.querySelectorAll('.reveal').forEach(el=>observer.observe(el));
})();


