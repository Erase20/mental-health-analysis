module.exports = {
  css: {
    loaderOptions: {
      scss: {
        sassOptions: {
          api: 'modern-compiler' // 强制使用新版 API，消除 legacy 警告
        }
      }
    }
  }
}