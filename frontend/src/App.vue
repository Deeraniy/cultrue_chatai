<template>
  <div id="app">
    <nav class="pixel-navbar">
      <router-link to="/" class="nav-link">文学智能推荐</router-link>
      <router-link to="/plan" class="nav-link">阅读计划跟踪</router-link>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
// Vue 3 setup script，无需export default
</script>

<style>
body {
  font-family: 'WeiWeiPixel', 'Press Start 2P', 'Pixel', monospace;
}
.pixel-navbar {
  display: flex;
  align-items: center;
  padding: 0 32px;
  height: 56px;
  background: url('@/assets/kenney_pixel-ui-pack/9-Slice/Ancient/white.png') repeat;
  border: 4px solid transparent;
  border-image: url('@/assets/kenney_pixel-ui-pack/9-Slice/Outline/blue.png') 4 repeat;
  font-family: 'Press Start 2P', 'Pixel', monospace;
  font-size: 18px;
  letter-spacing: 1px;
  margin-bottom: 16px;
}
.nav-link {
  color: #409eff;
  text-decoration: none;
  margin-right: 32px;
  font-family: inherit;
  transition: color 0.2s;
}
.nav-link.router-link-exact-active {
  color: #faad14;
  text-shadow: 1px 1px 0 #fff, 2px 2px 0 #d9bfa3;
}
</style>
