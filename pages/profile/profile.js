 const API_BASE_URL = 'http://127.0.0.1:8080';
 
 Page({
   data: {
     userInfo: {},
     stats: { totalFiles: 0, noticeCount: 8, faqCount: 12 }
   },
 
   onShow() {
     const userInfo = wx.getStorageSync('userInfo') || {};
     this.setData({ userInfo });
     if (userInfo.username) {
       this.loadStats(userInfo.username);
     }
   },
 
    goBack() { wx.navigateBack(); },
    goLogin() { wx.navigateTo({ url: '/pages/login/login' }); },
 
   loadStats(username) {
     wx.request({
       url: `${API_BASE_URL}/api/student/${username}`,
       method: 'GET',
       timeout: 10000,
       success: (res) => {
         if (res.data && res.data.success) {
           this.setData({ stats: { ...this.data.stats, totalFiles: res.data.data.total_files } });
         }
       },
       fail: () => {}
     });
   },
 
   onRefreshData() {
     if (!this.data.userInfo.username) {
       wx.showToast({ title: '请先登录', icon: 'none' });
       return;
     }
     wx.showLoading({ title: '正在刷新数据...', mask: true });
     wx.request({
       url: `${API_BASE_URL}/api/refresh`,
       method: 'POST',
       data: { username: this.data.userInfo.username, password: '' },
       header: { 'Content-Type': 'application/json' },
       timeout: 60000,
       success: (res) => {
         wx.hideLoading();
         if (res.data && res.data.success && res.data.task_id) {
           wx.showToast({ title: '数据刷新任务已提交', icon: 'success' });
         } else {
           wx.showToast({ title: '刷新失败', icon: 'none' });
         }
       },
       fail: () => {
         wx.hideLoading();
         wx.showToast({ title: '网络错误', icon: 'none' });
       }
     });
   },
 
   onClearCache() {
     wx.showModal({
       title: '清除缓存',
       content: '确定要清除本地缓存数据吗？',
       success: (res) => {
         if (res.confirm) {
           wx.clearStorageSync();
           this.setData({ userInfo: {}, stats: { totalFiles: 0, noticeCount: 8, faqCount: 12 } });
           wx.showToast({ title: '缓存已清除', icon: 'success' });
         }
       }
     });
   },
 
   onAbout() {
     wx.showModal({
       title: '关于系统',
       content: '校园信息智能查询智能体 v2.0\n基于微信小程序 + FastAPI + GLM-4.6V 开发\n支持：课程查询、成绩查询、考试安排、校园通知、校园导航、图书馆查询等功能。',
       confirmText: '确定'
     });
   },
 
   onLogout() {
     wx.showModal({
       title: '退出登录',
       content: '确定要退出当前账号吗？',
       success: (res) => {
         if (res.confirm) {
           wx.removeStorageSync('userInfo');
           this.setData({ userInfo: {} });
           wx.showToast({ title: '已退出', icon: 'success' });
         }
       }
     });
   }
 });
