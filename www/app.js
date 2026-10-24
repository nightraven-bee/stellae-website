(() => {
  'use strict';
  const config = window.STELLAE_CONFIG;
  if (!config) return;
  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const connection = navigator.connection;
  const safeUrl = value => {
    if (!value) return '';
    try {const url = new URL(value,location.href);return ['http:','https:'].includes(url.protocol) ? url.href : '';} catch {return '';}
  };
  const textLines = (element, lines) => {
    element.replaceChildren();
    lines.forEach((line,index) => {if(index) element.append(document.createElement('br'));element.append(document.createTextNode(line));});
  };
  $('#company').textContent = config.legal.company;
  $('#icp').textContent = config.legal.icp;
  $$('[data-room]').forEach(link => {link.href = safeUrl(config.roomUrl) || '#world';});
  for (const name of ['privacy','terms']) {
    const link = $('#'+name+'-link');
    const url = safeUrl(config.legal[name]);
    if (url) {link.href=url;link.hidden=false;link.target='_blank';link.rel='noopener';}
  }

  // Native dialogs provide Escape, focus trapping and focus restoration.
  const dialogs = $$('dialog');
  const openDialog = dialog => {if(!dialog.open) dialog.showModal();};
  dialogs.forEach(dialog => {
    dialog.querySelector('[data-close]').addEventListener('click',()=>dialog.close());
    dialog.addEventListener('click',event => {
      if(event.target!==dialog)return;
      const box=dialog.getBoundingClientRect();
      if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom) dialog.close();
    });
  });
  const menu = $('#menu-dialog');
  $('.menu-toggle').addEventListener('click',()=>openDialog(menu));
  $$('#menu-dialog nav a').forEach(link=>link.addEventListener('click',()=>menu.close()));
  matchMedia('(min-width: 701px)').addEventListener('change',event=>{if(event.matches&&menu.open)menu.close();});

  const downloadDialog = $('#download-dialog');
  const openDownloads = () => openDialog(downloadDialog);
  $$('[data-download]').forEach(button=>button.addEventListener('click',openDownloads));

  const heroVideo=$('#hero-video');
  const heroArt=heroVideo.parentElement;
  const motionToggle=$('#motion-toggle');
  let heroManualPaused=false;
  let heroVisible=true;
  let heroWasPlaying=false;
  let heroAttempt=0,heroFrame=0,heroFrameKind='';
  const cancelHeroFrame=()=>{
    if(heroFrame){if(heroFrameKind==='video')heroVideo.cancelVideoFrameCallback?.(heroFrame);else cancelAnimationFrame(heroFrame);}
    heroFrame=0;
  };
  const keepHeroPoster=()=>{heroArt.dataset.videoState='poster';};
  const revealHeroFrame=()=>{
    if(heroFrame||!heroVisible||document.hidden||heroVideo.readyState<2)return;
    const attempt=heroAttempt;
    const present=()=>{
      heroFrame=0;
      if(attempt!==heroAttempt||!heroVisible||document.hidden||heroVideo.readyState<2||heroVideo.seeking)return;
      heroArt.dataset.videoState=heroVideo.paused?'paused':'playing';
    };
    if(heroVideo.requestVideoFrameCallback){heroFrameKind='video';heroFrame=heroVideo.requestVideoFrameCallback(present);}
    else{heroFrameKind='animation';heroFrame=requestAnimationFrame(()=>{heroFrame=requestAnimationFrame(present);});}
  };
  const pauseHero=({poster=false}={})=>{
    heroAttempt++;cancelHeroFrame();heroVideo.pause();
    if(poster)keepHeroPoster();else if(heroArt.dataset.videoState==='playing')heroArt.dataset.videoState='paused';
  };
  const updateMotion=()=>{
    const playing=!heroVideo.paused&&!heroVideo.error;
    motionToggle.replaceChildren(document.createTextNode(playing?'Ⅱ ':'▷ '));
    const label=document.createElement('span');label.textContent=playing?'暂停动态':'播放动态';motionToggle.append(label);
    motionToggle.setAttribute('aria-label',playing?'暂停首屏动态':'播放首屏动态');
  };
  const startHero=async()=>{
    if(document.documentElement.classList.contains('is-loading')||!heroVisible||document.hidden||$('#trailer-dialog').open)return;
    const attempt=++heroAttempt;cancelHeroFrame();
    const source=heroVideo.querySelector('source');
    if(!source.hasAttribute('src')||heroVideo.error){keepHeroPoster();source.src=source.dataset.src;heroVideo.load();}
    heroVideo.muted=true;
    try{await heroVideo.play();if(attempt===heroAttempt)revealHeroFrame();}
    catch{if(attempt===heroAttempt){if(heroVideo.readyState<2)keepHeroPoster();updateMotion();}}
  };
  heroVideo.addEventListener('play',updateMotion);heroVideo.addEventListener('pause',updateMotion);
  for(const event of ['playing','loadeddata','seeked'])heroVideo.addEventListener(event,revealHeroFrame);
  for(const event of ['emptied','waiting','seeking'])heroVideo.addEventListener(event,()=>{cancelHeroFrame();keepHeroPoster();});
  heroVideo.addEventListener('stalled',()=>{if(heroVideo.readyState<2)keepHeroPoster();});
  heroVideo.addEventListener('error',()=>{cancelHeroFrame();keepHeroPoster();updateMotion();});
  heroVideo.addEventListener('canplay',()=>{
    if(heroVisible&&!heroManualPaused&&!reduced.matches&&!connection?.saveData&&!document.hidden&&heroVideo.paused)startHero();
  });
  heroVideo.addEventListener('timeupdate',()=>{if(heroArt.dataset.videoState==='poster'&&!heroVideo.paused)revealHeroFrame();});
  motionToggle.addEventListener('click',()=>{
    if(heroVideo.paused||heroVideo.error){heroManualPaused=false;startHero();}
    else{heroManualPaused=true;pauseHero();}
  });
  if(!reduced.matches&&!connection?.saveData) startHero();
  document.addEventListener('stellae:entered',()=>{
    if(heroVisible&&!heroManualPaused&&!reduced.matches&&!connection?.saveData&&!document.hidden)startHero();
  },{once:true});
  reduced.addEventListener('change',event=>{if(event.matches){pauseHero();heroManualPaused=true;}});

  const featureVideo=$('#feature-video');
  const featurePlay=$('#feature-play');
  let featureIndex=0;
  const featureButtons=[];
  const updateFeaturePlay=()=>{
    featurePlay.querySelector('span').textContent=featureVideo.paused?'播放功能实录':'暂停功能实录';
    featurePlay.setAttribute('aria-label',featureVideo.paused?'播放功能实录':'暂停功能实录');
  };
  const renderFeature=(index,focus=false)=>{
    featureIndex=index;
    const item=config.features[index];
    featureVideo.pause();featureVideo.removeAttribute('src');featureVideo.load();
    featureVideo.poster=item.poster;featureVideo.dataset.source=item.video;
    featureVideo.setAttribute('aria-label',item.note);
    $('#feature-en').textContent=item.en;
    $('#feature-number').textContent=String(index+1).padStart(2,'0');
    textLines($('#feature-title'),item.title);
    $('#feature-description').textContent=item.description;
    $('#feature-source').textContent=item.note;
    $('#feature-panel').setAttribute('aria-labelledby','feature-tab-'+item.key);
    featureButtons.forEach((button,i)=>{button.setAttribute('aria-selected',String(index===i));button.tabIndex=index===i?0:-1;});
    if(focus)featureButtons[index].focus();
    updateFeaturePlay();
  };
  const tabKeyboard=(event,index,total,select)=>{
    let next=index;
    if(event.key==='ArrowRight')next=(index+1)%total;
    else if(event.key==='ArrowLeft')next=(index+total-1)%total;
    else if(event.key==='Home')next=0;
    else if(event.key==='End')next=total-1;
    else return;
    event.preventDefault();select(next,true);
  };
  config.features.forEach((item,index)=>{
    const button=document.createElement('button');button.type='button';button.role='tab';
    button.id='feature-tab-'+item.key;button.textContent=item.name;button.setAttribute('aria-label',item.name);button.setAttribute('aria-controls','feature-panel');
    button.addEventListener('click',()=>renderFeature(index));
    button.addEventListener('keydown',event=>tabKeyboard(event,index,config.features.length,renderFeature));
    $('#feature-tabs').append(button);featureButtons.push(button);
  });
  renderFeature(0);
  featurePlay.addEventListener('click',async()=>{
    if(featureVideo.paused){
      if(!featureVideo.hasAttribute('src')) featureVideo.src=featureVideo.dataset.source;
      try{await featureVideo.play();}catch{featurePlay.querySelector('span').textContent='播放失败，点击重试';}
    }else featureVideo.pause();
  });
  featureVideo.addEventListener('play',updateFeaturePlay);featureVideo.addEventListener('pause',updateFeaturePlay);
  featureVideo.addEventListener('error',()=>{featurePlay.querySelector('span').textContent='播放失败，点击重试';});
  $$('[data-feature]').forEach(link=>link.addEventListener('click',()=>{
    const index=config.features.findIndex(item=>item.key===link.dataset.feature);if(index>=0)renderFeature(index);
  }));

  // Keep the app's front/back artwork and 520ms flip; add optical foil,
  // independent art/text parallax and a first-interaction cursor cue.
  function createFlashCard(item,options={}) {
    const button=document.createElement('button');button.type='button';button.className='flash-card';button.dataset.holo='css';
    button.dataset.card=item.index;button.setAttribute('aria-label','翻转'+item.name+'卡片');
    const tilt=document.createElement('span');tilt.className='flash-tilt';
    const front=document.createElement('span');front.className='flash-face flash-front';
    const back=document.createElement('span');back.className='flash-face flash-back';
    const makeImage=(source,alt)=>{const image=document.createElement('img');image.src=source;image.alt=alt;image.loading='lazy';image.width=700;image.height=994;return image;};
    const frontClip=document.createElement('span');frontClip.className='flash-face-clip';
    const backClip=document.createElement('span');backClip.className='flash-face-clip';
    const flatPoster=makeImage(item.image,item.name+'正面插画');
    frontClip.append(flatPoster);
    if(item.layers){
      button.style.setProperty('--subject-scale',item.layers.subjectScale??1);
      button.style.setProperty('--subject-offset-y',item.layers.subjectShiftY??'0%');
      const scene=document.createElement('span');scene.className='flash-art-depth';scene.setAttribute('aria-hidden','true');
      const planes=item.layers.planes||['background','subject','foreground'].map(kind=>({kind,src:item.layers[kind]}));
      const layerImages=planes.map((plane,index)=>{
        const image=makeImage(plane.src,'');image.loading='eager';image.className='flash-depth-layer flash-depth-'+plane.kind;image.dataset.layer=plane.kind;
        if(item.layers.planes){
          image.classList.add('flash-depth-plane');
          image.style.setProperty('--layer-x',plane.x+'px');image.style.setProperty('--layer-y',plane.y+'px');image.style.setProperty('--layer-order',index);
        }
        scene.append(image);return image;
      });
      frontClip.append(scene);button.dataset.layered='loading';
      Promise.all(layerImages.map(image=>image.decode())).then(()=>{
        flatPoster.remove();button.dataset.layered='true';
      }).catch(error=>{scene.remove();button.dataset.layered='error';button.dataset.layerError=error.message;});
    }
    backClip.append(makeImage(item.back,item.name+'背面：记忆快照'));
    const shade=document.createElement('span');shade.className='flash-text-shade';shade.setAttribute('aria-hidden','true');
    const holo=document.createElement('span');holo.className='flash-holo';holo.setAttribute('aria-hidden','true');
    const title=document.createElement('span');title.className='flash-heading';
    const name=document.createElement('span');name.className='flash-name';name.textContent=item.name;
    const en=document.createElement('span');en.className='flash-en';en.textContent=item.en;title.append(name,en);
    const quote=document.createElement('span');quote.className='flash-quote';quote.textContent=item.quote;
    const dot=document.createElement('span');dot.className='flash-rarity';dot.setAttribute('aria-hidden','true');
    const surface=document.createElement('canvas');surface.className='flash-shader';surface.setAttribute('aria-hidden','true');
    const glare=document.createElement('span');glare.className='flash-glare';glare.setAttribute('aria-hidden','true');
    const grating=document.createElement('span');grating.className='flash-grating';grating.setAttribute('aria-hidden','true');
    frontClip.append(shade,holo,surface,glare,grating,title,quote,dot);front.append(frontClip);back.append(backClip);tilt.append(front,back);button.append(tilt);
    if(options.preview)button.dataset.preview='true';
    button.setAttribute('aria-keyshortcuts','ArrowLeft ArrowRight ArrowUp ArrowDown Enter Space');
    if(options.guide){
      const guide=document.createElement('span');guide.className='flash-click-guide';guide.setAttribute('aria-hidden','true');
      const ring=document.createElement('span');ring.className='guide-click-ring';
      const ring2=document.createElement('span');ring2.className='guide-click-ring guide-click-ring-second';
      const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 36 44');
      const arrow=document.createElementNS('http://www.w3.org/2000/svg','path');arrow.setAttribute('d','M5 3 5 32 12.8 24.3 19 38 25 35 18.8 21.7 30 21.7Z');svg.append(arrow);
      const label=document.createElement('span');label.className='guide-click-label';label.textContent='点击翻面';
      guide.append(ring,ring2,svg,label);button.append(guide);
    }
    const material=window.StellaeHolo?.mount(surface,button,Number(item.index)*.17);
    let flipped=!!options.flipped;
    const setFlipped=value=>{
      flipped=!!value;button.dataset.flipped=String(flipped);button.setAttribute('aria-pressed',String(flipped));
      front.setAttribute('aria-hidden',String(flipped));back.setAttribute('aria-hidden',String(!flipped));
      material?.refresh();
      if(options.onFlip) options.onFlip(flipped);
    };
    setFlipped(flipped);
    let down=null,dragged=false,frame=0,aimX=0,aimY=0;
    const resetTilt=()=>{
      cancelAnimationFrame(frame);button.classList.remove('is-interacting');
      button.style.setProperty('--tilt-x','0deg');button.style.setProperty('--tilt-y','0deg');
      button.style.setProperty('--holo-x','0px');button.style.setProperty('--holo-y','0px');button.style.setProperty('--holo-opacity','.15');
      button.style.setProperty('--art-x','0px');button.style.setProperty('--art-y','0px');
      button.style.setProperty('--text-x','0px');button.style.setProperty('--text-y','0px');
      button.style.setProperty('--surface-active','0');aimX=0;aimY=0;material?.set(0,0,false);
      button.style.setProperty('--view-x','0');button.style.setProperty('--view-y','0');
    };
    const applyTilt=(x,y)=>{
      if(reduced.matches)return;
      aimX=Math.max(-1,Math.min(1,x));aimY=Math.max(-1,Math.min(1,y));
      cancelAnimationFrame(frame);
      frame=requestAnimationFrame(()=>{
        button.classList.add('is-interacting');
        const tiltMax=options.preview?20:17;
        button.style.setProperty('--tilt-x',(-aimY*tiltMax).toFixed(2)+'deg');button.style.setProperty('--tilt-y',(aimX*tiltMax).toFixed(2)+'deg');
        button.style.setProperty('--holo-x',(aimX*button.clientWidth*.35).toFixed(1)+'px');button.style.setProperty('--holo-y',(aimY*button.clientHeight*.25).toFixed(1)+'px');
        button.style.setProperty('--holo-opacity','.58');button.style.setProperty('--surface-active','1');
        button.style.setProperty('--glare-x',((aimX+1)*50).toFixed(1)+'%');button.style.setProperty('--glare-y',((aimY+1)*50).toFixed(1)+'%');
        button.style.setProperty('--art-x',(-aimX*6).toFixed(2)+'px');button.style.setProperty('--art-y',(-aimY*6).toFixed(2)+'px');
        button.style.setProperty('--text-x',(aimX*4).toFixed(2)+'px');button.style.setProperty('--text-y',(aimY*4).toFixed(2)+'px');
        button.style.setProperty('--foil-angle',(118+aimX*36+aimY*22).toFixed(1)+'deg');
        button.style.setProperty('--view-x',aimX.toFixed(4));button.style.setProperty('--view-y',aimY.toFixed(4));
        material?.set(aimX,aimY,true);
      });
    };
    button.addEventListener('pointerdown',event=>{
      down={x:event.clientX,y:event.clientY};dragged=false;
      if(options.preview&&event.pointerType==='touch')button.setPointerCapture(event.pointerId);
    });
    button.addEventListener('pointermove',event=>{
      if(down&&Math.hypot(event.clientX-down.x,event.clientY-down.y)>8)dragged=true;
      if(event.pointerType==='touch'&&(!options.preview||!down))return;
      const bounds=button.getBoundingClientRect();
      applyTilt(((event.clientX-bounds.left)/bounds.width-.5)*2,((event.clientY-bounds.top)/bounds.height-.5)*2);
    });
    button.addEventListener('pointerleave',()=>{down=null;resetTilt();});
    button.addEventListener('pointercancel',()=>{down=null;dragged=false;resetTilt();});
    button.addEventListener('pointerup',event=>{down=null;if(event.pointerType==='touch')resetTilt();});
    button.addEventListener('blur',resetTilt);
    button.addEventListener('keydown',event=>{
      if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))return;
      event.preventDefault();
      applyTilt(aimX+(event.key==='ArrowRight'?.25:event.key==='ArrowLeft'?-.25:0),aimY+(event.key==='ArrowDown'?.25:event.key==='ArrowUp'?-.25:0));
    });
    button.addEventListener('click',event=>{
      if(dragged&&event.detail){dragged=false;return;}
      $('#memory-gallery').classList.add('is-discovered');setFlipped(!flipped);
    });
    reduced.addEventListener('change',resetTilt);
    return {button,setFlipped,dispose(){cancelAnimationFrame(frame);reduced.removeEventListener('change',resetTilt);material?.dispose();}};
  }
  config.memories.forEach((item,index)=>{
    const article=document.createElement('article');article.className='memory-card';
    const inline=createFlashCard(item,{guide:index===0});
    inline.button.setAttribute('aria-describedby','flash-instruction');
    article.append(inline.button);
    $('#memory-gallery').append(article);
  });

  const trailer=$('#trailer-dialog');const trailerVideo=$('#trailer-video');
  const trailerPlayer=$('#trailer-player');
  let trailerAttempt=0,trailerFullscreen=false,trailerOrientation=false;
  const fullscreenElement=()=>document.fullscreenElement||document.webkitFullscreenElement;
  const exitTrailerFullscreen=()=>{
    if(fullscreenElement()!==trailerPlayer)return;
    try{const result=document.exitFullscreen?.()||document.webkitExitFullscreen?.();result?.catch(()=>{});}catch{}
  };
  const unlockTrailer=()=>{
    if(!trailerOrientation)return;trailerOrientation=false;
    try{screen.orientation?.unlock?.();}catch{}
  };
  const fitTrailer=()=>{
    if(!trailer.open||!trailer.classList.contains('landscape-playback'))return;
    const box=trailerPlayer.getBoundingClientRect(),rotate=box.height>box.width;
    trailerPlayer.style.setProperty('--player-width',(rotate?box.height:box.width)+'px');
    trailerPlayer.style.setProperty('--player-height',(rotate?box.width:box.height)+'px');
    trailerPlayer.style.setProperty('--player-rotation',rotate?'90deg':'0deg');
    trailer.dataset.rotated=String(rotate);
  };
  const landscapeTrailer=attempt=>{
    fitTrailer();
    // A narrow desktop window uses the rotated page player; touch devices may
    // additionally enter native fullscreen and lock the physical screen.
    if(!matchMedia('(pointer:coarse)').matches)return;
    // Request the screen while the original click still grants user activation.
    try{
      const request=trailerPlayer.requestFullscreen?trailerPlayer.requestFullscreen({navigationUI:'hide'}):trailerPlayer.webkitRequestFullscreen?.();
      Promise.resolve(request).then(async()=>{
        if(attempt!==trailerAttempt||!trailer.open){if(!trailer.open)exitTrailerFullscreen();return;}
        trailerFullscreen=fullscreenElement()===trailerPlayer;fitTrailer();
        if(trailerFullscreen&&screen.orientation?.lock){
          trailerOrientation=true;
          try{await screen.orientation.lock('landscape');}catch{}
          if(!trailer.open)unlockTrailer();
          else if(attempt===trailerAttempt)fitTrailer();
        }
      }).catch(()=>{if(attempt===trailerAttempt)fitTrailer();});
    }catch{fitTrailer();}
  };
  const trailerFullscreenChanged=()=>{
    if(fullscreenElement()===trailerPlayer){trailerFullscreen=true;fitTrailer();}
    else if(trailerFullscreen){trailerFullscreen=false;if(trailer.open)trailer.close();}
  };
  document.addEventListener('fullscreenchange',trailerFullscreenChanged);
  document.addEventListener('webkitfullscreenchange',trailerFullscreenChanged);
  addEventListener('resize',fitTrailer,{passive:true});
  window.visualViewport?.addEventListener('resize',fitTrailer,{passive:true});
  $$('[data-trailer]').forEach(button=>button.addEventListener('click',()=>{
    const attempt=++trailerAttempt;
    heroWasPlaying=!heroVideo.paused;pauseHero();featureVideo.pause();
    const landscape=matchMedia('(max-width:700px), (pointer:coarse) and (max-height:700px)').matches;
    trailer.classList.toggle('landscape-playback',landscape);
    if(landscape)trailerVideo.controlsList?.add('nofullscreen');
    trailerVideo.src=config.trailer;$('#trailer-error').hidden=true;openDialog(trailer);
    trailerVideo.play().catch(()=>{if(attempt===trailerAttempt&&trailer.open)$('#trailer-error').hidden=false;});
    if(landscape)landscapeTrailer(attempt);
  }));
  trailerVideo.addEventListener('error',()=>{$('#trailer-error').hidden=false;});
  trailer.addEventListener('close',()=>{
    trailerAttempt++;trailerFullscreen=false;unlockTrailer();exitTrailerFullscreen();
    trailer.classList.remove('landscape-playback');delete trailer.dataset.rotated;
    trailerPlayer.style.removeProperty('--player-width');trailerPlayer.style.removeProperty('--player-height');trailerPlayer.style.removeProperty('--player-rotation');
    trailerVideo.controlsList?.remove('nofullscreen');
    trailerVideo.pause();trailerVideo.removeAttribute('src');trailerVideo.load();
    if(heroWasPlaying&&heroVisible&&!heroManualPaused&&!document.hidden)startHero();
  });
  document.addEventListener('visibilitychange',()=>{
    if(document.hidden){pauseHero({poster:true});featureVideo.pause();trailerVideo.pause();}
    else if(heroVisible&&!heroManualPaused&&!reduced.matches&&!trailer.open&&!connection?.saveData)startHero();
  });

  const onScroll=()=>{
    const y=window.scrollY;$('#header').classList.toggle('scrolled',y>40);
    $('#mobile-download').classList.toggle('show',y>$('#home').offsetHeight-100);
  };
  addEventListener('scroll',onScroll,{passive:true});onScroll();
  if('IntersectionObserver' in window){
    if(!reduced.matches){
      const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('visible');observer.unobserve(entry.target);}}),{threshold:.08});
      $$('.reveal').forEach(element=>observer.observe(element));document.documentElement.classList.add('motion-ready');
    }
    const setHeroVisible=visible=>{
      heroVisible=visible;
      if(!heroVisible)pauseHero({poster:true});
      else if(!heroManualPaused&&!reduced.matches&&!connection?.saveData&&!trailer.open&&!document.hidden)startHero();
    };
    if(document.documentElement.classList.contains('panel-interface')){
      document.addEventListener('stellae:panelchange',event=>{
        setHeroVisible(event.detail.id==='home');
        if(event.detail.id!=='experience')featureVideo.pause();
      });
    }else{
      const heroObserver=new IntersectionObserver(entries=>setHeroVisible(entries[0].isIntersecting),{threshold:.05});heroObserver.observe($('#home'));
    }
    const featureObserver=new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)featureVideo.pause();},{threshold:.05});featureObserver.observe(featureVideo);
    if(!document.documentElement.classList.contains('panel-interface')){const navObserver=new IntersectionObserver(entries=>{
      entries.forEach(entry=>{if(entry.isIntersecting){$$('.desktop-nav a').forEach(link=>{if(link.hash==='#'+entry.target.id)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});}});
    },{rootMargin:'-20% 0px -55% 0px',threshold:0});
    $$('.desktop-nav a').forEach(link=>{const section=$(link.hash);if(section)navObserver.observe(section);});}
  }
})();
