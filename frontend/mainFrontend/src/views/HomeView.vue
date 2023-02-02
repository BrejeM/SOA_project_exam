<template>
  <div class="home">
    <img alt="Vue logo" width="200" height="200" src="../assets/snoo.png">
    <HelloWorld msg="Welcome to the Reddit TrustScore"/>
    
  </div>
</template>

<script>
// @ is an alias to /src
import HelloWorld from 'E:/UBB/SOA/redditAPI/frontend/own/reddit_trust/src/components/HelloWorld.vue'
//import ReactButton from '@/components/ReactButton.js';

export default {
  name: 'HomeView',
  components: {
    HelloWorld
  }
}
</script>
