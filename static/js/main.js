
const CART_KEY = "bagan_bazar_cart";
function getCart(){try{return JSON.parse(localStorage.getItem(CART_KEY)||"[]")}catch(e){return []}}
function saveCart(c){localStorage.setItem(CART_KEY,JSON.stringify(c));updateCartCount()}
function addToCart(id,name,price,image){
 let c=getCart(), found=c.find(x=>x.id===id);
 if(found) found.qty++; else c.push({id,name,price,image,qty:1});
 saveCart(c); alert(name+" কার্টে যোগ হয়েছে!");
}
function updateCartCount(){let n=getCart().reduce((s,x)=>s+x.qty,0);document.querySelectorAll("[data-cart-count]").forEach(x=>x.textContent=n)}
function searchProducts(){
 const q=(document.getElementById("productSearch")?.value||"").toLowerCase();
 document.querySelectorAll("[data-product]").forEach(card=>{card.style.display=card.dataset.product.toLowerCase().includes(q)?"":"none"});
}
function renderCheckoutCart(){
 const host=document.getElementById("checkoutCart"); if(!host)return;
 const cart=getCart(); let total=0;
 if(!cart.length){host.innerHTML="<p>আপনার কার্ট খালি। <a href='/'>পণ্য দেখুন</a></p>";return}
 host.innerHTML=cart.map(x=>{total+=x.price*x.qty;return `<div class="cart-line"><span>${x.name} × ${x.qty}</span><b>৳${(x.price*x.qty).toFixed(0)}</b></div>`}).join("")+
 `<hr><div class="cart-line"><span>পণ্যের মূল্য</span><b>৳${total.toFixed(0)}</b></div><div class="cart-line"><span>ডেলিভারি চার্জ</span><b>৳60</b></div><div class="cart-line"><strong>সর্বমোট</strong><strong>৳${(total+60).toFixed(0)}</strong></div>`;
 document.getElementById("cartJson").value=JSON.stringify(cart.map(x=>({id:x.id,qty:x.qty})));
}
document.addEventListener("DOMContentLoaded",()=>{updateCartCount();renderCheckoutCart()});

// Automatic hero carousel with manual dot navigation
function initHeroSlider(){
 const slides=[...document.querySelectorAll('.hero-slide')];
 const dots=[...document.querySelectorAll('.hero-dots button')];
 if(!slides.length)return;
 let active=0, timer;
 const show=(index)=>{active=(index+slides.length)%slides.length;slides.forEach((s,i)=>s.classList.toggle('active',i===active));dots.forEach((d,i)=>d.classList.toggle('active',i===active));};
 const start=()=>{clearInterval(timer);timer=setInterval(()=>show(active+1),5200)};
 dots.forEach((dot,i)=>dot.addEventListener('click',()=>{show(i);start()}));
 start();
}
function initReveal(){
 const targets=document.querySelectorAll('.section,.promo-row,.features,.blog-card,.product-card,.category');
 targets.forEach(el=>el.classList.add('reveal'));
 if(!('IntersectionObserver' in window)){targets.forEach(el=>el.classList.add('is-visible'));return;}
 const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('is-visible');observer.unobserve(entry.target)}}),{threshold:.08});
 targets.forEach(el=>observer.observe(el));
}
document.addEventListener('DOMContentLoaded',()=>{initHeroSlider();initReveal()});

// Prevent broken-image icons if a third-party image host is temporarily unavailable.
document.addEventListener('error', function(event){
 const img=event.target;
 if(img && img.tagName==='IMG' && !img.dataset.fallbackApplied){
   img.dataset.fallbackApplied='1';
   img.src='/static/images/garden-fallback.svg';
 }
}, true);

// Hero backgrounds use the same resilient fallback strategy as inline product photos.
function validateHeroBackgrounds(){
 document.querySelectorAll('.hero-slide').forEach(slide=>{
   const bg=getComputedStyle(slide).backgroundImage;
   const match=bg.match(/url\(["']?(.*?)["']?\)/);
   if(!match || !match[1]) return;
   const probe=new Image();
   probe.onerror=()=>slide.style.setProperty('--hero-bg', "url('/static/images/garden-fallback.svg')");
   probe.src=match[1];
 });
}
document.addEventListener('DOMContentLoaded',validateHeroBackgrounds);
