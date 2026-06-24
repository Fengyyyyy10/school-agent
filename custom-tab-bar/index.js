const PAGE_MAP = {
  chat: '/pages/chat/chat',
  campus: '/pages/campus/campus',
  profile: '/pages/profile/profile'
};

Component({
  properties: {},
  data: {
    active: 'chat'
  },
  lifetimes: {
    attached() {
      const pages = getCurrentPages();
      const current = pages[pages.length - 1];
      if (current) {
        const route = current.route || '';
        for (const [key, path] of Object.entries(PAGE_MAP)) {
          if (route.includes(key)) {
            this.setData({ active: key });
            break;
          }
        }
      }
    }
  },
  pageLifetimes: {
    show() {
      const pages = getCurrentPages();
      const current = pages[pages.length - 1];
      if (current) {
        const route = current.route || '';
        for (const [key, path] of Object.entries(PAGE_MAP)) {
          if (route.includes(key)) {
            this.setData({ active: key });
            break;
          }
        }
      }
    }
  },
  methods: {
    switchTab(e) {
      const path = e.currentTarget.dataset.path;
      const url = PAGE_MAP[path];
      if (url) {
        wx.switchTab({ url });
      }
    }
  }
});
