Page({
  data: {
    url: 'https://lib.cuit.edu.cn/'
  },

  onLoad(options) {
    if (options.url) {
      this.setData({ url: decodeURIComponent(options.url) });
    }
  },

  onMessage(e) {
    console.log('WebView message:', e.detail);
  }
});
