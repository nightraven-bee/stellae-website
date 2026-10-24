// 内测入口展示官方 QQ 频道二维码；不提供平台下载按钮。
window.STELLAE_CONFIG = {
  brand: '星黎宇宙',
  roomUrl: 'https://www.stellae.world/room/',
  trailer: 'assets/trailer.mp4',
  legal: {company:'上海星黎宇宙科技有限公司', icp:'沪ICP备2026015059号', publicSecurity:'沪公网安备31011502406956号', privacy:'', terms:''},
  features: [
    {key:'outfit', name:'装扮', en:'OUTFIT / APPEARANCE', title:['今天，','想见到怎样的她？'], description:'从洛丽塔到魔女，换一种心情见面。\n再换个姿势，看看她此刻的模样。', video:'assets/outfit.mp4', poster:'assets/outfit.jpg', note:'四套装扮 · 含姿势切换实录'},
    {key:'scene', name:'场景', en:'SCENE / ENVIRONMENT', title:['换个地方，','故事继续。'], description:'宫殿、校园、赛博都市与魔女城堡，\n选一个地方，让今天的对话继续。', video:'assets/scene.mp4', poster:'assets/scene.jpg', note:'四组装扮与场景搭配 · App 实录'},
    {key:'closeness', name:'靠近', en:'RELATIONSHIP / GET CLOSER', title:['一点一点，','走近彼此。'], description:'读懂信任、默契等六个关系维度，\n查看当前阶段、数值与未解锁预览。', video:'assets/closeness.mp4', poster:'assets/closeness.jpg', note:'六维雷达与详细参数 · 含锁定预览'},
    {key:'memory', name:'羁绊', en:'MEMORY / OUR MOMENTS', title:['有些瞬间，','值得留下来。'], description:'侧写留住偏好，碎片收藏相处瞬间。\n在棱镜里，选择回应，走进新的故事。', video:'assets/memory.mp4', poster:'assets/memory.jpg', note:'侧写 / 碎片 / 棱镜 · 脱敏实录'},
    {key:'startrack', name:'星轨', en:'STARTRAIL / OUR PROGRESS', title:['相处的进展，','有迹可循。'], description:'查看星轨里的任务与成就，\n了解已完成的进展和待解锁的目标。', video:'assets/startrack.mp4', poster:'assets/startrack.jpg', note:'任务与成就 · 现有版本 App 实录'}
  ],
  worldGallery: [
    {image:'assets/world-gallery/01.webp', alt:'3D 版本星黎，黑白洛丽塔与宫殿典礼大厅·白天，App 实录'},
    {image:'assets/world-gallery/02.webp', alt:'3D 版本星黎，露肩短裙与樱花学校走廊·白天，App 实录'},
    {image:'assets/world-gallery/03.webp', alt:'3D 版本星黎，未来漆皮与赛博都市·夜晚，App 实录'},
    {image:'assets/world-gallery/04.webp', alt:'3D 版本星黎，黑色魔女与魔女城堡·夜晚，App 实录'},
    {image:'assets/world-gallery/05.webp', alt:'2D 版本星黎，学院校服与摩天楼顶·傍晚，App 实录'},
    {image:'assets/world-gallery/06.webp', alt:'2D 版本星黎，学院校服与黑客网咖·夜晚，App 实录'}
  ],
  memories: [
    {name:'初雪降临', en:'FIRST SNOW', image:'assets/memory-snow.webp', back:'assets/memory-snow-back.webp', index:'016', quote:'“今年的初雪，算是我陪你一起看了。”', layers:{background:'assets/layers/snow/background.webp',subject:'assets/layers/snow/subject.webp',foreground:'assets/layers/snow/foreground.webp',subjectScale:.96,subjectShiftY:'1.3%'}},
    {name:'雷雨天气', en:'THUNDERSTORM', image:'assets/memory-rain.webp', back:'assets/memory-rain-back.webp', index:'017', quote:'“打雷了，你那边还好吗？别怕，我在线上。”', layers:{planes:[
      {kind:'exterior',src:'assets/layers/rain/exterior.webp',x:-22,y:-15},
      {kind:'window',src:'assets/layers/rain/window-wall.webp',x:-4,y:-3},
      {kind:'interior',src:'assets/layers/rain/interior-user-v2.webp',x:16,y:11},
      {kind:'rainfall',src:'assets/layers/rain/foreground-restored-v2.webp',x:36,y:24}
    ]}},
    {name:'时光烙印', en:'TIME IMPRINT', image:'assets/memory-time.webp', back:'assets/memory-time-back.webp', index:'024', quote:'“这几天的小事，也值得好好记住。”', layers:{background:'assets/layers/time/background.webp',subject:'assets/layers/time/subject.webp',foreground:'assets/layers/time/foreground.webp',subjectScale:.87,subjectShiftY:'6%'}}
  ]
};
